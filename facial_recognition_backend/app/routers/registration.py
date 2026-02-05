from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from app.utils.security import verify_registration_token
from app.config import settings
from app.database import supabase_client
from app.services.liveness_detection import process_liveness

router = APIRouter()

class VerifyTokenResponse(BaseModel):
    valid: bool
    unit_id: str | None = None
    error: str | None = None

class RegistrationStartRequest(BaseModel):
    full_name: str
    admission_number: str
    unit_id: str

class LivenessCheckRequest(BaseModel):
    frames: list
    unit_id: str
    admission_number: str

class RegistrationCompleteRequest(BaseModel):
    unit_id: str
    admission_number: str
    embeddings: list

@router.get("/verify-token/{token}", response_model=VerifyTokenResponse)
def verify_token(token: str):
    try:
        payload = verify_registration_token(token)
        return VerifyTokenResponse(valid=True, unit_id=payload.get("unit_id"))
    except HTTPException as e:
        unit = supabase_client.table("units").select("id").eq("registration_token", token).execute().data
        if unit:
            return VerifyTokenResponse(valid=True, unit_id=unit[0]["id"])
        return VerifyTokenResponse(valid=False, error=str(e.detail))

@router.post("/start")
def start_registration(data: RegistrationStartRequest):
    # Check if already registered
    existing = supabase_client.table("students").select("*").eq("admission_number", data.admission_number).eq("unit_id", data.unit_id).execute().data
    if existing:
        raise HTTPException(status_code=400, detail="Already registered.")
    # Create student record
    result = supabase_client.table("students").insert({
        "unit_id": data.unit_id,
        "admission_number": data.admission_number,
        "full_name": data.full_name,
        "embeddings": []
    }).execute()
    return {"status": "started"}

@router.get("/instructions")
def get_instructions():
    return {
        "poses": [
            {"type": "center", "desc": "Look straight ahead"},
            {"type": "tilt_down", "desc": "Tilt your head down"},
            {"type": "turn_right", "desc": "Turn your head right"},
            {"type": "turn_left", "desc": "Turn your head left"}
        ],
        "min_frames_per_pose": settings.LIVENESS_MIN_FRAMES_PER_POSE
    }

@router.post("/liveness-check")
def liveness_check(data: LivenessCheckRequest):
    # Validate and process frames
    result = process_liveness(data.frames)
    if not result["valid"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"embeddings": result["embeddings"]}

@router.post("/complete")
def complete_registration(data: RegistrationCompleteRequest):
    # Store embeddings
    supabase_client.table("students").update({"embeddings": data.embeddings}).eq("unit_id", data.unit_id).eq("admission_number", data.admission_number).execute()
    return {"status": "completed"}
