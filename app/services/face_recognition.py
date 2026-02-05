"""
Face Recognition Service
Extracts embeddings using ArcFace model from InsightFace
"""
from insightface.app import FaceAnalysis
import cv2
import numpy as np
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class FaceRecognitionService:
    """Handles face embedding extraction using ArcFace"""
    
    def __init__(self):
        self.app = None
        self.recognition_model = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize ArcFace recognition model"""
        try:
            self.app = FaceAnalysis(
                name='buffalo_l',
                providers=['CPUExecutionProvider']
            )
            self.app.prepare(ctx_id=0, det_size=(640, 640))
            
            # Get recognition model
            self.recognition_model = self.app.models['recognition']
            
            logger.info("ArcFace recognition model initialized successfully")
        
        except Exception as e:
            logger.error(f"Failed to initialize ArcFace model: {e}")
            raise
    
    def extract_embedding(self, normalized_face: np.ndarray) -> Optional[np.ndarray]:
        """
        Extract embedding from a normalized face
        Input: RGB normalized face (128x128)
        Output: 512-dimensional embedding vector
        """
        if normalized_face is None:
            logger.warning("Invalid face for embedding extraction")
            return None
        
        try:
            # Convert RGB to BGR (OpenCV format expected by model)
            face_bgr = cv2.cvtColor(normalized_face, cv2.COLOR_RGB2BGR)
            
            # Extract embedding
            embedding = self.recognition_model.get_feat(face_bgr)
            
            # Normalize embedding (L2 normalization)
            embedding = embedding / np.linalg.norm(embedding)
            
            return embedding
        
        except Exception as e:
            logger.error(f"Embedding extraction failed: {e}")
            return None
    
    def extract_embeddings_from_list(
        self,
        normalized_faces: List[np.ndarray]
    ) -> List[np.ndarray]:
        """
        Extract embeddings from a list of normalized faces
        Returns only successful embeddings
        """
        embeddings = []
        
        for i, face in enumerate(normalized_faces):
            embedding = self.extract_embedding(face)
            
            if embedding is not None:
                embeddings.append(embedding)
            else:
                logger.warning(f"Embedding extraction failed for face {i+1}")
        
        logger.info(f"Extracted {len(embeddings)} embeddings from {len(normalized_faces)} faces")
        return embeddings
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings
        Returns: similarity score (0 to 1, higher is more similar)
        """
        try:
            # Cosine similarity
            similarity = np.dot(embedding1, embedding2)
            
            # Clip to [0, 1] range
            similarity = np.clip(similarity, 0, 1)
            
            return float(similarity)
        
        except Exception as e:
            logger.error(f"Similarity computation failed: {e}")
            return 0.0
    
    def find_best_match(
        self,
        query_embedding: np.ndarray,
        database_embeddings: List[np.ndarray],
        threshold: float = 0.5
    ) -> tuple:
        """
        Find best match for query embedding in database
        
        Returns:
            (best_match_index, similarity_score) or (-1, 0.0) if no match
        """
        if len(database_embeddings) == 0:
            return -1, 0.0
        
        best_similarity = 0.0
        best_index = -1
        
        for i, db_embedding in enumerate(database_embeddings):
            similarity = self.compute_similarity(query_embedding, db_embedding)
            
            if similarity > best_similarity:
                best_similarity = similarity
                best_index = i
        
        # Check if best match exceeds threshold
        if best_similarity >= threshold:
            return best_index, best_similarity
        else:
            return -1, best_similarity
    
    def compute_average_embedding(
        self,
        embeddings: List[np.ndarray]
    ) -> Optional[np.ndarray]:
        """
        Compute average embedding from multiple embeddings
        Useful for creating a single representative embedding from multiple poses
        """
        if len(embeddings) == 0:
            return None
        
        try:
            # Stack embeddings and compute mean
            embeddings_array = np.vstack(embeddings)
            avg_embedding = np.mean(embeddings_array, axis=0)
            
            # Re-normalize
            avg_embedding = avg_embedding / np.linalg.norm(avg_embedding)
            
            return avg_embedding
        
        except Exception as e:
            logger.error(f"Average embedding computation failed: {e}")
            return None


# Global instance
face_recognizer = FaceRecognitionService()