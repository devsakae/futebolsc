import React from 'react';
import { View, Text, StyleSheet, Button } from 'react-native';

const ContactScreen = ({ route, navigation }) => {
  const { title } = route.params || { title: 'Contato' };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{title}</Text>
      <Text style={styles.description}>
        Esta é a página de {title.toLowerCase()}.
      </Text>
      <Text style={styles.info}>
        Em breve traremos mais informações aqui.
      </Text>
      <View style={styles.buttonContainer}>
        <Button title="Voltar" onPress={() => navigation.goBack()} />
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
    backgroundColor: '#fff',
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#2196F3',
    marginBottom: 10,
  },
  description: {
    fontSize: 16,
    textAlign: 'center',
    marginBottom: 5,
  },
  info: {
    fontSize: 14,
    color: '#888',
    textAlign: 'center',
    marginBottom: 30,
  },
  buttonContainer: {
    width: '100%',
    paddingHorizontal: 50,
  },
});

export default ContactScreen;
