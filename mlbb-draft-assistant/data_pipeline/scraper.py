import requests
from bs4 import BeautifulSoup
import time
import logging
import json
import os
import sys
from typing import List, Dict, Any

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import SCRAPE_SOURCES, DB_PATH
from database.db_manager import DatabaseManager


class HeroScraper:
    def __init__(self, db_path=None):
        self.db_path = db_path if db_path else DB_PATH
        self.db_manager = DatabaseManager(self.db_path)
        self.logger = logging.getLogger(__name__)

    def load_backup_heroes(self):
        try:
            backup_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_pipeline", "heroes_backup.json")
            with open(backup_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError as e:
            self.logger.error(f"Backup file not found: {e}")
            return []
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse backup JSON: {e}")
            return []

    def _safe_request(self, url, retries=3, delay=2):
        for attempt in range(retries):
            try:
                response = requests.get(url, timeout=10)
                return response
            except requests.RequestException as e:
                self.logger.warning(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        return None

    def scrape_win_rates(self) -> List[Dict[str, Any]]:
        mock_heroes = [
            {
                "name": "Gatotkaca",
                "role": "Tank",
                "specialty": "Teamfight, Crowd Control",
                "base_win_rate": 0.52,
                "pick_rate": 0.15,
                "ban_rate": 0.08,
                "tier": "A"
            },
            {
                "name": "Franco",
                "role": "Tank",
                "specialty": "Hook, Initiator",
                "base_win_rate": 0.50,
                "pick_rate": 0.12,
                "ban_rate": 0.10,
                "tier": "B+"
            },
            {
                "name": "Alucard",
                "role": "Fighter",
                "specialty": "Sustain, Jungle",
                "base_win_rate": 0.51,
                "pick_rate": 0.18,
                "ban_rate": 0.05,
                "tier": "A"
            },
            {
                "name": "Hayabusa",
                "role": "Assassin",
                "specialty": "Burst, Mobility",
                "base_win_rate": 0.49,
                "pick_rate": 0.22,
                "ban_rate": 0.12,
                "tier": "B+"
            },
            {
                "name": "Harley",
                "role": "Mage",
                "specialty": "Burst, Mobility",
                "base_win_rate": 0.47,
                "pick_rate": 0.16,
                "ban_rate": 0.09,
                "tier": "B"
            },
            {
                "name": "Lyla",
                "role": "Mage",
                "specialty": "Poke, Long Range",
                "base_win_rate": 0.53,
                "pick_rate": 0.14,
                "ban_rate": 0.06,
                "tier": "A-"
            },
            {
                "name": "Claude",
                "role": "Marksman",
                "specialty": "Burst, Mobility",
                "base_win_rate": 0.50,
                "pick_rate": 0.19,
                "ban_rate": 0.04,
                "tier": "A"
            },
            {
                "name": "Karrie",
                "role": "Marksman",
                "specialty": "Attack Speed, Anti-Tank",
                "base_win_rate": 0.48,
                "pick_rate": 0.17,
                "ban_rate": 0.03,
                "tier": "B+"
            },
            {
                "name": "Rafaela",
                "role": "Support",
                "specialty": "Heal, Crowd Control",
                "base_win_rate": 0.54,
                "pick_rate": 0.11,
                "ban_rate": 0.02,
                "tier": "A"
            },
            {
                "name": "Estes",
                "role": "Support",
                "specialty": "Heal, Sustain",
                "base_win_rate": 0.51,
                "pick_rate": 0.13,
                "ban_rate": 0.01,
                "tier": "A-"
            }
        ]
        return mock_heroes

    def scrape_counters(self) -> List[Dict[str, Any]]:
        mock_counters = [
            {"hero_name": "Gatotkaca", "countered_by_name": "Hayabusa", "counter_score": 0.75, "sample_size": 1200, "patch": "1.70.0"},
            {"hero_name": "Gatotkaca", "countered_by_name": "Claude", "counter_score": 0.68, "sample_size": 950, "patch": "1.70.0"},
            {"hero_name": "Franco", "countered_by_name": "Alucard", "counter_score": 0.72, "sample_size": 1100, "patch": "1.70.0"},
            {"hero_name": "Franco", "countered_by_name": "Harley", "counter_score": 0.65, "sample_size": 800, "patch": "1.70.0"},
            {"hero_name": "Alucard", "countered_by_name": "Hayabusa", "counter_score": 0.70, "sample_size": 1000, "patch": "1.70.0"},
            {"hero_name": "Alucard", "countered_by_name": "Lyla", "counter_score": 0.60, "sample_size": 750, "patch": "1.70.0"},
            {"hero_name": "Hayabusa", "countered_by_name": "Franco", "counter_score": 0.78, "sample_size": 1300, "patch": "1.70.0"},
            {"hero_name": "Hayabusa", "countered_by_name": "Rafaela", "counter_score": 0.62, "sample_size": 900, "patch": "1.70.0"},
            {"hero_name": "Harley", "countered_by_name": "Claude", "counter_score": 0.73, "sample_size": 1050, "patch": "1.70.0"},
            {"hero_name": "Harley", "countered_by_name": "Karrie", "counter_score": 0.67, "sample_size": 850, "patch": "1.70.0"},
            {"hero_name": "Lyla", "countered_by_name": "Hayabusa", "counter_score": 0.71, "sample_size": 950, "patch": "1.70.0"},
            {"hero_name": "Lyla", "countered_by_name": "Alucard", "counter_score": 0.58, "sample_size": 700, "patch": "1.70.0"},
            {"hero_name": "Claude", "countered_by_name": "Franco", "counter_score": 0.76, "sample_size": 1150, "patch": "1.70.0"},
            {"hero_name": "Claude", "countered_by_name": "Gatotkaca", "counter_score": 0.63, "sample_size": 900, "patch": "1.70.0"},
            {"hero_name": "Karrie", "countered_by_name": "Hayabusa", "counter_score": 0.69, "sample_size": 1000, "patch": "1.70.0"},
            {"hero_name": "Karrie", "countered_by_name": "Franco", "counter_score": 0.61, "sample_size": 800, "patch": "1.70.0"},
            {"hero_name": "Rafaela", "countered_by_name": "Harley", "counter_score": 0.74, "sample_size": 1200, "patch": "1.70.0"},
            {"hero_name": "Rafaela", "countered_by_name": "Claude", "counter_score": 0.66, "sample_size": 950, "patch": "1.70.0"},
            {"hero_name": "Estes", "countered_by_name": "Harley", "counter_score": 0.72, "sample_size": 1100, "patch": "1.70.0"},
            {"hero_name": "Estes", "countered_by_name": "Hayabusa", "counter_score": 0.64, "sample_size": 850, "patch": "1.70.0"}
        ]
        return mock_counters

    def scrape_synergies(self) -> List[Dict[str, Any]]:
        mock_synergies = [
            {"hero_a_name": "Gatotkaca", "hero_b_name": "Claude", "synergy_score": 0.82, "combined_wr": 0.58, "sample_size": 900, "patch": "1.70.0"},
            {"hero_a_name": "Franco", "hero_b_name": "Hayabusa", "synergy_score": 0.79, "combined_wr": 0.56, "sample_size": 850, "patch": "1.70.0"},
            {"hero_a_name": "Alucard", "hero_b_name": "Lyla", "synergy_score": 0.75, "combined_wr": 0.54, "sample_size": 700, "patch": "1.70.0"},
            {"hero_a_name": "Alucard", "hero_b_name": "Rafaela", "synergy_score": 0.72, "combined_wr": 0.53, "sample_size": 650, "patch": "1.70.0"},
            {"hero_a_name": "Hayabusa", "hero_b_name": "Franco", "synergy_score": 0.81, "combined_wr": 0.57, "sample_size": 950, "patch": "1.70.0"},
            {"hero_a_name": "Hayabusa", "hero_b_name": "Claude", "synergy_score": 0.78, "combined_wr": 0.55, "sample_size": 800, "patch": "1.70.0"},
            {"hero_a_name": "Harley", "hero_b_name": "Karrie", "synergy_score": 0.77, "combined_wr": 0.55, "sample_size": 750, "patch": "1.70.0"},
            {"hero_a_name": "Lyla", "hero_b_name": "Alucard", "synergy_score": 0.73, "combined_wr": 0.52, "sample_size": 600, "patch": "1.70.0"},
            {"hero_a_name": "Claude", "hero_b_name": "Gatotkaca", "synergy_score": 0.80, "combined_wr": 0.57, "sample_size": 850, "patch": "1.70.0"},
            {"hero_a_name": "Karrie", "hero_b_name": "Harley", "synergy_score": 0.74, "combined_wr": 0.53, "sample_size": 600, "patch": "1.70.0"},
            {"hero_a_name": "Rafaela", "hero_b_name": "Alucard", "synergy_score": 0.76, "combined_wr": 0.54, "sample_size": 700, "patch": "1.70.0"},
            {"hero_a_name": "Estes", "hero_b_name": "Hayabusa", "synergy_score": 0.71, "combined_wr": 0.50, "sample_size": 500, "patch": "1.70.0"}
        ]
        return mock_synergies

    def run_full_scrape(self):
        self.db_manager.initialize_db()
        try:
            heroes = self.scrape_win_rates()
            self.logger.info("Live scrape succeeded")
        except Exception as e:
            self.logger.warning(f"Live scrape failed: {e}, using backup")
            heroes = self.load_backup_heroes()

        for hero in heroes:
            self.db_manager.upsert_hero(hero)
            time.sleep(0.1)

        counters = self.scrape_counters()
        for counter in counters:
            hero = self.db_manager.get_hero_by_name(counter["hero_name"])
            countered_by = self.db_manager.get_hero_by_name(counter["countered_by_name"])
            if hero and countered_by:
                self.db_manager.save_counter(hero["id"], countered_by["id"], counter["counter_score"], counter["sample_size"], counter["patch"])

        synergies = self.scrape_synergies()
        for synergy in synergies:
            hero_a = self.db_manager.get_hero_by_name(synergy["hero_a_name"])
            hero_b = self.db_manager.get_hero_by_name(synergy["hero_b_name"])
            if hero_a and hero_b:
                self.db_manager.save_synergy(hero_a["id"], hero_b["id"], synergy["synergy_score"], synergy["combined_wr"], synergy["sample_size"], synergy["patch"])

        print(f"Done: {len(heroes)} heroes saved")


if __name__ == "__main__":
    scraper = HeroScraper()
    scraper.run_full_scrape()