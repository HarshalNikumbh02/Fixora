import { useEffect, useState } from 'react';
import { Text, View, TouchableOpacity, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

// Separated styles
import { styles } from '../../styles/dashboardStyles';

export default function DashboardScreen() {
  const router = useRouter();
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    // Fetch the token from internal storage when the screen loads
    const loadToken = async () => {
      const savedToken = await AsyncStorage.getItem('userToken');
      if (savedToken) {
        setToken(savedToken);
      }
    };
    loadToken();
  }, []);

  const handleLogout = async () => {
    // 1. Wipe the secure token from the phone
    await AsyncStorage.removeItem('userToken');
    await AsyncStorage.removeItem('userId');
    
    // 2. Send the user back to the login screen
    router.replace('/');
  };

  return (
    <View style={styles.container}>
      
      {/* Dashboard Header */}
      <View style={styles.header}>
        <Text style={styles.greeting}>Welcome Home! 🏡</Text>
        <Text style={styles.subtitle}>Fixora Resident Dashboard</Text>
      </View>

      {/* Maintenance Request Card */}
      <TouchableOpacity 
        style={styles.card} 
        onPress={() => Alert.alert("Coming Soon", "This will open the Maintenance form!")}
      >
        <Text style={styles.cardTitle}>🔧 Request Maintenance</Text>
        <Text style={styles.cardDescription}>Report plumbing, electrical, or structural issues</Text>
      </TouchableOpacity>

      {/* Society Dues Card */}
      <TouchableOpacity 
        style={styles.card} 
        onPress={() => Alert.alert("Coming Soon", "This will open the Payments portal!")}
      >
        <Text style={styles.cardTitle}>💳 Pay Society Dues</Text>
        <Text style={styles.cardDescription}>View statements and pay monthly maintenance</Text>
      </TouchableOpacity>

      {/* Logout Button */}
      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Log Out</Text>
      </TouchableOpacity>
      
    </View>
  );
}