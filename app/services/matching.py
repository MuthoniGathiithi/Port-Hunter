"""
Face Matching Service
Matches detected faces against registered students for attendance
"""
import numpy as np
from typing import List, Dict, Optional, Tuple
import logging
from app.config import settings
from app.services.face_recognition import face_recognizer

logger = logging.getLogger(__name__)


class FaceMatchingService:
    """Handles matching detected faces with registered students"""
    
    def __init__(self):
        self.similarity_threshold = settings.RECOGNITION_SIMILARITY_THRESHOLD
    
    def match_single_face(
        self,
        query_embedding: np.ndarray,
        student_records: List[Dict]
    ) -> Optional[Dict]:
        """
        Match a single detected face against all registered students
        
        Args:
            query_embedding: Embedding from detected face
            student_records: List of student dictionaries with 'id', 'name', 'admission_number', 'embeddings'
        
        Returns:
            Best match dictionary with student info and similarity score, or None
        """
        best_match = None
        best_similarity = 0.0
        
        for student in student_records:
            student_embeddings = student.get('embeddings', [])
            
            if not student_embeddings or len(student_embeddings) == 0:
                continue
            
            # Compare against all embeddings for this student
            # (they have multiple embeddings from different registration poses)
            max_similarity = 0.0
            
            for student_embedding in student_embeddings:
                # Convert to numpy array if it's a list
                if isinstance(student_embedding, list):
                    student_embedding = np.array(student_embedding)
                
                similarity = face_recognizer.compute_similarity(
                    query_embedding,
                    student_embedding
                )
                
                if similarity > max_similarity:
                    max_similarity = similarity
            
            # Keep track of best match
            if max_similarity > best_similarity:
                best_similarity = max_similarity
                best_match = {
                    'student_id': student['id'],
                    'student_name': student['full_name'],
                    'admission_number': student['admission_number'],
                    'similarity_score': max_similarity
                }
        
        # Check if best match exceeds threshold
        if best_match and best_similarity >= self.similarity_threshold:
            logger.info(
                f"Match found: {best_match['student_name']} "
                f"(confidence: {best_similarity:.3f})"
            )
            return best_match
        else:
            logger.info(f"No match found (best similarity: {best_similarity:.3f})")
            return None
    
    def match_multiple_faces(
        self,
        query_embeddings: List[np.ndarray],
        student_records: List[Dict],
        detected_faces_metadata: List[Dict]
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Match multiple detected faces against registered students
        
        Args:
            query_embeddings: List of embeddings from detected faces
            student_records: List of registered students
            detected_faces_metadata: Metadata for each detected face (bbox, confidence, etc.)
        
        Returns:
            Tuple of (matched_students, unknown_faces)
            - matched_students: List of dicts with student info and match details
            - unknown_faces: List of dicts with unmatched face data
        """
        matched_students = []
        unknown_faces = []
        matched_student_ids = set()
        
        for idx, query_embedding in enumerate(query_embeddings):
            metadata = detected_faces_metadata[idx] if idx < len(detected_faces_metadata) else {}
            
            # Try to match this face
            match_result = self.match_single_face(query_embedding, student_records)
            
            if match_result:
                student_id = match_result['student_id']
                
                # Check if student already matched (avoid duplicates)
                if student_id not in matched_student_ids:
                    matched_students.append({
                        **match_result,
                        'bbox': metadata.get('bbox'),
                        'detection_confidence': metadata.get('confidence')
                    })
                    matched_student_ids.add(student_id)
                else:
                    logger.info(
                        f"Student {match_result['student_name']} already marked present"
                    )
            else:
                # Unknown face
                unknown_faces.append({
                    'embedding': query_embedding.tolist(),
                    'bbox': metadata.get('bbox'),
                    'detection_confidence': metadata.get('confidence'),
                    'landmarks': metadata.get('landmarks')
                })
        
        logger.info(
            f"Matching complete: {len(matched_students)} matched, "
            f"{len(unknown_faces)} unknown"
        )
        
        return matched_students, unknown_faces
    
    def get_absent_students(
        self,
        all_students: List[Dict],
        present_student_ids: List[str]
    ) -> List[Dict]:
        """
        Determine which students are absent
        
        Args:
            all_students: All registered students in unit
            present_student_ids: IDs of students marked present
        
        Returns:
            List of absent student dictionaries
        """
        absent_students = []
        present_ids_set = set(present_student_ids)
        
        for student in all_students:
            if student['id'] not in present_ids_set:
                absent_students.append({
                    'student_id': student['id'],
                    'student_name': student['full_name'],
                    'admission_number': student['admission_number'],
                    'status': 'absent'
                })
        
        logger.info(f"Found {len(absent_students)} absent students")
        return absent_students
    
    def process_attendance(
        self,
        detected_embeddings: List[np.ndarray],
        detected_faces_metadata: List[Dict],
        registered_students: List[Dict]
    ) -> Dict:
        """
        Complete attendance processing pipeline
        
        Args:
            detected_embeddings: Embeddings from all detected faces
            detected_faces_metadata: Metadata for detected faces
            registered_students: All registered students in unit
        
        Returns:
            Dictionary with complete attendance results
        """
        # Match detected faces
        matched_students, unknown_faces = self.match_multiple_faces(
            detected_embeddings,
            registered_students,
            detected_faces_metadata
        )
        
        # Get present student IDs
        present_student_ids = [s['student_id'] for s in matched_students]
        
        # Get absent students
        absent_students = self.get_absent_students(
            registered_students,
            present_student_ids
        )
        
        # Compile results
        results = {
            'total_registered': len(registered_students),
            'total_present': len(matched_students),
            'total_absent': len(absent_students),
            'total_unknown_faces': len(unknown_faces),
            'present_students': matched_students,
            'absent_students': absent_students,
            'unknown_faces': unknown_faces
        }
        
        logger.info(
            f"Attendance summary - Registered: {results['total_registered']}, "
            f"Present: {results['total_present']}, "
            f"Absent: {results['total_absent']}, "
            f"Unknown: {results['total_unknown_faces']}"
        )
        
        return results
    
    def merge_results_from_multiple_photos(
        self,
        results_list: List[Dict]
    ) -> Dict:
        """
        Merge attendance results from multiple classroom photos
        
        Logic: Student is present if detected in ANY photo (union)
        
        Args:
            results_list: List of attendance result dictionaries
        
        Returns:
            Merged attendance results
        """
        if len(results_list) == 0:
            return {
                'total_registered': 0,
                'total_present': 0,
                'total_absent': 0,
                'total_unknown_faces': 0,
                'present_students': [],
                'absent_students': [],
                'unknown_faces': []
            }
        
        # Use union for present students
        all_present_ids = set()
        present_students_map = {}
        
        for results in results_list:
            for student in results['present_students']:
                student_id = student['student_id']
                if student_id not in all_present_ids:
                    all_present_ids.add(student_id)
                    present_students_map[student_id] = student
        
        # Collect all unknown faces
        all_unknown_faces = []
        for results in results_list:
            all_unknown_faces.extend(results['unknown_faces'])
        
        # Get total registered (should be same across all photos)
        total_registered = results_list[0]['total_registered']
        
        # Recalculate absent
        all_students = []
        for results in results_list:
            # Reconstruct full student list
            all_students = results['present_students'] + results['absent_students']
            break
        
        merged_results = {
            'total_registered': total_registered,
            'total_present': len(all_present_ids),
            'total_absent': total_registered - len(all_present_ids),
            'total_unknown_faces': len(all_unknown_faces),
            'present_students': list(present_students_map.values()),
            'absent_students': self.get_absent_students(
                all_students,
                list(all_present_ids)
            ),
            'unknown_faces': all_unknown_faces
        }
        
        logger.info(
            f"Merged results from {len(results_list)} photos - "
            f"Present: {merged_results['total_present']}"
        )
        
        return merged_results


# Global instance
face_matcher = FaceMatchingService()