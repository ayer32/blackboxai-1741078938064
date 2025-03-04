import React, { createContext, useContext, useState, useEffect } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { API_URL, AUTH_TOKEN_KEY, USER_ID_KEY } from '../constants';

interface AuthState {
  isAuthenticated: boolean;
  token: string | null;
  userId: string | null;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (token: string, userId: string) => Promise<void>;
  logout: () => Promise<void>;
  registerFace: (imageData: string) => Promise<boolean>;
  verifyFace: (imageData: string) => Promise<boolean>;
}

const initialState: AuthState = {
  isAuthenticated: false,
  token: null,
  userId: null,
  isLoading: true,
};

const AuthContext = createContext<AuthContextType>({
  ...initialState,
  login: async () => {},
  logout: async () => {},
  registerFace: async () => false,
  verifyFace: async () => false,
});

export const useAuth = () => useContext(AuthContext);

interface AuthProviderProps {
  children: React.ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [state, setState] = useState<AuthState>(initialState);

  useEffect(() => {
    loadAuthState();
  }, []);

  const loadAuthState = async () => {
    try {
      const [token, userId] = await Promise.all([
        AsyncStorage.getItem(AUTH_TOKEN_KEY),
        AsyncStorage.getItem(USER_ID_KEY),
      ]);

      if (token && userId) {
        // Verify token validity with backend
        const response = await fetch(`${API_URL}/verify-token`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        if (response.ok) {
          setState({
            isAuthenticated: true,
            token,
            userId,
            isLoading: false,
          });
          return;
        }
      }

      setState({
        ...initialState,
        isLoading: false,
      });
    } catch (error) {
      console.error('Error loading auth state:', error);
      setState({
        ...initialState,
        isLoading: false,
      });
    }
  };

  const login = async (token: string, userId: string) => {
    try {
      await Promise.all([
        AsyncStorage.setItem(AUTH_TOKEN_KEY, token),
        AsyncStorage.setItem(USER_ID_KEY, userId),
      ]);

      setState({
        isAuthenticated: true,
        token,
        userId,
        isLoading: false,
      });
    } catch (error) {
      console.error('Error saving auth state:', error);
      throw new Error('Failed to save authentication state');
    }
  };

  const logout = async () => {
    try {
      await Promise.all([
        AsyncStorage.removeItem(AUTH_TOKEN_KEY),
        AsyncStorage.removeItem(USER_ID_KEY),
      ]);

      setState({
        isAuthenticated: false,
        token: null,
        userId: null,
        isLoading: false,
      });
    } catch (error) {
      console.error('Error clearing auth state:', error);
      throw new Error('Failed to clear authentication state');
    }
  };

  const registerFace = async (imageData: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/face/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(state.token && { Authorization: `Bearer ${state.token}` }),
        },
        body: JSON.stringify({
          user_id: state.userId,
          image_data: imageData,
        }),
      });

      const result = await response.json();
      return result.success;
    } catch (error) {
      console.error('Error registering face:', error);
      return false;
    }
  };

  const verifyFace = async (imageData: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/face/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: state.userId,
          image_data: imageData,
        }),
      });

      const result = await response.json();
      
      if (result.success && result.access_token) {
        await login(result.access_token, state.userId || '');
        return true;
      }
      
      return false;
    } catch (error) {
      console.error('Error verifying face:', error);
      return false;
    }
  };

  return (
    <AuthContext.Provider
      value={{
        ...state,
        login,
        logout,
        registerFace,
        verifyFace,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
