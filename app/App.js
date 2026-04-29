import 'react-native-gesture-handler';
import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createDrawerNavigator } from '@react-navigation/drawer';
import { StatusBar } from 'expo-status-bar';

import HomeScreen from './src/screens/HomeScreen';
import ContactScreen from './src/screens/ContactScreen';

const Drawer = createDrawerNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Drawer.Navigator 
        initialRouteName="Home"
        screenOptions={{
          headerStyle: {
            backgroundColor: '#2E7D32', // Green header
          },
          headerTintColor: '#fff',
          headerTitleStyle: {
            fontWeight: 'bold',
          },
          drawerActiveTintColor: '#2E7D32',
          drawerInactiveTintColor: '#666',
        }}
      >
        <Drawer.Screen 
          name="Home" 
          component={HomeScreen} 
          options={{ title: 'Futebol SC' }}
        />
        <Drawer.Screen 
          name="Login" 
          component={ContactScreen} 
          initialParams={{ title: 'Login' }}
        />
        <Drawer.Screen 
          name="Teams" 
          component={ContactScreen} 
          initialParams={{ title: 'Times' }}
        />
        <Drawer.Screen 
          name="Tournaments" 
          component={ContactScreen} 
          initialParams={{ title: 'Torneios' }}
        />
      </Drawer.Navigator>
    </NavigationContainer>
  );
}
