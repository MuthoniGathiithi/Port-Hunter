# Facial Recognition Attendance System Backend

## Tech Stack
- FastAPI
- Supabase (PostgreSQL)
- InsightFace (SCRFD detection + ArcFace recognition)
- OpenCV, NumPy
- JWT authentication

## Features
- Lecturer authentication (JWT)
- Unit management
- Student registration with liveness detection
- Attendance sessions with face recognition
- Background processing
- Secure password hashing
- Configurable thresholds

## Setup
1. Copy `.env.template` to `.env` and fill in your Supabase and secret keys.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Docs
Visit `/docs` for interactive API documentation.
