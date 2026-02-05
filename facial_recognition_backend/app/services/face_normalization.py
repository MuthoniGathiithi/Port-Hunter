import cv2
import numpy as np

def align_face(image: np.ndarray, landmarks: np.ndarray) -> np.ndarray:
    # Align face based on eye positions, rotate to horizontal, resize to 128x128
    left_eye = landmarks[0]
    right_eye = landmarks[1]
    # Calculate angle between eyes
    dy = right_eye[1] - left_eye[1]
    dx = right_eye[0] - left_eye[0]
    angle = np.degrees(np.arctan2(dy, dx))
    # Center between eyes
    eyes_center = ((left_eye[0] + right_eye[0]) // 2, (left_eye[1] + right_eye[1]) // 2)
    # Get rotation matrix
    M = cv2.getRotationMatrix2D(eyes_center, angle, 1)
    aligned = cv2.warpAffine(image, M, (image.shape[1], image.shape[0]), flags=cv2.INTER_CUBIC)
    # Crop and resize to 128x128
    h, w = aligned.shape[:2]
    min_dim = min(h, w)
    start_x = (w - min_dim) // 2
    start_y = (h - min_dim) // 2
    cropped = aligned[start_y:start_y+min_dim, start_x:start_x+min_dim]
    resized = cv2.resize(cropped, (128, 128))
    return resized

def quality_checks(image: np.ndarray) -> bool:
    # Check sharpness
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    if laplacian_var < 30:
        return False  # blurry
    # Check brightness
    mean_brightness = np.mean(gray)
    if mean_brightness < 40 or mean_brightness > 220:
        return False
    # Check contrast
    contrast = gray.std()
    if contrast < 20:
        return False
    return True
