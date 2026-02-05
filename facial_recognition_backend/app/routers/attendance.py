from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from app.utils.security import get_current_lecturer
from app.database import supabase_client
from app.services.matching import match_faces
import uuid
import logging
from datetime import datetime, timezone
from app.queue import task_queue

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
    present: list | None = None
    absent: list | None = None
    unknown: list | None = None
    classroom_photos: list | None = None
    unit_name: str | None = None

@router.post("/", response_model=AttendanceSessionResponse)
def create_session(data: AttendanceCreateRequest, lecturer_id: str = Depends(get_current_lecturer)):
    unit = supabase_client.table("units").select("id,unit_name").eq("id", data.unit_id).eq("lecturer_id", lecturer_id).execute().data
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")
    session_id = str(uuid.uuid4())
    session_date = datetime.now(timezone.utc).isoformat()
    result = supabase_client.table("attendance_sessions").insert({
        "id": session_id,
        "unit_id": data.unit_id,
        "session_date": session_date,
        "classroom_photos": data.classroom_photos,
        "totals": {"present": 0, "absent": 0, "unknown": 0},
        "status": "processing"
    }).execute()
    task_queue.enqueue(process_attendance, session_id, data.unit_id, data.classroom_photos)
    session = result.data[0]
    return AttendanceSessionResponse(**session, unit_name=unit[0]["unit_name"])

@router.get("/sessions")
def list_sessions(
    unit_id: str | None = Query(default=None),
    lecturer_id: str = Depends(get_current_lecturer),
):
    units = supabase_client.table("units").select("id,unit_name").eq("lecturer_id", lecturer_id).execute().data
    if not units:
        return []
    unit_map = {u["id"]: u["unit_name"] for u in units}
    unit_ids = list(unit_map.keys())
    if unit_id:
        if unit_id not in unit_map:
            raise HTTPException(status_code=404, detail="Unit not found.")
        unit_ids = [unit_id]
    sessions = supabase_client.table("attendance_sessions").select("*").in_("unit_id", unit_ids).execute().data
    for s in sessions:
        s["unit_name"] = unit_map.get(s["unit_id"])
    return sessions

@router.get("/sessions/{id}", response_model=AttendanceSessionResponse)
def get_session(id: str, lecturer_id: str = Depends(get_current_lecturer)):
    session = supabase_client.table("attendance_sessions").select("*").eq("id", id).execute().data
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    session = session[0]
    unit = supabase_client.table("units").select("unit_name,lecturer_id").eq("id", session["unit_id"]).execute().data
    if not unit or unit[0]["lecturer_id"] != lecturer_id:
        raise HTTPException(status_code=403, detail="Not allowed.")
    return AttendanceSessionResponse(**session, unit_name=unit[0]["unit_name"])

@router.get("/sessions/{id}/status")
def get_status(id: str):
    session = supabase_client.table("attendance_sessions").select("status").eq("id", id).execute().data
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
    return {"status": session[0]["status"]}

# Background processing

def process_attendance(session_id: str, unit_id: str, classroom_photos: list):
    try:
        results = match_faces(classroom_photos, session_id, unit_id)
        # Update session with results
        supabase_client.table("attendance_sessions").update({
            "totals": results["totals"],
            "present": results["present"],
            "absent": results["absent"],
            "unknown": results["unknown"],
            "status": "completed"
        }).eq("id", session_id).execute()
        # Store attendance records, unknown faces, etc.
        # ...
        logging.info(f"Attendance processed for session {session_id}")
    except Exception as e:
        supabase_client.table("attendance_sessions").update({"status": "error"}).eq("id", session_id).execute()
        logging.error(f"Attendance processing failed: {e}")
