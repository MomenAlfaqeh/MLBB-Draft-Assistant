import pandas as pd
import sqlite3
from pathlib import Path
import requests
import json

if 'data_loader' not in globals():
    from mage_ai.data_preparation.decorators import data_loader
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@data_loader
def scrape_mlbb_heroes(**kwargs) -> pd.DataFrame:
    """
    Hybrid data loader with priority system:
    Priority 1: Load from current_patch.json (manual updates each patch)
    Priority 2: Enhance with Moonton API (adds new heroes + hero IDs + image URLs)
    Priority 3: Fallback to SQLite for any missing heroes
    """
    print("Loading heroes using hybrid data system...")
    
    # Priority 1: Load from current_patch.json
    patch_path = Path(__file__).parent.parent.parent / 'data_pipeline' / 'patch_data' / 'current_patch.json'
    df = None
    
    if patch_path.exists():
        try:
            with open(patch_path, 'r') as f:
                patch_data = json.load(f)
            
            heroes = patch_data.get('heroes', [])
            df = pd.DataFrame(heroes)
            print(f"Priority 1: Loaded {len(df)} heroes from {patch_path}")
            print(f"Patch: {patch_data.get('patch', 'unknown')}")
            
            # Ensure required columns exist
            required_cols = ['name', 'role', 'specialty', 'win_rate', 'pick_rate', 'ban_rate', 'tier']
            for col in required_cols:
                if col not in df.columns:
                    df[col] = None
                    
            # Rename specialty to specialty if needed
            if 'specialty' in df.columns and 'specialty' not in df.columns:
                df['specialty'] = df['specialty']
                
        except Exception as e:
            print(f"Error loading patch data: {e}")
    
    # If no patch data, try SQLite
    if df is None or df.empty:
        print("Priority 3: Falling back to SQLite...")
        db_path = Path(__file__).parent.parent.parent / 'database' / 'mlbb.db'
        
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM heroes")
                heroes = [dict(row) for row in cursor.fetchall()]
                conn.close()
                
                df = pd.DataFrame(heroes)
                df = df.rename(columns={'base_win_rate': 'win_rate', 'specialty': 'specialty'})
                print(f"Loaded {len(df)} heroes from SQLite")
            except Exception as e:
                print(f"Error loading from database: {e}")
    
    # Priority 2: Enhance with Moonton API
    print("\nPriority 2: Enhancing with Moonton API...")
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
        }
        r = requests.get('https://mapi.mobilelegends.com/hero/list', headers=headers, timeout=10)
        if r.status_code == 200:
            data = r.json()
            api_heroes = data.get('data', [])
            print(f"Moonton API returned {len(api_heroes)} heroes")
            
            # Create lookup by name
            api_dict = {h['name'].lower(): h for h in api_heroes if 'name' in h}
            
            # Add hero_id from API if available
            if 'id' in df.columns and 'hero_id' not in df.columns:
                df['hero_id'] = df['name'].apply(
                    lambda x: api_dict.get(x.lower(), {}).get('heroid')
                )
                
            # Add new heroes from API that aren't in df
            existing_names = set(df['name'].str.lower())
            new_heroes = []
            for hero in api_heroes:
                if hero.get('name', '').lower() not in existing_names:
                    new_heroes.append({
                        'name': hero.get('name'),
                        'role': None,
                        'specialty': None,
                        'win_rate': None,
                        'pick_rate': None,
                        'ban_rate': None,
                        'tier': None,
                        'hero_id': hero.get('heroid')
                    })
            
            if new_heroes:
                print(f"Adding {len(new_heroes)} new heroes from API")
                df = pd.concat([df, pd.DataFrame(new_heroes)], ignore_index=True)
                
    except Exception as e:
        print(f"Could not fetch from Moonton API: {e}")
    
    # Ensure all required columns exist
    required_cols = ['id', 'name', 'role', 'specialty', 'win_rate', 'pick_rate', 'ban_rate', 'tier']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    # Select only required columns
    df = df[required_cols]
    
    print(f"\nTotal heroes loaded: {len(df)}")
    return df
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM heroes")
        count = cursor.fetchone()[0]
        print(f"Found {count} heroes in SQLite")
        
        cursor.execute("SELECT * FROM heroes")
        heroes = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Convert to DataFrame and rename columns to match expected schema
        df = pd.DataFrame(heroes)
        
        # Rename columns if needed
        column_mapping = {
            'base_win_rate': 'win_rate',
            'specialty': 'specialty',
        }
        df = df.rename(columns=column_mapping)
        
        # Try to enhance with Moonton API data (hero IDs)
        print("\nFetching hero IDs from Moonton API...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            r = requests.get('https://mapi.mobilelegends.com/hero/list', headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                api_heroes = data.get('data', [])
                print(f"Moonton API returned {len(api_heroes)} heroes")
                
                # Add hero_id from API if available
                api_dict = {h['name'].lower(): h.get('heroid') for h in api_heroes if 'name' in h}
                df['api_hero_id'] = df['name'].apply(
                    lambda x: api_dict.get(x.lower())
                )
        except Exception as e:
            print(f"Could not fetch from Moonton API: {e}")
        
        # Ensure all required columns exist
        required_cols = ['id', 'name', 'role', 'specialty', 'win_rate', 
                        'pick_rate', 'ban_rate', 'tier']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        # Select only the columns we need
        df = df[required_cols]
        
        print(f"\nTotal heroes loaded: {len(df)}")
        return df
        
    except Exception as e:
        print(f"Error loading from database: {e}")
        return pd.DataFrame(get_sample_heroes())
    
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM heroes")
        count = cursor.fetchone()[0]
        print(f"Found {count} heroes in SQLite")
        
        cursor.execute("SELECT * FROM heroes")
        heroes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        df = pd.DataFrame(heroes)
        
        # Rename columns to match expected schema
        column_mapping = {
            'base_win_rate': 'win_rate',
            'specialty': 'specialty',
        }
        df = df.rename(columns=column_mapping)
        
        # Try to enhance with Moonton API data
        print("\nFetching additional hero data from Moonton API...")
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
            }
            r = requests.get('https://mapi.mobilelegends.com/hero/list', headers=headers, timeout=10)
            if r.status_code == 200:
                data = r.json()
                api_heroes = data.get('data', [])
                print(f"Moonton API returned {len(api_heroes)} heroes")
                
                # Add hero_id from API if available
                api_dict = {h['name'].lower(): h for h in api_heroes}
                df['api_hero_id'] = df['name'].apply(
                    lambda x: api_dict.get(x.lower(), {}).get('heroid')
                )
        except Exception as e:
            print(f"Could not fetch from Moonton API: {e}")
        
        # Ensure all required columns exist
        required_cols = ['id', 'name', 'role', 'specialty', 'win_rate', 
                        'pick_rate', 'ban_rate', 'tier']
        for col in required_cols:
            if col not in df.columns:
                df[col] = None
        
        df = df[required_cols]
        
        print(f"\nTotal heroes loaded: {len(df)}")
        return df
        
    except Exception as e:
        print(f"Error loading from database: {e}")
        return pd.DataFrame(get_sample_heroes())


def get_sample_heroes():
    """Return sample hero data as fallback"""
    return [
        {'name': 'Alucard', 'role': 'Fighter', 'specialty': 'Charge/Push', 'win_rate': 0.51, 'pick_rate': 0.15, 'ban_rate': 0.02, 'tier': 'A'},
        {'name': 'Fanny', 'role': 'Assassin', 'specialty': 'Burst/Damage', 'win_rate': 0.48, 'pick_rate': 0.08, 'ban_rate': 0.25, 'tier': 'S'},
        {'name': 'Tigreal', 'role': 'Tank', 'specialty': 'Initiator/Crowd Control', 'win_rate': 0.52, 'pick_rate': 0.12, 'ban_rate': 0.05, 'tier': 'A'},
    ]


@test
def test_output(df) -> None:
    assert df is not None, 'The output is undefined'
    if not df.empty:
        assert 'name' in df.columns, 'Missing name column'
