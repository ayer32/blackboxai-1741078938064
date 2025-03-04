import React, { useEffect, useState } from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { Platform, StatusBar } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Voice from '@react-native-voice/voice';

// Screens
import HomeScreen from './screens/HomeScreen';
import AuthScreen from './screens/AuthScreen';
import ChatScreen from './screens/ChatScreen';
import SettingsScreen from './screens/SettingsScreen';

// Components
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider } from './context/AuthContext';
import { APIProvider } from './context/APIContext';

// Navigation
const Stack = createStackNavigator();

// Constants
import { THEME_KEY, API_URL } from './constants';

const App = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    initializeApp();
    return () => {
      // Cleanup voice recognition
      Voice.destroy().then(Voice.removeAllListeners);
    };
  }, []);

  const initializeApp = async () => {
    try {
      // Load theme preference
      const savedTheme = await AsyncStorage.getItem(THEME_KEY);
      if (savedTheme) {
        setIsDarkMode(savedTheme === 'dark');
      }

      // Check authentication status
      const authToken = await AsyncStorage.getItem('authToken');
      if (authToken) {
        // Verify token validity
        const response = await fetch(`${API_URL}/verify-token`, {
          headers: { Authorization: `Bearer ${authToken}` }
        });
        setIsAuthenticated(response.ok);
      }
    } catch (error) {
      console.error('Initialization error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return null; // Or a loading screen
  }

  return (
    <ThemeProvider initialTheme={isDarkMode ? 'dark' : 'light'}>
      <AuthProvider>
        <APIProvider>
          <NavigationContainer>
            <StatusBar
              barStyle={isDarkMode ? 'light-content' : 'dark-content'}
              backgroundColor={isDarkMode ? '#000' : '#fff'}
            />
            <Stack.Navigator
              screenOptions={{
                headerStyle: {
                  backgroundColor: isDarkMode ? '#1a1a1a' : '#fff',
                },
                headerTintColor: isDarkMode ? '#fff' : '#000',
                cardStyle: { backgroundColor: isDarkMode ? '#000' : '#fff' },
              }}
            >
              {!isAuthenticated ? (
                <Stack.Screen
                  name="Auth"
                  component={AuthScreen}
                  options={{ headerShown: false }}
                />
              ) : (
                <>
                  <Stack.Screen
                    name="Home"
                    component={HomeScreen}
                    options={{ title: 'Krish AI Assistant' }}
                  />
                  <Stack.Screen
                    name="Chat"
                    component={ChatScreen}
                    options={{ title: 'Chat with Krish' }}
                  />
                  <Stack.Screen
                    name="Settings"
                    component={SettingsScreen}
                    options={{ title: 'Settings' }}
                  />
                </>
              )}
            </Stack.Navigator>
          </NavigationContainer>
        </APIProvider>
      </AuthProvider>
    </ThemeProvider>
  );
};

export default App;

// Register the app for web as PWA
if (Platform.OS === 'web') {
  const registerServiceWorker = async () => {
    if ('serviceWorker' in navigator) {
      try {
        await navigator.serviceWorker.register('/service-worker.js');
        console.log('Service Worker registered successfully');
      } catch (error) {
        console.error('Service Worker registration failed:', error);
      }
    }
  };

  registerServiceWorker();
}
