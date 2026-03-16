# coding=iso-8859-1
import requests, os, certifi, re, time
from datetime import datetime
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pymongo.mongo_client import MongoClient
from bson.objectid import ObjectId

load_dotenv()

class Match:
    def __init__(self) -> None:
        self.match_id = ObjectId()
        self.fcf_id = 0
        self.tournament = ""
        self.date = ""
        self.homeTeam = ""
        self.homeLogo = ""
        self.homeScore = 0
        self.awayTeam = ""
        self.awayScore = 0
        self.awayLogo = ""
        self.stadium = ""
        self.location = ""
        self.schedule = ""

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        return f"Match(tournament={self.tournament}, date={self.date}, schedule={self.schedule} homeTeam={self.homeTeam}, homeLogo={self.homeLogo}, awayTeam={self.awayTeam}, awayLogo={self.awayLogo}, stadium={self.stadium}, location={self.location})"

    def to_dict(self):
        return self.__dict__

    @classmethod
    def from_dict(cls, data):
        return cls(**data)

class WebScraper:
    def __init__(self, year: int):
        self.year = year
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.lista = []
        # self.scrapped_match = Match() # type: ignore
        try:
            self.client = MongoClient(os.getenv("MONGODB_URI"), tlsCAFile=certifi.where())
            self.client.jogos.command('ping')
            print("Conectado ao MongoDB!")
            self.db_father = self.client["jogos"]
            self.collection = self.client["jogos"]["fcf_sc_" + str(year)]
            self.collection.create_index("match_id", unique=True, sparse=True)
        except Exception as e:
            print(f"Erro ao conectar MongoDB: {e}")
            self.client = None
            self.db_father = None
            self.collection = None

    def lista_competicoes(self, nome, url):
        self.lista.append({
            "nome": nome,
            "url": url
        })

    def scrape(self, url) -> BeautifulSoup | None:
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup
        except requests.RequestException as e:
            print(f"Error scrape/scraping {url}: {e}")
            return None

    def scrap_FCF_profissional(self):
        scrap_url = "https://fcf.com.br/competicoes/competicoes-profissionais-" + str(self.year)
        try:
            fcf_soup = self.scrape(scrap_url)
            competicoes_div = fcf_soup.find("div", id="cb-content") # type: ignore
            competicoes = competicoes_div.find("article").find("ul").find_all("li") # type: ignore
            for torneio in competicoes:
                if torneio.find("ul"):
                    continue
                torneio_data = torneio.find("a")
                self.lista_competicoes(torneio_data.text, torneio_data.get("href"))
        except Exception as e:
            print(f"Error scrap_FCF_profissional!", e)
            return
        finally:
            return None

    def scrap_FCF_naoprofi(self):
        scrap_url = "https://fcf.com.br/competicoes/competicoes-nao-profissionais-" + str(self.year)
        try:
            fcf_soup = self.scrape(scrap_url)
            competicoes_div = fcf_soup.find("div", id="cb-content") # type: ignore
            competicoes = competicoes_div.find("article").find("ul").find_all("li") # type: ignore
            for torneio in competicoes:
                if torneio.find("ul"):
                    continue
                torneio_data = torneio.find("a")
                self.lista_competicoes(torneio_data.text, torneio_data.get("href"))
        except Exception as e:
            print(f"Error scrap_FCF!", e)
            return
        finally:
            return None

    def scrap_FCF_competicao(self, scrap_url, tournament_name):
        try:
            competicao_soup = self.scrape(scrap_url)
            tabela_url = competicao_soup.find("a", string=lambda text: text and text == "Tabela") # type: ignore
            if not tabela_url:
                print("Não encontrou Tabela")
                return
            tabela_soup = self.scrape(tabela_url.get("href"))
            tables_tabela = tabela_soup.find_all("table", { "class": "ReportTable" })
            for idx, table in enumerate(tables_tabela):
                if "Jogo: " in table.text:
                    self.scrapped_match = Match()
                    self.scrapped_match.tournament = tournament_name
                    match = self.handle_FCF_match(tables_tabela[idx:idx + 6])
                    for k, v in match.items():
                        self.scrapped_match[k] = v

                    print(f"[{self.scrapped_match.tournament}] Partida #{self.scrapped_match.fcf_id} em {self.scrapped_match.date}, {self.scrapped_match.homeTeam} {self.scrapped_match.homeScore} vs {self.scrapped_match.awayScore} {self.scrapped_match.awayTeam}")
                    this_match = { "tournament": self.scrapped_match.tournament, "homeTeam": self.scrapped_match.homeTeam, "awayTeam": self.scrapped_match.awayTeam, "fcf_id": self.scrapped_match.fcf_id }
                    this_update = { "$set": self.scrapped_match.to_dict() }
                    result = self.collection.update_one(this_match, this_update, upsert=True)
                    if result.upserted_id is not None:
                        print(f"Novo jogo! Salvo com id: {result.upserted_id}")
                    elif result.modified_count > 0:
                        print(f"Documento(s) atualizado(s): {result.modified_count}")
                    else:
                        print("Document found, but no changes were needed.")
        except Exception as e:
            print(f"Error scrap_FCF_competicao:", e)
        finally:
            return None

    def handle_FCF_match(self, match_soup):
        vi = 0
        match_object = {}
        # parte 1
        match_header = match_soup[vi].find_all("tr")
        for tr in match_header:
            match_data_raw, location = tr.text.split('  /')
            match_data_arr = match_data_raw.split('-')
            jFcfId = re.sub(r'[^\d]', '', match_data_arr[0]) or 0
            jDataA = match_data_arr[1].strip() or "Desconhecido"
            jDataB = match_data_arr[2].split("/")[1].strip()
            jEstadio = "".join(match_data_arr[3:]).split("Estádio:")[1].strip() or "Desconhecido"
            match_object["fcf_id"] = jFcfId
            match_object["date"] = jDataA
            match_object["schedule"] = jDataB
            match_object["stadium"] = jEstadio
            match_object["location"] = location.strip()

        # parte 2
        vi += 1
        td_logos = match_soup[vi].find_all("img")
        while len(td_logos) == 0:
            vi += 1
            td_logos = match_soup[vi].find_all("img")
            if vi > 5:
                raise RuntimeError("no logo found here")
        home_logo_raw, away_logo_raw = td_logos
        match_object["homeLogo"] = home_logo_raw.get("src").split("?nocache")[0]
        match_object["awayLogo"] = away_logo_raw.get("src").split("?nocache")[0]

        # parte 3
        match_scores = match_soup[vi].find_all("td")
        match_object["homeScore"] = int(match_scores[1].text) if isinstance(match_scores[1].text.strip(),int) else 0
        match_object["awayScore"] = int(match_scores[3].text) if isinstance(match_scores[3].text.strip(),int) else 0

        # parte 4
        vi += 1
        match_names = match_soup[vi].find_all("td")
        match_object["homeTeam"] = match_names[1].text
        match_object["awayTeam"] = match_names[3].text

        return match_object

def main():
    scrap_year = input("Ano (ou enter para o atual): ")
    scrap_year = datetime.today().year if scrap_year == "" else int(scrap_year)
    scrap_one = input("Torneio específico? Insira URL caso sim: ")
    if scrap_one:
        scrap_tournament_name = ""
        while scrap_tournament_name == "":
            scrap_tournament_name = input("Nome do torneio: ")
        scraper = WebScraper(scrap_year)
        scraper.scrap_FCF_competicao(scrap_one, scrap_tournament_name)
    else:
        scrap_all = input("Scrap automático de todos os torneios (Y/n)? ")
        scrap_all = scrap_all == "y" or scrap_all == ""
        scraper = WebScraper(scrap_year)
        scraper.scrap_FCF_profissional()
        scraper.scrap_FCF_naoprofi()
        for tournament in scraper.lista: # type: ignore
            if not scrap_all:
                scrap_this = input(f"Scrap {tournament["nome"]} - {tournament["url"]} (Y/n)? ")
                if scrap_this != "y" and scrap_this != "":
                    continue
            print("Iniciando SCRAP para", tournament["nome"], tournament["url"])
            scraper.scrap_FCF_competicao(tournament['url'], tournament['nome'])

if __name__ == "__main__":
    main()