import { useState } from 'react';
import { Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

// 🟢 Separated Styles imported from root styles folder
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

      // Read response as plain text first to stop the JSON parser from crashing
      const rawText = await response.text(); 

      try {
        const data = JSON.parse(rawText);

        if (response.ok) {
          await AsyncStorage.setItem('userToken', data.token);
          await AsyncStorage.setItem('userId', String(data.user_id));
          router.replace('/dashboard');
        } else {
          Alert.alert("Login Failed", data.error || "Invalid credentials.");
        }
      } catch (parseError) {
        // 🔴 If Django crashes, this will print the exact Python error page to your terminal!
        console.log("============== DJANGO CRASH LOG START ==============");
        console.log(rawText);
        console.log("============== DJANGO CRASH LOG END ==============");
        
        Alert.alert("Server Error", "Django sent an invalid response. Check your VS Code terminal log.");
      }

    } catch (error) {
      Alert.alert("Network Error", "Could not connect to the server.");
      console.error(error);
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