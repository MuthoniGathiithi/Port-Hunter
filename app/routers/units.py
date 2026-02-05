"""
Units Router
Handles unit/class creation and management
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.models import (
    UnitCreate,
    UnitResponse,
    UnitUpdate,
    UnitWithStats,
    SuccessResponse
)
from app.utils.security import get_current_lecturer
from typing import List
import secrets
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/units", tags=["Units"])


def generate_registration_token() -> str:
    """Generate a unique registration token"""
    return secrets.token_urlsafe(32)


@router.post("", response_model=UnitResponse, status_code=status.HTTP_201_CREATED)
async def create_unit(
    unit_data: UnitCreate,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Create a new unit/class
    Requires authentication
    """
    try:
        # Generate unique registration token
        registration_token = generate_registration_token()
        
        # Insert unit
        result = db.table('units').insert({
            'lecturer_id': lecturer['id'],
            'unit_name': unit_data.unit_name,
            'unit_code': unit_data.unit_code,
            'registration_token': registration_token,
            'is_active': True
        }).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create unit"
            )
        
        unit = result.data[0]
        
        logger.info(f"Unit created: {unit['unit_name']} by {lecturer['email']}")
        
        return UnitResponse(**unit)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unit creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create unit"
        )


@router.get("", response_model=List[UnitWithStats])
async def get_lecturer_units(
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Get all units for current lecturer with statistics
    """
    try:
        # Get units
        units_result = db.table('units')\
            .select('*')\
            .eq('lecturer_id', lecturer['id'])\
            .order('created_at', desc=True)\
            .execute()
        
        units = units_result.data if units_result.data else []
        
        # Enrich with statistics
        enriched_units = []
        for unit in units:
            # Count students
            students_result = db.table('students')\
                .select('id', count='exact')\
                .eq('unit_id', unit['id'])\
                .eq('is_active', True)\
                .execute()
            
            total_students = students_result.count if students_result.count else 0
            
            # Count sessions
            sessions_result = db.table('attendance_sessions')\
                .select('id,session_date', count='exact')\
                .eq('unit_id', unit['id'])\
                .order('session_date', desc=True)\
                .limit(1)\
                .execute()
            
            total_sessions = sessions_result.count if sessions_result.count else 0
            last_session_date = None
            if sessions_result.data and len(sessions_result.data) > 0:
                last_session_date = sessions_result.data[0].get('session_date')
            
            enriched_units.append(UnitWithStats(
                **unit,
                total_students=total_students,
                total_sessions=total_sessions,
                last_session_date=last_session_date
            ))
        
        return enriched_units
    
    except Exception as e:
        logger.error(f"Error fetching units: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch units"
        )


@router.get("/{unit_id}", response_model=UnitWithStats)
async def get_unit_details(
    unit_id: str,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Get detailed information about a specific unit
    """
    try:
        # Get unit
        unit_result = db.table('units')\
            .select('*')\
            .eq('id', unit_id)\
            .eq('lecturer_id', lecturer['id'])\
            .execute()
        
        if not unit_result.data or len(unit_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        
        unit = unit_result.data[0]
        
        # Get statistics
        students_result = db.table('students')\
            .select('id', count='exact')\
            .eq('unit_id', unit_id)\
            .eq('is_active', True)\
            .execute()
        
        sessions_result = db.table('attendance_sessions')\
            .select('id,session_date', count='exact')\
            .eq('unit_id', unit_id)\
            .order('session_date', desc=True)\
            .limit(1)\
            .execute()
        
        total_students = students_result.count if students_result.count else 0
        total_sessions = sessions_result.count if sessions_result.count else 0
        last_session_date = None
        if sessions_result.data and len(sessions_result.data) > 0:
            last_session_date = sessions_result.data[0].get('session_date')
        
        return UnitWithStats(
            **unit,
            total_students=total_students,
            total_sessions=total_sessions,
            last_session_date=last_session_date
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching unit details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch unit details"
        )


@router.patch("/{unit_id}", response_model=UnitResponse)
async def update_unit(
    unit_id: str,
    unit_update: UnitUpdate,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Update unit information
    """
    try:
        # Verify ownership
        unit_result = db.table('units')\
            .select('id')\
            .eq('id', unit_id)\
            .eq('lecturer_id', lecturer['id'])\
            .execute()
        
        if not unit_result.data or len(unit_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        
        # Build update data
        update_data = unit_update.dict(exclude_unset=True)
        
        if not update_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        # Update unit
        result = db.table('units')\
            .update(update_data)\
            .eq('id', unit_id)\
            .execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update unit"
            )
        
        logger.info(f"Unit updated: {unit_id}")
        
        return UnitResponse(**result.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unit update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update unit"
        )


@router.delete("/{unit_id}", response_model=SuccessResponse)
async def delete_unit(
    unit_id: str,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Delete a unit (soft delete - mark as inactive)
    """
    try:
        # Verify ownership
        unit_result = db.table('units')\
            .select('id')\
            .eq('id', unit_id)\
            .eq('lecturer_id', lecturer['id'])\
            .execute()
        
        if not unit_result.data or len(unit_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        
        # Mark as inactive
        db.table('units')\
            .update({'is_active': False})\
            .eq('id', unit_id)\
            .execute()
        
        logger.info(f"Unit deleted: {unit_id}")
        
        return SuccessResponse(
            message="Unit deleted successfully"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unit deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete unit"
        )


@router.get("/{unit_id}/students", response_model=List[dict])
async def get_unit_students(
    unit_id: str,
    lecturer=Depends(get_current_lecturer),
    db=Depends(get_db)
):
    """
    Get all students registered in a unit
    """
    try:
        # Verify ownership
        unit_result = db.table('units')\
            .select('id')\
            .eq('id', unit_id)\
            .eq('lecturer_id', lecturer['id'])\
            .execute()
        
        if not unit_result.data or len(unit_result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Unit not found"
            )
        
        # Get students (without embeddings for listing)
        students_result = db.table('students')\
            .select('id,unit_id,admission_number,full_name,is_active,created_at')\
            .eq('unit_id', unit_id)\
            .eq('is_active', True)\
            .order('full_name')\
            .execute()
        
        students = students_result.data if students_result.data else []
        
        return students
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching students: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch students"
        )