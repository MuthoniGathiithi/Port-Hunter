import base64
import re
from typing import Tuple

import cv2
import numpy as np

DATA_URL_PATTERN = re.compile(r"^data:image/.+;base64,")


def decode_base64_image(data: str) -> np.ndarray:
    if not data:
        raise ValueError("Empty image data")
    if DATA_URL_PATTERN.match(data):
        data = DATA_URL_PATTERN.sub("", data)
    try:
        decoded = base64.b64decode(data)
    except Exception as exc:
        raise ValueError("Invalid base64 image data") from exc
    np_arr = np.frombuffer(decoded, dtype=np.uint8)
    img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("Failed to decode image")
    return img


def encode_image_to_base64(image: np.ndarray, quality: int = 85) -> str:
    encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    ok, buffer = cv2.imencode(".jpg", image, encode_params)
    if not ok:
        raise ValueError("Failed to encode image")
    encoded = base64.b64encode(buffer.tobytes()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"
