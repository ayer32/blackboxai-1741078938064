import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TouchableOpacity,
  StyleSheet,
  Animated,
  Platform,
} from 'react-native';
import Slider from '@react-native-community/slider';
import { useTheme } from '../context/ThemeContext';
import { useAPI } from '../context/APIContext';
import theme from '../styles/theme';
import AIAvatar from './AIAvatar';

interface Voice {
  id: string;
  name: string;
  accent: string;
  gender: 'male' | 'female' | 'neutral';
  preview: string;
}

interface VoiceCustomizationProps {
  onVoiceSelect: (voice: Voice) => void;
  onSettingsChange: (settings: VoiceSettings) => void;
}

interface VoiceSettings {
  pitch: number;
  rate: number;
  volume: number;
}

const AVAILABLE_VOICES: Voice[] = [
  {
    id: 'en-US-1',
    name: 'Sarah',
    accent: 'American',
    gender: 'female',
    preview: 'Hello, I am Sarah, your AI assistant.',
  },
  {
    id: 'en-GB-1',
    name: 'James',
    accent: 'British',
    gender: 'male',
    preview: 'Hello, I am James, your AI assistant.',
  },
  {
    id: 'en-AU-1',
    name: 'Emma',
    accent: 'Australian',
    gender: 'female',
    preview: 'Hello, I am Emma, your AI assistant.',
  },
  {
    id: 'en-IN-1',
    name: 'Raj',
    accent: 'Indian',
    gender: 'male',
    preview: 'Hello, I am Raj, your AI assistant.',
  },
];

const VoiceCustomization: React.FC<VoiceCustomizationProps> = ({
  onVoiceSelect,
  onSettingsChange,
}) => {
  const { isDark } = useTheme();
  const { apiClient } = useAPI();
  const [selectedVoice, setSelectedVoice] = useState<Voice>(AVAILABLE_VOICES[0]);
  const [isPlaying, setIsPlaying] = useState(false);
  const [settings, setSettings] = useState<VoiceSettings>({
    pitch: 1,
    rate: 1,
    volume: 1,
  });

  const playAnimation = new Animated.Value(0);

  useEffect(() => {
    if (isPlaying) {
      Animated.sequence([
        Animated.timing(playAnimation, {
          toValue: 1,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.timing(playAnimation, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [isPlaying]);

  const playPreview = async (voice: Voice) => {
    try {
      setIsPlaying(true);
      await apiClient.post('/api/voice/preview', {
        voice: voice.id,
        text: voice.preview,
        settings,
      });
      setIsPlaying(false);
    } catch (error) {
      console.error('Error playing voice preview:', error);
      setIsPlaying(false);
    }
  };

  const handleVoiceSelect = (voice: Voice) => {
    setSelectedVoice(voice);
    onVoiceSelect(voice);
    playPreview(voice);
  };

  const handleSettingChange = (key: keyof VoiceSettings, value: number) => {
    const newSettings = { ...settings, [key]: value };
    setSettings(newSettings);
    onSettingsChange(newSettings);
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      padding: theme.spacing.md,
    },
    section: {
      marginBottom: theme.spacing.xl,
    },
    sectionTitle: {
      fontSize: theme.typography.fontSize.lg,
      fontWeight: theme.typography.fontWeight.bold,
      color: isDark ? theme.colors.neutral[50] : theme.colors.neutral[900],
      marginBottom: theme.spacing.md,
    },
    voiceGrid: {
      flexDirection: 'row',
      flexWrap: 'wrap',
      marginHorizontal: -theme.spacing.sm,
    },
    voiceCard: {
      width: '45%',
      margin: theme.spacing.sm,
      padding: theme.spacing.md,
      borderRadius: theme.borderRadius.md,
      ...theme.glassmorphism[isDark ? 'dark' : 'light'],
    },
    selectedVoiceCard: {
      borderColor: theme.colors.primary[isDark ? 'dark' : 'light'],
      borderWidth: 2,
    },
    voiceName: {
      fontSize: theme.typography.fontSize.base,
      fontWeight: theme.typography.fontWeight.semibold,
      color: isDark ? theme.colors.neutral[50] : theme.colors.neutral[900],
      marginBottom: theme.spacing.xs,
    },
    voiceAccent: {
      fontSize: theme.typography.fontSize.sm,
      color: isDark ? theme.colors.neutral[400] : theme.colors.neutral[600],
      marginBottom: theme.spacing.sm,
    },
    previewButton: {
      backgroundColor: theme.colors.primary[isDark ? 'dark' : 'light'],
      padding: theme.spacing.sm,
      borderRadius: theme.borderRadius.sm,
      alignItems: 'center',
    },
    previewButtonText: {
      color: theme.colors.neutral[50],
      fontSize: theme.typography.fontSize.sm,
      fontWeight: theme.typography.fontWeight.medium,
    },
    sliderContainer: {
      marginBottom: theme.spacing.lg,
    },
    sliderLabel: {
      fontSize: theme.typography.fontSize.sm,
      color: isDark ? theme.colors.neutral[400] : theme.colors.neutral[600],
      marginBottom: theme.spacing.xs,
    },
    sliderValue: {
      fontSize: theme.typography.fontSize.sm,
      color: isDark ? theme.colors.neutral[400] : theme.colors.neutral[600],
      textAlign: 'right',
    },
  });

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Choose a Voice</Text>
        <View style={styles.voiceGrid}>
          {AVAILABLE_VOICES.map((voice) => (
            <TouchableOpacity
              key={voice.id}
              style={[
                styles.voiceCard,
                selectedVoice.id === voice.id && styles.selectedVoiceCard,
              ]}
              onPress={() => handleVoiceSelect(voice)}
            >
              <Text style={styles.voiceName}>{voice.name}</Text>
              <Text style={styles.voiceAccent}>{voice.accent}</Text>
              <TouchableOpacity
                style={styles.previewButton}
                onPress={() => playPreview(voice)}
              >
                <Text style={styles.previewButtonText}>
                  {isPlaying ? 'Playing...' : 'Preview'}
                </Text>
              </TouchableOpacity>
            </TouchableOpacity>
          ))}
        </View>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Voice Settings</Text>
        
        <View style={styles.sliderContainer}>
          <Text style={styles.sliderLabel}>Pitch</Text>
          <Slider
            value={settings.pitch}
            onValueChange={(value) => handleSettingChange('pitch', value)}
            minimumValue={0.5}
            maximumValue={2}
            step={0.1}
            minimumTrackTintColor={theme.colors.primary[isDark ? 'dark' : 'light']}
            maximumTrackTintColor={isDark ? theme.colors.neutral[700] : theme.colors.neutral[300]}
            thumbTintColor={theme.colors.primary[isDark ? 'dark' : 'light']}
          />
          <Text style={styles.sliderValue}>{settings.pitch.toFixed(1)}</Text>
        </View>

        <View style={styles.sliderContainer}>
          <Text style={styles.sliderLabel}>Speed</Text>
          <Slider
            value={settings.rate}
            onValueChange={(value) => handleSettingChange('rate', value)}
            minimumValue={0.5}
            maximumValue={2}
            step={0.1}
            minimumTrackTintColor={theme.colors.primary[isDark ? 'dark' : 'light']}
            maximumTrackTintColor={isDark ? theme.colors.neutral[700] : theme.colors.neutral[300]}
            thumbTintColor={theme.colors.primary[isDark ? 'dark' : 'light']}
          />
          <Text style={styles.sliderValue}>{settings.rate.toFixed(1)}</Text>
        </View>

        <View style={styles.sliderContainer}>
          <Text style={styles.sliderLabel}>Volume</Text>
          <Slider
            value={settings.volume}
            onValueChange={(value) => handleSettingChange('volume', value)}
            minimumValue={0}
            maximumValue={1}
            step={0.1}
            minimumTrackTintColor={theme.colors.primary[isDark ? 'dark' : 'light']}
            maximumTrackTintColor={isDark ? theme.colors.neutral[700] : theme.colors.neutral[300]}
            thumbTintColor={theme.colors.primary[isDark ? 'dark' : 'light']}
          />
          <Text style={styles.sliderValue}>{settings.volume.toFixed(1)}</Text>
        </View>
      </View>

      <AIAvatar
        size={120}
        speaking={isPlaying}
        emotion={isPlaying ? 'happy' : 'neutral'}
        style={{ alignSelf: 'center', marginTop: theme.spacing.xl }}
      />
    </ScrollView>
  );
};

export default VoiceCustomization;
