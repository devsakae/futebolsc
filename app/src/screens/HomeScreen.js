import React, { useState, useEffect, useRef } from 'react';
import { 
  View, 
  Text, 
  FlatList, 
  ActivityIndicator, 
  StyleSheet, 
  RefreshControl,
  SafeAreaView
} from 'react-native';
import { Picker } from '@react-native-picker/picker';
import { fetchMatches, fetchTeams } from '../services/api';
import MatchCard from '../components/MatchCard';

const HomeScreen = () => {
  const [matches, setMatches] = useState([]);
  const [teams, setTeams] = useState([]);
  const [selectedTeam, setSelectedTeam] = useState('TODOS');
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState(null);
  const [spotlightId, setSpotlightId] = useState(null);
  const flatListRef = useRef(null);

  const getTodayStr = () => {
    const today = new Date();
    const day = String(today.getDate()).padStart(2, '0');
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const year = today.getFullYear();
    return `${day}/${month}/${year}`;
  };

  const findHighlightIndex = (matchList) => {
    if (!matchList || matchList.length === 0) return -1;
    
    const todayStr = getTodayStr();
    
    // 1. Procura jogo EXATAMENTE hoje para destacar
    const todayIndex = matchList.findIndex(m => m.date === todayStr);
    
    if (todayIndex !== -1) {
      return { index: todayIndex, highlight: true };
    }

    // 2. Se não tem hoje, apenas busca o mais próximo para rolar (sem destacar visualmente)
    const now = new Date();
    let minDiff = Infinity;
    let closestIndex = 0;

    matchList.forEach((match, i) => {
      try {
        const [day, month, year] = match.date.split('/');
        const matchDate = new Date(year, month - 1, day);
        const diff = Math.abs(now - matchDate);
        if (diff < minDiff) {
          minDiff = diff;
          closestIndex = i;
        }
      } catch (e) {}
    });

    return { index: closestIndex, highlight: false };
  };

  const loadData = async (team, initial = false) => {
    try {
      if (initial) setLoading(true);
      else setRefreshing(true);

      const [matchesData, teamsData] = await Promise.all([
        fetchMatches(team),
        initial ? fetchTeams() : Promise.resolve(teams)
      ]);

      setMatches(matchesData);
      if (initial) setTeams(teamsData);
      
      const result = findHighlightIndex(matchesData);
      if (result.index !== -1) {
        setSpotlightId(result.highlight ? matchesData[result.index]._id : null);
        triggerAutoScroll(result.index);
      } else {
        setSpotlightId(null);
      }
    } catch (err) {
      setError('Erro ao carregar dados.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const triggerAutoScroll = (index) => {
    setTimeout(() => {
      if (flatListRef.current && index !== -1 && matches.length > index) {
        flatListRef.current.scrollToIndex({
          index,
          animated: true,
          viewPosition: 0.5,
        });
      }
    }, 800);
  };

  useEffect(() => {
    loadData('TODOS', true);
  }, []);

  const handleTeamChange = (itemValue) => {
    setSelectedTeam(itemValue);
    loadData(itemValue);
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#2E7D32" />
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.pickerContainer}>
        <Text style={styles.pickerLabel}>Filtrar por Time:</Text>
        <View style={styles.pickerWrapper}>
          <Picker
            selectedValue={selectedTeam}
            onValueChange={handleTeamChange}
            style={styles.picker}
            dropdownIconColor="#2E7D32"
          >
            <Picker.Item label="Hoje (Todos os times)" value="TODOS" />
            {teams.map((team) => (
              <Picker.Item key={team} label={team} value={team} />
            ))}
          </Picker>
        </View>
      </View>

      <FlatList
        ref={flatListRef}
        data={matches}
        keyExtractor={(item) => item._id || Math.random().toString()}
        renderItem={({ item }) => (
          <MatchCard 
            match={item} 
            isSpotlight={item._id === spotlightId} 
          />
        )}
        onScrollToIndexFailed={(info) => {
          flatListRef.current?.scrollToOffset({ offset: info.averageItemLength * info.index, animated: true });
        }}
        contentContainerStyle={styles.list}
        ListEmptyComponent={
          <View style={styles.center}>
            <Text style={styles.emptyText}>Nenhum jogo encontrado.</Text>
          </View>
        }
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={() => loadData(selectedTeam)} colors={['#2E7D32']} />
        }
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F5F5F5',
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  pickerContainer: {
    padding: 15,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  pickerLabel: {
    fontSize: 11,
    color: '#666',
    marginBottom: 5,
    fontWeight: 'bold',
    textTransform: 'uppercase',
  },
  pickerWrapper: {
    backgroundColor: '#f9f9f9',
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
    overflow: 'hidden',
  },
  picker: {
    height: 50,
    width: '100%',
  },
  list: {
    paddingBottom: 40,
  },
  emptyText: {
    color: '#888',
    fontSize: 16,
    marginTop: 50,
  },
});

export default HomeScreen;
