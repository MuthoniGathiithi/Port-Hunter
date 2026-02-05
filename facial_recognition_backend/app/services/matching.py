import uuid
import numpy as np
from app.services.face_recognition import cosine_similarity, extract_embeddings
from app.services.face_detection import detect_faces
from app.services.face_normalization import align_face, quality_checks
from app.database import supabase_client
from app.config import settings
from app.utils.image import decode_base64_image, encode_image_to_base64


def _load_students(unit_id: str):
    students = (
        supabase_client.table("students")
        .select("id,full_name,admission_number,embeddings")
        .eq("unit_id", unit_id)
        .execute()
        .data
    )
    normalized = []
    for s in students:
        embeddings = []
        for emb in s.get("embeddings") or []:
            try:
                embeddings.append(np.array(emb, dtype=np.float32))
            except Exception:
                continue
        normalized.append(
            {
                "id": s["id"],
                "full_name": s.get("full_name"),
                "admission_number": s.get("admission_number"),
                "embeddings": embeddings,
            }
        )
    return normalized


def match_faces(classroom_photos: list, session_id: str, unit_id: str) -> dict:
    students = _load_students(unit_id)
    present_map = {}
    unknown = []

    for photo in classroom_photos:
        try:
            image = decode_base64_image(photo)
        except Exception:
            continue
        faces = detect_faces(image)
        for face in faces:
            landmarks = face.get("landmarks")
            if landmarks is None or len(landmarks) < 2:
                continue
            aligned = align_face(image, landmarks)
            if not quality_checks(aligned):
                continue
            try:
                emb = extract_embeddings(aligned)
            except Exception:
                continue

            best_student = None
            best_score = -1.0
            for student in students:
                for s_emb in student["embeddings"]:
                    score = cosine_similarity(emb, s_emb)
                    if score > best_score:
                        best_score = score
                        best_student = student

            if best_student and best_score >= settings.RECOGNITION_SIMILARITY_THRESHOLD:
                current = present_map.get(best_student["id"])
                if current is None or best_score > current["confidence_score"]:
                    present_map[best_student["id"]] = {
                        "id": best_student["id"],
                        "full_name": best_student["full_name"],
                        "admission_number": best_student["admission_number"],
                        "confidence_score": float(best_score),
                    }
            else:
                cropped = face.get("cropped")
                cropped_b64 = encode_image_to_base64(cropped) if cropped is not None else None
                unknown.append(
                    {
                        "id": str(uuid.uuid4()),
                        "confidence_score": float(best_score if best_score > 0 else 0),
                        "cropped_face_url": cropped_b64,
                    }
                )

    present = list(present_map.values())
    present_ids = {p["id"] for p in present}
    absent = [
        {"id": s["id"], "full_name": s["full_name"], "admission_number": s["admission_number"]}
        for s in students
        if s["id"] not in present_ids
    ]

    return {
        "totals": {"present": len(present), "absent": len(absent), "unknown": len(unknown)},
        "present": present,
        "absent": absent,
        "unknown": unknown,
    }
