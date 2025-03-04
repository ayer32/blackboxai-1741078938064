// API Configuration
export const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

// Storage Keys
export const THEME_KEY = '@krish_ai:theme';
export const AUTH_TOKEN_KEY = '@krish_ai:auth_token';
export const USER_ID_KEY = '@krish_ai:user_id';

// Theme Configuration
export const theme = {
  light: {
    primary: '#0ea5e9',
    background: '#ffffff',
    surface: '#f3f4f6',
    text: '#1f2937',
    textSecondary: '#6b7280',
    border: '#e5e7eb',
    error: '#ef4444',
    success: '#10b981',
    warning: '#f59e0b',
  },
  dark: {
    primary: '#38bdf8',
    background: '#111827',
    surface: '#1f2937',
    text: '#f9fafb',
    textSecondary: '#9ca3af',
    border: '#374151',
    error: '#f87171',
    success: '#34d399',
    warning: '#fbbf24',
  },
};

// Animation Configuration
export const ANIMATION_CONFIG = {
  duration: 200,
  easing: 'ease-in-out',
};

// Face Verification Configuration
export const FACE_VERIFICATION = {
  minConfidence: 0.7,
  livenessThreshold: 0.8,
  maxRetries: 3,
  captureInterval: 500, // ms
};

// Voice Recognition Configuration
export const VOICE_CONFIG = {
  continuous: false,
  interimResults: false,
  lang: 'en-US',
};

// Supported Languages
export const SUPPORTED_LANGUAGES = {
  en: 'English',
  es: 'Spanish',
  fr: 'French',
  de: 'German',
  it: 'Italian',
  pt: 'Portuguese',
  nl: 'Dutch',
  pl: 'Polish',
  ru: 'Russian',
  ja: 'Japanese',
  ko: 'Korean',
  zh: 'Chinese',
  ar: 'Arabic',
  hi: 'Hindi',
};

// PWA Configuration
export const PWA_CONFIG = {
  name: 'Krish AI Assistant',
  shortName: 'Krish AI',
  description: 'Advanced AI Assistant with Voice Commands and Face Verification',
  backgroundColor: '#ffffff',
  themeColor: '#0ea5e9',
  displayMode: 'standalone',
  scope: '/',
  startUrl: '/',
  orientation: 'portrait',
};

// Error Messages
export const ERROR_MESSAGES = {
  FACE_REGISTRATION: 'Face registration failed. Please try again.',
  FACE_VERIFICATION: 'Face verification failed. Please try again.',
  VOICE_PERMISSION: 'Please allow microphone access to use voice commands.',
  CAMERA_PERMISSION: 'Please allow camera access for face verification.',
  NETWORK: 'Network error. Please check your connection.',
  UNKNOWN: 'An unknown error occurred. Please try again.',
};

// Success Messages
export const SUCCESS_MESSAGES = {
  FACE_REGISTERED: 'Face registered successfully!',
  FACE_VERIFIED: 'Face verification successful!',
  SETTINGS_SAVED: 'Settings saved successfully!',
};

// Navigation Routes
export const ROUTES = {
  AUTH: 'Auth',
  HOME: 'Home',
  CHAT: 'Chat',
  SETTINGS: 'Settings',
};

// Local Storage Version (for migrations)
export const STORAGE_VERSION = '1.0.0';
