import React, { useEffect, useRef } from 'react';
import {
  View,
  StyleSheet,
  Animated,
  Easing,
  Platform,
  ViewStyle,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import LottieView from 'lottie-react-native';
import { useTheme } from '../context/ThemeContext';
import theme from '../styles/theme';

interface AIAvatarProps {
  size?: number;
  speaking?: boolean;
  emotion?: 'neutral' | 'happy' | 'thinking' | 'listening';
  style?: ViewStyle;
}

const AIAvatar: React.FC<AIAvatarProps> = ({
  size = 120,
  speaking = false,
  emotion = 'neutral',
  style,
}) => {
  const { isDark } = useTheme();
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const rotateAnim = useRef(new Animated.Value(0)).current;
  const scaleAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Pulse animation
    Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1.1,
          duration: 1500,
          easing: Easing.inOut(Easing.sine),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 1500,
          easing: Easing.inOut(Easing.sine),
          useNativeDriver: true,
        }),
      ])
    ).start();

    // Rotation animation
    Animated.loop(
      Animated.timing(rotateAnim, {
        toValue: 1,
        duration: 10000,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, []);

  useEffect(() => {
    // Speaking animation
    if (speaking) {
      Animated.sequence([
        Animated.timing(scaleAnim, {
          toValue: 1.1,
          duration: 150,
          easing: Easing.ease,
          useNativeDriver: true,
        }),
        Animated.timing(scaleAnim, {
          toValue: 1,
          duration: 150,
          easing: Easing.ease,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [speaking]);

  const rotate = rotateAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '360deg'],
  });

  const getEmotionAnimation = () => {
    switch (emotion) {
      case 'happy':
        return require('../assets/animations/happy-avatar.json');
      case 'thinking':
        return require('../assets/animations/thinking-avatar.json');
      case 'listening':
        return require('../assets/animations/listening-avatar.json');
      default:
        return require('../assets/animations/neutral-avatar.json');
    }
  };

  const styles = StyleSheet.create({
    container: {
      width: size,
      height: size,
      alignItems: 'center',
      justifyContent: 'center',
    },
    avatarContainer: {
      width: size * 0.9,
      height: size * 0.9,
      borderRadius: size * 0.45,
      overflow: 'hidden',
      ...theme.shadows.lg[isDark ? 'dark' : 'light'],
    },
    gradientBackground: {
      position: 'absolute',
      width: '100%',
      height: '100%',
      opacity: 0.8,
    },
    glowEffect: {
      position: 'absolute',
      width: size * 1.2,
      height: size * 1.2,
      borderRadius: size * 0.6,
      backgroundColor: isDark ? theme.colors.primary.dark : theme.colors.primary.light,
      opacity: 0.15,
    },
    hologramEffect: {
      position: 'absolute',
      width: '100%',
      height: '100%',
      borderRadius: size * 0.45,
      borderWidth: 1,
      borderColor: isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.1)',
    },
    lottieContainer: {
      width: '100%',
      height: '100%',
    },
  });

  return (
    <View style={[styles.container, style]}>
      <Animated.View
        style={[
          styles.glowEffect,
          {
            transform: [{ scale: pulseAnim }],
          },
        ]}
      />
      <Animated.View
        style={[
          styles.avatarContainer,
          {
            transform: [
              { rotate },
              { scale: scaleAnim },
            ],
          },
        ]}
      >
        <LinearGradient
          colors={theme.gradients.primary}
          style={styles.gradientBackground}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
        />
        <View style={styles.hologramEffect} />
        <LottieView
          source={getEmotionAnimation()}
          autoPlay
          loop
          style={styles.lottieContainer}
          speed={1}
          renderMode={Platform.select({ web: 'svg', default: 'hardware' })}
        />
      </Animated.View>
    </View>
  );
};

export default AIAvatar;
