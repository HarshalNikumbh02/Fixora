import { StyleSheet } from 'react-native';

export const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f8fafc',
    padding: 24,
  },
  header: {
    marginTop: 60,
    marginBottom: 30,
  },
  greeting: {
    fontSize: 32,
    fontWeight: '800',
    color: '#1f2c48',
    letterSpacing: -0.5,
  },
  subtitle: {
    fontSize: 16,
    color: '#64748b',
    marginTop: 6,
    fontWeight: '500',
  },
  card: {
    backgroundColor: 'white',
    padding: 22,
    borderRadius: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.05,
    shadowRadius: 10,
    elevation: 3, // For Android shadow
  },
  cardTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1f2c48',
    marginBottom: 4,
  },
  cardDescription: {
    fontSize: 14,
    color: '#64748b',
  },
  logoutButton: {
    backgroundColor: '#ef4444', // A clean red for the logout action
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 30,
  },
  logoutText: {
    color: 'white',
    fontWeight: '700',
    fontSize: 16,
  },
});