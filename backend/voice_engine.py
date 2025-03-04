import torch
from TTS.api import TTS
from typing import Dict, List, Optional, Any
import json
import os
import numpy as np
from pydub import AudioSegment
import io
import logging
from dataclasses import dataclass
import azure.cognitiveservices.speech as speechsdk
from google.cloud import texttospeech
from elevenlabs import generate, set_api_key
from dotenv import load_dotenv

load_dotenv()

@dataclass
class VoiceConfig:
    name: str
    gender: str
    accent: str
    age: int
    emotion: str
    pitch: float = 1.0
    speed: float = 1.0
    volume: float = 1.0

class VoiceEngine:
    def __init__(self):
        self.setup_providers()
        self.load_voice_configs()
        self.setup_logging()

    def setup_providers(self):
        """Initialize various TTS providers"""
        # Azure Speech Service
        self.azure_speech_key = os.getenv("AZURE_SPEECH_KEY")
        self.azure_service_region = os.getenv("AZURE_SERVICE_REGION")
        
        # Google Cloud TTS
        self.google_credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        
        # ElevenLabs
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        if self.elevenlabs_api_key:
            set_api_key(self.elevenlabs_api_key)

        # Local Coqui TTS
        self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    def load_voice_configs(self):
        """Load voice configurations"""
        self.voices = {
            # American Voices
            "sarah": VoiceConfig(
                name="Sarah",
                gender="female",
                accent="American",
                age=30,
                emotion="friendly"
            ),
            "michael": VoiceConfig(
                name="Michael",
                gender="male",
                accent="American",
                age=35,
                emotion="professional"
            ),
            
            # British Voices
            "emma": VoiceConfig(
                name="Emma",
                gender="female",
                accent="British",
                age=28,
                emotion="cheerful"
            ),
            "james": VoiceConfig(
                name="James",
                gender="male",
                accent="British",
                age=40,
                emotion="formal"
            ),
            
            # Australian Voices
            "olivia": VoiceConfig(
                name="Olivia",
                gender="female",
                accent="Australian",
                age=25,
                emotion="energetic"
            ),
            
            # Indian Voices
            "priya": VoiceConfig(
                name="Priya",
                gender="female",
                accent="Indian",
                age=32,
                emotion="helpful"
            ),
            
            # Additional Accents
            "sofia": VoiceConfig(
                name="Sofia",
                gender="female",
                accent="Spanish",
                age=30,
                emotion="warm"
            ),
            "hans": VoiceConfig(
                name="Hans",
                gender="male",
                accent="German",
                age=45,
                emotion="authoritative"
            )
        }

    def setup_logging(self):
        """Set up logging for voice engine"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('voice_engine')

    async def synthesize_speech(
        self,
        text: str,
        voice_id: str,
        settings: Optional[Dict[str, float]] = None
    ) -> bytes:
        """Synthesize speech using the specified voice and settings"""
        try:
            voice_config = self.voices.get(voice_id)
            if not voice_config:
                raise ValueError(f"Voice {voice_id} not found")

            # Apply custom settings if provided
            if settings:
                voice_config.pitch = settings.get('pitch', voice_config.pitch)
                voice_config.speed = settings.get('speed', voice_config.speed)
                voice_config.volume = settings.get('volume', voice_config.volume)

            # Try ElevenLabs first for highest quality
            if self.elevenlabs_api_key:
                try:
                    audio = await self._synthesize_elevenlabs(text, voice_config)
                    if audio:
                        return audio
                except Exception as e:
                    self.logger.warning(f"ElevenLabs synthesis failed: {str(e)}")

            # Fall back to Azure
            if self.azure_speech_key:
                try:
                    audio = await self._synthesize_azure(text, voice_config)
                    if audio:
                        return audio
                except Exception as e:
                    self.logger.warning(f"Azure synthesis failed: {str(e)}")

            # Fall back to Google Cloud
            if self.google_credentials_path:
                try:
                    audio = await self._synthesize_google(text, voice_config)
                    if audio:
                        return audio
                except Exception as e:
                    self.logger.warning(f"Google synthesis failed: {str(e)}")

            # Final fallback to local TTS
            return await self._synthesize_local(text, voice_config)

        except Exception as e:
            self.logger.error(f"Speech synthesis failed: {str(e)}")
            raise

    async def _synthesize_elevenlabs(self, text: str, voice_config: VoiceConfig) -> Optional[bytes]:
        """Synthesize speech using ElevenLabs"""
        try:
            audio = generate(
                text=text,
                voice=voice_config.name,
                model="eleven_monolingual_v1"
            )
            return audio
        except Exception as e:
            self.logger.error(f"ElevenLabs synthesis error: {str(e)}")
            return None

    async def _synthesize_azure(self, text: str, voice_config: VoiceConfig) -> Optional[bytes]:
        """Synthesize speech using Azure"""
        try:
            speech_config = speechsdk.SpeechConfig(
                subscription=self.azure_speech_key,
                region=self.azure_service_region
            )
            
            # Map voice config to Azure voice
            voice_name = self._get_azure_voice_name(voice_config)
            speech_config.speech_synthesis_voice_name = voice_name

            # Configure speech synthesis
            synthesizer = speechsdk.SpeechSynthesizer(
                speech_config=speech_config,
                audio_config=None
            )

            # Apply voice settings
            ssml = self._generate_ssml(text, voice_config)
            result = synthesizer.speak_ssml_async(ssml).get()

            if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
                return result.audio_data
            else:
                return None

        except Exception as e:
            self.logger.error(f"Azure synthesis error: {str(e)}")
            return None

    async def _synthesize_google(self, text: str, voice_config: VoiceConfig) -> Optional[bytes]:
        """Synthesize speech using Google Cloud TTS"""
        try:
            client = texttospeech.TextToSpeechClient()

            synthesis_input = texttospeech.SynthesisInput(text=text)

            voice = texttospeech.VoiceSelectionParams(
                language_code=self._get_google_language_code(voice_config),
                name=self._get_google_voice_name(voice_config)
            )

            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3,
                pitch=voice_config.pitch,
                speaking_rate=voice_config.speed,
                volume_gain_db=20 * np.log10(voice_config.volume)
            )

            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config
            )

            return response.audio_content

        except Exception as e:
            self.logger.error(f"Google synthesis error: {str(e)}")
            return None

    async def _synthesize_local(self, text: str, voice_config: VoiceConfig) -> bytes:
        """Synthesize speech using local Coqui TTS"""
        try:
            wav = self.tts.tts(
                text=text,
                speaker_wav="path/to/speaker/reference.wav",
                language=self._get_local_language_code(voice_config)
            )

            # Convert numpy array to bytes
            bytes_io = io.BytesIO()
            audio_segment = AudioSegment(
                wav.tobytes(),
                frame_rate=22050,
                sample_width=2,
                channels=1
            )
            audio_segment.export(bytes_io, format="mp3")
            return bytes_io.getvalue()

        except Exception as e:
            self.logger.error(f"Local synthesis error: {str(e)}")
            raise

    def _generate_ssml(self, text: str, voice_config: VoiceConfig) -> str:
        """Generate SSML markup for voice synthesis"""
        return f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">
            <voice name="{voice_config.name}">
                <prosody pitch="{voice_config.pitch*100}%" 
                         rate="{voice_config.speed*100}%" 
                         volume="{voice_config.volume*100}%">
                    {text}
                </prosody>
            </voice>
        </speak>
        """

    def _get_azure_voice_name(self, voice_config: VoiceConfig) -> str:
        """Map voice config to Azure voice name"""
        # Add your Azure voice mapping logic here
        return f"en-US-{voice_config.name}Neural"

    def _get_google_language_code(self, voice_config: VoiceConfig) -> str:
        """Map voice config to Google language code"""
        accent_mapping = {
            "American": "en-US",
            "British": "en-GB",
            "Australian": "en-AU",
            "Indian": "en-IN",
            "Spanish": "es-ES",
            "German": "de-DE"
        }
        return accent_mapping.get(voice_config.accent, "en-US")

    def _get_google_voice_name(self, voice_config: VoiceConfig) -> str:
        """Map voice config to Google voice name"""
        # Add your Google voice mapping logic here
        return f"{self._get_google_language_code(voice_config)}-Standard-A"

    def _get_local_language_code(self, voice_config: VoiceConfig) -> str:
        """Map voice config to local TTS language code"""
        # Add your local TTS language mapping logic here
        return "en"

    def get_available_voices(self) -> List[Dict[str, Any]]:
        """Get list of available voices and their configurations"""
        return [
            {
                "id": voice_id,
                "name": config.name,
                "gender": config.gender,
                "accent": config.accent,
                "age": config.age,
                "emotion": config.emotion
            }
            for voice_id, config in self.voices.items()
        ]

    def get_voice_config(self, voice_id: str) -> Optional[VoiceConfig]:
        """Get configuration for specific voice"""
        return self.voices.get(voice_id)

    async def preview_voice(
        self,
        voice_id: str,
        settings: Optional[Dict[str, float]] = None
    ) -> bytes:
        """Generate a preview of the specified voice"""
        preview_text = f"Hello, I am {self.voices[voice_id].name}, your AI assistant."
        return await self.synthesize_speech(preview_text, voice_id, settings)
