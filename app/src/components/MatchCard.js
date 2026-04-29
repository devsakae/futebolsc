import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';

const MatchCard = ({ match, isSpotlight }) => {
  const isFutureMatch = () => {
    try {
      const [day, month, year] = match.date.split('/');
      const matchDate = new Date(year, month - 1, day);
      const today = new Date();
      today.setHours(0, 0, 0, 0);
      return matchDate > today;
    } catch (e) {
      return false;
    }
  };

  const future = isFutureMatch();

  return (
    <View style={[styles.card, isSpotlight ? styles.spotlightCard : styles.standardCard]}>
      {/* Top: Tournament and Date/Time */}
      <View style={styles.header}>
        <Text style={[styles.tournamentText, isSpotlight && styles.spotlightTournamentText]}>
          {match.tournament}
        </Text>
        <Text style={[styles.dateTimeText, isSpotlight && styles.spotlightDateTimeText]}>
          {match.date} · {match.schedule}
        </Text>
      </View>

      {/* Center: Teams Row */}
      <View style={styles.contentRow}>
        <View style={styles.teamInfo}>
          <Image 
            source={{ uri: match.homeLogo }} 
            style={isSpotlight ? styles.spotlightLogo : styles.standardLogo} 
            resizeMode="contain"
          />
          <Text style={[styles.teamName, isSpotlight && styles.spotlightTeamName]} numberOfLines={1}>
            {match.homeTeam}
          </Text>
        </View>

        <View style={styles.centerInfo}>
          {future ? (
            <Text style={[styles.vsTextLabel, isSpotlight && styles.spotlightScoreText]}>x</Text>
          ) : (
            <Text style={[styles.scoreText, isSpotlight && styles.spotlightScoreText]}>
              {match.homeScore} - {match.awayScore}
            </Text>
          )}
        </View>

        <View style={styles.teamInfo}>
          <Image 
            source={{ uri: match.awayLogo }} 
            style={isSpotlight ? styles.spotlightLogo : styles.standardLogo} 
            resizeMode="contain"
          />
          <Text style={[styles.teamName, isSpotlight && styles.spotlightTeamName]} numberOfLines={1}>
            {match.awayTeam}
          </Text>
        </View>
      </View>

      {/* Bottom: Location */}
      {(match.stadium || match.location) && (
        <View style={styles.footer}>
          <Text style={[styles.locationText, isSpotlight && styles.spotlightLocationText]}>
            📍 {match.stadium}{match.location ? ` - ${match.location}` : ''}
          </Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 8,
    marginVertical: 6,
    marginHorizontal: 16,
    padding: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 1.41,
  },
  standardCard: {
    height: 140, // Increased slightly to fit new layout
    justifyContent: 'space-between',
  },
  spotlightCard: {
    height: 230, // Increased to fit new layout
    borderWidth: 2,
    borderColor: '#2E7D32',
    backgroundColor: '#F1F8E9',
    elevation: 6,
    padding: 18,
    marginVertical: 12,
  },
  header: {
    alignItems: 'center',
    marginBottom: 5,
  },
  tournamentText: {
    fontSize: 12, // Increased slightly
    fontWeight: '700',
    color: '#2E7D32',
    textAlign: 'center',
    textTransform: 'uppercase',
  },
  spotlightTournamentText: {
    fontSize: 15,
  },
  dateTimeText: {
    fontSize: 10,
    color: '#666',
    marginTop: 2,
    fontWeight: '500',
  },
  spotlightDateTimeText: {
    fontSize: 12,
  },
  contentRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 4,
  },
  teamInfo: {
    flex: 1,
    alignItems: 'center',
  },
  standardLogo: {
    width: 32,
    height: 32,
    marginBottom: 4,
  },
  spotlightLogo: {
    width: 60,
    height: 60,
    marginBottom: 8,
  },
  teamName: {
    fontSize: 11,
    fontWeight: '500',
    color: '#333',
    textAlign: 'center',
  },
  spotlightTeamName: {
    fontSize: 14,
    fontWeight: '700',
  },
  centerInfo: {
    paddingHorizontal: 10,
    alignItems: 'center',
    minWidth: 60,
  },
  scoreText: {
    fontSize: 18,
    fontWeight: '800',
    color: '#333',
  },
  vsTextLabel: {
    fontSize: 20,
    fontWeight: '300',
    color: '#aaa',
  },
  spotlightScoreText: {
    fontSize: 28,
  },
  footer: {
    marginTop: 6,
    alignItems: 'center',
    borderTopWidth: 0.5,
    borderTopColor: '#eee',
    paddingTop: 6,
  },
  locationText: {
    fontSize: 9,
    color: '#888',
    textAlign: 'center',
  },
  spotlightLocationText: {
    fontSize: 11,
    fontWeight: '500',
  },
});

export default MatchCard;
