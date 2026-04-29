# Project constants for MLBB AI Draft Assistant

# Database configuration
DB_PATH = "database/mlbb.db"

# Server configuration
SERVER_HOST = "localhost"
SERVER_PORT = 8080

# Vision engine settings
CAPTURE_INTERVAL_MS = 2000
HERO_ICONS_PATH = "vision_engine/hero_icons/"
TEMPLATE_MATCH_THRESHOLD = 0.80

# Scraping sources
SCRAPE_SOURCES = [
    "https://mlbb.gg",
    "https://liquipedia.net/mobilelegends"
]

# Hero roles
ROLE_LIST = ["Tank", "Fighter", "Assassin", "Mage", "Marksman", "Support"]

# Scoring algorithm weights
SCORING_WEIGHTS = {
    "meta_wr": 0.30,
    "counter_score": 0.35,
    "synergy_score": 0.25,
    "comp_bonus": 0.10
}

# BigQuery configuration
BIGQUERY_PROJECT_ID = "mlbb-draft-assistant-494814"
BIGQUERY_DATASET = "mlbb_draft"
USE_BIGQUERY = True