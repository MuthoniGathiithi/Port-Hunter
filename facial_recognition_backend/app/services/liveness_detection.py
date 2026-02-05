import numpy as np
import cv2
from insightface.app import FaceAnalysis
from app.config import settings
from app.services.face_recognition import extract_embeddings
from app.utils.image import decode_base64_image

POSES = {
    "center": {"yaw": [-15, 15], "pitch": [-15, 15]},
    "tilt_down": {"yaw": [-15, 15], "pitch": [15, 45]},
    "turn_right": {"yaw": [20, 50], "pitch": [-15, 15]},
    "turn_left": {"yaw": [-50, -20], "pitch": [-15, 15]}
}

MIN_FRAMES = settings.LIVENESS_MIN_FRAMES_PER_POSE

# Face detector for pose estimation
pose_app = FaceAnalysis(name="scrfd", providers=["CPUExecutionProvider"])
pose_app.prepare(ctx_id=0, det_size=(640, 640))

# 3D facial landmark model points (approximate)
MODEL_POINTS = np.array(
    [
        [-30.0, 0.0, -30.0],  # left eye
        [30.0, 0.0, -30.0],   # right eye
        [0.0, 0.0, 0.0],      # nose tip
        [-20.0, -30.0, -30.0],  # left mouth
        [20.0, -30.0, -30.0],   # right mouth
    ],
    dtype=np.float64,
)


def estimate_head_pose(frame: np.ndarray) -> dict:
    faces = pose_app.get(frame)
    if not faces:
        raise ValueError("No face detected for head pose")
    kps = faces[0]["kps"]
    image_points = np.array(
        [kps[0], kps[1], kps[2], kps[3], kps[4]],
        dtype=np.float64,
    )
    h, w = frame.shape[:2]
    focal_length = w
    center = (w / 2, h / 2)
    camera_matrix = np.array(
        [[focal_length, 0, center[0]], [0, focal_length, center[1]], [0, 0, 1]],
        dtype=np.float64,
    )
    dist_coeffs = np.zeros((4, 1))
    success, rvec, tvec = cv2.solvePnP(
        MODEL_POINTS, image_points, camera_matrix, dist_coeffs, flags=cv2.SOLVEPNP_ITERATIVE
    )
    if not success:
        raise ValueError("Head pose estimation failed")
    rotation_matrix, _ = cv2.Rodrigues(rvec)
    pose_mat = cv2.hconcat((rotation_matrix, tvec))
    _, _, _, _, _, _, euler = cv2.decomposeProjectionMatrix(pose_mat)
    pitch, yaw, roll = [float(angle) for angle in euler]
    return {"yaw": yaw, "pitch": pitch, "roll": roll}

# Main liveness processing

def process_liveness(frames: list) -> dict:
    embeddings = []
    for pose_type, pose_frames in group_frames_by_pose(frames).items():
        if len(pose_frames) < MIN_FRAMES:
            return {"valid": False, "error": f"Not enough frames for {pose_type}"}
        valid_frames = []
        for frame in pose_frames:
            try:
                pose = estimate_head_pose(frame)
            except Exception:
                continue
            yaw_range = POSES[pose_type]["yaw"]
            pitch_range = POSES[pose_type]["pitch"]
            if yaw_range[0] <= pose["yaw"] <= yaw_range[1] and pitch_range[0] <= pose["pitch"] <= pitch_range[1]:
                valid_frames.append(frame)
        if not valid_frames:
            return {"valid": False, "error": f"No valid frames for {pose_type}"}
        # Extract embeddings from best quality frames
        for vf in valid_frames[:3]:
            try:
                emb = extract_embeddings(vf)
            except Exception:
                continue
            embeddings.append(emb.tolist())
    if not embeddings:
        return {"valid": False, "error": "No valid embeddings extracted"}
    return {"valid": True, "embeddings": embeddings}

def group_frames_by_pose(frames: list) -> dict:
    poses = {"center": [], "tilt_down": [], "turn_right": [], "turn_left": []}
    for f in frames:
        if "pose_type" not in f or "frame_data" not in f:
            continue
        try:
            frame = decode_base64_image(f["frame_data"])
        except Exception:
            continue
        poses[f["pose_type"]].append(frame)
    return poses
