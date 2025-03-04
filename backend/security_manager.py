from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization
import base64
import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import hashlib
import logging
from enum import Enum
import jwt
from fastapi import HTTPException

class DataCategory(Enum):
    VOICE = "voice_data"
    FACIAL = "facial_data"
    BIOMETRIC = "biometric_data"
    PERSONAL = "personal_data"
    PREFERENCES = "preferences"
    INTERACTION = "interaction_history"
    LOCATION = "location_data"

class SecurityManager:
    def __init__(self):
        self.setup_encryption()
        self.setup_logging()
        self.load_privacy_settings()
        
    def setup_encryption(self):
        """Initialize encryption keys and settings"""
        # Generate or load master key
        if os.path.exists('keys/master.key'):
            with open('keys/master.key', 'rb') as f:
                self.master_key = f.read()
        else:
            os.makedirs('keys', exist_ok=True)
            self.master_key = Fernet.generate_key()
            with open('keys/master.key', 'wb') as f:
                f.write(self.master_key)

        # Initialize Fernet cipher
        self.cipher = Fernet(self.master_key)
        
        # Generate RSA key pair for end-to-end encryption
        self.private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048
        )
        self.public_key = self.private_key.public_key()

    def setup_logging(self):
        """Set up secure logging"""
        logging.basicConfig(
            filename='security.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('security_manager')

    def load_privacy_settings(self):
        """Load privacy settings and GDPR configurations"""
        self.privacy_settings = {
            'retention_periods': {
                DataCategory.VOICE.value: 30,  # days
                DataCategory.FACIAL.value: 30,
                DataCategory.BIOMETRIC.value: 90,
                DataCategory.PERSONAL.value: 365,
                DataCategory.PREFERENCES.value: 365,
                DataCategory.INTERACTION.value: 180,
                DataCategory.LOCATION.value: 30
            },
            'encryption_required': {
                DataCategory.VOICE.value: True,
                DataCategory.FACIAL.value: True,
                DataCategory.BIOMETRIC.value: True,
                DataCategory.PERSONAL.value: True,
                DataCategory.PREFERENCES.value: True,
                DataCategory.INTERACTION.value: True,
                DataCategory.LOCATION.value: True
            },
            'consent_required': {
                DataCategory.VOICE.value: True,
                DataCategory.FACIAL.value: True,
                DataCategory.BIOMETRIC.value: True,
                DataCategory.PERSONAL.value: True,
                DataCategory.PREFERENCES.value: True,
                DataCategory.INTERACTION.value: True,
                DataCategory.LOCATION.value: True
            }
        }

    async def encrypt_data(self, data: Any, category: DataCategory) -> str:
        """Encrypt data using appropriate method based on category"""
        try:
            # Convert data to JSON string
            data_str = json.dumps(data)
            
            # Add metadata for GDPR compliance
            metadata = {
                'category': category.value,
                'timestamp': datetime.utcnow().isoformat(),
                'encryption_version': '1.0'
            }
            
            # Combine data and metadata
            full_data = json.dumps({
                'metadata': metadata,
                'data': data_str
            })
            
            # Encrypt
            encrypted_data = self.cipher.encrypt(full_data.encode())
            return base64.b64encode(encrypted_data).decode()
            
        except Exception as e:
            self.logger.error(f"Encryption error: {str(e)}")
            raise HTTPException(status_code=500, detail="Encryption failed")

    async def decrypt_data(self, encrypted_data: str, category: DataCategory) -> Any:
        """Decrypt data and verify metadata"""
        try:
            # Decode and decrypt
            decoded_data = base64.b64decode(encrypted_data)
            decrypted_data = self.cipher.decrypt(decoded_data)
            
            # Parse JSON
            full_data = json.loads(decrypted_data)
            metadata = full_data['metadata']
            
            # Verify category and check retention period
            if metadata['category'] != category.value:
                raise ValueError("Data category mismatch")
                
            timestamp = datetime.fromisoformat(metadata['timestamp'])
            retention_days = self.privacy_settings['retention_periods'][category.value]
            if datetime.utcnow() - timestamp > timedelta(days=retention_days):
                raise ValueError("Data retention period expired")
            
            return json.loads(full_data['data'])
            
        except Exception as e:
            self.logger.error(f"Decryption error: {str(e)}")
            raise HTTPException(status_code=500, detail="Decryption failed")

    async def get_user_privacy_settings(self, user_id: str) -> Dict[str, Any]:
        """Get user's privacy settings and consent status"""
        try:
            privacy_file = f'privacy/{user_id}_privacy.json'
            if os.path.exists(privacy_file):
                with open(privacy_file, 'r') as f:
                    return json.load(f)
            return {
                'consents': {cat.value: False for cat in DataCategory},
                'retention_preferences': self.privacy_settings['retention_periods'].copy(),
                'data_usage_preferences': {cat.value: [] for cat in DataCategory}
            }
        except Exception as e:
            self.logger.error(f"Error getting privacy settings: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get privacy settings")

    async def update_user_privacy_settings(
        self,
        user_id: str,
        settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update user's privacy settings and consent preferences"""
        try:
            os.makedirs('privacy', exist_ok=True)
            privacy_file = f'privacy/{user_id}_privacy.json'
            
            # Validate settings
            required_keys = {'consents', 'retention_preferences', 'data_usage_preferences'}
            if not all(key in settings for key in required_keys):
                raise ValueError("Missing required privacy settings")
            
            # Save settings
            with open(privacy_file, 'w') as f:
                json.dump(settings, f)
            
            self.logger.info(f"Updated privacy settings for user {user_id}")
            return settings
            
        except Exception as e:
            self.logger.error(f"Error updating privacy settings: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to update privacy settings")

    async def delete_user_data(
        self,
        user_id: str,
        categories: Optional[List[DataCategory]] = None
    ) -> Dict[str, Any]:
        """Delete user data for specified categories"""
        try:
            if categories is None:
                categories = list(DataCategory)
            
            deleted_data = {}
            for category in categories:
                # Delete data files
                data_path = f'data/{user_id}/{category.value}'
                if os.path.exists(data_path):
                    os.remove(data_path)
                    deleted_data[category.value] = True
                
            self.logger.info(f"Deleted data for user {user_id}: {categories}")
            return {
                'status': 'success',
                'deleted_categories': deleted_data
            }
            
        except Exception as e:
            self.logger.error(f"Error deleting user data: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to delete user data")

    async def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data in GDPR-compliant format"""
        try:
            export_data = {
                'user_id': user_id,
                'export_date': datetime.utcnow().isoformat(),
                'data': {}
            }
            
            # Collect data from all categories
            for category in DataCategory:
                data_path = f'data/{user_id}/{category.value}'
                if os.path.exists(data_path):
                    with open(data_path, 'r') as f:
                        encrypted_data = f.read()
                        decrypted_data = await self.decrypt_data(encrypted_data, category)
                        export_data['data'][category.value] = decrypted_data
            
            return export_data
            
        except Exception as e:
            self.logger.error(f"Error exporting user data: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to export user data")

    async def verify_consent(
        self,
        user_id: str,
        category: DataCategory
    ) -> bool:
        """Verify user consent for specific data category"""
        try:
            settings = await self.get_user_privacy_settings(user_id)
            return settings['consents'].get(category.value, False)
        except Exception as e:
            self.logger.error(f"Error verifying consent: {str(e)}")
            return False

    async def log_data_access(
        self,
        user_id: str,
        category: DataCategory,
        action: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log data access for audit purposes"""
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat(),
                'user_id': user_id,
                'category': category.value,
                'action': action,
                'details': details or {}
            }
            
            os.makedirs('audit_logs', exist_ok=True)
            with open(f'audit_logs/{datetime.utcnow().date()}.log', 'a') as f:
                f.write(json.dumps(log_entry) + '\n')
                
        except Exception as e:
            self.logger.error(f"Error logging data access: {str(e)}")

    async def get_data_access_logs(
        self,
        user_id: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get data access logs for audit purposes"""
        try:
            logs = []
            if not start_date:
                start_date = datetime.utcnow() - timedelta(days=30)
            if not end_date:
                end_date = datetime.utcnow()
            
            current_date = start_date
            while current_date <= end_date:
                log_file = f'audit_logs/{current_date.date()}.log'
                if os.path.exists(log_file):
                    with open(log_file, 'r') as f:
                        for line in f:
                            log_entry = json.loads(line)
                            if log_entry['user_id'] == user_id:
                                logs.append(log_entry)
                current_date += timedelta(days=1)
            
            return logs
            
        except Exception as e:
            self.logger.error(f"Error getting access logs: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to get access logs")
