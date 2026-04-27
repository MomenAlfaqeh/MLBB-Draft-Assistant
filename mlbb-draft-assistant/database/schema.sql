-- Schema for MLBB AI Draft Assistant

-- Heroes table
CREATE TABLE IF NOT EXISTS heroes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    role TEXT NOT NULL,
    specialty TEXT,
    base_win_rate REAL,
    pick_rate REAL,
    ban_rate REAL,
    tier TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Hero counters table
CREATE TABLE IF NOT EXISTS hero_counters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_id INTEGER NOT NULL,
    countered_by_id INTEGER NOT NULL,
    counter_score REAL NOT NULL,
    sample_size INTEGER,
    patch_date TEXT,
    FOREIGN KEY (hero_id) REFERENCES heroes (id),
    FOREIGN KEY (countered_by_id) REFERENCES heroes (id),
    UNIQUE(hero_id, countered_by_id)
);

-- Hero synergies table
CREATE TABLE IF NOT EXISTS hero_synergies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_a_id INTEGER NOT NULL,
    hero_b_id INTEGER NOT NULL,
    synergy_score REAL NOT NULL,
    combined_wr REAL,
    sample_size INTEGER,
    patch_date TEXT,
    FOREIGN KEY (hero_a_id) REFERENCES heroes (id),
    FOREIGN KEY (hero_b_id) REFERENCES heroes (id),
    UNIQUE(hero_a_id, hero_b_id)
);

-- Hero templates table (for vision engine)
CREATE TABLE IF NOT EXISTS hero_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    hero_id INTEGER NOT NULL,
    image_hash TEXT,
    template_path TEXT,
    resolution TEXT,
    version TEXT,
    FOREIGN KEY (hero_id) REFERENCES heroes (id)
);

-- Meta snapshots table
CREATE TABLE IF NOT EXISTS meta_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patch_version TEXT NOT NULL,
    rank_tier TEXT,
    snapshot_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    hero_stats_json TEXT
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_hero_counters_hero_id ON hero_counters(hero_id);
CREATE INDEX IF NOT EXISTS idx_hero_synergies_hero_a_id ON hero_synergies(hero_a_id);
CREATE INDEX IF NOT EXISTS idx_hero_synergies_hero_b_id ON hero_synergies(hero_b_id);
CREATE INDEX IF NOT EXISTS idx_heroes_name ON heroes(name);