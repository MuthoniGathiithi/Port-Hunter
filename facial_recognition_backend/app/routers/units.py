from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.utils.security import get_current_lecturer, create_registration_token
from app.database import supabase_client
import uuid

router = APIRouter()

class UnitCreateRequest(BaseModel):
    unit_name: str
    unit_code: str

class UnitResponse(BaseModel):
    id: str
    unit_name: str
    unit_code: str
    registration_token: str
    is_active: bool
    student_count: int = 0
    session_count: int = 0

@router.post("/", response_model=UnitResponse)
def create_unit(data: UnitCreateRequest, lecturer_id: str = Depends(get_current_lecturer)):
    unit_id = str(uuid.uuid4())
    token = create_registration_token(unit_id=unit_id)
    result = supabase_client.table("units").insert({
        "id": unit_id,
        "lecturer_id": lecturer_id,
        "unit_name": data.unit_name,
        "unit_code": data.unit_code,
        "registration_token": token,
        "is_active": True
    }).execute()
    unit = result.data[0]
    return UnitResponse(**unit, student_count=0, session_count=0)

@router.get("/")
def list_units(lecturer_id: str = Depends(get_current_lecturer)):
    units = supabase_client.table("units").select("*").eq("lecturer_id", lecturer_id).eq("is_active", True).execute().data
    # Add stats
    for unit in units:
        unit["student_count"] = supabase_client.table("students").select("id", count="exact").eq("unit_id", unit["id"]).execute().count or 0
        unit["session_count"] = supabase_client.table("attendance_sessions").select("id", count="exact").eq("unit_id", unit["id"]).execute().count or 0
    return units

@router.get("/{id}", response_model=UnitResponse)
def get_unit(id: str, lecturer_id: str = Depends(get_current_lecturer)):
    unit = supabase_client.table("units").select("*").eq("id", id).eq("lecturer_id", lecturer_id).execute().data
    if not unit:
        raise HTTPException(status_code=404, detail="Unit not found.")
    unit = unit[0]
    unit["student_count"] = supabase_client.table("students").select("id", count="exact").eq("unit_id", unit["id"]).execute().count or 0
    unit["session_count"] = supabase_client.table("attendance_sessions").select("id", count="exact").eq("unit_id", unit["id"]).execute().count or 0
    return UnitResponse(**unit)

@router.patch("/{id}", response_model=UnitResponse)
def update_unit(id: str, data: UnitCreateRequest, lecturer_id: str = Depends(get_current_lecturer)):
    result = supabase_client.table("units").update({
        "unit_name": data.unit_name,
        "unit_code": data.unit_code
    }).eq("id", id).eq("lecturer_id", lecturer_id).execute()
    unit = result.data[0]
    unit["student_count"] = supabase_client.table("students").select("id", count="exact").eq("unit_id", unit["id"]).execute().count or 0
    unit["session_count"] = supabase_client.table("attendance_sessions").select("id", count="exact").eq("unit_id", unit["id"]).execute().count or 0
    return UnitResponse(**unit)

@router.delete("/{id}")
def delete_unit(id: str, lecturer_id: str = Depends(get_current_lecturer)):
    supabase_client.table("units").update({"is_active": False}).eq("id", id).eq("lecturer_id", lecturer_id).execute()
    return {"status": "deleted"}

@router.get("/{id}/students")
def list_students(id: str, lecturer_id: str = Depends(get_current_lecturer)):
    students = supabase_client.table("students").select("*").eq("unit_id", id).execute().data
    return students
