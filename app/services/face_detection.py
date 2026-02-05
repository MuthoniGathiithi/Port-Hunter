"""
Face Detection Service
Uses SCRFD (InsightFace) for robust face detection
"""
from insightface.app import FaceAnalysis
import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging
from app.config import settings

logger = logging.getLogger(__name__)


class FaceDetectionService:
    """Handles face detection using SCRFD"""
    
    def __init__(self):
        self.app = None
        self._initialize_detector()
    
    def _initialize_detector(self):
        """Initialize SCRFD detector with buffalo_l model"""
        try:
            self.app = FaceAnalysis(
                name='buffalo_l',
                providers=['CPUExecutionProvider']
            )
            logger.info("SCRFD detector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize SCRFD: {e}")
            raise
    
    def preprocess_image(self, image_bgr: np.ndarray) -> np.ndarray:
        """
        Apply preprocessing: CLAHE for lighting + sharpening for blur
        """
        try:
            # Convert to LAB color space
            lab = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # CLAHE on L-channel (brightness)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            l_eq = clahe.apply(l)
            
            # Merge channels back
            lab_eq = cv2.merge((l_eq, a, b))
            image_eq = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)
            
            # Sharpening filter
            kernel = np.array([
                [0, -1, 0],
                [-1, 5, -1],
                [0, -1, 0]
            ])
            sharpened = cv2.filter2D(image_eq, -1, kernel)
            
            return sharpened
        
        except Exception as e:
            logger.error(f"Preprocessing failed: {e}")
            return image_bgr  # Return original if preprocessing fails
    
    def load_image_from_base64(self, base64_string: str) -> Optional[np.ndarray]:
        """Load image from base64 string"""
        try:
            import base64
            
            # Remove data URL prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            # Decode base64
            img_data = base64.b64decode(base64_string)
            
            # Convert to numpy array
            nparr = np.frombuffer(img_data, np.uint8)
            
            # Decode image
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                logger.error("Failed to decode image")
                return None
            
            return img
        
        except Exception as e:
            logger.error(f"Error loading image from base64: {e}")
            return None
    
    def load_and_prepare_image(self, image_source: str) -> Optional[np.ndarray]:
        """
        Load image from base64 string, preprocess, convert to RGB
        """
        image_bgr = self.load_image_from_base64(image_source)
        
        if image_bgr is None:
            return None
        
        # Preprocess
        processed = self.preprocess_image(image_bgr)
        
        # Convert to RGB (InsightFace expects RGB)
        image_rgb = cv2.cvtColor(processed, cv2.COLOR_BGR2RGB)
        
        return image_rgb
    
    def iou(self, boxA: List[float], boxB: List[float]) -> float:
        """Compute Intersection over Union between two bounding boxes"""
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])
        
        interW = max(0, xB - xA)
        interH = max(0, yB - yA)
        interArea = interW * interH
        
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])
        
        unionArea = float(boxAArea + boxBArea - interArea)
        
        if unionArea == 0:
            return 0
        
        return interArea / unionArea
    
    def remove_duplicates(self, faces: List, iou_threshold: float = 0.5) -> List:
        """Remove duplicate detections using IoU threshold"""
        unique_faces = []
        
        for f in faces:
            keep = True
            for uf in unique_faces:
                if self.iou(f.bbox.tolist(), uf.bbox.tolist()) > iou_threshold:
                    keep = False
                    break
            if keep:
                unique_faces.append(f)
        
        return unique_faces
    
    def multi_scale_detect(
        self,
        image_rgb: np.ndarray,
        scales: List[int] = [640, 1024, 1280],
        base_thresh: float = None,
        min_thresh: float = 0.1
    ) -> List:
        """
        Run detection at multiple scales with adaptive thresholding
        """
        if base_thresh is None:
            base_thresh = settings.DETECTION_CONFIDENCE_THRESHOLD
        
        all_faces = []
        
        # Step 1: Normal scales, normal threshold
        for size in scales:
            self.app.prepare(ctx_id=0, det_size=(size, size))
            faces = self.app.get(image_rgb)
            
            for f in faces:
                if f.det_score >= base_thresh:
                    all_faces.append(f)
        
        # Step 2: If faces look fewer than expected, retry with lower threshold
        if len(all_faces) < 20:
            logger.info("Retrying with smaller scale + lower threshold for tiny/blurred faces")
            tiny_scales = [320, 480]
            
            for size in tiny_scales:
                self.app.prepare(ctx_id=0, det_size=(size, size))
                faces = self.app.get(image_rgb)
                
                for f in faces:
                    if f.det_score >= min_thresh:
                        all_faces.append(f)
        
        # Step 3: Remove duplicates
        all_faces = self.remove_duplicates(all_faces, iou_threshold=0.5)
        
        logger.info(f"Detected {len(all_faces)} unique faces")
        return all_faces
    
    def crop_detected_faces(
        self,
        face_details: List,
        image_rgb: np.ndarray,
        det_thresh: float = None
    ) -> Tuple[List[np.ndarray], List[np.ndarray], List[dict]]:
        """
        Crop faces and return:
        - cropped images
        - landmarks
        - detection metadata (bbox, confidence)
        """
        if det_thresh is None:
            det_thresh = settings.DETECTION_CONFIDENCE_THRESHOLD
        
        face_list = []
        landmarks_list = []
        metadata_list = []
        
        for face in face_details:
            if face.det_score < det_thresh:
                continue
            
            x1, y1, x2, y2 = face.bbox.astype(int)
            
            # Ensure coordinates are within image bounds
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(image_rgb.shape[1], x2)
            y2 = min(image_rgb.shape[0], y2)
            
            cropped_face = image_rgb[y1:y2, x1:x2]
            
            face_list.append(cropped_face)
            landmarks_list.append(face.kps)
            
            metadata_list.append({
                'bbox': [float(x1), float(y1), float(x2), float(y2)],
                'confidence': float(face.det_score),
                'landmarks': face.kps.tolist()
            })
        
        return face_list, landmarks_list, metadata_list
    
    def detect_faces_in_image(
        self,
        base64_image: str
    ) -> Tuple[List[np.ndarray], List[np.ndarray], List[dict]]:
        """
        Complete pipeline: load image -> detect faces -> crop faces
        Returns: (cropped_faces, landmarks, metadata)
        """
        # Load and preprocess image
        image_rgb = self.load_and_prepare_image(base64_image)
        
        if image_rgb is None:
            raise ValueError("Failed to load image")
        
        # Detect faces
        face_details = self.multi_scale_detect(image_rgb)
        
        if len(face_details) == 0:
            logger.warning("No faces detected in image")
            return [], [], []
        
        # Crop faces
        cropped_faces, landmarks, metadata = self.crop_detected_faces(
            face_details,
            image_rgb
        )
        
        return cropped_faces, landmarks, metadata


# Global instance
face_detector = FaceDetectionService()