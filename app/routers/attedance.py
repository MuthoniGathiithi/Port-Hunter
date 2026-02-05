"""
Attendance Router
Handles classroom photo processing and attendance marking
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from app.database import get_db
from app.models import (
    AttendanceCreate,
    AttendanceSessionResponse,
    AttendanceDetailResponse,
    AttendanceRecordResponse,
    UnknownFaceResponse,
    ProcessingStatus
)
from app.utils.security import get_current_lecturer
from app.services.face_detection import face_detector
from app.services.face_normalization import face_normalizer
from app.services.face_recognition import face_recognizer
from app.services.matching import face_matcher
from typing import List
from datetime import datetime, date, time
import json
import base64
import logging
import uuid

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/attendance", tags=["Attendance"])


async def process_attendance_background(
    session_id: str,
    unit_id: str,
    classroom_photos: List[str],
    db
):
    """
    Background task to process attendance
    Updates session status as it progresses
    """
    try:
        # Update status to processing
        db.table('attendance_sessions')\
            .update({'processing_status': 'processing'})\
            .eq('id', session_id)\
            .execute()
        
        # Get all registered students in unit
        students_result = db.table('students')\
            .select('*')\
            .eq('unit_id', unit_id)\
            .eq('is_active', True)\
            .execute()
        
        registered_students = students_result.data if students_result.data else []
        
        # Parse embeddings from JSON
        for student in registered_students:
            if isinstance(student.get('embeddings'), str):
                student['embeddings'] = json.loads(student['embeddings'])
        
        logger.info(f"Processing {len(classroom_photos)} photos for {len(registered_students)} registered students")
        
        # Process each classroom photo
        all_results = []
        
        for photo_idx, photo_base64 in enumerate(classroom_photos):
            logger.info(f"Processing photo {photo_idx + 1}/{len(classroom_photos)}")
            
            try:
                # Detect faces
                cropped_faces, landmarks, metadata = face_detector.detect_faces_in_image(photo_base64)
                
                if len(cropped_faces) == 0:
                    logger.warning(f"No faces detected in photo {photo_idx + 1}")
                    continue
                
                logger.info(f"Detected {len(cropped_faces)} faces in photo {photo_idx + 1}")
                
                # Normalize faces
                normalized_faces = face_normalizer.normalize_face_list(cropped_faces, landmarks)
                
                # Extract embeddings
                embeddings = face_recognizer.extract_embeddings_from_list(normalized_faces)
                
                if len(embeddings) == 0:
                    logger.warning(f"No embeddings extracted from photo {photo_idx + 1}")
                    continue
                
                logger.info(f"Extracted {len(embeddings)} embeddings from photo {photo_idx + 1}")
                
                # Match faces with registered students
                photo_results = face_matcher.process_attendance(
                    embeddings,
                    metadata,
                    registered_students
                )
                
                all_results.append(photo_results)
            
            except Exception as e:
                logger.error(f"Error processing photo {photo_idx + 1}: {e}")
                continue
        
        # Merge results from all photos
        if len(all_results) > 0:
            final_results = face_matcher.merge_results_from_multiple_photos(all_results)
        else:
            final_results = {
                'total_registered': len(registered_students),
                'total_present': 0,
                'total_absent': len(registered_students),
                'total_unknown_faces': 0,
                'present_students': [],
                'absent_students': [],
                'unknown_faces': []
            }
        
        # Save attendance records for present students
        for student_data in final_results['present_students']:
            db.table('attendance_records').insert({
                'session_id': session_id,
                'student_id': student_data['student_id'],
                'status': 'present',
                'confidence_score': student_data.get('similarity_score'),
                'detected_face_data': json.dumps({
                    'bbox': student_data.get('bbox'),
                    'detection_confidence': student_data.get('detection_confidence')
                })
            }).execute()
        
        # Save attendance records for absent students
        for student_data in final_results['absent_students']:
            db.table('attendance_records').insert({
                'session_id': session_id,
                'student_id': student_data['student_id'],
                'status': 'absent',
                'confidence_score': None,
                'detected_face_data': None
            }).execute()
        
        # Save unknown faces (with cropped face images)
        # Note: In production, you'd upload these to Supabase Storage
        # For now, we'll store the base64 data temporarily
        for unknown_face in final_results['unknown_faces']:
            # Here you would upload to Supabase Storage and get URL
            # For now, using placeholder
            cropped_face_url = f"unknown_face_{uuid.uuid4()}.jpg"
            
            db.table('unknown_faces').insert({
                'session_id': session_id,
                'cropped_face_url': cropped_face_url,
                'bbox': json.dumps(unknown_face.get('bbox', {})),
                'confidence_score': unknown_face.get('detection_confidence'),
                'embedding': json.dumps(unknown_face.get('embedding', []))
            }).execute()
        
        # Update session with final counts
        db.table('attendance_sessions')\
            .update({
                'total_students_registered': final_results['total_registered'],
                'total_present': final_results['total_present'],
                'total_absent': final_results['total_absent'],
                'total_unknown_faces': final_results['total_unknown_faces'],
                'processing_status': 'completed'
            })\
            .eq('id', session_id)\
            .execute()
        
        logger.info(f"Attendance processing completed for session {session_id}")
    
    except Exception as e:
        logger.error(f"Attendance processing failed: {e}")
        
        # Update status to failed
        db.table('attendance_sessions')\
            .update({'processing_status': 'failed'})\
            .eq('id', session_id)\
            .execute()


@router.post("", response_model=AttendanceSessionResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_attendance_session(
    attendance_data: AttendanceCreate,
    background_tasks: BackgroundTasks,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Create new attendance session and start processing
    Returns immediately with session ID while processing in background
    """
    try:
        # Verify unit ownership
        unit_result = db.table('units')\
            .select('*')\
            .eq('id', str(attendance_data.unit_id))\
            .eq('lecturer_id', lecturer['id'])\
            .execute()
        
        if not unit_result.data or len(unit_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        
        unit = unit_result.data[0]
        
        # Create attendance session
        now = datetime.now()
        
        session_result = db.table('attendance_sessions').insert({
            'unit_id': str(attendance_data.unit_id),
            'lecturer_id': lecturer['id'],
            'session_date': now.date().isoformat(),
            'session_time': now.time().isoformat(),
            'classroom_photos': json.dumps(attendance_data.classroom_photos),
            'processing_status': 'pending'
        }).execute()
        
        if not session_result.data or len(session_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create attendance session"
            )
        
        session = session_result.data[0]
        
        logger.info(f"Attendance session created: {session['id']} for unit {unit['unit_name']}")
        
        # Start background processing
        background_tasks.add_task(
            process_attendance_background,
            session['id'],
            str(attendance_data.unit_id),
            attendance_data.classroom_photos,
            db
        )
        
        return AttendanceSessionResponse(
            id=session['id'],
            unit_id=session['unit_id'],
            unit_name=unit['unit_name'],
            session_date=session['session_date'],
            session_time=session['session_time'],
            total_students_registered=0,
            total_present=0,
            total_absent=0,
            total_unknown_faces=0,
            processing_status='pending',
            created_at=session['created_at']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Attendance session creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create attendance session"
        )


@router.get("/sessions", response_model=List[AttendanceSessionResponse])
async def get_attendance_sessions(
    unit_id: str = None,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Get attendance sessions for lecturer
    Optionally filter by unit_id
    """
    try:
        query = db.table('attendance_sessions')\
            .select('*, units!inner(unit_name)')\
            .eq('lecturer_id', lecturer['id'])\
            .order('created_at', desc=True)
        
        if unit_id:
            query = query.eq('unit_id', unit_id)
        
        result = query.execute()
        
        sessions = []
        for session in (result.data if result.data else []):
            unit_name = session.get('units', {}).get('unit_name', 'Unknown Unit')
            sessions.append(AttendanceSessionResponse(
                id=session['id'],
                unit_id=session['unit_id'],
                unit_name=unit_name,
                session_date=session['session_date'],
                session_time=session['session_time'],
                total_students_registered=session.get('total_students_registered', 0),
                total_present=session.get('total_present', 0),
                total_absent=session.get('total_absent', 0),
                total_unknown_faces=session.get('total_unknown_faces', 0),
                processing_status=session['processing_status'],
                created_at=session['created_at']
            ))
        
        return sessions
    
    except Exception as e:
        logger.error(f"Error fetching attendance sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch attendance sessions"
        )


@router.get("/sessions/{session_id}", response_model=AttendanceDetailResponse)
async def get_attendance_details(
    session_id: str,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Get detailed attendance information for a session
    """
    try:
        # Get session
        session_result = db.table('attendance_sessions')\
            .select('*, units!inner(unit_name)')\
            .eq('id', session_id)\
            .eq('lecturer_id', lecturer['id'])\
            .execute()
        
        if not session_result.data or len(session_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Attendance session not found"
            )
        
        session = session_result.data[0]
        unit_name = session.get('units', {}).get('unit_name', 'Unknown Unit')
        
        # Get attendance records
        records_result = db.table('attendance_records')\
            .select('*, students(admission_number, full_name)')\
            .eq('session_id', session_id)\
            .execute()
        
        records = []
        for record in (records_result.data if records_result.data else []):
            student_info = record.get('students', {})
            records.append(AttendanceRecordResponse(
                student_id=record.get('student_id'),
                student_name=student_info.get('full_name'),
                admission_number=student_info.get('admission_number'),
                status=record['status'],
                confidence_score=record.get('confidence_score')
            ))
        
        # Get unknown faces
        unknown_result = db.table('unknown_faces')\
            .select('*')\
            .eq('session_id', session_id)\
            .execute()
        
        unknown_faces = []
        for unknown in (unknown_result.data if unknown_result.data else []):
            bbox = json.loads(unknown['bbox']) if isinstance(unknown['bbox'], str) else unknown['bbox']
            unknown_faces.append(UnknownFaceResponse(
                id=unknown['id'],
                cropped_face_url=unknown['cropped_face_url'],
                bbox=bbox,
                confidence_score=unknown.get('confidence_score', 0.0)
            ))
        
        # Parse classroom photos
        classroom_photos = json.loads(session['classroom_photos']) if isinstance(session['classroom_photos'], str) else session['classroom_photos']
        
        return AttendanceDetailResponse(
            id=session['id'],
            unit_id=session['unit_id'],
            unit_name=unit_name,
            session_date=session['session_date'],
            session_time=session['session_time'],
            total_students_registered=session.get('total_students_registered', 0),
            total_present=session.get('total_present', 0),
            total_absent=session.get('total_absent', 0),
            total_unknown_faces=session.get('total_unknown_faces', 0),
            processing_status=session['processing_status'],
            created_at=session['created_at'],
            records=records,
            unknown_faces=unknown_faces,
            classroom_photos=classroom_photos
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching attendance details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch attendance details"
        )


@router.get("/sessions/{session_id}/status", response_model=ProcessingStatus)
async def get_processing_status(
    session_id: str,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Check processing status of an attendance session
    Used for polling by frontend
    """
    try:
        session_result = db.table('attendance_sessions')\
            .select('processing_status, total_present, total_absent')\
            .eq('id', session_id)\
            .eq('lecturer_id', lecturer['id'])\
            .execute()
        
        if not session_result.data or len(session_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Session not found"
            )
        
        session = session_result.data[0]
        status_value = session['processing_status']
        
        if status_value == 'pending':
            progress = 0.0
            message = "Waiting to start processing..."
        elif status_value == 'processing':
            progress = 0.5
            message = "Processing faces and matching students..."
        elif status_value == 'completed':
            progress = 1.0
            message = f"Complete! {session['total_present']} present, {session['total_absent']} absent"
        else:  # failed
            progress = 0.0
            message = "Processing failed. Please try again."
        
        return ProcessingStatus(
            status=status_value,
            progress=progress,
            message=message
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching processing status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch status"
        )