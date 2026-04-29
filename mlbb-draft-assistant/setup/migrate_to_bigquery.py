import sqlite3
import sys
from google.cloud import bigquery
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import DB_PATH

PROJECT_ID = "mlbb-draft-assistant-494814"
DATASET = "mlbb_draft"

def migrate_to_bigquery():
    client = bigquery.Client(project=PROJECT_ID)
    dataset_id = f"{PROJECT_ID}.{DATASET}"
    
    db_path = Path(__file__).parent.parent / DB_PATH
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    print("Starting migration to BigQuery...")
    
    cursor.execute("SELECT COUNT(*) FROM heroes")
    hero_count = cursor.fetchone()[0]
    print(f"Found {hero_count} heroes in SQLite")
    
    cursor.execute("SELECT * FROM heroes")
    heroes = [dict(row) for row in cursor.fetchall()]
    
    heroes_table = client.get_table(f"{dataset_id}.heroes")
    
    hero_rows = []
    for hero in heroes:
        hero_rows.append({
            "id": hero["id"],
            "name": hero["name"],
            "role": hero["role"],
            "specialty": hero["specialty"],
            "base_win_rate": hero["base_win_rate"],
            "pick_rate": hero["pick_rate"],
            "ban_rate": hero["ban_rate"],
            "tier": hero["tier"],
            "patch": None,
            "last_updated": hero["last_updated"],
        })
    
    errors = client.insert_rows_json(heroes_table, hero_rows)
    if errors:
        print(f"Errors inserting heroes: {errors}")
    else:
        print(f"Successfully inserted {len(hero_rows)} heroes")
    
    cursor.execute("SELECT COUNT(*) FROM hero_counters")
    counter_count = cursor.fetchone()[0]
    print(f"Found {counter_count} counters in SQLite")
    
    cursor.execute("SELECT * FROM hero_counters")
    counters = [dict(row) for row in cursor.fetchall()]
    
    counters_table = client.get_table(f"{dataset_id}.hero_counters")
    
    counter_rows = []
    for counter in counters:
        counter_rows.append({
            "hero_id": counter["hero_id"],
            "countered_by_id": counter["countered_by_id"],
            "counter_score": counter["counter_score"],
            "sample_size": counter["sample_size"],
            "patch": counter.get("patch_date"),
        })
    
    errors = client.insert_rows_json(counters_table, counter_rows)
    if errors:
        print(f"Errors inserting counters: {errors}")
    else:
        print(f"Successfully inserted {len(counter_rows)} counters")
    
    cursor.execute("SELECT COUNT(*) FROM hero_synergies")
    synergy_count = cursor.fetchone()[0]
    print(f"Found {synergy_count} synergies in SQLite")
    
    cursor.execute("SELECT * FROM hero_synergies")
    synergies = [dict(row) for row in cursor.fetchall()]
    
    synergies_table = client.get_table(f"{dataset_id}.hero_synergies")
    
    synergy_rows = []
    for synergy in synergies:
        synergy_rows.append({
            "hero_a_id": synergy["hero_a_id"],
            "hero_b_id": synergy["hero_b_id"],
            "synergy_score": synergy["synergy_score"],
            "combined_wr": synergy["combined_wr"],
            "sample_size": synergy["sample_size"],
            "patch": synergy.get("patch_date"),
        })
    
    errors = client.insert_rows_json(synergies_table, synergy_rows)
    if errors:
        print(f"Errors inserting synergies: {errors}")
    else:
        print(f"Successfully inserted {len(synergy_rows)} synergies")
    
    conn.close()
    
    print("\nMigration complete!")
    print(f"Total rows migrated:")
    print(f"  - Heroes: {len(hero_rows)}")
    print(f"  - Counters: {len(counter_rows)}")
    print(f"  - Synergies: {len(synergy_rows)}")

if __name__ == "__main__":
    migrate_to_bigquery()
