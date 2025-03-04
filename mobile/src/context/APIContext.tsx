import React, { createContext, useContext } from 'react';
import { useAuth } from './AuthContext';
import { API_URL } from '../constants';

interface APIContextType {
  processVoiceCommand: (audioBlob: Blob) => Promise<string>;
  processTextCommand: (text: string, language?: string) => Promise<any>;
  updateUserContext: (context: any) => Promise<boolean>;
  getUserContext: () => Promise<any>;
}

const APIContext = createContext<APIContextType>({
  processVoiceCommand: async () => '',
  processTextCommand: async () => ({}),
  updateUserContext: async () => false,
  getUserContext: async () => ({}),
});

export const useAPI = () => useContext(APIContext);

interface APIProviderProps {
  children: React.ReactNode;
}

export const APIProvider: React.FC<APIProviderProps> = ({ children }) => {
  const { token, userId } = useAuth();

  const getHeaders = () => {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  };

  const processVoiceCommand = async (audioBlob: Blob): Promise<string> => {
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob);

      const response = await fetch(`${API_URL}/api/speech-to-text`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Speech-to-text processing failed');
      }

      const data = await response.json();
      return data.text;
    } catch (error) {
      console.error('Error processing voice command:', error);
      throw error;
    }
  };

  const processTextCommand = async (text: string, language: string = 'en') => {
    try {
      const response = await fetch(`${API_URL}/api/process-command`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          text,
          source_lang: language,
          target_lang: language,
          user_id: userId,
        }),
      });

      if (!response.ok) {
        throw new Error('Command processing failed');
      }

      return await response.json();
    } catch (error) {
      console.error('Error processing text command:', error);
      throw error;
    }
  };

  const updateUserContext = async (context: any): Promise<boolean> => {
    try {
      const response = await fetch(`${API_URL}/api/update-context`, {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({
          user_id: userId,
          context,
        }),
      });

      return response.ok;
    } catch (error) {
      console.error('Error updating user context:', error);
      return false;
    }
  };

  const getUserContext = async () => {
    try {
      const response = await fetch(`${API_URL}/api/get-context/${userId}`, {
        headers: getHeaders(),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch user context');
      }

      return await response.json();
    } catch (error) {
      console.error('Error fetching user context:', error);
      throw error;
    }
  };

  return (
    <APIContext.Provider
      value={{
        processVoiceCommand,
        processTextCommand,
        updateUserContext,
        getUserContext,
      }}
    >
      {children}
    </APIContext.Provider>
  );
};

export default APIContext;
