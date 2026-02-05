"""
Liveness Detection Service
Processes video frames for Binance-style face registration with pose instructions
"""
import numpy as np
import cv2
from typing import List, Dict, Tuple, Optional
import logging
from app.config import settings
from app.services.face_detection import face_detector
from app.services.face_normalization import face_normalizer
from app.services.face_recognition import face_recognizer

logger = logging.getLogger(__name__)


class LivenessDetectionService:
    """Handles video-based liveness detection with pose validation"""
    
    # Pose requirements (head rotation angles in degrees)
    POSE_REQUIREMENTS = {
        'center': {'yaw': (-15, 15), 'pitch': (-15, 15)},
        'tilt_down': {'yaw': (-15, 15), 'pitch': (15, 45)},
        'turn_right': {'yaw': (20, 50), 'pitch': (-15, 15)},
        'turn_left': {'yaw': (-50, -20), 'pitch': (-15, 15)}
    }
    
    def __init__(self):
        self.min_frames_per_pose = settings.LIVENESS_MIN_FRAMES_PER_POSE
    
    def estimate_head_pose(self, landmarks: np.ndarray, image_shape: tuple) -> Dict[str, float]:
        """
        Estimate head pose (yaw, pitch, roll) from facial landmarks
        
        Args:
            landmarks: 5-point landmarks [left_eye, right_eye, nose, left_mouth, right_mouth]
            image_shape: (height, width, channels)
        
        Returns:
            Dictionary with yaw, pitch, roll angles in degrees
        """
        try:
            # Extract key points
            left_eye = landmarks[0]
            right_eye = landmarks[1]
            nose = landmarks[2]
            left_mouth = landmarks[3]
            right_mouth = landmarks[4]
            
            # Calculate yaw (left-right rotation)
            # Based on horizontal position of nose relative to eyes
            eye_center_x = (left_eye[0] + right_eye[0]) / 2
            nose_x = nose[0]
            
            # Normalize to image width
            yaw_offset = (nose_x - eye_center_x) / (image_shape[1] / 2)
            yaw = yaw_offset * 50  # Scale to approximate degrees
            
            # Calculate pitch (up-down rotation)
            # Based on vertical positions
            eye_center_y = (left_eye[1] + right_eye[1]) / 2
            mouth_center_y = (left_mouth[1] + right_mouth[1]) / 2
            nose_y = nose[1]
            
            # Expected vertical distance when looking straight
            expected_distance = abs(mouth_center_y - eye_center_y)
            actual_nose_distance = abs(nose_y - eye_center_y)
            
            pitch_ratio = (actual_nose_distance / expected_distance) - 0.5
            pitch = pitch_ratio * 60  # Scale to approximate degrees
            
            # Calculate roll (head tilt)
            dx = right_eye[0] - left_eye[0]
            dy = right_eye[1] - left_eye[1]
            roll = np.degrees(np.arctan2(dy, dx))
            
            return {
                'yaw': float(yaw),
                'pitch': float(pitch),
                'roll': float(roll)
            }
        
        except Exception as e:
            logger.error(f"Head pose estimation failed: {e}")
            return {'yaw': 0.0, 'pitch': 0.0, 'roll': 0.0}
    
    def validate_pose(self, angles: Dict[str, float], expected_pose: str) -> bool:
        """
        Validate if detected angles match expected pose
        
        Args:
            angles: Detected yaw, pitch, roll
            expected_pose: One of 'center', 'tilt_down', 'turn_right', 'turn_left'
        
        Returns:
            True if pose is valid
        """
        if expected_pose not in self.POSE_REQUIREMENTS:
            logger.warning(f"Unknown pose type: {expected_pose}")
            return False
        
        requirements = self.POSE_REQUIREMENTS[expected_pose]
        
        # Check yaw (left-right)
        yaw_min, yaw_max = requirements['yaw']
        yaw_valid = yaw_min <= angles['yaw'] <= yaw_max
        
        # Check pitch (up-down)
        pitch_min, pitch_max = requirements['pitch']
        pitch_valid = pitch_min <= angles['pitch'] <= pitch_max
        
        return yaw_valid and pitch_valid
    
    def process_frame(
        self,
        base64_frame: str,
        expected_pose: str
    ) -> Optional[Dict]:
        """
        Process a single frame from liveness video
        
        Returns:
            Dictionary with face data if valid, None otherwise
        """
        try:
            # Detect faces in frame
            cropped_faces, landmarks_list, metadata = face_detector.detect_faces_in_image(base64_frame)
            
            if len(cropped_faces) == 0:
                logger.warning("No face detected in frame")
                return None
            
            if len(cropped_faces) > 1:
                logger.warning(f"Multiple faces detected ({len(cropped_faces)}), using largest")
            
            # Use the first/largest face
            face = cropped_faces[0]
            landmarks = landmarks_list[0]
            face_metadata = metadata[0]
            
            # Check detection confidence
            if face_metadata['confidence'] < 0.5:
                logger.warning(f"Low confidence detection: {face_metadata['confidence']}")
                return None
            
            # Estimate head pose
            image_shape = face.shape
            angles = self.estimate_head_pose(landmarks, image_shape)
            
            # Validate pose
            is_valid_pose = self.validate_pose(angles, expected_pose)
            
            # Normalize face
            normalized_face = face_normalizer.normalize_face(face, landmarks)
            
            if normalized_face is None:
                logger.warning("Face normalization failed")
                return None
            
            # Check quality
            quality = face_normalizer.quality_check(normalized_face)
            
            return {
                'face': face,
                'normalized_face': normalized_face,
                'landmarks': landmarks,
                'angles': angles,
                'is_valid_pose': is_valid_pose,
                'quality': quality,
                'confidence': face_metadata['confidence']
            }
        
        except Exception as e:
            logger.error(f"Frame processing failed: {e}")
            return None
    
    def process_liveness_video(
        self,
        frames_by_pose: Dict[str, List[str]]
    ) -> Dict:
        """
        Process complete liveness detection video
        
        Args:
            frames_by_pose: Dictionary mapping pose types to lists of base64 frames
                {
                    'center': [frame1, frame2, ...],
                    'tilt_down': [frame1, frame2, ...],
                    'turn_right': [frame1, frame2, ...],
                    'turn_left': [frame1, frame2, ...]
                }
        
        Returns:
            Dictionary with results:
            {
                'is_live': bool,
                'poses_detected': {'center': True, 'tilt_down': True, ...},
                'embeddings': [emb1, emb2, ...],
                'quality_scores': {...},
                'message': str
            }
        """
        results = {
            'is_live': False,
            'poses_detected': {},
            'embeddings': [],
            'quality_scores': {},
            'message': ''
        }
        
        all_normalized_faces = []
        pose_validations = {}
        
        # Process each pose
        for pose_type, frames in frames_by_pose.items():
            logger.info(f"Processing {len(frames)} frames for pose: {pose_type}")
            
            valid_frames = []
            
            for frame_base64 in frames:
                frame_data = self.process_frame(frame_base64, pose_type)
                
                if frame_data and frame_data['is_valid_pose']:
                    valid_frames.append(frame_data)
            
            # Check if enough valid frames
            pose_valid = len(valid_frames) >= self.min_frames_per_pose
            pose_validations[pose_type] = pose_valid
            
            logger.info(f"Pose '{pose_type}': {len(valid_frames)} valid frames (required: {self.min_frames_per_pose})")
            
            # Collect normalized faces from valid frames
            if pose_valid:
                # Take best quality frames
                sorted_frames = sorted(
                    valid_frames,
                    key=lambda x: x['quality'].get('sharpness', 0),
                    reverse=True
                )
                
                # Take top 3 frames from each pose
                for frame_data in sorted_frames[:3]:
                    all_normalized_faces.append(frame_data['normalized_face'])
        
        # Update results
        results['poses_detected'] = pose_validations
        
        # Check if all required poses detected
        required_poses = ['center', 'tilt_down', 'turn_right', 'turn_left']
        all_poses_valid = all(pose_validations.get(pose, False) for pose in required_poses)
        
        if not all_poses_valid:
            missing_poses = [pose for pose in required_poses if not pose_validations.get(pose, False)]
            results['message'] = f"Failed liveness check. Missing or invalid poses: {', '.join(missing_poses)}"
            return results
        
        # Extract embeddings from collected faces
        if len(all_normalized_faces) > 0:
            embeddings = face_recognizer.extract_embeddings_from_list(all_normalized_faces)
            
            if len(embeddings) > 0:
                results['embeddings'] = embeddings
                results['is_live'] = True
                results['message'] = f"Liveness check passed! Extracted {len(embeddings)} embeddings from {len(all_normalized_faces)} frames"
            else:
                results['message'] = "Failed to extract embeddings from faces"
        else:
            results['message'] = "No valid faces collected from video"
        
        return results
    
    def group_frames_by_pose(self, frames: List[Dict]) -> Dict[str, List[str]]:
        """
        Group frames by their pose type
        
        Args:
            frames: List of frame objects with 'pose_type' and 'frame_data'
        
        Returns:
            Dictionary mapping pose types to frame lists
        """
        grouped = {
            'center': [],
            'tilt_down': [],
            'turn_right': [],
            'turn_left': []
        }
        
        for frame in frames:
            pose_type = frame.get('pose_type', '').lower()
            frame_data = frame.get('frame_data', '')
            
            if pose_type in grouped and frame_data:
                grouped[pose_type].append(frame_data)
        
        return grouped


# Global instance
liveness_detector = LivenessDetectionService()