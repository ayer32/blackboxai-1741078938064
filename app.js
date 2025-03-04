// Face Verification and Voice Recognition Setup
class KrishAI {
    constructor() {
        this.recognition = null;
        this.synthesis = window.speechSynthesis;
        this.isListening = false;
        this.currentLanguage = 'en';
        this.userId = this.generateUserId();
        this.context = {};
        this.isAuthenticated = false;
        this.authToken = null;
        this.setupSpeechRecognition();
        this.setupNotifications();
        this.loadSupportedLanguages();
        this.setupFaceVerification();
    }

    setupFaceVerification() {
        // Set up video elements for face capture
        this.setupVideoElements();
        
        // Add face registration and verification buttons
        this.addFaceAuthButtons();
    }

    setupVideoElements() {
        // Create video container if it doesn't exist
        if (!document.getElementById('face-auth-container')) {
            const container = document.createElement('div');
            container.id = 'face-auth-container';
            container.className = 'fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white dark:bg-gray-800 p-6 rounded-lg shadow-xl z-50 hidden';
            
            container.innerHTML = `
                <div class="relative">
                    <video id="face-video" class="w-[640px] h-[480px] bg-black rounded-lg"></video>
                    <canvas id="face-canvas" class="hidden"></canvas>
                    <div class="absolute top-4 right-4 space-x-2">
                        <button id="capture-face" class="px-4 py-2 bg-primary-500 text-white rounded-lg">Capture</button>
                        <button id="close-face-auth" class="px-4 py-2 bg-gray-500 text-white rounded-lg">Close</button>
                    </div>
                </div>
                <div class="mt-4 text-center text-gray-700 dark:text-gray-300" id="face-auth-status"></div>
            `;
            
            document.body.appendChild(container);
            
            // Add event listeners
            document.getElementById('close-face-auth').addEventListener('click', () => {
                this.stopCamera();
                container.classList.add('hidden');
            });
            
            document.getElementById('capture-face').addEventListener('click', () => {
                this.captureFace();
            });
        }
    }

    addFaceAuthButtons() {
        const nav = document.querySelector('nav .flex.items-center.space-x-4');
        if (!nav) return;

        const authButtons = document.createElement('div');
        authButtons.className = 'flex items-center space-x-2';
        authButtons.innerHTML = `
            <button id="register-face" class="px-4 py-2 bg-primary-500 text-white rounded-lg">
                Register Face
            </button>
            <button id="verify-face" class="px-4 py-2 bg-primary-500 text-white rounded-lg">
                Verify Face
            </button>
        `;

        nav.appendChild(authButtons);

        // Add event listeners
        document.getElementById('register-face').addEventListener('click', () => {
            this.startFaceRegistration();
        });

        document.getElementById('verify-face').addEventListener('click', () => {
            this.startFaceVerification();
        });
    }

    async startCamera() {
        try {
            const video = document.getElementById('face-video');
            const stream = await navigator.mediaDevices.getUserMedia({ 
                video: { 
                    width: 640,
                    height: 480,
                    facingMode: "user"
                } 
            });
            video.srcObject = stream;
            await video.play();
            
            document.getElementById('face-auth-container').classList.remove('hidden');
        } catch (error) {
            console.error('Error accessing camera:', error);
            this.showNotification('Error accessing camera. Please ensure camera permissions are granted.', 'error');
        }
    }

    stopCamera() {
        const video = document.getElementById('face-video');
        const stream = video.srcObject;
        if (stream) {
            const tracks = stream.getTracks();
            tracks.forEach(track => track.stop());
            video.srcObject = null;
        }
    }

    async captureFace() {
        const video = document.getElementById('face-video');
        const canvas = document.getElementById('face-canvas');
        const context = canvas.getContext('2d');

        // Set canvas size to match video
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        // Draw video frame to canvas
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert to base64
        const imageData = canvas.toDataURL('image/jpeg');

        return imageData;
    }

    async startFaceRegistration() {
        await this.startCamera();
        document.getElementById('face-auth-status').textContent = 'Position your face in the frame and click Capture';
        document.getElementById('capture-face').onclick = async () => {
            const imageData = await this.captureFace();
            await this.registerFace(imageData);
        };
    }

    async startFaceVerification() {
        await this.startCamera();
        document.getElementById('face-auth-status').textContent = 'Position your face in the frame and click Capture';
        document.getElementById('capture-face').onclick = async () => {
            const imageData = await this.captureFace();
            await this.verifyFace(imageData);
        };
    }

    async registerFace(imageData) {
        try {
            const response = await fetch('http://localhost:8000/api/face/register', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    image_data: imageData
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.showNotification('Face registered successfully!');
                this.stopCamera();
                document.getElementById('face-auth-container').classList.add('hidden');
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            console.error('Error registering face:', error);
            this.showNotification('Error registering face. Please try again.', 'error');
        }
    }

    async verifyFace(imageData) {
        try {
            const response = await fetch('http://localhost:8000/api/face/verify', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    user_id: this.userId,
                    image_data: imageData
                })
            });

            const result = await response.json();
            
            if (result.success) {
                this.isAuthenticated = true;
                this.authToken = result.access_token;
                this.showNotification('Face verification successful!');
                this.stopCamera();
                document.getElementById('face-auth-container').classList.add('hidden');
                this.updateAuthUI();
            } else {
                this.showNotification(result.error, 'error');
            }
        } catch (error) {
            console.error('Error verifying face:', error);
            this.showNotification('Error verifying face. Please try again.', 'error');
        }
    }

    updateAuthUI() {
        const verifyButton = document.getElementById('verify-face');
        const registerButton = document.getElementById('register-face');
        
        if (this.isAuthenticated) {
            verifyButton.textContent = 'Verified';
            verifyButton.classList.add('bg-green-500');
            registerButton.classList.add('hidden');
        } else {
            verifyButton.textContent = 'Verify Face';
            verifyButton.classList.remove('bg-green-500');
            registerButton.classList.remove('hidden');
        }
    }

    // Existing methods with authentication headers added
    async processAudioWithWhisper(audioBlob) {
        const formData = new FormData();
        formData.append('audio', audioBlob);
        formData.append('source_lang', this.currentLanguage);

        try {
            const response = await fetch('http://localhost:8000/api/speech-to-text', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: formData
            });
            const data = await response.json();
            return data.text;
        } catch (error) {
            console.error('Error processing audio:', error);
            this.showNotification('Error processing audio. Please try again.', 'error');
            return null;
        }
    }

    async processCommandWithNLU(text) {
        try {
            const response = await fetch('http://localhost:8000/api/process-command', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${this.authToken}`
                },
                body: JSON.stringify({
                    text: text,
                    source_lang: this.currentLanguage,
                    target_lang: this.currentLanguage,
                    user_id: this.userId,
                    context: this.context
                })
            });
            const data = await response.json();
            
            if (data.requires_more_info && data.follow_up_questions.length > 0) {
                this.handleFollowUpQuestions(data.follow_up_questions);
            }

            if (data.intent && data.intent.entities) {
                await this.updateContext(data.intent.entities);
            }

            return data.response;
        } catch (error) {
            console.error('Error processing command:', error);
            this.showNotification('Error processing command. Please try again.', 'error');
            return null;
        }
    }

    // ... (rest of the existing methods remain unchanged)
}

// Initialize Krish AI when the page loads
document.addEventListener('DOMContentLoaded', () => {
    const krish = new KrishAI();

    // Add click handler to voice command button
    const voiceButton = document.querySelector('.voice-trigger');
    if (voiceButton) {
        voiceButton.addEventListener('click', () => {
            if (!krish.isAuthenticated) {
                krish.showNotification('Please verify your face before using voice commands.', 'error');
                return;
            }
            
            if (!krish.isListening) {
                krish.startListening();
            } else {
                krish.stopListening();
            }
        });
    }
});
