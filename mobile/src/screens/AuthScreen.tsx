import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { Camera, CameraType } from '@react-native-camera/camera';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { theme, ERROR_MESSAGES, SUCCESS_MESSAGES } from '../constants';

interface CaptureResponse {
  base64: string;
}

const AuthScreen: React.FC = () => {
  const navigation = useNavigation();
  const { isDark } = useTheme();
  const { registerFace, verifyFace, isAuthenticated } = useAuth();
  
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const cameraRef = useRef<Camera | null>(null);

  useEffect(() => {
    requestCameraPermission();
  }, []);

  useEffect(() => {
    if (isAuthenticated) {
      navigation.navigate('Home');
    }
  }, [isAuthenticated, navigation]);

  const requestCameraPermission = async () => {
    if (Platform.OS === 'web') {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      setHasPermission(true);
      return;
    }

    const { status } = await Camera.requestCameraPermissionsAsync();
    setHasPermission(status === 'granted');
  };

  const captureImage = async (): Promise<string | null> => {
    if (!cameraRef.current) return null;

    try {
      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: true,
        skipProcessing: true,
      });

      return `data:image/jpeg;base64,${photo.base64}`;
    } catch (error) {
      console.error('Error capturing image:', error);
      return null;
    }
  };

  const handleRegistration = async () => {
    setIsProcessing(true);
    try {
      const imageData = await captureImage();
      if (!imageData) {
        Alert.alert('Error', ERROR_MESSAGES.FACE_REGISTRATION);
        return;
      }

      const success = await registerFace(imageData);
      if (success) {
        Alert.alert('Success', SUCCESS_MESSAGES.FACE_REGISTERED);
        setIsRegistering(false);
      } else {
        Alert.alert('Error', ERROR_MESSAGES.FACE_REGISTRATION);
      }
    } catch (error) {
      console.error('Registration error:', error);
      Alert.alert('Error', ERROR_MESSAGES.FACE_REGISTRATION);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleVerification = async () => {
    setIsProcessing(true);
    try {
      const imageData = await captureImage();
      if (!imageData) {
        Alert.alert('Error', ERROR_MESSAGES.FACE_VERIFICATION);
        return;
      }

      const success = await verifyFace(imageData);
      if (!success) {
        Alert.alert('Error', ERROR_MESSAGES.FACE_VERIFICATION);
      }
    } catch (error) {
      console.error('Verification error:', error);
      Alert.alert('Error', ERROR_MESSAGES.FACE_VERIFICATION);
    } finally {
      setIsProcessing(false);
    }
  };

  if (hasPermission === null) {
    return (
      <View style={styles.container}>
        <ActivityIndicator size="large" color={theme.light.primary} />
      </View>
    );
  }

  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <Text style={styles.text}>{ERROR_MESSAGES.CAMERA_PERMISSION}</Text>
      </View>
    );
  }

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: isDark ? theme.dark.background : theme.light.background,
    },
    camera: {
      flex: 1,
    },
    overlay: {
      ...StyleSheet.absoluteFillObject,
      justifyContent: 'flex-end',
      padding: 20,
    },
    buttonContainer: {
      flexDirection: 'row',
      justifyContent: 'space-around',
      marginBottom: 20,
    },
    button: {
      backgroundColor: isDark ? theme.dark.primary : theme.light.primary,
      padding: 15,
      borderRadius: 10,
      minWidth: 150,
      alignItems: 'center',
    },
    buttonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
    },
    text: {
      color: isDark ? theme.dark.text : theme.light.text,
      fontSize: 16,
      textAlign: 'center',
      margin: 20,
    },
    guide: {
      position: 'absolute',
      top: '30%',
      left: '10%',
      right: '10%',
      padding: 20,
      backgroundColor: 'rgba(0, 0, 0, 0.7)',
      borderRadius: 10,
    },
    guideText: {
      color: '#fff',
      fontSize: 14,
      textAlign: 'center',
    },
  });

  return (
    <View style={styles.container}>
      <Camera
        ref={cameraRef}
        style={styles.camera}
        type={CameraType.front}
      >
        <View style={styles.overlay}>
          {!isProcessing && (
            <View style={styles.guide}>
              <Text style={styles.guideText}>
                {isRegistering
                  ? 'Position your face in the frame and ensure good lighting'
                  : 'Look directly at the camera for face verification'}
              </Text>
            </View>
          )}
          <View style={styles.buttonContainer}>
            {isProcessing ? (
              <ActivityIndicator size="large" color="#fff" />
            ) : (
              <>
                <TouchableOpacity
                  style={styles.button}
                  onPress={() => setIsRegistering(!isRegistering)}
                >
                  <Text style={styles.buttonText}>
                    {isRegistering ? 'Switch to Verify' : 'Switch to Register'}
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.button}
                  onPress={isRegistering ? handleRegistration : handleVerification}
                >
                  <Text style={styles.buttonText}>
                    {isRegistering ? 'Register Face' : 'Verify Face'}
                  </Text>
                </TouchableOpacity>
              </>
            )}
          </View>
        </View>
      </Camera>
    </View>
  );
};

export default AuthScreen;
