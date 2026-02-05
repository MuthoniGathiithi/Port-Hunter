"""
Face Normalization Service
Handles face alignment and normalization for consistent recognition
"""
import numpy as np
import cv2
import math
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class FaceNormalizationService:
    """Handles face alignment and normalization"""
    
    def __init__(self, target_size: tuple = (128, 128)):
        self.target_size = target_size
    
    def normalize_face(
        self,
        cropped_face: np.ndarray,
        landmarks: np.ndarray
    ) -> Optional[np.ndarray]:
        """
        Normalize a single face:
        1. Align based on eye positions
        2. Rotate to horizontal
        3. Resize to target size
        """
        if cropped_face is None or landmarks is None:
            logger.warning("Invalid input for normalization")
            return None
        
        try:
            # SCRFD landmarks: [left_eye, right_eye, nose, left_mouth, right_mouth]
            left_eye = landmarks[0]  # First point is left eye
            right_eye = landmarks[1]  # Second point is right eye
            
            left_eye_x, left_eye_y = left_eye[0], left_eye[1]
            right_eye_x, right_eye_y = right_eye[0], right_eye[1]
            
            # Calculate angle for rotation
            dy = right_eye_y - left_eye_y
            dx = right_eye_x - left_eye_x
            
            if dx == 0:
                angle_degrees = 0
            else:
                tan_ratio = dy / dx
                angle_radians = math.atan(tan_ratio)
                angle_degrees = math.degrees(angle_radians)
            
            # Get rotation matrix
            center = (cropped_face.shape[1] // 2, cropped_face.shape[0] // 2)
            rotation_matrix = cv2.getRotationMatrix2D(center, angle_degrees, 1.0)
            
            # Apply rotation
            normalized_face = cv2.warpAffine(
                cropped_face,
                rotation_matrix,
                (cropped_face.shape[1], cropped_face.shape[0]),
                flags=cv2.INTER_CUBIC
            )
            
            # Resize to target size
            resized_face = cv2.resize(normalized_face, self.target_size)
            
            return resized_face
        
        except Exception as e:
            logger.error(f"Normalization failed: {e}")
            return None
    
    def normalize_face_list(
        self,
        face_list: List[np.ndarray],
        landmarks_list: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        Normalize a list of faces
        Returns only successfully normalized faces
        """
        processed_faces = []
        
        for i, (face, landmarks) in enumerate(zip(face_list, landmarks_list)):
            result = self.normalize_face(face, landmarks)
            
            if result is not None:
                processed_faces.append(result)
            else:
                logger.warning(f"Face {i+1} failed normalization - skipped")
        
        logger.info(f"Normalized {len(processed_faces)} out of {len(face_list)} faces")
        return processed_faces
    
    def quality_check(self, face: np.ndarray) -> dict:
        """
        Check face quality metrics
        Returns dict with quality scores
        """
        try:
            # Calculate sharpness (Laplacian variance)
            gray = cv2.cvtColor(face, cv2.COLOR_RGB2GRAY)
            laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
            
            # Calculate brightness
            brightness = np.mean(gray)
            
            # Calculate contrast
            contrast = gray.std()
            
            # Determine if face is blurry (low sharpness)
            is_sharp = laplacian_var > 100
            
            # Determine if lighting is good
            is_well_lit = 50 < brightness < 200
            
            # Determine if contrast is sufficient
            has_contrast = contrast > 30
            
            quality = {
                'sharpness': float(laplacian_var),
                'brightness': float(brightness),
                'contrast': float(contrast),
                'is_sharp': bool(is_sharp),
                'is_well_lit': bool(is_well_lit),
                'has_contrast': bool(has_contrast),
                'overall_quality': bool(is_sharp and is_well_lit and has_contrast)
            }
            
            return quality
        
        except Exception as e:
            logger.error(f"Quality check failed: {e}")
            return {
                'overall_quality': False,
                'error': str(e)
            }


# Global instance
face_normalizer = FaceNormalizationService()