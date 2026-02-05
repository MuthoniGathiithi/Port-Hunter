"""
Authentication Router
Handles lecturer registration and login
"""
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.models import (
    LecturerCreate,
    LecturerLogin,
    LecturerResponse,
    Token,
    SuccessResponse
)
from app.utils.security import (
    get_password_hash,
    verify_password,
    create_access_token
)
from datetime import timedelta
from app.config import settings
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
async def register_lecturer(
    lecturer_data: LecturerCreate,
    db=Depends(get_db)
):
    """
    Register a new lecturer
    """
    try:
        # Check if email already exists
        existing = db.table('lecturers').select('id').eq('email', lecturer_data.email).execute()
        
        if existing.data and len(existing.data) > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = get_password_hash(lecturer_data.password)
        
        # Insert lecturer
        result = db.table('lecturers').insert({
            'email': lecturer_data.email,
            'password_hash': password_hash,
            'full_name': lecturer_data.full_name
        }).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create lecturer account"
            )
        
        lecturer = result.data[0]
        
        logger.info(f"New lecturer registered: {lecturer['email']}")
        
        return SuccessResponse(
            message="Lecturer account created successfully",
            data={
                "lecturer_id": lecturer['id'],
                "email": lecturer['email']
            }
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


@router.post("/login", response_model=Token)
async def login_lecturer(
    credentials: LecturerLogin,
    db=Depends(get_db)
):
    """
    Lecturer login - returns JWT access token
    """
    try:
        # Find lecturer by email
        result = db.table('lecturers').select('*').eq('email', credentials.email).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        lecturer = result.data[0]
        
        # Verify password
        if not verify_password(credentials.password, lecturer['password_hash']):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": str(lecturer['id'])},
            expires_delta=access_token_expires
        )
        
        logger.info(f"Lecturer logged in: {lecturer['email']}")
        
        return Token(access_token=access_token, token_type="bearer")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


@router.get("/me", response_model=LecturerResponse)
async def get_current_lecturer_info(
    lecturer=Depends(get_current_lecturer)
):
    """
    Get current lecturer's information
    Requires authentication
    """
    return LecturerResponse(
        id=lecturer['id'],
        email=lecturer['email'],
        full_name=lecturer['full_name'],
        created_at=lecturer['created_at']
    )


# Import after function definitions to avoid circular import
from app.utils.security import get_current_lecturer