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
import { Camera, CameraType, FaceDetectionResult } from 'expo-camera';
import { BlurView } from 'expo-blur';
import LottieView from 'lottie-react-native';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useAPI } from '../context/APIContext';
import theme from '../styles/theme';

// Define types
interface Face {
  bounds: {
    origin: { x: number; y: number };
    size: { width: number; height: number };
  };
}

interface DetectedFaces {
  faces: Face[];
}

interface FaceDetector {
  FaceDetectorMode: { fast: number };
  FaceDetectorLandmarks: { none: number };
  FaceDetectorClassifications: { none: number };
}

const FaceDetector: FaceDetector = {
  FaceDetectorMode: { fast: 1 },
  FaceDetectorLandmarks: { none: 0 },
  FaceDetectorClassifications: { none: 0 },
};

const FaceRegistrationScreen: React.FC = () => {
  const { isDark } = useTheme();
  const { registerFace } = useAuth();
  const { processTextCommand } = useAPI();
  const [hasPermission, setHasPermission] = useState<boolean | null>(null);
  const [isRegistering, setIsRegistering] = useState(false);
  const [registrationSuccess, setRegistrationSuccess] = useState(false);
  const [isFaceCentered, setIsFaceCentered] = useState(false);
  const [registrationStep, setRegistrationStep] = useState(0);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [qualityScore, setQualityScore] = useState(0);
  const cameraRef = useRef<Camera | null>(null);
  const animationRef = useRef<LottieView | null>(null);

  const resetRegistration = () => {
    setIsRegistering(false);
    setRegistrationSuccess(false);
    setRegistrationStep(0);
    setErrorMessage(null);
    setQualityScore(0);
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: isDark ? theme.colors.neutral[900] : theme.colors.neutral[50],
    },
    camera: {
      flex: 1,
    },
    overlay: {
      ...StyleSheet.absoluteFillObject,
      justifyContent: 'space-between',
      padding: theme.spacing.lg,
    },
    header: {
      marginTop: Platform.OS === 'ios' ? 60 : 40,
      alignItems: 'center',
    },
    title: {
      fontSize: theme.typography.fontSize['2xl'],
      fontWeight: theme.typography.fontWeight.semibold as '600',
      color: theme.colors.neutral[50],
      textAlign: 'center',
      marginBottom: theme.spacing.sm,
    },
    instructions: {
      fontSize: theme.typography.fontSize.base,
      fontWeight: theme.typography.fontWeight.normal as '400',
      color: theme.colors.neutral[200],
      textAlign: 'center',
      marginBottom: theme.spacing.xl,
      paddingHorizontal: theme.spacing.xl,
    },
    guideFrame: {
      position: 'absolute',
      top: '50%',
      left: '50%',
      width: 280,
      height: 280,
      marginLeft: -140,
      marginTop: -140,
      borderWidth: 2,
      borderColor: isFaceCentered 
        ? theme.colors.success[isDark ? 'dark' : 'light']
        : theme.colors.primary[isDark ? 'dark' : 'light'],
      borderRadius: 140,
      justifyContent: 'center',
      alignItems: 'center',
    },
    qualityIndicator: {
      position: 'absolute',
      top: -30,
      width: '100%',
      flexDirection: 'row',
      justifyContent: 'center',
      alignItems: 'center',
      gap: theme.spacing.xs,
    },
    qualityDot: {
      width: 8,
      height: 8,
      borderRadius: 4,
      backgroundColor: theme.colors.neutral[400],
    },
    qualityDotActive: {
      backgroundColor: theme.colors.success[isDark ? 'dark' : 'light'],
    },
    stepIndicator: {
      flexDirection: 'row',
      justifyContent: 'center',
      marginTop: theme.spacing.md,
      gap: theme.spacing.sm,
    },
    stepDot: {
      width: 6,
      height: 6,
      borderRadius: 3,
      backgroundColor: theme.colors.neutral[400],
    },
    stepDotActive: {
      backgroundColor: theme.colors.primary[isDark ? 'dark' : 'light'],
    },
    errorContainer: {
      backgroundColor: theme.colors.error[isDark ? 'dark' : 'light'] + '20',
      padding: theme.spacing.sm,
      borderRadius: theme.borderRadius.md,
      marginTop: theme.spacing.sm,
    },
    errorText: {
      color: theme.colors.error[isDark ? 'dark' : 'light'],
      fontSize: theme.typography.fontSize.sm,
      fontWeight: theme.typography.fontWeight.normal as '400',
      textAlign: 'center',
    },
    buttonContainer: {
      marginBottom: theme.spacing.xl,
      alignItems: 'center',
    },
    button: {
      backgroundColor: isFaceCentered
        ? theme.colors.primary[isDark ? 'dark' : 'light']
        : theme.colors.neutral[600],
      paddingHorizontal: theme.spacing.xl,
      paddingVertical: theme.spacing.lg,
      borderRadius: theme.borderRadius.full,
      alignItems: 'center',
    },
    buttonText: {
      color: theme.colors.neutral[50],
      fontSize: theme.typography.fontSize.lg,
      fontWeight: theme.typography.fontWeight.semibold as '600',
    },
    statusText: {
      color: theme.colors.neutral[50],
      fontSize: theme.typography.fontSize.sm,
      fontWeight: theme.typography.fontWeight.normal as '400',
      marginTop: theme.spacing.md,
    },
  });

  useEffect(() => {
    (async () => {
      const { status } = await Camera.requestCameraPermissionsAsync();
      setHasPermission(status === 'granted');
    })();
  }, []);

  const checkFaceQuality = (face: Face) => {
    const minSize = 100;
    const maxSize = 240;
    const { width, height } = face.bounds.size;
    
    let score = 0;
    
    if (width > minSize && width < maxSize && height > minSize && height < maxSize) {
      score += 0.4;
    }
    
    if (isFaceCentered) {
      score += 0.3;
    }
    
    score += 0.3;
    
    setQualityScore(score);
    return score > 0.7;
  };

  const takePicture = async () => {
    if (!cameraRef.current || !isFaceCentered) return;

    try {
      setIsRegistering(true);
      setRegistrationStep(1);
      setErrorMessage(null);

      const photo = await cameraRef.current.takePictureAsync({
        quality: 0.8,
        base64: true,
      });

      setRegistrationStep(2);

      const success = await registerFace(`data:image/jpeg;base64,${photo.base64}`);

      if (success) {
        setRegistrationStep(3);
        setRegistrationSuccess(true);
        if (animationRef.current) {
          animationRef.current.play();
        }
        Alert.alert(
          'Success',
          'Face registered successfully! You can now use face verification for authentication.',
          [{ text: 'OK', onPress: resetRegistration }]
        );
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to register face. Please try again.';
      setErrorMessage(errorMessage);
      Alert.alert('Error', errorMessage, [{ text: 'Try Again', onPress: resetRegistration }]);
    } finally {
      setIsRegistering(false);
    }
  };

  const handleFaceDetected = (result: { faces: Face[] }) => {
    const detectedFaces = result.faces;
    if (detectedFaces.length > 0) {
      const face = detectedFaces[0];
      const centerX = face.bounds.origin.x + face.bounds.size.width / 2;
      const centerY = face.bounds.origin.y + face.bounds.size.height / 2;
      
      const isXCentered = centerX > 160 && centerX < 240;
      const isYCentered = centerY > 260 && centerY < 340;
      
      setIsFaceCentered(isXCentered && isYCentered);
      checkFaceQuality(face);
    } else {
      setIsFaceCentered(false);
      setQualityScore(0);
    }
  };

  if (hasPermission === null) {
    return <View style={styles.container} />;
  }

  if (hasPermission === false) {
    return (
      <View style={styles.container}>
        <Text style={styles.errorText}>No access to camera</Text>
      </View>
    );
  }

  const renderQualityIndicator = () => {
    const dots = [0.2, 0.4, 0.6, 0.8, 1.0];
    return (
      <View style={styles.qualityIndicator}>
        {dots.map((threshold, index) => (
          <View
            key={index}
            style={[
              styles.qualityDot,
              qualityScore >= threshold && styles.qualityDotActive,
            ]}
          />
        ))}
      </View>
    );
  };

  const renderStepIndicator = () => {
    const steps = [0, 1, 2, 3];
    return (
      <View style={styles.stepIndicator}>
        {steps.map((step) => (
          <View
            key={step}
            style={[
              styles.stepDot,
              registrationStep >= step && styles.stepDotActive,
            ]}
          />
        ))}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <Camera
        ref={cameraRef}
        style={styles.camera}
        type={CameraType.front}
        onFacesDetected={(result: FaceDetectionResult) => handleFaceDetected(result as { faces: Face[] })}
        faceDetectorSettings={{
          mode: FaceDetector.FaceDetectorMode.fast,
          detectLandmarks: FaceDetector.FaceDetectorLandmarks.none,
          runClassifications: FaceDetector.FaceDetectorClassifications.none,
          minDetectionInterval: 100,
          tracking: true,
        }}
      >
        <BlurView intensity={40} tint="dark" style={styles.overlay}>
          <View style={styles.header}>
            <Text style={styles.title}>Face Registration</Text>
            <Text style={styles.instructions}>
              Position your face within the frame and ensure good lighting.
              Remove glasses and keep a neutral expression.
            </Text>
          </View>

          <View style={styles.guideFrame}>
            {renderQualityIndicator()}
            {registrationSuccess && (
              <LottieView
                ref={animationRef}
                source={require('../../assets/animations/success.json')}
                autoPlay={false}
                loop={false}
                style={{ flex: 1 }}
              />
            )}
          </View>

          {renderStepIndicator()}

          {errorMessage && (
            <View style={styles.errorContainer}>
              <Text style={styles.errorText}>{errorMessage}</Text>
            </View>
          )}

          <View style={styles.buttonContainer}>
            <TouchableOpacity
              style={styles.button}
              onPress={takePicture}
              disabled={isRegistering || !isFaceCentered}
            >
              {isRegistering ? (
                <ActivityIndicator color={theme.colors.neutral[50]} />
              ) : (
                <Text style={styles.buttonText}>
                  {isFaceCentered ? 'Register Face' : 'Center Your Face'}
                </Text>
              )}
            </TouchableOpacity>
            <Text style={styles.statusText}>
              {isFaceCentered 
                ? 'Face detected - Ready to register'
                : 'Position your face in the center'}
            </Text>
          </View>
        </BlurView>
      </Camera>
    </View>
  );
};

export default FaceRegistrationScreen;
