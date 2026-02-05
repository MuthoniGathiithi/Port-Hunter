"""
Student Registration Router
Handles student face registration with liveness detection
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.models import (
    StudentRegistrationStart,
    LivenessVideoData,
    LivenessDetectionResult,
    StudentResponse,
    SuccessResponse
)
from app.utils.security import verify_registration_token
from app.services.liveness_detection import liveness_detector
import logging
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/register", tags=["Student Registration"])


@router.get("/verify-token/{registration_token}")
async def verify_token(
    registration_token: str,
    db=Depends(get_db)
):
    """
    Verify registration token and get unit information
    Public endpoint - no authentication required
    """
    try:
        unit = verify_registration_token(registration_token, db)
        
        return {
            "valid": True,
            "unit_name": unit['unit_name'],
            "unit_code": unit['unit_code'],
            "message": "Registration link is valid"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token verification error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to verify token"
        )


@router.post("/start", response_model=SuccessResponse)
async def start_registration(
    registration_data: StudentRegistrationStart,
    db=Depends(get_db)
):
    """
    Start student registration process
    Validates token and checks for duplicate admission number
    """
    try:
        # Verify token
        unit = verify_registration_token(registration_data.registration_token, db)
        
        # Check if student already registered in this unit
        existing = db.table('students')\
            .select('id')\
            .eq('unit_id', unit['id'])\
            .eq('admission_number', registration_data.admission_number)\
            .execute()
        
        if existing.data and len(existing.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This admission number is already registered in this unit"
            )
        
        return SuccessResponse(
            message="Ready to proceed with liveness detection",
            data={
                "unit_id": unit['id'],
                "unit_name": unit['unit_name']
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration start error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start registration"
        )


@router.post("/liveness-check", response_model=LivenessDetectionResult)
async def check_liveness(
    liveness_data: LivenessVideoData,
    db=Depends(get_db)
):
    """
    Process liveness detection video frames
    This endpoint receives frames grouped by pose type
    """
    try:
        # Verify token
        unit = verify_registration_token(liveness_data.registration_token, db)
        
        # Group frames by pose
        frames_by_pose = liveness_detector.group_frames_by_pose([
            {
                'pose_type': frame.pose_type,
                'frame_data': frame.frame_data
            }
            for frame in liveness_data.frames
        ])
        
        # Process liveness detection
        result = liveness_detector.process_liveness_video(frames_by_pose)
        
        if not result['is_live']:
            return LivenessDetectionResult(
                is_live=False,
                poses_detected=result['poses_detected'],
                quality_scores={},
                embeddings=[],
                message=result['message']
            )
        
        # Convert embeddings to serializable format
        embeddings_list = [emb.tolist() for emb in result['embeddings']]
        
        return LivenessDetectionResult(
            is_live=True,
            poses_detected=result['poses_detected'],
            quality_scores={},
            embeddings=embeddings_list,
            message=result['message']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Liveness check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Liveness detection failed: {str(e)}"
        )


@router.post("/complete", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def complete_registration(
    registration_data: dict,  # Contains: registration_token, full_name, admission_number, embeddings
    db=Depends(get_db)
):
    """
    Complete student registration after successful liveness check
    Stores student data and embeddings in database
    """
    try:
        # Extract data
        registration_token = registration_data.get('registration_token')
        full_name = registration_data.get('full_name')
        admission_number = registration_data.get('admission_number')
        embeddings = registration_data.get('embeddings', [])
        
        if not all([registration_token, full_name, admission_number, embeddings]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing required fields"
            )
        
        # Verify token
        unit = verify_registration_token(registration_token, db)
        
        # Check for duplicates again (double-check)
        existing = db.table('students')\
            .select('id')\
            .eq('unit_id', unit['id'])\
            .eq('admission_number', admission_number)\
            .execute()
        
        if existing.data and len(existing.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admission number already registered"
            )
        
        # Prepare embeddings data
        embeddings_json = json.dumps(embeddings)
        
        # Insert student
        result = db.table('students').insert({
            'unit_id': unit['id'],
            'admission_number': admission_number,
            'full_name': full_name,
            'embeddings': embeddings_json,
            'registration_metadata': json.dumps({
                'total_embeddings': len(embeddings),
                'poses_captured': ['center', 'tilt_down', 'turn_right', 'turn_left']
            }),
            'is_active': True
        }).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to save student data"
            )
        
        student = result.data[0]
        
        logger.info(
            f"Student registered: {full_name} ({admission_number}) in unit {unit['unit_name']}"
        )
        
        return StudentResponse(
            id=student['id'],
            unit_id=student['unit_id'],
            admission_number=student['admission_number'],
            full_name=student['full_name'],
            is_active=student['is_active'],
            created_at=student['created_at']
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration completion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to complete registration"
        )


@router.get("/instructions")
async def get_registration_instructions():
    """
    Get liveness detection instructions for the frontend
    """
    return {
        "instructions": [
            {
                "pose_type": "center",
                "title": "Look Straight Ahead",
                "description": "Face the camera directly and keep your head still",
                "duration_seconds": 2
            },
            {
                "pose_type": "tilt_down",
                "title": "Tilt Your Head Down",
                "description": "Slowly tilt your head down, looking at the bottom of the screen",
                "duration_seconds": 2
            },
            {
                "pose_type": "turn_right",
                "title": "Turn Your Head Right",
                "description": "Slowly turn your head to your right side",
                "duration_seconds": 2
            },
            {
                "pose_type": "turn_left",
                "title": "Turn Your Head Left",
                "description": "Slowly turn your head to your left side",
                "duration_seconds": 2
            }
        ],
        "requirements": [
            "Ensure good lighting",
            "Remove glasses or face coverings",
            "Keep face centered in frame",
            "Follow each instruction smoothly"
        ]
    }