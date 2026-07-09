import { useState } from 'react';
import { Text, View, TextInput, TouchableOpacity, Alert, ActivityIndicator, Image } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import * as ImagePicker from 'expo-image-picker';

// Separated Styles
import { styles } from '../../styles/complaintStyles';

export default function RaiseComplaintScreen() {
  const router = useRouter();
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [imageUri, setImageUri] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Function to open the iOS/Android gallery
  const pickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    
    if (permissionResult.granted === false) {
      Alert.alert("Permission Required", "Fixora needs access to your photos to upload an image.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8, // Compresses image slightly to save user data and server space
    });

    if (!result.canceled) {
      setImageUri(result.assets[0].uri);
    }
  };

  const handleSubmit = async () => {
    if (!title || !description) {
      Alert.alert("Error", "Please fill out all fields.");
      return;
    }

    setIsSubmitting(true);

    try {
      const token = await AsyncStorage.getItem('userToken');

      // 📦 Build FormData container instead of standard JSON
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);

      // Append the image file if the resident selected one
      if (imageUri) {
        const filename = imageUri.split('/').pop() || 'upload.jpg';
        const match = /\.(\w+)$/.exec(filename);
        const type = match ? `image/${match[1]}` : `image/jpeg`;

        // We cast as 'any' to bypass strict web TypeScript compiler rules for React Native files
        formData.append('image', {
          uri: imageUri,
          name: filename,
          type: type
        } as any);
      }

      const response = await fetch('https://fixora-app.onrender.com/api/complaints/create/', {
        method: 'POST',
        headers: {
          'Authorization': `Token ${token}`,
          // ⚠️ IMPORTANT: Never set 'Content-Type': 'application/json' here!
          // The device needs to generate its own multipart boundary header automatically.
        },
        body: formData,
      });

      const rawText = await response.text();

      if (response.ok) {
        Alert.alert("Success", "Your complaint and photo have been submitted!");
        router.replace('/dashboard');
      } else {
        console.log("SERVER RESPONSE ERROR:", rawText);
        Alert.alert("Submission Failed", "Could not process request.");
      }
    } catch (error) {
      Alert.alert("Network Error", "Unable to connect to the server.");
      console.error(error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>New Complaint</Text>
        <Text style={styles.subtitle}>Report an issue with an optional photo attachment</Text>
      </View>

      <Text style={styles.label}>Issue Title</Text>
      <TextInput
        style={styles.input}
        placeholder="e.g., Water leakage in kitchen ceiling"
        placeholderTextColor="#94a3b8"
        value={title}
        onChangeText={setTitle}
      />

      <Text style={styles.label}>Detailed Description</Text>
      <TextInput
        style={[styles.input, styles.textArea]}
        placeholder="Provide details about the issue..."
        placeholderTextColor="#94a3b8"
        value={description}
        onChangeText={setDescription}
        multiline
        numberOfLines={4}
      />

      <Text style={styles.label}>Evidence Photo</Text>
      <TouchableOpacity style={styles.photoButton} onPress={pickImage}>
        <Text style={styles.photoButtonText}>
          {imageUri ? "📸 Change Selected Photo" : "🖼️ Choose from Gallery"}
        </Text>
      </TouchableOpacity>

      {/* Show the selected thumbnail image if it exists */}
      {imageUri && <Image source={{ uri: imageUri }} style={styles.previewImage} />}

      <TouchableOpacity style={styles.submitButton} onPress={handleSubmit} disabled={isSubmitting}>
        {isSubmitting ? <ActivityIndicator color="white" /> : <Text style={styles.submitText}>Submit Request</Text>}
      </TouchableOpacity>
    </View>
  );
}