import numpy as np
from insightface.app import FaceAnalysis
from app.config import settings

arcface_app = FaceAnalysis(name='arcface', providers=['CPUExecutionProvider'])
arcface_app.prepare(ctx_id=0)

# Extract 512-dim embeddings

def extract_embeddings(face_img: np.ndarray) -> np.ndarray:
    faces = arcface_app.get(face_img)
    if not faces:
        raise ValueError("No face detected for embedding extraction")
    emb = faces[0]["embedding"]
    emb = emb / np.linalg.norm(emb)
    return emb

def cosine_similarity(emb1: np.ndarray, emb2: np.ndarray) -> float:
    return float(np.dot(emb1, emb2))
