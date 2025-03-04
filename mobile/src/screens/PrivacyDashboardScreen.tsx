import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  Switch,
  TouchableOpacity,
  StyleSheet,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { useTheme } from '../context/ThemeContext';
import { useAuth } from '../context/AuthContext';
import { useAPI } from '../context/APIContext';
import { theme } from '../constants';

interface PrivacySettings {
  consents: {
    [key: string]: boolean;
  };
  retention_preferences: {
    [key: string]: number;
  };
  data_usage_preferences: {
    [key: string]: string[];
  };
}

const PrivacyDashboardScreen: React.FC = () => {
  const { isDark } = useTheme();
  const { userId } = useAuth();
  const { apiClient } = useAPI();

  const [settings, setSettings] = useState<PrivacySettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [accessLogs, setAccessLogs] = useState<any[]>([]);

  useEffect(() => {
    loadPrivacySettings();
    loadAccessLogs();
  }, []);

  const loadPrivacySettings = async () => {
    try {
      const response = await apiClient.get(`/api/privacy/settings/${userId}`);
      setSettings(response.data);
    } catch (error) {
      Alert.alert('Error', 'Failed to load privacy settings');
    } finally {
      setLoading(false);
    }
  };

  const loadAccessLogs = async () => {
    try {
      const response = await apiClient.get(`/api/privacy/logs/${userId}`);
      setAccessLogs(response.data);
    } catch (error) {
      console.error('Failed to load access logs:', error);
    }
  };

  const updateConsent = async (category: string, value: boolean) => {
    if (!settings) return;

    try {
      setSaving(true);
      const updatedSettings = {
        ...settings,
        consents: {
          ...settings.consents,
          [category]: value,
        },
      };

      await apiClient.put(`/api/privacy/settings/${userId}`, updatedSettings);
      setSettings(updatedSettings);
    } catch (error) {
      Alert.alert('Error', 'Failed to update consent settings');
    } finally {
      setSaving(false);
    }
  };

  const updateRetentionPeriod = async (category: string, days: number) => {
    if (!settings) return;

    try {
      setSaving(true);
      const updatedSettings = {
        ...settings,
        retention_preferences: {
          ...settings.retention_preferences,
          [category]: days,
        },
      };

      await apiClient.put(`/api/privacy/settings/${userId}`, updatedSettings);
      setSettings(updatedSettings);
    } catch (error) {
      Alert.alert('Error', 'Failed to update retention settings');
    } finally {
      setSaving(false);
    }
  };

  const exportData = async () => {
    try {
      const response = await apiClient.get(`/api/privacy/data/export/${userId}`);
      // Handle the exported data (e.g., save to file or share)
      Alert.alert('Success', 'Your data has been exported successfully');
    } catch (error) {
      Alert.alert('Error', 'Failed to export data');
    }
  };

  const deleteData = async (categories: string[]) => {
    try {
      await apiClient.post(`/api/privacy/data/delete/${userId}`, { categories });
      Alert.alert('Success', 'Selected data has been deleted');
      loadPrivacySettings();
    } catch (error) {
      Alert.alert('Error', 'Failed to delete data');
    }
  };

  const styles = StyleSheet.create({
    container: {
      flex: 1,
      backgroundColor: isDark ? theme.dark.background : theme.light.background,
    },
    section: {
      padding: 16,
      borderBottomWidth: 1,
      borderBottomColor: isDark ? theme.dark.border : theme.light.border,
    },
    sectionTitle: {
      fontSize: 18,
      fontWeight: '600',
      color: isDark ? theme.dark.text : theme.light.text,
      marginBottom: 12,
    },
    row: {
      flexDirection: 'row',
      justifyContent: 'space-between',
      alignItems: 'center',
      paddingVertical: 8,
    },
    label: {
      fontSize: 16,
      color: isDark ? theme.dark.text : theme.light.text,
    },
    description: {
      fontSize: 14,
      color: isDark ? theme.dark.textSecondary : theme.light.textSecondary,
      marginTop: 4,
    },
    button: {
      backgroundColor: isDark ? theme.dark.primary : theme.light.primary,
      padding: 12,
      borderRadius: 8,
      alignItems: 'center',
      marginTop: 8,
    },
    buttonText: {
      color: '#fff',
      fontSize: 16,
      fontWeight: '600',
    },
    dangerButton: {
      backgroundColor: theme.light.error,
    },
    logEntry: {
      padding: 12,
      borderBottomWidth: 1,
      borderBottomColor: isDark ? theme.dark.border : theme.light.border,
    },
    logText: {
      fontSize: 14,
      color: isDark ? theme.dark.text : theme.light.text,
    },
    logDate: {
      fontSize: 12,
      color: isDark ? theme.dark.textSecondary : theme.light.textSecondary,
      marginTop: 4,
    },
  });

  if (loading) {
    return (
      <View style={[styles.container, { justifyContent: 'center', alignItems: 'center' }]}>
        <ActivityIndicator size="large" color={isDark ? theme.dark.primary : theme.light.primary} />
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      {/* Consent Management */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data Collection Consent</Text>
        {settings && Object.entries(settings.consents).map(([category, value]) => (
          <View key={category} style={styles.row}>
            <View>
              <Text style={styles.label}>{category.replace('_', ' ').toUpperCase()}</Text>
              <Text style={styles.description}>
                Allow collection and processing of your {category.replace('_', ' ')}
              </Text>
            </View>
            <Switch
              value={value}
              onValueChange={(newValue) => updateConsent(category, newValue)}
              disabled={saving}
            />
          </View>
        ))}
      </View>

      {/* Data Retention */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data Retention</Text>
        {settings && Object.entries(settings.retention_preferences).map(([category, days]) => (
          <View key={category} style={styles.row}>
            <Text style={styles.label}>{category.replace('_', ' ').toUpperCase()}</Text>
            <TouchableOpacity
              onPress={() => {
                Alert.prompt(
                  'Update Retention Period',
                  'Enter number of days to retain data',
                  (text) => updateRetentionPeriod(category, parseInt(text, 10))
                );
              }}
            >
              <Text style={styles.label}>{days} days</Text>
            </TouchableOpacity>
          </View>
        ))}
      </View>

      {/* Data Export */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data Export</Text>
        <TouchableOpacity style={styles.button} onPress={exportData}>
          <Text style={styles.buttonText}>Export My Data</Text>
        </TouchableOpacity>
      </View>

      {/* Data Deletion */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Data Deletion</Text>
        <TouchableOpacity
          style={[styles.button, styles.dangerButton]}
          onPress={() => {
            Alert.alert(
              'Delete Data',
              'Are you sure you want to delete your data?',
              [
                { text: 'Cancel', style: 'cancel' },
                {
                  text: 'Delete',
                  style: 'destructive',
                  onPress: () => deleteData(Object.keys(settings?.consents || {})),
                },
              ]
            );
          }}
        >
          <Text style={styles.buttonText}>Delete My Data</Text>
        </TouchableOpacity>
      </View>

      {/* Access Logs */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Recent Activity</Text>
        {accessLogs.map((log, index) => (
          <View key={index} style={styles.logEntry}>
            <Text style={styles.logText}>
              {log.action} - {log.category}
            </Text>
            <Text style={styles.logDate}>{new Date(log.timestamp).toLocaleString()}</Text>
          </View>
        ))}
      </View>
    </ScrollView>
  );
};

export default PrivacyDashboardScreen;
