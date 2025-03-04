import React, { useEffect, useRef, useState } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  Animated,
  Dimensions,
  StyleSheet,
  Platform,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import LottieView from 'lottie-react-native';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import theme from '../styles/theme';
import AIAvatar from '../components/AIAvatar';
import ChatInterface from '../components/ChatInterface';
import VoiceCustomization from '../components/VoiceCustomization';

const { width, height } = Dimensions.get('window');

const ModernHomeScreen: React.FC = () => {
  const { isDark } = useTheme();
  const { user } = useAuth();
  const [activeFeature, setActiveFeature] = useState<string | null>(null);
  const [isListening, setIsListening] = useState(false);

  // Animations
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(0.9)).current;
  const avatarRotateAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 1000,
        useNativeDriver: true,
      }),
      Animated.spring(scaleAnim, {
        toValue: 1,
        tension: 50,
        friction: 7,
        useNativeDriver: true,
      }),
    ]).start();

    // Continuous avatar rotation
    Animated.loop(
      Animated.timing(avatarRotateAnim, {
        toValue: 1,
        duration: 20000,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  const avatarRotate = avatarRotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const features = [
    {
      id: 'chat',
      title: 'AI Chat',
      icon: require('../assets/animations/chat.json'),
      description: 'Have natural conversations with context awareness',
    },
    {
      id: 'voice',
      title: 'Voice Control',
      icon: require('../assets/animations/voice.json'),
      description: 'Customize voice and speech patterns',
    },
    {
      id: 'automation',
      title: 'Task Automation',
      icon: require('../assets/animations/automation.json'),
      description: 'Automate your daily routines',
    },
    {
      id: 'security',
      title: 'Face Security',
      icon: require('../assets/animations/security.json'),
      description: 'Biometric authentication and privacy',
    },
  ];

  const renderFeatureCard = (feature: typeof features[0]) => (
    <TouchableOpacity
      key={feature.id}
      onPress={() => setActiveFeature(feature.id)}
      style={[
        styles.featureCard,
        activeFeature === feature.id && styles.activeFeatureCard,
      ]}
    >
      <BlurView
        intensity={80}
        tint={isDark ? 'dark' : 'light'}
        style={styles.featureCardContent}
      >
        <LottieView
          source={feature.icon}
          autoPlay
          loop
          style={styles.featureIcon}
        />
        <Text style={styles.featureTitle}>{feature.title}</Text>
        <Text style={styles.featureDescription}>{feature.description}</Text>
      </BlurView>
    </TouchableOpacity>
  );

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: isDark ? theme.colors.neutral[900] : theme.colors.neutral[50],
    },
    header: {
      paddingTop: Platform.OS === 'ios' ? 60 : 40,
      paddingHorizontal: theme.spacing.lg,
      paddingBottom: theme.spacing.xl,
    },
    avatarContainer: {
      alignItems: 'center',
      marginBottom: theme.spacing.xl,
    },
    welcomeText: {
      fontSize: theme.typography.fontSize['3xl'],
      fontWeight: theme.typography.fontWeight.bold,
      color: isDark ? theme.colors.neutral[50] : theme.colors.neutral[900],
      textAlign: 'center',
      marginBottom: theme.spacing.sm,
    },
    subtitleText: {
      fontSize: theme.typography.fontSize.lg,
      color: isDark ? theme.colors.neutral[400] : theme.colors.neutral[600],
      textAlign: 'center',
    },
    featuresGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      padding: theme.spacing.md,
      justifyContent: 'space-between',
    },
    featureCard: {
      width: (width - theme.spacing.md * 3) / 2,
      marginBottom: theme.spacing.md,
      borderRadius: theme.borderRadius.lg,
      overflow: 'hidden',
      ...theme.shadows.lg[isDark ? 'dark' : 'light'],
    },
    activeFeatureCard: {
      transform: [{ scale: 1.05 }],
      borderWidth: 2,
      borderColor: theme.colors.primary[isDark ? 'dark' : 'light'],
    },
    featureCardContent: {
      padding: theme.spacing.lg,
      height: 200,
      justifyContent: 'center',
      alignItems: 'center',
    },
    featureIcon: {
      width: 60,
      height: 60,
      marginBottom: theme.spacing.md,
    },
    featureTitle: {
      fontSize: theme.typography.fontSize.lg,
      fontWeight: theme.typography.fontWeight.bold,
      color: isDark ? theme.colors.neutral[50] : theme.colors.neutral[900],
      marginBottom: theme.spacing.sm,
      textAlign: 'center',
    },
    featureDescription: {
      fontSize: theme.typography.fontSize.sm,
      color: isDark ? theme.colors.neutral[400] : theme.colors.neutral[600],
      textAlign: 'center',
    },
    mainContent: {
      flex: 1,
      marginTop: theme.spacing.xl,
    },
    gradientBackground: {
      ...StyleSheet.absoluteFillObject,
      opacity: 0.5,
    },
  });

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={theme.gradients.primary}
        style={styles.gradientBackground}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      />
      
      <ScrollView>
        <Animated.View
          style={[
            styles.header,
            {
              opacity: fadeAnim,
              transform: [{ scale: scaleAnim }],
            },
          ]}
        >
          <View style={styles.avatarContainer}>
            <Animated.View style={{ transform: [{ rotate: avatarRotate }] }}>
              <AIAvatar
                size={150}
                emotion="happy"
                speaking={isListening}
              />
            </Animated.View>
          </View>
          
          <Text style={styles.welcomeText}>
            Welcome back, {user?.name}
          </Text>
          <Text style={styles.subtitleText}>
            How can I assist you today?
          </Text>
        </Animated.View>

        <View style={styles.featuresGrid}>
          {features.map(renderFeatureCard)}
        </View>

        <View style={styles.mainContent}>
          {activeFeature === 'chat' && (
            <ChatInterface
              onSendMessage={async (message) => {
                // Handle message sending
              }}
              onStartVoice={() => setIsListening(true)}
              onStopVoice={() => setIsListening(false)}
              isListening={isListening}
            />
          )}
          {activeFeature === 'voice' && (
            <VoiceCustomization
              onVoiceSelect={() => {}}
              onSettingsChange={() => {}}
            />
          )}
          {/* Add other feature components */}
        </View>
      </ScrollView>
    </View>
  );
};

export default ModernHomeScreen;
