import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import librosa
import cv2
from typing import Dict, List, Any, Optional, Tuple
import json
import os
from datetime import datetime, timedelta
import pickle
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
from collections import defaultdict
import torch
from transformers import pipeline
from deepface import DeepFace

class AIEnhancement:
    def __init__(self):
        self.memory_path = "memory"
        self.models_path = "models"
        os.makedirs(self.memory_path, exist_ok=True)
        os.makedirs(self.models_path, exist_ok=True)
        
        self.setup_models()
        self.load_memory()

    def setup_models(self):
        """Initialize AI models for various analyses"""
        # Emotion detection models
        self.voice_emotion = pipeline("audio-classification", model="speechbrain/emotion-recognition-wav2vec2-IEMOCAP")
        self.face_emotion = DeepFace.build_model("Emotion")
        
        # Load or create behavioral model
        behavior_model_path = os.path.join(self.models_path, "behavior_model.pkl")
        if os.path.exists(behavior_model_path):
            with open(behavior_model_path, 'rb') as f:
                self.behavior_model = pickle.load(f)
        else:
            self.behavior_model = self._create_behavior_model()

    def _create_behavior_model(self):
        """Create initial behavior prediction model"""
        model = models.Sequential([
            layers.Dense(128, activation='relu', input_shape=(50,)),
            layers.Dropout(0.3),
            layers.Dense(64, activation='relu'),
            layers.Dropout(0.2),
            layers.Dense(32, activation='relu'),
            layers.Dense(10, activation='softmax')
        ])
        model.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])
        return model

    def load_memory(self):
        """Load user memory and interaction history"""
        self.memory = defaultdict(lambda: {
            'preferences': {},
            'interactions': [],
            'emotions': [],
            'behavior_patterns': [],
            'context_history': []
        })
        
        memory_file = os.path.join(self.memory_path, "user_memory.json")
        if os.path.exists(memory_file):
            with open(memory_file, 'r') as f:
                saved_memory = json.load(f)
                for user_id, data in saved_memory.items():
                    self.memory[user_id].update(data)

    def save_memory(self):
        """Save user memory to disk"""
        memory_file = os.path.join(self.memory_path, "user_memory.json")
        with open(memory_file, 'w') as f:
            json.dump(self.memory, f)

    async def analyze_voice_emotion(self, audio_data: bytes) -> Dict[str, float]:
        """Analyze emotion from voice data"""
        try:
            # Convert audio to required format
            y, sr = librosa.load(audio_data, sr=16000)
            
            # Extract audio features
            mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Get emotion predictions
            predictions = self.voice_emotion(y)
            
            # Extract additional voice features
            pitch = librosa.pitch_tuning(y)
            tempo = librosa.beat.tempo(y)
            
            emotions = {
                pred['label']: pred['score']
                for pred in predictions
            }
            
            return {
                'emotions': emotions,
                'features': {
                    'pitch': float(np.mean(pitch)),
                    'tempo': float(tempo[0]),
                    'energy': float(np.mean(librosa.feature.rms(y=y)))
                }
            }
        except Exception as e:
            print(f"Error in voice emotion analysis: {str(e)}")
            return {'emotions': {'neutral': 1.0}, 'features': {}}

    async def analyze_facial_emotion(self, image_data: bytes) -> Dict[str, float]:
        """Analyze emotion from facial expression"""
        try:
            # Convert image data to numpy array
            nparr = np.frombuffer(image_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            # Analyze facial emotions
            result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
            
            return {
                'emotions': result[0]['emotion'],
                'dominant_emotion': result[0]['dominant_emotion']
            }
        except Exception as e:
            print(f"Error in facial emotion analysis: {str(e)}")
            return {'emotions': {'neutral': 1.0}, 'dominant_emotion': 'neutral'}

    async def update_user_context(
        self,
        user_id: str,
        interaction_data: Dict[str, Any],
        emotions: Optional[Dict[str, Any]] = None
    ):
        """Update user context with new interaction data and emotions"""
        timestamp = datetime.now().isoformat()
        
        # Update interaction history
        self.memory[user_id]['interactions'].append({
            'timestamp': timestamp,
            'data': interaction_data
        })
        
        # Update emotion history if available
        if emotions:
            self.memory[user_id]['emotions'].append({
                'timestamp': timestamp,
                'emotions': emotions
            })
        
        # Update behavior patterns
        self._update_behavior_patterns(user_id, interaction_data)
        
        # Trim old data
        self._trim_old_data(user_id)
        
        # Save updated memory
        self.save_memory()

    def _update_behavior_patterns(self, user_id: str, interaction_data: Dict[str, Any]):
        """Update user behavior patterns"""
        patterns = self.memory[user_id]['behavior_patterns']
        
        # Extract features from interaction
        features = self._extract_behavior_features(interaction_data)
        
        # Add new pattern
        patterns.append({
            'timestamp': datetime.now().isoformat(),
            'features': features
        })
        
        # Update behavior model if enough data
        if len(patterns) >= 10:
            self._update_behavior_model(user_id)

    def _extract_behavior_features(self, interaction_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract relevant features from interaction data"""
        features = {
            'time_of_day': datetime.now().hour,
            'day_of_week': datetime.now().weekday(),
            'command_type': interaction_data.get('type', 'unknown'),
            'command_category': interaction_data.get('category', 'unknown'),
        }
        
        return features

    def _update_behavior_model(self, user_id: str):
        """Update the behavior prediction model for a user"""
        patterns = self.memory[user_id]['behavior_patterns']
        
        # Prepare training data
        X = np.array([list(p['features'].values()) for p in patterns])
        
        # Normalize data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Update model
        self.behavior_model.fit(X_scaled, X_scaled, epochs=5, batch_size=32, verbose=0)

    async def get_predictive_suggestions(
        self,
        user_id: str,
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate predictive suggestions based on user behavior"""
        try:
            # Get recent patterns
            patterns = self.memory[user_id]['behavior_patterns'][-50:]
            if not patterns:
                return []
            
            # Extract current context features
            current_features = self._extract_behavior_features(current_context)
            
            # Find similar past behaviors
            similar_patterns = self._find_similar_patterns(patterns, current_features)
            
            # Generate suggestions
            suggestions = self._generate_suggestions(similar_patterns, current_context)
            
            return suggestions
        except Exception as e:
            print(f"Error generating suggestions: {str(e)}")
            return []

    def _find_similar_patterns(
        self,
        patterns: List[Dict[str, Any]],
        current_features: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find patterns similar to current context"""
        # Convert patterns to feature vectors
        X = np.array([list(p['features'].values()) for p in patterns])
        current = np.array(list(current_features.values())).reshape(1, -1)
        
        # Normalize
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        current_scaled = scaler.transform(current)
        
        # Find similar patterns using K-means
        kmeans = KMeans(n_clusters=min(5, len(patterns)))
        kmeans.fit(X_scaled)
        
        # Get cluster of current features
        current_cluster = kmeans.predict(current_scaled)[0]
        
        # Return patterns in same cluster
        similar_indices = np.where(kmeans.labels_ == current_cluster)[0]
        return [patterns[i] for i in similar_indices]

    def _generate_suggestions(
        self,
        similar_patterns: List[Dict[str, Any]],
        current_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate suggestions based on similar patterns"""
        suggestions = []
        
        # Group patterns by command type and category
        grouped_patterns = defaultdict(list)
        for pattern in similar_patterns:
            key = (pattern['features']['command_type'], pattern['features']['command_category'])
            grouped_patterns[key].append(pattern)
        
        # Generate suggestions for most common patterns
        for (cmd_type, category), patterns in sorted(
            grouped_patterns.items(),
            key=lambda x: len(x[1]),
            reverse=True
        )[:3]:
            suggestion = {
                'type': cmd_type,
                'category': category,
                'confidence': len(patterns) / len(similar_patterns),
                'context': {
                    'time_of_day': current_context.get('time_of_day'),
                    'day_of_week': current_context.get('day_of_week')
                }
            }
            suggestions.append(suggestion)
        
        return suggestions

    def _trim_old_data(self, user_id: str):
        """Remove old data to prevent memory overflow"""
        max_age = timedelta(days=30)
        now = datetime.now()
        
        for key in ['interactions', 'emotions', 'behavior_patterns']:
            self.memory[user_id][key] = [
                item for item in self.memory[user_id][key]
                if (now - datetime.fromisoformat(item['timestamp'])) <= max_age
            ]

    async def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get learned user preferences"""
        return self.memory[user_id]['preferences']

    async def update_user_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any]
    ):
        """Update user preferences"""
        self.memory[user_id]['preferences'].update(preferences)
        self.save_memory()

    async def get_emotional_context(
        self,
        user_id: str,
        timeframe: timedelta = timedelta(hours=1)
    ) -> Dict[str, Any]:
        """Get recent emotional context for user"""
        now = datetime.now()
        recent_emotions = [
            e for e in self.memory[user_id]['emotions']
            if (now - datetime.fromisoformat(e['timestamp'])) <= timeframe
        ]
        
        if not recent_emotions:
            return {'dominant_emotion': 'neutral', 'emotions': {}}
        
        # Aggregate emotions
        emotion_counts = defaultdict(float)
        for entry in recent_emotions:
            for emotion, score in entry['emotions'].items():
                emotion_counts[emotion] += score
        
        # Normalize
        total = sum(emotion_counts.values())
        emotions = {k: v/total for k, v in emotion_counts.items()}
        
        return {
            'dominant_emotion': max(emotions.items(), key=lambda x: x[1])[0],
            'emotions': emotions
        }
