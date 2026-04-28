#!/usr/bin/env python3
"""
Populate MLBB database with all ~120 heroes with realistic data.
Run: cd mlbb-draft-assistant && python3 data_pipeline/populate_heroes.py
"""

import sys
import os
from typing import List, Dict, Tuple

# Add project root to path - go up to mlbb-draft-assistant directory
project_root = os.path.join(os.path.dirname(__file__), '..')
sys.path.append(os.path.abspath(project_root))

# Also add current working directory variations
current_dir = os.getcwd()
possible_paths = [
    current_dir,
    os.path.join(current_dir, 'mlbb-draft-assistant'),
    os.path.join(current_dir, '..'),
]
for p in possible_paths:
    if os.path.exists(os.path.join(p, 'database')):
        sys.path.append(p)
        break

from database.db_manager import DatabaseManager
from config import DB_PATH

# Comprehensive hero data: (name, role, specialty, win_rate, pick_rate, ban_rate, tier)
HEROES_DATA = [
    # TANKS (19 heroes)
    ("Tigreal", "Tank", "Crowd Control", 0.512, 0.15, 0.08, "S"),
    ("Akai", "Tank", "Crowd Control", 0.498, 0.08, 0.03, "A"),
    ("Franco", "Tank", "Crowd Control", 0.489, 0.12, 0.05, "A"),
    ("Minotaur", "Tank", "Crowd Control", 0.502, 0.07, 0.02, "A"),
    ("Lolita", "Tank", "Crowd Control", 0.495, 0.05, 0.02, "A"),
    ("Atlas", "Tank", "Crowd Control", 0.521, 0.18, 0.12, "S"),
    ("Johnson", "Tank", "Crowd Control", 0.488, 0.06, 0.03, "B"),
    ("Hylos", "Tank", "Crowd Control", 0.501, 0.07, 0.02, "A"),
    ("Uranus", "Tank", "Sustain", 0.509, 0.09, 0.04, "S"),
    ("Gatotkaca", "Tank", "Crowd Control", 0.496, 0.05, 0.02, "A"),
    ("Esmeralda", "Tank", "Magic Damage", 0.514, 0.14, 0.09, "S"),
    ("Terizla", "Tank", "Crowd Control", 0.507, 0.08, 0.03, "A"),
    ("Belerick", "Tank", "Crowd Control", 0.485, 0.03, 0.01, "B"),
    ("Grock", "Tank", "Crowd Control", 0.491, 0.04, 0.02, "B"),
    ("Edith", "Tank", "Crowd Control", 0.516, 0.16, 0.10, "S"),
    ("Barats", "Tank", "Crowd Control", 0.499, 0.06, 0.02, "A"),
    ("Fredrinn", "Tank", "Sustain", 0.518, 0.13, 0.08, "S"),
    ("Chip", "Tank", "Crowd Control", 0.502, 0.10, 0.04, "A"),
    ("Hockney", "Tank", "Crowd Control", 0.497, 0.04, 0.01, "B"),

    # FIGHTERS (23 heroes)
    ("Chou", "Fighter", "Crowd Control", 0.508, 0.15, 0.11, "S"),
    ("Roger", "Fighter", "Burst", 0.501, 0.07, 0.03, "A"),
    ("Alucard", "Fighter", "Lifesteal", 0.492, 0.10, 0.04, "A"),
    ("Zilong", "Fighter", "Physical Damage", 0.496, 0.08, 0.03, "A"),
    ("Balmond", "Fighter", "Burst", 0.488, 0.06, 0.02, "B"),
    ("Bane", "Fighter", "Wave Clear", 0.494, 0.04, 0.01, "B"),
    ("Freya", "Fighter", "Burst", 0.503, 0.06, 0.03, "A"),
    ("Ruby", "Fighter", "Crowd Control", 0.507, 0.09, 0.04, "A"),
    ("Argus", "Fighter", "Lifesteal", 0.498, 0.07, 0.03, "A"),
    ("Martis", "Fighter", "Burst", 0.509, 0.11, 0.05, "S"),
    ("Sun", "Fighter", "Wave Clear", 0.495, 0.05, 0.02, "B"),
    ("Minsitthar", "Fighter", "Crowd Control", 0.501, 0.06, 0.02, "A"),
    ("Dyrroth", "Fighter", "Burst", 0.506, 0.12, 0.06, "S"),
    ("X.Borg", "Fighter", "Burst", 0.502, 0.08, 0.03, "A"),
    ("Guinevere", "Fighter", "Burst", 0.510, 0.10, 0.07, "S"),
    ("Yin", "Fighter", "Burst", 0.511, 0.14, 0.09, "S"),
    ("Yu Zhong", "Fighter", "Lifesteal", 0.507, 0.09, 0.05, "S"),
    ("Benedetta", "Fighter", "Physical Damage", 0.513, 0.16, 0.12, "S"),
    ("Paquito", "Fighter", "Burst", 0.504, 0.08, 0.04, "A"),
    ("Aulus", "Fighter", "Burst", 0.505, 0.07, 0.03, "A"),
    ("Cici", "Fighter", "Physical Damage", 0.499, 0.11, 0.05, "A"),
    ("Arlott", "Fighter", "Burst", 0.512, 0.13, 0.08, "S"),
    ("Lukas", "Fighter", "Burst", 0.510, 0.12, 0.07, "S"),
    ("Suyou", "Fighter", "Burst", 0.509, 0.10, 0.06, "S"),

    # ASSASSINS (16 heroes)
    ("Lancelot", "Assassin", "Burst", 0.515, 0.18, 0.15, "S"),
    ("Hayabusa", "Assassin", "Burst", 0.511, 0.14, 0.10, "S"),
    ("Gusion", "Assassin", "Burst", 0.518, 0.20, 0.18, "S"),
    ("Fanny", "Assassin", "Burst", 0.522, 0.12, 0.25, "S"),
    ("Natalia", "Assassin", "Burst", 0.505, 0.09, 0.06, "A"),
    ("Selena", "Assassin", "Burst", 0.508, 0.08, 0.07, "A"),
    ("Helcurt", "Assassin", "Burst", 0.495, 0.04, 0.02, "B"),
    ("Saber", "Assassin", "Burst", 0.498, 0.07, 0.03, "A"),
    ("Karina", "Assassin", "Burst", 0.501, 0.06, 0.03, "A"),
    ("Ling", "Assassin", "Burst", 0.516, 0.11, 0.12, "S"),
    ("Natan", "Assassin", "Physical Damage", 0.503, 0.09, 0.05, "A"),
    ("Julian", "Assassin", "Burst", 0.514, 0.15, 0.11, "S"),
    ("Joy", "Assassin", "Burst", 0.517, 0.17, 0.14, "S"),
    ("Aamon", "Assassin", "Burst", 0.506, 0.08, 0.05, "A"),
    ("Harley", "Assassin", "Burst", 0.502, 0.07, 0.04, "A"),
    ("Mathilda", "Assassin", "Mobility", 0.501, 0.06, 0.03, "A"),

    # MAGES (22 heroes)
    ("Kagura", "Mage", "Burst", 0.516, 0.15, 0.12, "S"),
    ("Vale", "Mage", "Crowd Control", 0.509, 0.10, 0.06, "S"),
    ("Eudora", "Mage", "Burst", 0.495, 0.08, 0.03, "B"),
    ("Cyclops", "Mage", "Burst", 0.501, 0.09, 0.04, "A"),
    ("Nana", "Mage", "Crowd Control", 0.498, 0.07, 0.03, "A"),
    ("Lylia", "Mage", "Burst", 0.507, 0.11, 0.07, "S"),
    ("Lunox", "Mage", "Burst", 0.512, 0.12, 0.09, "S"),
    ("Kadita", "Mage", "Burst", 0.514, 0.14, 0.11, "S"),
    ("Chang'e", "Mage", "Wave Clear", 0.503, 0.08, 0.04, "A"),
    ("Odette", "Mage", "Burst", 0.500, 0.06, 0.03, "A"),
    ("Faramis", "Mage", "Crowd Control", 0.502, 0.07, 0.03, "A"),
    ("Xavier", "Mage", "Burst", 0.515, 0.13, 0.10, "S"),
    ("Novaria", "Mage", "Burst", 0.508, 0.09, 0.05, "A"),
    ("Zhuxin", "Mage", "Crowd Control", 0.510, 0.11, 0.08, "S"),
    ("Yve", "Mage", "Crowd Control", 0.504, 0.08, 0.04, "A"),
    ("Valentina", "Mage", "Burst", 0.511, 0.10, 0.07, "S"),
    ("Pharsa", "Mage", "Burst", 0.498, 0.05, 0.02, "B"),
    ("Aurora", "Mage", "Crowd Control", 0.501, 0.06, 0.03, "A"),
    ("Gord", "Mage", "Burst", 0.494, 0.04, 0.02, "B"),
    ("Alice", "Mage", "Lifesteal", 0.506, 0.07, 0.04, "A"),
    ("Harith", "Mage", "Burst", 0.509, 0.12, 0.08, "S"),
    ("Kimmy", "Mage", "Magic Damage", 0.497, 0.05, 0.02, "B"),

    # MARKSMEN (20 heroes)
    ("Layla", "Marksman", "Physical Damage", 0.488, 0.12, 0.03, "B"),
    ("Miya", "Marksman", "Physical Damage", 0.501, 0.15, 0.06, "A"),
    ("Moskov", "Marksman", "Physical Damage", 0.509, 0.11, 0.08, "S"),
    ("Bruno", "Marksman", "Physical Damage", 0.502, 0.09, 0.04, "A"),
    ("Clint", "Marksman", "Physical Damage", 0.498, 0.06, 0.03, "B"),
    ("Hanabi", "Marksman", "Physical Damage", 0.499, 0.10, 0.05, "A"),
    ("Kimmy", "Marksman", "Magic Damage", 0.497, 0.05, 0.02, "B"),
    ("Granger", "Marksman", "Physical Damage", 0.514, 0.18, 0.13, "S"),
    ("Lesley", "Marksman", "Physical Damage", 0.505, 0.12, 0.07, "S"),
    ("Irithel", "Marksman", "Physical Damage", 0.503, 0.08, 0.04, "A"),
    ("Karrie", "Marksman", "Magic Damage", 0.501, 0.07, 0.03, "A"),
    ("Claude", "Marksman", "Physical Damage", 0.510, 0.14, 0.09, "S"),
    ("Wanwan", "Marksman", "Physical Damage", 0.512, 0.13, 0.10, "S"),
    ("Yi Sun-shin", "Marksman", "Physical Damage", 0.506, 0.09, 0.05, "A"),
    ("Brody", "Marksman", "Physical Damage", 0.511, 0.15, 0.11, "S"),
    ("Beatrix", "Marksman", "Physical Damage", 0.508, 0.10, 0.07, "S"),
    ("Popol and Kupa", "Marksman", "Crowd Control", 0.502, 0.06, 0.03, "A"),
    ("Melissa", "Marksman", "Physical Damage", 0.504, 0.08, 0.05, "A"),
    ("Natan", "Marksman", "Physical Damage", 0.500, 0.07, 0.03, "A"),
    ("Ixia", "Marksman", "Physical Damage", 0.506, 0.11, 0.06, "S"),

    # SUPPORTS (18 heroes)
    ("Rafaela", "Support", "Heal", 0.501, 0.08, 0.03, "A"),
    ("Estes", "Support", "Heal", 0.508, 0.12, 0.07, "S"),
    ("Angela", "Support", "Heal", 0.503, 0.09, 0.04, "A"),
    ("Diggie", "Support", "Crowd Control", 0.498, 0.06, 0.02, "B"),
    ("Lolita", "Support", "Crowd Control", 0.495, 0.05, 0.02, "A"),
    ("Minotaur", "Support", "Crowd Control", 0.502, 0.07, 0.02, "A"),
    ("Atlas", "Support", "Crowd Control", 0.521, 0.18, 0.12, "S"),
    ("Mathilda", "Support", "Mobility", 0.501, 0.06, 0.03, "A"),
    ("Floryn", "Support", "Heal", 0.509, 0.11, 0.06, "S"),
    ("Faramis", "Support", "Crowd Control", 0.502, 0.07, 0.03, "A"),
    ("Nana", "Support", "Crowd Control", 0.498, 0.07, 0.03, "A"),
    ("Kaja", "Support", "Crowd Control", 0.499, 0.05, 0.02, "B"),
    ("Chip", "Support", "Crowd Control", 0.502, 0.10, 0.04, "A"),
    ("Zhuxin", "Support", "Crowd Control", 0.510, 0.11, 0.08, "S"),
    ("Carmilla", "Support", "Crowd Control", 0.497, 0.04, 0.01, "B"),
    ("Dawnbringer", "Support", "Heal", 0.500, 0.03, 0.01, "B"),
    ("Vexana", "Support", "Burst", 0.494, 0.03, 0.01, "B"),
    ("Selena", "Support", "Burst", 0.508, 0.08, 0.07, "A"),
]

# Counter relationships: (hero_being_countered, counter_hero, score)
# Score 0.0-1.0, higher = stronger counter
COUNTERS_DATA = [
    # Assassins countered by CC tanks
    ("Fanny", "Chou", 0.85),
    ("Fanny", "Franco", 0.80),
    ("Fanny", "Tigreal", 0.75),
    ("Fanny", "Atlas", 0.82),
    ("Lancelot", "Chou", 0.78),
    ("Lancelot", "Franco", 0.72),
    ("Lancelot", "Atlas", 0.76),
    ("Gusion", "Chou", 0.80),
    ("Gusion", "Franco", 0.75),
    ("Gusion", "Tigreal", 0.70),
    ("Hayabusa", "Chou", 0.76),
    ("Hayabusa", "Franco", 0.70),
    ("Hayabusa", "Atlas", 0.74),
    ("Ling", "Chou", 0.82),
    ("Ling", "Franco", 0.78),
    ("Ling", "Atlas", 0.80),
    ("Joy", "Chou", 0.79),
    ("Joy", "Franco", 0.73),
    ("Joy", "Atlas", 0.77),
    ("Julian", "Chou", 0.77),
    ("Julian", "Franco", 0.71),
    ("Julian", "Atlas", 0.75),

    # Marksmen countered by Assassins
    ("Granger", "Fanny", 0.82),
    ("Granger", "Lancelot", 0.78),
    ("Granger", "Gusion", 0.80),
    ("Lesley", "Fanny", 0.80),
    ("Lesley", "Lancelot", 0.76),
    ("Lesley", "Gusion", 0.78),
    ("Claude", "Fanny", 0.78),
    ("Claude", "Lancelot", 0.74),
    ("Claude", "Gusion", 0.76),
    ("Brody", "Fanny", 0.76),
    ("Brody", "Lancelot", 0.72),
    ("Brody", "Gusion", 0.74),
    ("Wanwan", "Fanny", 0.75),
    ("Wanwan", "Lancelot", 0.73),
    ("Wanwan", "Gusion", 0.70),
    ("Beatrix", "Fanny", 0.77),
    ("Beatrix", "Lancelot", 0.75),
    ("Beatrix", "Gusion", 0.73),
    ("Miya", "Fanny", 0.85),
    ("Miya", "Lancelot", 0.82),
    ("Miya", "Gusion", 0.80),
    ("Layla", "Fanny", 0.88),
    ("Layla", "Lancelot", 0.85),
    ("Layla", "Gusion", 0.83),

    # Mages countered by Assassins
    ("Kagura", "Fanny", 0.80),
    ("Kagura", "Lancelot", 0.82),
    ("Kagura", "Gusion", 0.78),
    ("Kadita", "Fanny", 0.78),
    ("Kadita", "Lancelot", 0.80),
    ("Kadita", "Gusion", 0.76),
    ("Lunox", "Fanny", 0.76),
    ("Lunox", "Lancelot", 0.78),
    ("Lunox", "Gusion", 0.74),
    ("Vale", "Fanny", 0.75),
    ("Vale", "Lancelot", 0.77),
    ("Vale", "Gusion", 0.73),
    ("Xavier", "Fanny", 0.79),
    ("Xavier", "Lancelot", 0.81),
    ("Xavier", "Gusion", 0.77),

    # Tanks countered by true damage/high penetration
    ("Tigreal", "Karrie", 0.80),
    ("Tigreal", "Dyrroth", 0.70),
    ("Tigreal", "Yu Zhong", 0.72),
    ("Atlas", "Karrie", 0.78),
    ("Atlas", "Dyrroth", 0.68),
    ("Atlas", "Yu Zhong", 0.70),
    ("Gatotkaca", "Karrie", 0.82),
    ("Gatotkaca", "Dyrroth", 0.72),
    ("Esmeralda", "Karrie", 0.75),
    ("Esmeralda", "Yu Zhong", 0.70),

    # Fighters countered by kiting/sustain
    ("Chou", "Lancelot", 0.72),
    ("Chou", "Gusion", 0.70),
    ("Chou", "Fanny", 0.74),
    ("Dyrroth", "Karrie", 0.75),
    ("Dyrroth", "Lancelot", 0.73),
    ("Benedetta", "Fanny", 0.70),
    ("Benedetta", "Lancelot", 0.72),
    ("Yu Zhong", "Karrie", 0.73),
    ("Yu Zhong", "Lancelot", 0.71),

    # Supports countered by burst
    ("Estes", "Gusion", 0.80),
    ("Estes", "Lancelot", 0.78),
    ("Estes", "Fanny", 0.82),
    ("Rafaela", "Gusion", 0.76),
    ("Rafaela", "Lancelot", 0.74),
    ("Floryn", "Gusion", 0.78),
    ("Floryn", "Lancelot", 0.76),
]

# Synergy relationships: (hero_a, hero_b, score)
# Score 0.0-1.0, higher = better synergy
SYNERGIES_DATA = [
    # Tank + Marksman protection
    ("Tigreal", "Granger", 0.85),
    ("Tigreal", "Claude", 0.82),
    ("Tigreal", "Brody", 0.80),
    ("Atlas", "Granger", 0.88),
    ("Atlas", "Claude", 0.86),
    ("Atlas", "Wanwan", 0.84),
    ("Atlas", "Beatrix", 0.83),
    ("Franco", "Miya", 0.78),
    ("Franco", "Layla", 0.80),
    ("Johnson", "Granger", 0.76),
    ("Johnson", "Claude", 0.78),

    # Support + Marksman healing/support
    ("Estes", "Granger", 0.90),
    ("Estes", "Claude", 0.88),
    ("Estes", "Brody", 0.86),
    ("Estes", "Wanwan", 0.85),
    ("Estes", "Beatrix", 0.84),
    ("Rafaela", "Miya", 0.82),
    ("Rafaela", "Layla", 0.80),
    ("Floryn", "Granger", 0.87),
    ("Floryn", "Claude", 0.85),
    ("Floryn", "Brody", 0.83),
    ("Angela", "Granger", 0.84),
    ("Angela", "Claude", 0.82),

    # Mage + Tank/Support combo
    ("Kagura", "Tigreal", 0.82),
    ("Kagura", "Atlas", 0.84),
    ("Kagura", "Estes", 0.80),
    ("Vale", "Tigreal", 0.78),
    ("Vale", "Franco", 0.76),
    ("Lunox", "Atlas", 0.80),
    ("Lunox", "Estes", 0.78),
    ("Kadita", "Tigreal", 0.79),
    ("Kadita", "Floryn", 0.77),
    ("Xavier", "Atlas", 0.83),
    ("Xavier", "Estes", 0.81),

    # Assassin + Support gank setup
    ("Fanny", "Mathilda", 0.88),
    ("Fanny", "Diggie", 0.76),
    ("Lancelot", "Mathilda", 0.85),
    ("Lancelot", "Estes", 0.75),
    ("Gusion", "Mathilda", 0.86),
    ("Gusion", "Angela", 0.78),
    ("Hayabusa", "Mathilda", 0.82),
    ("Hayabusa", "Floryn", 0.76),
    ("Ling", "Mathilda", 0.84),
    ("Ling", "Diggie", 0.74),
    ("Joy", "Mathilda", 0.83),
    ("Joy", "Angela", 0.77),
    ("Julian", "Mathilda", 0.81),
    ("Julian", "Floryn", 0.75),

    # Fighter + Support/Tank combo
    ("Chou", "Estes", 0.82),
    ("Chou", "Floryn", 0.80),
    ("Chou", "Tigreal", 0.78),
    ("Dyrroth", "Rafaela", 0.79),
    ("Dyrroth", "Floryn", 0.77),
    ("Yu Zhong", "Estes", 0.81),
    ("Yu Zhong", "Atlas", 0.76),
    ("Benedetta", "Floryn", 0.78),
    ("Benedetta", "Angela", 0.76),
    ("Yin", "Estes", 0.79),
    ("Yin", "Tigreal", 0.77),
    ("Guinevere", "Floryn", 0.80),
    ("Guinevere", "Mathilda", 0.75),
    ("Arlott", "Estes", 0.78),
    ("Arlott", "Floryn", 0.76),
    ("Lukas", "Estes", 0.77),
    ("Lukas", "Atlas", 0.75),
    ("Suyou", "Floryn", 0.76),
    ("Suyou", "Mathilda", 0.74),

    # Marksman + Marksman (dual carry)
    ("Granger", "Claude", 0.75),
    ("Brody", "Wanwan", 0.73),
    ("Beatrix", "Lesley", 0.72),
    ("Miya", "Layla", 0.70),

    # Mage + Mage combo
    ("Kagura", "Lunox", 0.82),
    ("Vale", "Xavier", 0.80),
    ("Kadita", "Zhuxin", 0.78),
    ("Lylia", "Valentina", 0.76),
]

def get_hero_id(db_manager: DatabaseManager, hero_name: str) -> int:
    """Get hero ID by name"""
    hero = db_manager.get_hero_by_name(hero_name)
    return hero["id"] if hero else None

def populate_heroes(db_manager: DatabaseManager):
    """Populate heroes table"""
    print(f"Populating {len(HEROES_DATA)} heroes...")
    for name, role, specialty, win_rate, pick_rate, ban_rate, tier in HEROES_DATA:
        hero_data = {
            "name": name,
            "role": role,
            "specialty": specialty,
            "base_win_rate": win_rate,
            "pick_rate": pick_rate,
            "ban_rate": ban_rate,
            "tier": tier
        }
        db_manager.upsert_hero(hero_data)
    print(f"✓ Inserted/updated {len(HEROES_DATA)} heroes")

def populate_counters(db_manager: DatabaseManager):
    """Populate hero_counters table"""
    print(f"Populating {len(COUNTERS_DATA)} counter relationships...")
    count = 0
    for hero_name, counter_name, score in COUNTERS_DATA:
        hero_id = get_hero_id(db_manager, hero_name)
        counter_id = get_hero_id(db_manager, counter_name)
        if hero_id and counter_id:
            db_manager.save_counter(hero_id, counter_id, score)
            count += 1
    print(f"✓ Inserted {count} counter relationships")

def populate_synergies(db_manager: DatabaseManager):
    """Populate hero_synergies table"""
    print(f"Populating {len(SYNERGIES_DATA)} synergy relationships...")
    count = 0
    for hero_a_name, hero_b_name, score in SYNERGIES_DATA:
        hero_a_id = get_hero_id(db_manager, hero_a_name)
        hero_b_id = get_hero_id(db_manager, hero_b_name)
        if hero_a_id and hero_b_id:
            db_manager.save_synergy(hero_a_id, hero_b_id, score)
            count += 1
    print(f"✓ Inserted {count} synergy relationships")

def main():
    print("=" * 60)
    print("MLBB Hero Database Populator")
    print("=" * 60)
    
    db_manager = DatabaseManager(DB_PATH)
    
    # Initialize database (create tables if not exist)
    db_manager.initialize_db()
    
    # Populate data
    populate_heroes(db_manager)
    populate_counters(db_manager)
    populate_synergies(db_manager)
    
    # Show statistics
    print("\n" + "=" * 60)
    print("DATABASE STATISTICS")
    print("=" * 60)
    
    heroes = db_manager.get_all_heroes()
    print(f"Total heroes: {len(heroes)}")
    
    # Count by role
    from collections import Counter
    roles = Counter(h["role"] for h in heroes)
    print("\nHeroes by role:")
    for role, count in sorted(roles.items()):
        print(f"  {role}: {count}")
    
    # Count counters and synergies
    conn = db_manager.connect()
    cursor = conn.execute("SELECT COUNT(*) FROM hero_counters")
    counters_count = cursor.fetchone()[0]
    cursor = conn.execute("SELECT COUNT(*) FROM hero_synergies")
    synergies_count = cursor.fetchone()[0]
    db_manager.disconnect()
    
    print(f"\nTotal counters: {counters_count}")
    print(f"Total synergies: {synergies_count}")
    print("=" * 60)
    print("✓ Database population complete!")

if __name__ == "__main__":
    main()
