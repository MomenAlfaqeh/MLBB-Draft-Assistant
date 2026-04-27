import sqlite3
import json
import os
from typing import List, Dict, Any, Optional
from pathlib import Path

class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to the SQLite database"""
        # Ensure directory exists
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
        
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        return self.conn
    
    def disconnect(self):
        """Close the database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def initialize_db(self):
        """Initialize the database by running schema.sql"""
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        conn = self.connect()
        conn.executescript(schema_sql)
        conn.commit()
        self.disconnect()
    
    def get_all_heroes(self) -> List[Dict[str, Any]]:
        """Get all heroes from the database"""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM heroes ORDER BY name")
        heroes = [dict(row) for row in cursor.fetchall()]
        self.disconnect()
        return heroes
    
    def get_hero_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a hero by name"""
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM heroes WHERE name = ?", (name,))
        row = cursor.fetchone()
        self.disconnect()
        return dict(row) if row else None
    
    def upsert_hero(self, hero_data: Dict[str, Any]):
        """Insert or update a hero"""
        conn = self.connect()
        conn.execute("""
            INSERT INTO heroes (name, role, specialty, base_win_rate, pick_rate, ban_rate, tier, last_updated)
            VALUES (:name, :role, :specialty, :base_win_rate, :pick_rate, :ban_rate, :tier, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                role = excluded.role,
                specialty = excluded.specialty,
                base_win_rate = excluded.base_win_rate,
                pick_rate = excluded.pick_rate,
                ban_rate = excluded.ban_rate,
                tier = excluded.tier,
                last_updated = CURRENT_TIMESTAMP
        """, hero_data)
        conn.commit()
        self.disconnect()
    
    def get_counters(self, hero_id: int) -> List[Dict[str, Any]]:
        """Get all counters for a hero"""
        conn = self.connect()
        cursor = conn.execute("""
            SELECT hc.*, h.name as countered_by_name 
            FROM hero_counters hc 
            JOIN heroes h ON hc.countered_by_id = h.id 
            WHERE hc.hero_id = ?
        """, (hero_id,))
        counters = [dict(row) for row in cursor.fetchall()]
        self.disconnect()
        return counters
    
    def get_synergies(self, hero_id: int) -> List[Dict[str, Any]]:
        """Get all synergies for a hero"""
        conn = self.connect()
        cursor = conn.execute("""
            SELECT hs.*, 
                   CASE 
                       WHEN hs.hero_a_id = ? THEN hb.name 
                       ELSE ha.name 
                   END as synergy_with_name
            FROM hero_synergies hs
            JOIN heroes ha ON hs.hero_a_id = ha.id
            JOIN heroes hb ON hs.hero_b_id = hb.id
            WHERE hs.hero_a_id = ? OR hs.hero_b_id = ?
        """, (hero_id, hero_id, hero_id))
        synergies = [dict(row) for row in cursor.fetchall()]
        self.disconnect()
        return synergies
    
    def save_counter(self, hero_id: int, countered_by_id: int, score: float, 
                     sample_size: int = None, patch: str = None):
        """Save or update a counter relationship"""
        conn = self.connect()
        conn.execute("""
            INSERT INTO hero_counters (hero_id, countered_by_id, counter_score, sample_size, patch_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(hero_id, countered_by_id) DO UPDATE SET
                counter_score = excluded.counter_score,
                sample_size = excluded.sample_size,
                patch_date = excluded.patch_date
        """, (hero_id, countered_by_id, score, sample_size, patch))
        conn.commit()
        self.disconnect()
    
    def save_synergy(self, hero_a: int, hero_b: int, score: float, 
                     combined_wr: float = None, sample_size: int = None, patch: str = None):
        """Save or update a synergy relationship"""
        conn = self.connect()
        # Ensure consistent ordering (smaller ID first)
        if hero_a > hero_b:
            hero_a, hero_b = hero_b, hero_a
        
        conn.execute("""
            INSERT INTO hero_synergies (hero_a_id, hero_b_id, synergy_score, combined_wr, sample_size, patch_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hero_a_id, hero_b_id) DO UPDATE SET
                synergy_score = excluded.synergy_score,
                combined_wr = excluded.combined_wr,
                sample_size = excluded.sample_size,
                patch_date = excluded.patch_date
        """, (hero_a, hero_b, score, combined_wr, sample_size, patch))
        conn.commit()
        self.disconnect()