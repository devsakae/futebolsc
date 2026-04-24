# Futebol SC Scraper

This project is a Python-based automation tool designed to scrape soccer match data from official sources in Santa Catarina, Brazil, specifically from the [Federação Catarinense de Futebol (FCF)](https://fcf.com.br) and [Meu Time na Rede](https://www.meutimenarede.com.br).

## Purpose

The primary goal of this project is to collect and centralize match information, including schedules, scores, team logos, and detailed match statistics (lineups, cards, substitutions, etc.). The scraped data is stored in a structured format in a NoSQL database (Firestore/MongoDB) to support further analysis or application integration.

## Project Structure

- `main.py`: Entry point for the FCF scraper, designed to run as a Google Cloud Function.
- `meutimenarede/`: Contains specialized scrapers for the "Meu Time na Rede" portal, focusing on historical match details, players, and team information.
- `requirements.txt`: Project dependencies (BeautifulSoup4, Requests, PyMongo, etc.).

## Database Schema (Matches)

The match data is saved in the database following a structured document schema. Below is the representation of the `matches` document:

### FCF Match Schema
Basic match information scraped from FCF:

| Field | Type | Description |
| :--- | :--- | :--- |
| `match_id` | Integer | Official match ID from FCF |
| `tournament` | String | Name of the competition |
| `date` | String | Match date (DD/MM/YYYY) |
| `schedule` | String | Match time (HH:MM) |
| `homeTeam` | String | Name of the home team |
| `homeLogo` | String | URL to the home team's logo |
| `homeScore` | Integer | Goals scored by the home team |
| `awayTeam` | String | Name of the away team |
| `awayLogo` | String | URL to the away team's logo |
| `awayScore` | Integer | Goals scored by the away team |
| `stadium` | String | Name of the stadium |
| `location` | String | City/Location of the match |

### Detailed Match Schema (Meu Time na Rede)
Extended match details including technical data:

| Field | Type | Description |
| :--- | :--- | :--- |
| `campeonato` | String | Tournament name |
| `fase` | String | Competition phase |
| `rodada` | String | Round number |
| `date` | String | Match date |
| `homeTeam` | String | Home team name |
| `awayTeam` | String | Away team name |
| `homeScore` | String | Home team goals |
| `awayScore` | String | Away team goals |
| `publico` | String | Total attendance |
| `pagantes` | String | Paying attendance |
| `renda` | String | Total revenue |
| `arbitragem` | Array (Map) | List of officials (Referees, Assistants) |
| `home_treinador` | String | Home team coach |
| `home_escalacao` | Array (Map) | Home team lineup (Pos, Num, Name, URL) |
| `home_cards` | Array (Map) | Cards issued to home team (Name, Card color, Pos) |
| `home_goals` | Array (Map) | Home team goals (Author, Minute, Half) |
| `home_subs` | Array (Map) | Home team substitutions |
| `away_treinador` | String | Away team coach |
| `away_players` | Array (Map) | Away team lineup |
| `away_cards` | Array (Map) | Cards issued to away team |
| `away_goals` | Array (Map) | Away team goals |
| `away_subs` | Array (Map) | Away team substitutions |

## Setup and Usage

1. **Environment Variables**: Use a `.env` file to store your database credentials.
   - `MONGO_URI` or `FIRESTORE_URI`
2. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Run Scraper**:
   ```bash
   python main.py
   ```
