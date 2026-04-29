const BASE_URL = 'https://api-futebol-qqpfwbjxua-rj.a.run.app';
const ACCESS_TOKEN = process.env.EXPO_PUBLIC_API_TOKEN;

export const fetchTeams = async () => {
  try {
    const response = await fetch(`${BASE_URL}/teams`, {
      method: 'GET',
      headers: {
        'x-access-token': ACCESS_TOKEN,
        'Content-Type': 'application/json',
      },
    });
    if (!response.ok) throw new Error('Falha ao buscar times');
    return await response.json();
  } catch (error) {
    throw error;
  }
};

export const fetchMatches = async (teamName = null) => {
  try {
    let url = `${BASE_URL}/matches/today`;
    
    if (teamName && teamName !== 'TODOS') {
      const encodedTeam = encodeURIComponent(teamName);
      url = `${BASE_URL}/matches/team/${encodedTeam}`;
    }

    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'x-access-token': ACCESS_TOKEN,
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) throw new Error(`Erro na API: ${response.status}`);
    return await response.json();
  } catch (error) {
    throw error;
  }
};
