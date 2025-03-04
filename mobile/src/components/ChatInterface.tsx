import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Animated,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Dimensions,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { BlurView } from 'expo-blur';
import LottieView from 'lottie-react-native';
import { useTheme } from '../context/ThemeContext';
import theme from '../styles/theme';
import AIAvatar from './AIAvatar';

interface Message {
  id: string;
  text: string;
  isUser: boolean;
  timestamp: Date;
  emotion?: 'neutral' | 'happy' | 'thinking' | 'listening';
}

interface ChatInterfaceProps {
  onSendMessage: (message: string) => Promise<void>;
  onStartVoice: () => void;
  onStopVoice: () => void;
  isListening: boolean;
}

const { width } = Dimensions.get('window');

const ChatInterface: React.FC<ChatInterfaceProps> = ({
  onSendMessage,
  onStartVoice,
  onStopVoice,
  isListening,
}) => {
  const { isDark } = useTheme();
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const scrollViewRef = useRef<ScrollView>(null);
  const fadeAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(50)).current;

  useEffect(() => {
    Animated.parallel([
      Animated.timing(fadeAnim, {
        toValue: 1,
        duration: 500,
        useNativeDriver: true,
      }),
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 500,
        useNativeDriver: true,
      }),
    ]).start();
  }, []);

  const handleSend = async () => {
    if (!inputText.trim()) return;

    const newMessage: Message = {
      id: Date.now().toString(),
      text: inputText,
      isUser: true,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, newMessage]);
    setInputText('');
    setIsTyping(true);

    try {
      await onSendMessage(inputText);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsTyping(false);
    }
  };

  const renderMessage = (message: Message, index: number) => {
    const isLastMessage = index === messages.length - 1;

    return (
      <Animated.View
        key={message.id}
        style={[
          styles.messageContainer,
          message.isUser ? styles.userMessage : styles.aiMessage,
          isLastMessage && {
            opacity: fadeAnim,
            transform: [{ translateY: slideAnim }],
          },
        ]}
      >
        {!message.isUser && (
          <AIAvatar
            size={40}
            emotion={message.emotion}
            speaking={isTyping && isLastMessage}
            style={styles.messageAvatar}
          />
        )}
        <BlurView
          intensity={80}
          tint={isDark ? 'dark' : 'light'}
          style={[
            styles.messageContent,
            message.isUser ? styles.userMessageContent : styles.aiMessageContent,
          ]}
        >
          <Text
            style={[
              styles.messageText,
              message.isUser ? styles.userMessageText : styles.aiMessageText,
            ]}
          >
            {message.text}
          </Text>
          <Text style={styles.timestamp}>
            {message.timestamp.toLocaleTimeString([], {
              hour: '2-digit',
              minute: '2-digit',
            })}
          </Text>
        </BlurView>
      </Animated.View>
    );
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: isDark ? theme.colors.neutral[900] : theme.colors.neutral[50],
    },
    messagesContainer: {
      flex: 1,
      padding: theme.spacing.md,
    },
    messageContainer: {
      flexDirection: 'row',
      marginBottom: theme.spacing.md,
      alignItems: 'flex-end',
    },
    userMessage: {
      justifyContent: 'flex-end',
    },
    aiMessage: {
      justifyContent: 'flex-start',
    },
    messageAvatar: {
      marginRight: theme.spacing.sm,
    },
    messageContent: {
      maxWidth: width * 0.7,
      padding: theme.spacing.md,
      borderRadius: theme.borderRadius.lg,
      ...theme.shadows.md[isDark ? 'dark' : 'light'],
    },
    userMessageContent: {
      backgroundColor: theme.colors.primary[isDark ? 'dark' : 'light'],
      borderBottomRightRadius: 0,
    },
    aiMessageContent: {
      backgroundColor: isDark ? theme.colors.neutral[800] : theme.colors.neutral[100],
      borderBottomLeftRadius: 0,
    },
    messageText: {
      fontSize: theme.typography.fontSize.base,
      lineHeight: theme.typography.lineHeight.relaxed,
    },
    userMessageText: {
      color: theme.colors.neutral[50],
    },
    aiMessageText: {
      color: isDark ? theme.colors.neutral[50] : theme.colors.neutral[900],
    },
    timestamp: {
      fontSize: theme.typography.fontSize.xs,
      color: isDark ? theme.colors.neutral[400] : theme.colors.neutral[600],
      marginTop: theme.spacing.xs,
      textAlign: 'right',
    },
    inputContainer: {
      padding: theme.spacing.md,
      borderTopWidth: 1,
      borderTopColor: isDark ? theme.colors.neutral[800] : theme.colors.neutral[200],
      backgroundColor: isDark ? theme.colors.neutral[900] : theme.colors.neutral[50],
    },
    inputWrapper: {
      flexDirection: 'row',
      alignItems: 'center',
    },
    input: {
      flex: 1,
      backgroundColor: isDark ? theme.colors.neutral[800] : theme.colors.neutral[100],
      borderRadius: theme.borderRadius.full,
      paddingHorizontal: theme.spacing.lg,
      paddingVertical: theme.spacing.md,
      fontSize: theme.typography.fontSize.base,
      color: isDark ? theme.colors.neutral[50] : theme.colors.neutral[900],
      ...theme.shadows.sm[isDark ? 'dark' : 'light'],
    },
    voiceButton: {
      width: 48,
      height: 48,
      borderRadius: 24,
      marginLeft: theme.spacing.md,
      justifyContent: 'center',
      alignItems: 'center',
      backgroundColor: isListening
        ? theme.colors.error[isDark ? 'dark' : 'light']
        : theme.colors.primary[isDark ? 'dark' : 'light'],
      ...theme.shadows.md[isDark ? 'dark' : 'light'],
    },
    typingIndicator: {
      flexDirection: 'row',
      alignItems: 'center',
      padding: theme.spacing.sm,
    },
    typingText: {
      fontSize: theme.typography.fontSize.sm,
      color: isDark ? theme.colors.neutral[400] : theme.colors.neutral[600],
      marginLeft: theme.spacing.sm,
    },
  });

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <ScrollView
        ref={scrollViewRef}
        style={styles.messagesContainer}
        onContentSizeChange={() => scrollViewRef.current?.scrollToEnd()}
      >
        {messages.map((message, index) => renderMessage(message, index))}
        {isTyping && (
          <View style={styles.typingIndicator}>
            <LottieView
              source={require('../assets/animations/typing.json')}
              autoPlay
              loop
              style={{ width: 40, height: 20 }}
            />
            <Text style={styles.typingText}>Krish is typing...</Text>
          </View>
        )}
      </ScrollView>

      <View style={styles.inputContainer}>
        <View style={styles.inputWrapper}>
          <TextInput
            style={styles.input}
            placeholder="Type a message..."
            placeholderTextColor={isDark ? theme.colors.neutral[400] : theme.colors.neutral[600]}
            value={inputText}
            onChangeText={setInputText}
            onSubmitEditing={handleSend}
            multiline
          />
          <TouchableOpacity
            style={styles.voiceButton}
            onPress={isListening ? onStopVoice : onStartVoice}
          >
            <LottieView
              source={
                isListening
                  ? require('../assets/animations/recording.json')
                  : require('../assets/animations/mic.json')
              }
              autoPlay
              loop
              style={{ width: 24, height: 24 }}
            />
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
};

export default ChatInterface;
