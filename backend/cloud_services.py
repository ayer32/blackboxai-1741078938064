from typing import Dict, List, Any, Optional, BinaryIO
import boto3
import google.cloud.storage
import google.cloud.speech
import google.cloud.vision
from azure.storage.blob import BlobServiceClient
from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.speech import SpeechConfig, SpeechRecognizer
from msrest.authentication import CognitiveServicesCredentials
import logging
import os
from dotenv import load_dotenv

load_dotenv()

class CloudServices:
    def __init__(self):
        self.setup_logging()
        self.initialize_aws()
        self.initialize_gcp()
        self.initialize_azure()

    def setup_logging(self):
        """Set up logging for cloud operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('cloud_services')

    def initialize_aws(self):
        """Initialize AWS services"""
        try:
            self.aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
            self.aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
            self.aws_region = os.getenv("AWS_REGION", "us-east-1")

            # Initialize AWS clients
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )

            self.rekognition_client = boto3.client(
                'rekognition',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )

            self.transcribe_client = boto3.client(
                'transcribe',
                aws_access_key_id=self.aws_access_key,
                aws_secret_access_key=self.aws_secret_key,
                region_name=self.aws_region
            )

            self.logger.info("AWS services initialized successfully")

        except Exception as e:
            self.logger.error(f"AWS initialization error: {str(e)}")
            self.aws_available = False

    def initialize_gcp(self):
        """Initialize Google Cloud services"""
        try:
            self.gcp_project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            self.gcp_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

            # Initialize GCP clients
            self.gcs_client = google.cloud.storage.Client()
            self.speech_client = google.cloud.speech.SpeechClient()
            self.vision_client = google.cloud.vision.ImageAnnotatorClient()

            self.logger.info("GCP services initialized successfully")

        except Exception as e:
            self.logger.error(f"GCP initialization error: {str(e)}")
            self.gcp_available = False

    def initialize_azure(self):
        """Initialize Azure services"""
        try:
            self.azure_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
            self.azure_face_key = os.getenv("AZURE_FACE_KEY")
            self.azure_face_endpoint = os.getenv("AZURE_FACE_ENDPOINT")
            self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
            self.azure_speech_region = os.getenv("AZURE_SPEECH_REGION")

            # Initialize Azure clients
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.azure_connection_string
            )

            self.face_client = FaceClient(
                self.azure_face_endpoint,
                CognitiveServicesCredentials(self.azure_face_key)
            )

            self.speech_config = SpeechConfig(
                subscription=self.azure_speech_key,
                region=self.azure_speech_region
            )

            self.logger.info("Azure services initialized successfully")

        except Exception as e:
            self.logger.error(f"Azure initialization error: {str(e)}")
            self.azure_available = False

    # AWS Operations
    async def upload_to_s3(
        self,
        file_obj: BinaryIO,
        bucket: str,
        key: str
    ) -> Dict[str, str]:
        """Upload file to AWS S3"""
        try:
            self.s3_client.upload_fileobj(file_obj, bucket, key)
            url = f"https://{bucket}.s3.{self.aws_region}.amazonaws.com/{key}"
            return {"url": url, "bucket": bucket, "key": key}
        except Exception as e:
            self.logger.error(f"S3 upload error: {str(e)}")
            raise

    async def aws_face_detection(
        self,
        image_bytes: bytes
    ) -> List[Dict[str, Any]]:
        """Detect faces using AWS Rekognition"""
        try:
            response = self.rekognition_client.detect_faces(
                Image={'Bytes': image_bytes},
                Attributes=['ALL']
            )
            return response['FaceDetails']
        except Exception as e:
            self.logger.error(f"Rekognition error: {str(e)}")
            raise

    async def aws_transcribe_audio(
        self,
        audio_url: str,
        language_code: str = "en-US"
    ) -> str:
        """Transcribe audio using AWS Transcribe"""
        try:
            job_name = f"transcribe_{int(time.time())}"
            self.transcribe_client.start_transcription_job(
                TranscriptionJobName=job_name,
                Media={'MediaFileUri': audio_url},
                MediaFormat='mp3',
                LanguageCode=language_code
            )
            
            # Wait for completion
            while True:
                status = self.transcribe_client.get_transcription_job(
                    TranscriptionJobName=job_name
                )
                if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
                    break
                await asyncio.sleep(1)
                
            if status['TranscriptionJob']['TranscriptionJobStatus'] == 'COMPLETED':
                transcript_uri = status['TranscriptionJob']['Transcript']['TranscriptFileUri']
                # Get transcript text from URI
                return transcript_uri
            else:
                raise Exception("Transcription failed")
                
        except Exception as e:
            self.logger.error(f"Transcribe error: {str(e)}")
            raise

    # Google Cloud Operations
    async def upload_to_gcs(
        self,
        file_obj: BinaryIO,
        bucket_name: str,
        blob_name: str
    ) -> Dict[str, str]:
        """Upload file to Google Cloud Storage"""
        try:
            bucket = self.gcs_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            blob.upload_from_file(file_obj)
            url = f"https://storage.googleapis.com/{bucket_name}/{blob_name}"
            return {"url": url, "bucket": bucket_name, "name": blob_name}
        except Exception as e:
            self.logger.error(f"GCS upload error: {str(e)}")
            raise

    async def gcp_speech_to_text(
        self,
        audio_content: bytes,
        language_code: str = "en-US"
    ) -> str:
        """Convert speech to text using Google Cloud Speech-to-Text"""
        try:
            audio = google.cloud.speech.RecognitionAudio(content=audio_content)
            config = google.cloud.speech.RecognitionConfig(
                encoding=google.cloud.speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=16000,
                language_code=language_code,
            )
            
            response = self.speech_client.recognize(config=config, audio=audio)
            return " ".join(result.alternatives[0].transcript for result in response.results)
        except Exception as e:
            self.logger.error(f"Speech-to-Text error: {str(e)}")
            raise

    async def gcp_vision_analysis(
        self,
        image_content: bytes
    ) -> Dict[str, Any]:
        """Analyze image using Google Cloud Vision"""
        try:
            image = google.cloud.vision.Image(content=image_content)
            
            # Perform multiple analyses
            face_response = self.vision_client.face_detection(image=image)
            label_response = self.vision_client.label_detection(image=image)
            text_response = self.vision_client.text_detection(image=image)
            
            return {
                "faces": [face.face_annotations for face in face_response.face_annotations],
                "labels": [label.description for label in label_response.label_annotations],
                "text": text_response.text_annotations[0].description if text_response.text_annotations else ""
            }
        except Exception as e:
            self.logger.error(f"Vision analysis error: {str(e)}")
            raise

    # Azure Operations
    async def upload_to_azure_blob(
        self,
        file_obj: BinaryIO,
        container_name: str,
        blob_name: str
    ) -> Dict[str, str]:
        """Upload file to Azure Blob Storage"""
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            blob_client = container_client.get_blob_client(blob_name)
            blob_client.upload_blob(file_obj)
            url = blob_client.url
            return {"url": url, "container": container_name, "name": blob_name}
        except Exception as e:
            self.logger.error(f"Azure Blob upload error: {str(e)}")
            raise

    async def azure_face_verify(
        self,
        face_id1: str,
        face_id2: str
    ) -> Dict[str, Any]:
        """Verify two faces using Azure Face API"""
        try:
            verification = self.face_client.face.verify_face_to_face(
                face_id1=face_id1,
                face_id2=face_id2
            )
            return {
                "is_identical": verification.is_identical,
                "confidence": verification.confidence
            }
        except Exception as e:
            self.logger.error(f"Face verification error: {str(e)}")
            raise

    async def azure_speech_recognize(
        self,
        audio_stream: BinaryIO,
        language: str = "en-US"
    ) -> str:
        """Recognize speech using Azure Speech Service"""
        try:
            speech_recognizer = SpeechRecognizer(
                speech_config=self.speech_config,
                audio_config=audio_stream
            )
            
            result = speech_recognizer.recognize_once()
            if result.reason == ResultReason.RecognizedSpeech:
                return result.text
            else:
                raise Exception(f"Speech recognition failed: {result.reason}")
        except Exception as e:
            self.logger.error(f"Speech recognition error: {str(e)}")
            raise

    def get_available_services(self) -> Dict[str, bool]:
        """Get status of available cloud services"""
        return {
            "aws": self.aws_available,
            "gcp": self.gcp_available,
            "azure": self.azure_available
        }

    def get_service_quotas(self) -> Dict[str, Dict[str, Any]]:
        """Get service quotas and usage limits"""
        return {
            "aws": {
                "s3_storage": "5GB",
                "rekognition_requests": "5000/month",
                "transcribe_hours": "100/month"
            },
            "gcp": {
                "storage": "5GB",
                "speech_minutes": "60/day",
                "vision_requests": "1000/month"
            },
            "azure": {
                "blob_storage": "5GB",
                "face_requests": "1000/month",
                "speech_minutes": "60/day"
            }
        }
