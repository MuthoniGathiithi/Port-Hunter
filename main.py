import os, json
import numpy as np
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
from insightface.app import FaceAnalysis
import cv2, io
from contextlib import asynccontextmanager


face_app = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global face_app
    print("Loading buffalo_l model...")
    face_app = FaceAnalysis(name="buffalo_s", providers=["CPUExecutionProvider"])
    face_app.prepare(ctx_id=0, det_size=(320, 320))
    print("Face service ready.")
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

@app.middleware("http")
async def cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"]  = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

def load_cv2_image(file_bytes: bytes):
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)

def cosine_similarity(a, b):
    a = np.array(a, dtype=np.float32)
    b = np.array(b, dtype=np.float32)
    a = a / np.linalg.norm(a)
    b = b / np.linalg.norm(b)
    return float(np.dot(a, b))

@app.get("/")
def root():
    return {"status": "Face service running"}

@app.get("/ping")
def ping():
    return {"ok": True}

@app.post("/embed")
async def embed(photos: list[UploadFile] = File(...)):
    """Takes 1-5 pose photos → returns averaged embedding"""
    try:
        embeddings = []
        for photo in photos:
            file_bytes = await photo.read()
            img        = load_cv2_image(file_bytes)
            faces      = face_app.get(img)
            if faces:
                face = max(faces, key=lambda f: f.det_score)
                embeddings.append(face.embedding.tolist())

        if not embeddings:
            raise HTTPException(status_code=400, detail="No face detected in any photo. Ensure your face is clearly visible.")

        avg = np.mean(embeddings, axis=0).tolist()
        return {"embedding": avg, "poses_used": len(embeddings)}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/compare")
async def compare(photos: list[UploadFile] = File(...), stored_embeddings: str = Form(...)):
    """Takes class photos + stored embeddings → returns matches"""
    try:
        stored   = json.loads(stored_embeddings)
        detected = []

        for photo in photos:
            file_bytes = await photo.read()
            img        = load_cv2_image(file_bytes)
            faces      = face_app.get(img)
            for face in faces:
                detected.append(face.embedding.tolist())

        if not detected:
            raise HTTPException(status_code=400, detail="No faces detected in uploaded photos.")

        THRESHOLD = 0.35
        matches   = []
        seen_ids  = set()

        for det_emb in detected:
            best_sim = -1.0
            best     = None
            for s in stored:
                sim = cosine_similarity(det_emb, s["embedding"])
                if sim > best_sim:
                    best_sim = sim
                    best     = s
            print(f"Best: {best['name'] if best else 'none'} sim={best_sim:.4f}")
            if best and best_sim >= THRESHOLD and best["id"] not in seen_ids:
                seen_ids.add(best["id"])
                matches.append({"id": best["id"], "similarity": round(best_sim, 3)})

        return {"matches": matches}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))