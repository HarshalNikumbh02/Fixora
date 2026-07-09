import { useState } from 'react';
import { Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

// Separated Styles imported from root styles folder
import { styles } from '../../styles/loginStyles'; 

export default function HomeScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleLogin = async () => {
    if (!email || !password) {
      Alert.alert("Error", "Please enter both email/phone and password.");
      return;
    }

    setIsLoading(true);

    try {
      const response = await fetch('https://fixora-app.onrender.com/api/mobile-login/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: email, password: password }),
      });

      const rawText = await response.text(); 
      let data;

      // 1. ISOLATED CHECK: Did Django send valid data?
      try {
        data = JSON.parse(rawText);
      } catch (parseError) {
        console.log("============== REAL BACKEND CRASH ==============");
        print(rawText);
        Alert.alert("Server Error", "Django sent an invalid HTML page.");
        setIsLoading(false);
        return;
      }

      // 2. ISOLATED CHECK: Did the credentials pass?
      if (!response.ok) {
        Alert.alert("Login Failed", data.error || "Invalid credentials.");
        setIsLoading(false);
        return;
      }

      // 3. ISOLATED CHECK: Is the phone storage or navigation breaking?
      try {
        console.log("Django passed! Attempting to save token securely...");
        await AsyncStorage.setItem('userToken', data.token);
        await AsyncStorage.setItem('userId', String(data.user_id));
        
        console.log("Token saved! Redirecting to dashboard...");
        router.replace('/dashboard');
      } catch (phoneError: any) {
        console.log("============== PHONE DEVICE ERROR ==============");
        console.log(phoneError);
        Alert.alert("Device Error", `Could not complete action: ${phoneError.message}`);
      }

    } catch (networkError) {
      Alert.alert("Network Error", "Could not connect to the server.");
      console.error(networkError);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.headerContainer}>
        <Text style={styles.title}>Fixora</Text>
        <Text style={styles.subtitle}>Smart Society Care</Text>
      </View>

      <View style={styles.formContainer}>
        <TextInput
          style={styles.input}
          placeholder="Email or Phone Number"
          placeholderTextColor="#94a3b8"
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
        />

        <TextInput
          style={styles.input}
          placeholder="Password"
          placeholderTextColor="#94a3b8"
          value={password}
          onChangeText={setPassword}
          secureTextEntry 
        />

        <TouchableOpacity style={styles.loginButton} onPress={handleLogin} disabled={isLoading}>
          {isLoading ? <ActivityIndicator color="white" /> : <Text style={styles.loginButtonText}>Sign In</Text>}
        </TouchableOpacity>
      </View>
    </View>
  );
}