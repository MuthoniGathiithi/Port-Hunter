from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from app.utils.security import get_current_lecturer
from app.database import supabase_client
from app.services.matching import match_faces
import uuid
import logging

router = APIRouter()

class AttendanceCreateRequest(BaseModel):
    unit_id: str
    classroom_photos: list

class AttendanceSessionResponse(BaseModel):
    id: str
    unit_id: str
    session_date: str
    status: str
    totals: dict

@router.post("/", response_model=AttendanceSessionResponse)
def create_session(data: AttendanceCreateRequest, background_tasks: BackgroundTasks, lecturer_id: str = Depends(get_current_lecturer)):
    session_id = str(uuid.uuid4())
    result = supabase_client.table("attendance_sessions").insert({
        "id": session_id,
        "unit_id": data.unit_id,
        "session_date": "now()",
        "classroom_photos": data.classroom_photos,
        "totals": {},
        "status": "processing"
    }).execute()
    background_tasks.add_task(process_attendance, session_id, data.classroom_photos)
    session = result.data[0]
    return AttendanceSessionResponse(**session)

@router.get("/sessions")
def list_sessions(lecturer_id: str = Depends(get_current_lecturer)):
    sessions = supabase_client.table("attendance_sessions").select("*").eq("unit_id", lecturer_id).execute().data
    return sessions

@router.get("/sessions/{id}", response_model=AttendanceSessionResponse)
def get_session(id: str, lecturer_id: str = Depends(get_current_lecturer)):
    session = supabase_client.table("attendance_sessions").select("*").eq("id", id).execute().data
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return AttendanceSessionResponse(**session[0])

@router.get("/sessions/{id}/status")
def get_status(id: str):
    session = supabase_client.table("attendance_sessions").select("status").eq("id", id).execute().data
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": session[0]["status"]}

# Background processing

def process_attendance(session_id: str, classroom_photos: list):
    try:
        results = match_faces(classroom_photos, session_id)
        # Update session with results
        supabase_client.table("attendance_sessions").update({
            "totals": results["totals"],
            "status": "completed"
        }).eq("id", session_id).execute()
        # Store attendance records, unknown faces, etc.
        # ...
        logging.info(f"Attendance processed for session {session_id}")
    except Exception as e:
        supabase_client.table("attendance_sessions").update({"status": "error"}).eq("id", session_id).execute()
        logging.error(f"Attendance processing failed: {e}")
