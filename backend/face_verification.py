import cv2
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import load_model
from mtcnn import MTCNN
from deepface import DeepFace
import mediapipe as mp
from typing import Tuple, Dict, Optional
import os
import json
import base64
from datetime import datetime

class FaceVerificationSystem:
    def __init__(self):
        # Initialize face detection
        self.mtcnn = MTCNN()
        
        # Initialize MediaPipe for face mesh (used in liveness detection)
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Initialize user database
        self.users_db_path = "face_db"
        os.makedirs(self.users_db_path, exist_ok=True)
        
        # Load face embeddings database
        self.load_face_database()

    def load_face_database(self):
        """Load existing face embeddings database"""
        self.face_db = {}
        db_file = os.path.join(self.users_db_path, "face_db.json")
        if os.path.exists(db_file):
            with open(db_file, 'r') as f:
                self.face_db = json.load(f)

    def save_face_database(self):
        """Save face embeddings database"""
        db_file = os.path.join(self.users_db_path, "face_db.json")
        with open(db_file, 'w') as f:
            json.dump(self.face_db, f)

    def detect_face(self, image: np.ndarray) -> Optional[np.ndarray]:
        """Detect and align face in image"""
        try:
            # Detect face using MTCNN
            faces = self.mtcnn.detect_faces(image)
            if not faces:
                return None

            # Get the largest face
            face = max(faces, key=lambda x: x['confidence'])
            x, y, w, h = face['box']
            
            # Extract and align face
            face_img = image[y:y+h, x:x+w]
            return cv2.resize(face_img, (160, 160))
        except Exception as e:
            print(f"Error in face detection: {str(e)}")
            return None

    def check_liveness(self, image: np.ndarray) -> Tuple[bool, float]:
        """
        Check if the face is from a real person using multiple liveness detection methods
        Returns: (is_live, confidence_score)
        """
        try:
            # Convert to RGB
            rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            
            # Get face mesh landmarks
            results = self.face_mesh.process(rgb_image)
            if not results.multi_face_landmarks:
                return False, 0.0

            landmarks = results.multi_face_landmarks[0]
            
            # Perform liveness checks
            score = 0.0
            
            # Check 1: Depth variation in landmarks
            depths = [landmark.z for landmark in landmarks.landmark]
            depth_variation = np.std(depths)
            if depth_variation > 0.01:  # Natural face should have some depth variation
                score += 0.3
            
            # Check 2: Eye aspect ratio (blink detection)
            left_eye = self._get_eye_aspect_ratio(landmarks, "left")
            right_eye = self._get_eye_aspect_ratio(landmarks, "right")
            if 0.2 < left_eye < 0.5 and 0.2 < right_eye < 0.5:  # Natural eye aspect ratio range
                score += 0.3
            
            # Check 3: Texture analysis
            if self._check_texture_naturalness(image):
                score += 0.4
            
            return score >= 0.7, score
            
        except Exception as e:
            print(f"Error in liveness detection: {str(e)}")
            return False, 0.0

    def _get_eye_aspect_ratio(self, landmarks, eye_side: str) -> float:
        """Calculate eye aspect ratio for blink detection"""
        if eye_side == "left":
            pts = [33, 160, 158, 133, 153, 144]  # Left eye landmarks
        else:
            pts = [362, 385, 387, 263, 373, 380]  # Right eye landmarks
            
        points = [landmarks.landmark[pt] for pt in pts]
        
        # Calculate vertical distances
        v1 = np.sqrt((points[1].x - points[5].x)**2 + (points[1].y - points[5].y)**2)
        v2 = np.sqrt((points[2].x - points[4].x)**2 + (points[2].y - points[4].y)**2)
        
        # Calculate horizontal distance
        h = np.sqrt((points[0].x - points[3].x)**2 + (points[0].y - points[3].y)**2)
        
        return (v1 + v2) / (2.0 * h)

    def _check_texture_naturalness(self, image: np.ndarray) -> bool:
        """
        Check if the face texture appears natural using frequency analysis
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply FFT
        f_transform = np.fft.fft2(gray)
        f_shift = np.fft.fftshift(f_transform)
        magnitude_spectrum = np.abs(f_shift)
        
        # Calculate frequency distribution
        freq_distribution = np.sum(magnitude_spectrum) / (image.shape[0] * image.shape[1])
        
        # Natural faces typically have a certain range of frequency distribution
        return 10 < freq_distribution < 1000

    def register_face(self, image_data: str, user_id: str) -> Dict:
        """
        Register a new face in the database
        """
        try:
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Check liveness
            is_live, liveness_score = self.check_liveness(image)
            if not is_live:
                return {
                    "success": False,
                    "error": "Liveness check failed. Please use a real face."
                }
            
            # Detect and align face
            face = self.detect_face(image)
            if face is None:
                return {
                    "success": False,
                    "error": "No face detected in the image."
                }
            
            # Generate face embedding using DeepFace
            embedding = DeepFace.represent(face, model_name="Facenet")[0]["embedding"]
            
            # Save to database
            self.face_db[user_id] = {
                "embedding": embedding,
                "registered_at": datetime.now().isoformat(),
                "last_verified": None
            }
            self.save_face_database()
            
            return {
                "success": True,
                "message": "Face registered successfully"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Registration failed: {str(e)}"
            }

    def verify_face(self, image_data: str, user_id: str) -> Dict:
        """
        Verify a face against the registered face
        """
        try:
            if user_id not in self.face_db:
                return {
                    "success": False,
                    "error": "User not registered."
                }
            
            # Decode base64 image
            image_bytes = base64.b64decode(image_data.split(',')[1])
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Check liveness
            is_live, liveness_score = self.check_liveness(image)
            if not is_live:
                return {
                    "success": False,
                    "error": "Liveness check failed. Please use a real face."
                }
            
            # Detect and align face
            face = self.detect_face(image)
            if face is None:
                return {
                    "success": False,
                    "error": "No face detected in the image."
                }
            
            # Generate face embedding
            embedding = DeepFace.represent(face, model_name="Facenet")[0]["embedding"]
            
            # Compare with stored embedding
            stored_embedding = self.face_db[user_id]["embedding"]
            distance = np.linalg.norm(np.array(embedding) - np.array(stored_embedding))
            
            # Update last verification time if successful
            if distance < 0.6:  # Threshold for face match
                self.face_db[user_id]["last_verified"] = datetime.now().isoformat()
                self.save_face_database()
                return {
                    "success": True,
                    "message": "Face verification successful",
                    "confidence": 1 - (distance / 2)  # Convert distance to confidence score
                }
            else:
                return {
                    "success": False,
                    "error": "Face verification failed. Please try again."
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Verification failed: {str(e)}"
            }
