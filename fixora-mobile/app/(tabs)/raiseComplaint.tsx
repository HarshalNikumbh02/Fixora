import { useState } from 'react';
import { Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

// Separated Styles
import { styles } from '../../styles/complaintStyles';

export default function RaiseComplaintScreen() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async () => {
    if (!title || !description) {
      Alert.alert("Error", "Please fill out all fields.");
      return;
    }

    setIsSubmitting(true);

    try {
      const token = await AsyncStorage.getItem('userToken');

      const response = await fetch('https://fixora-app.onrender.com/api/complaints/create/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${token}`
        },
        body: JSON.stringify({ title, description }),
      });

      // 🟢 NEW: Read raw response to capture the exact error
      const rawText = await response.text();

      if (response.ok) {
        Alert.alert("Success", "Your maintenance request has been submitted!");
        router.replace('/dashboard');
      } else {
        // 🔴 Prints the exact database or backend logic error to your console
        console.log("============== BACKEND COMPLAINT ERROR ==============");
        console.log(rawText);
        console.log("=====================================================");

        Alert.alert("Submission Failed", "The server rejected the complaint. Check your terminal log.");
      }
    } catch (error) {
      Alert.alert("Network Error", "Unable to connect to the server.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>New Complaint</Text>
        <Text style={styles.subtitle}>Report an issue to the society committee</Text>
      </View>

      <Text style={styles.label}>Issue Title</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., Leaking pipe in bathroom"
        placeholderTextColor="#94a3b8"
        value={title}
        onChangeText={setTitle}
      />

      <Text style={styles.label}>Detailed Description</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Provide details like specific location, severity..."
        placeholderTextColor="#94a3b8"
        value={description}
        onChangeText={setDescription}
        multiline
        numberOfLines={4}
      />

      <TouchableOpacity style={styles.submitButton} onPress={handleSubmit} disabled={isSubmitting}>
        {isSubmitting ? <ActivityIndicator color="white" /> : <Text style={styles.submitText}>Submit Request</Text>}
      </TouchableOpacity>
    </View>
  );
}