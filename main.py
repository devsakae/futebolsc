# coding=utf-8
import os
import re
import sys
import certifi
import requests
import functions_framework

from datetime import datetime
from bs4 import BeautifulSoup
from pymongo.mongo_client import MongoClient

import google.cloud.logging as gcloud_logging
import logging

_gcloud_client = gcloud_logging.Client()
_gcloud_client.setup_logging()
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

MONGO_URI = os.environ.get("MONGO_URI", "")

def is_number(s: str) -> bool:
    try:
        float(s)
        return True
    except ValueError:
        return False

class Match:
    def __init__(self) -> None:
        self.match_id   = 0
        self.tournament = ""
        self.date       = ""
        self.homeTeam   = ""
        self.homeLogo   = ""
        self.homeScore  = 0
        self.awayTeam   = ""
        self.awayScore  = 0
        self.awayLogo   = ""
        self.stadium    = ""
        self.location   = ""
        self.schedule   = ""

    def __setitem__(self, key, value):
        setattr(self, key, value)

    def __str__(self):
        return (
            f"Match(tournament={self.tournament}, date={self.date}, "
            f"schedule={self.schedule}, homeTeam={self.homeTeam}, "
            f"awayTeam={self.awayTeam})"
        )

    def to_dict(self):
        return self.__dict__


class WebScraper:
    HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        )
    }

    def __init__(self, year: int):
        self.year  = year
        self.lista = []
        self._connect_db()

    def _connect_db(self):
        try:
            self.client = MongoClient(MONGO_URI, tlsCAFile=certifi.where())
            self.client.pyjogos.command("ping")
            logger.info("Conectado ao banco de dados!")
            self.db_father  = self.client["pyjogos"]
            self.collection = self.client["pyjogos"][f"fcf_sc_{self.year}"]
        except Exception as exc:
            logger.error("Erro ao conectar banco de dados! %s", exc)
            self.client     = None
            self.db_father  = None
            self.collection = None

    def scrape(self, url: str) -> BeautifulSoup | None:
        try:
            resp = requests.get(url, headers=self.HEADERS, timeout=15)
            resp.raise_for_status()
            return BeautifulSoup(resp.text, "html.parser")
        except requests.RequestException as exc:
            logger.error("Erro ao fazer scrape de %s: %s", url, exc)
            return None

    def _add_competicao(self, nome: str, url: str):
        self.lista.append({"nome": nome, "url": url})

    def _scrap_lista(self, path_suffix: str, label: str):
        url = f"https://fcf.com.br/competicoes/{path_suffix}-{self.year}"
        try:
            soup = self.scrape(url)
            div  = soup.find("div", id="cb-content")          # type: ignore[union-attr]
            items = div.find("article").find("ul").find_all("li")  # type: ignore[union-attr]
            for torneio in items:
                if torneio.find("ul"):
                    continue
                a = torneio.find("a")
                self._add_competicao(a.text, a.get("href"))
        except Exception as exc:
            logger.error("Erro ao listar competições (%s): %s", label, exc)

    def scrap_FCF_profissional(self):
        self._scrap_lista("competicoes-profissionais", "profissionais")

    def scrap_FCF_naoprofi(self):
        self._scrap_lista("competicoes-nao-profissionais", "nao-profissionais")

    def scrap_FCF_competicao(self, scrap_url: str, tournament_name: str):
        if self.collection is None:
            logger.error("no database connection - aborting scrap %s", tournament_name)
            return
        try:
            soup = self.scrape(scrap_url)
            tabela_tag = soup.find(  # type: ignore[union-attr]
                "a", string=lambda t: t and t == "Tabela"
            )
            if not tabela_tag:
                logger.warning("[%s] Aba 'Tabela' não encontrada em %s", tournament_name, scrap_url)
                return

            tabela_soup = self.scrape(tabela_tag.get("href"))
            tables = tabela_soup.find_all("table", {"class": "ReportTable"})  # type: ignore[union-attr]

            saved = updated = skipped = 0
            for idx, table in enumerate(tables):
                if "Jogo: " not in table.text:
                    continue
                self.scrapped_match = Match()
                self.scrapped_match.tournament = tournament_name
                match_data = self.handle_FCF_match(tables[idx : idx + 6])
                for k, v in match_data.items():
                    self.scrapped_match[k] = v

                logger.info(
                    "[%s] Partida #%s em %s: %s %s x %s %s",
                    self.scrapped_match.tournament,
                    self.scrapped_match.match_id,
                    self.scrapped_match.date,
                    self.scrapped_match.homeTeam,
                    self.scrapped_match.homeScore,
                    self.scrapped_match.awayScore,
                    self.scrapped_match.awayTeam,
                )

                query  = {
                    "tournament": self.scrapped_match.tournament,
                    "homeTeam":   self.scrapped_match.homeTeam,
                    "awayTeam":   self.scrapped_match.awayTeam,
                    "match_id":   int(self.scrapped_match.match_id),
                }
                update = {"$set": self.scrapped_match.to_dict()}
                result = self.collection.update_one(query, update, upsert=True)

                if result.upserted_id is not None:
                    logger.info("Novo jogo salvo com id: %s", result.upserted_id)
                    saved += 1
                elif result.modified_count > 0:
                    logger.info("Jogo atualizado (modified_count=%s)", result.modified_count)
                    updated += 1
                else:
                    skipped += 1

            logger.info(
                "[%s] Finished! new: %d, updated: %d, no changes: %d",
                tournament_name, saved, updated, skipped,
            )
        except Exception as exc:
            logger.error("Erro em scrap_FCF_competicao(%s): %s", tournament_name, exc, exc_info=True)

    def handle_FCF_match(self, match_soup) -> dict:
        vi = 0
        obj: dict = {}

        # parte 1 ? cabeçalho com id, data, estádio, local
        for tr in match_soup[vi].find_all("tr"):
            raw, location = tr.text.split("  /")
            parts = raw.split("-")
            obj["match_id"]  = int(re.sub(r"[^\d]", "", parts[0]) or 0)
            obj["date"]      = parts[1].strip()
            obj["schedule"]  = parts[2].split("/")[1].strip()
            obj["stadium"]   = "".join(parts[3:]).split("Estádio:")[1].strip()
            obj["location"]  = location.strip()

        # parte 2 ? logos
        vi += 1
        logos = match_soup[vi].find_all("img")
        while not logos:
            vi += 1
            logos = match_soup[vi].find_all("img")
            if vi > 5:
                raise RuntimeError("no logos! verify match")
        home_logo, away_logo = logos
        obj["homeLogo"] = home_logo.get("src").split("?nocache")[0]
        obj["awayLogo"] = away_logo.get("src").split("?nocache")[0]

        # parte 3 ? placar
        tds = match_soup[vi].find_all("td")
        obj["homeScore"] = int(tds[1].text) if is_number(tds[1].text.strip()) else 0
        obj["awayScore"] = int(tds[3].text) if is_number(tds[3].text.strip()) else 0

        # parte 4 ? nomes
        vi += 1
        names = match_soup[vi].find_all("td")
        obj["homeTeam"] = names[1].text
        obj["awayTeam"] = names[3].text

        return obj

@functions_framework.cloud_event
def run_scraper(cloud_event):
    year = datetime.today().year
    logger.info("=== starting Scraper FCF-SC for year %d ===", year)

    scraper = WebScraper(year)
    scraper.scrap_FCF_profissional()
    scraper.scrap_FCF_naoprofi()

    logger.info("tournaments found: %d", len(scraper.lista))

    for tournament in scraper.lista:
        nome = tournament["nome"]
        url  = tournament["url"]
        logger.info("Scraping: %s ? %s", nome, url)
        scraper.scrap_FCF_competicao(url, nome)

    logger.info("=== finished Scraper FCF-SC ===")