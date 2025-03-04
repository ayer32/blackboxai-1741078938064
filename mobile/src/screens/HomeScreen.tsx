import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  Platform,
  StyleSheet,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { Camera } from '@react-native-camera/camera';
import Voice from '@react-native-voice/voice';
import { useNavigation } from '@react-navigation/native';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useAPI } from '../context/APIContext';
import { theme, ERROR_MESSAGES } from '../constants';

const { width } = Dimensions.get('window');

const HomeScreen: React.FC = () => {
  const navigation = useNavigation();
  const { isDark } = useTheme();
  const { isAuthenticated, verifyFace } = useAuth();
  const { processVoiceCommand, processTextCommand } = useAPI();

  const [isListening, setIsListening] = useState(false);
  const [messages, setMessages] = useState<Array<{ text: string; isUser: boolean }>>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const cameraRef = useRef<any>(null);

  useEffect(() => {
    setupVoiceRecognition();
    return () => {
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const setupVoiceRecognition = () => {
    Voice.onSpeechStart = () => setIsListening(true);
    Voice.onSpeechEnd = () => setIsListening(false);
    Voice.onSpeechResults = async (event: any) => {
      if (event.value && event.value[0]) {
        const command = event.value[0];
        addMessage(command, true);
        await processCommand(command);
      }
    };
    Voice.onSpeechError = (error: any) => {
      console.error('Speech recognition error:', error);
      setIsListening(false);
    };
  };

  const startListening = async () => {
    try {
      await Voice.start('en-US');
    } catch (error) {
      console.error('Error starting voice recognition:', error);
    }
  };

  const stopListening = async () => {
    try {
      await Voice.stop();
    } catch (error) {
      console.error('Error stopping voice recognition:', error);
    }
  };

  const addMessage = (text: string, isUser: boolean) => {
    setMessages(prev => [...prev, { text, isUser }]);
    setTimeout(() => {
      scrollViewRef.current?.scrollToEnd({ animated: true });
    }, 100);
  };

  const processCommand = async (command: string) => {
    try {
      setIsProcessing(true);
      const response = await processTextCommand(command);
      if (response.response) {
        addMessage(response.response, false);
      }
    } catch (error) {
      console.error('Error processing command:', error);
      addMessage(ERROR_MESSAGES.UNKNOWN, false);
    } finally {
      setIsProcessing(false);
    }
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: isDark ? theme.dark.background : theme.light.background,
    },
    messagesContainer: {
      flex: 1,
      padding: 16,
    },
    message: {
      maxWidth: width * 0.8,
      padding: 12,
      borderRadius: 16,
      marginVertical: 4,
    },
    userMessage: {
      backgroundColor: isDark ? theme.dark.primary : theme.light.primary,
      alignSelf: 'flex-end',
    },
    assistantMessage: {
      backgroundColor: isDark ? theme.dark.surface : theme.light.surface,
      alignSelf: 'flex-start',
    },
    messageText: {
      color: isDark ? theme.dark.text : theme.light.text,
      fontSize: 16,
    },
    controlsContainer: {
      padding: 16,
      borderTopWidth: 1,
      borderTopColor: isDark ? theme.dark.border : theme.light.border,
    },
    micButton: {
      backgroundColor: isListening ? theme.light.error : (isDark ? theme.dark.primary : theme.light.primary),
      width: 64,
      height: 64,
      borderRadius: 32,
      alignItems: 'center',
      justifyContent: 'center',
      alignSelf: 'center',
    },
    micIcon: {
      color: '#fff',
      fontSize: 24,
    },
  });

  return (
    <View style={styles.container}>
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        contentContainerStyle={{ paddingBottom: 16 }}
      >
        {messages.map((message, index) => (
          <View
            key={index}
            style={[
              styles.message,
              message.isUser ? styles.userMessage : styles.assistantMessage,
            ]}
          >
            <Text style={styles.messageText}>{message.text}</Text>
          </View>
        ))}
        {isProcessing && (
          <ActivityIndicator
            size="small"
            color={isDark ? theme.dark.primary : theme.light.primary}
            style={{ marginTop: 8 }}
          />
        )}
      </ScrollView>

      <View style={styles.controlsContainer}>
        <TouchableOpacity
          style={styles.micButton}
          onPress={isListening ? stopListening : startListening}
          disabled={!isAuthenticated}
        >
          <Text style={styles.micIcon}>
            {isListening ? '⏹' : '🎤'}
          </Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

export default HomeScreen;
