from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, units, registration, attendance
import logging
from app.queue import task_queue

app = FastAPI(title="Facial Recognition Attendance System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.ALLOWED_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def health_check():
    return {"status": "ok"}

app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(units.router, prefix="/units", tags=["units"])
app.include_router(registration.router, prefix="/register", tags=["registration"])
app.include_router(attendance.router, prefix="/attendance", tags=["attendance"])

@app.on_event("startup")
def load_models():
    logging.info("Loading face recognition models...")
    from app.services import face_detection, face_recognition
    _ = face_detection.face_app
    _ = face_recognition.arcface_app
    task_queue.start()
    logging.info("Models loaded.")


@app.on_event("shutdown")
def shutdown_queue():
    task_queue.stop()
