"""
Main FastAPI Application
Entry point for the Facial Recognition Attendance System
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, units, registration, attendance
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Facial Recognition Attendance System",
    description="Backend API for classroom attendance using face recognition",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(units.router)
app.include_router(registration.router)
app.include_router(attendance.router)


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "Facial Recognition Attendance System API",
        "status": "online",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup"""
    logger.info("Starting Facial Recognition Attendance System...")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info("Loading face recognition models...")
    
    # Initialize models on startup
    try:
        from app.services.face_detection import face_detector
        from app.services.face_recognition import face_recognizer
        logger.info("✓ Face detection model loaded")
        logger.info("✓ Face recognition model loaded")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
        raise
    
    logger.info("Application ready!")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown"""
    logger.info("Shutting down Facial Recognition Attendance System...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )