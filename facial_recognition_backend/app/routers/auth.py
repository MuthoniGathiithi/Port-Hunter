from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, constr
from app.utils.security import hash_password, verify_password, create_access_token
from app.config import settings
from app.database import supabase_client
from datetime import timedelta

router = APIRouter()

class RegisterRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    full_name: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: EmailStr
    full_name: str

# Password validation helper
import re
def validate_password(password: str) -> bool:
    return (
        len(password) >= 8 and
        re.search(r"[A-Z]", password) and
        re.search(r"\d", password)
    )

@router.post("/register", response_model=UserResponse)
def register(data: RegisterRequest):
    if not validate_password(data.password):
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters, include an uppercase letter and a digit.")
    # Check if user exists
    existing = supabase_client.table("lecturers").select("*").eq("email", data.email).execute().data
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered.")
    hashed = hash_password(data.password)
    result = supabase_client.table("lecturers").insert({
        "email": data.email,
        "password_hash": hashed,
        "full_name": data.full_name
    }).execute()
    user = result.data[0]
    return UserResponse(id=user["id"], email=user["email"], full_name=user["full_name"])

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest):
    user = supabase_client.table("lecturers").select("*").eq("email", data.email).execute().data
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    user = user[0]
    if not verify_password(data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    token = create_access_token({"sub": user["id"]}, expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    return TokenResponse(access_token=token)

@router.get("/me", response_model=UserResponse)
def get_me(user_id: str):
    user = supabase_client.table("lecturers").select("*").eq("id", user_id).execute().data
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    user = user[0]
    return UserResponse(id=user["id"], email=user["email"], full_name=user["full_name"])
