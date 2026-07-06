import { useState } from 'react';
import { Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';

// Import your separated styles 
import { styles } from './loginStyles'; 

export default function HomeScreen() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false); // Controls the loading spinner

  const handleLogin = async () => {
    // 1. Basic validation
    if (!email || !password) {
      Alert.alert("Error", "Please enter both email/phone and password.");
      return;
    }

    // 2. Start the loading spinner
    setIsLoading(true);

    try {
      // 3. Send the POST request to your LIVE Render server
      const response = await fetch('https://fixora-app.onrender.com/api/mobile-login/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email, 
          password: password
        }),
      });

      const data = await response.json();

      // 4. Handle the server's response
      if (response.ok) {
        // Success! The server gave us a Token.
        Alert.alert("Success!", `Login worked! Token: ${data.token}`);
        
        // In the next step, we will save this token securely to the phone
        // and navigate to the Resident Dashboard!
      } else {
        // The server rejected the credentials (wrong password, etc.)
        Alert.alert("Login Failed", data.error || "Invalid credentials.");
      }
    } catch (error) {
      // The phone couldn't reach the internet/server
      Alert.alert("Network Error", "Could not connect to the server. Please try again.");
      console.error(error);
    } finally {
      // 5. Stop the loading spinner no matter what happens
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

        {/* Dynamic Login Button */}
        <TouchableOpacity 
          style={styles.loginButton} 
          onPress={handleLogin}
          disabled={isLoading} // Prevents double-tapping the button
        >
          {isLoading ? (
            <ActivityIndicator color="white" /> // Shows spinner if loading
          ) : (
            <Text style={styles.loginButtonText}>Sign In</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}