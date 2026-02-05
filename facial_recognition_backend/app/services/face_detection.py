import cv2
import numpy as np
from insightface.app import FaceAnalysis
from app.config import settings

face_app = FaceAnalysis(name='scrfd', providers=['CPUExecutionProvider'])
face_app.prepare(ctx_id=0, det_size=(640, 640))

# Multi-scale detection
SCALES = [320, 480, 640, 1024, 1280]

# Adaptive thresholding
BASE_THRESHOLD = settings.DETECTION_CONFIDENCE_THRESHOLD
MIN_THRESHOLD = 0.1

# Preprocessing: CLAHE + sharpening

def preprocess_image(image: np.ndarray) -> np.ndarray:
    img_yuv = cv2.cvtColor(image, cv2.COLOR_BGR2YUV)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    img_yuv[:,:,0] = clahe.apply(img_yuv[:,:,0])
    img_clahe = cv2.cvtColor(img_yuv, cv2.COLOR_YUV2BGR)
    kernel = np.array([[0, -1, 0], [-1, 5,-1], [0, -1, 0]])
    img_sharp = cv2.filter2D(img_clahe, -1, kernel)
    return img_sharp

# Duplicate removal with IoU

def iou(boxA, boxB):
    xA = max(boxA[0], boxB[0])
    yA = max(boxA[1], boxB[1])
    xB = min(boxA[2], boxB[2])
    yB = min(boxA[3], boxB[3])
    interArea = max(0, xB - xA) * max(0, yB - yA)
    boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
    boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
    iou = interArea / float(boxAArea + boxBArea - interArea)
    return iou

def remove_duplicates(faces, threshold=0.5):
    unique = []
    for face in faces:
        if all(iou(face['bbox'], u['bbox']) < threshold for u in unique):
            unique.append(face)
    return unique

# Main detection function

def detect_faces(image: np.ndarray):
    image = preprocess_image(image)
    results = []
    for scale in SCALES:
        face_app.prepare(det_size=(scale, scale))
        faces = face_app.get(image)
        for face in faces:
            if face['det_score'] >= BASE_THRESHOLD:
                results.append({
                    'bbox': face['bbox'],
                    'landmarks': face['kps'],
                    'score': face['det_score'],
                    'cropped': image[int(face['bbox'][1]):int(face['bbox'][3]), int(face['bbox'][0]):int(face['bbox'][2])]
                })
    results = remove_duplicates(results)
    return results
