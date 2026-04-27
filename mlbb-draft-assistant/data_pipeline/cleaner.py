import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from config import ROLE_LIST

class DataCleaner:
    def __init__(self):
        pass
    
    def clean_hero_data(self, raw_data: list) -> list:
        """
        Validate and normalize hero dicts
        - ensures win_rate is between 0.3 and 0.7
        - ensures role is in ROLE_LIST
        - strips whitespace from strings
        """
        cleaned_data = []
        
        for hero in raw_data:
            # Skip if not a dictionary
            if not isinstance(hero, dict):
                continue
                
            cleaned_hero = hero.copy()
            
            # Clean string fields
            string_fields = ['name', 'role', 'specialty', 'tier']
            for field in string_fields:
                if field in cleaned_hero and isinstance(cleaned_hero[field], str):
                    cleaned_hero[field] = cleaned_hero[field].strip()
            
            # Validate and normalize win_rate
            if 'base_win_rate' in cleaned_hero:
                try:
                    win_rate = float(cleaned_hero['base_win_rate'])
                    # Clamp between 0.3 and 0.7
                    cleaned_hero['base_win_rate'] = max(0.3, min(0.7, win_rate))
                except (ValueError, TypeError):
                    # If invalid, set to default
                    cleaned_hero['base_win_rate'] = 0.5
            
            # Validate role
            if 'role' in cleaned_hero:
                if cleaned_hero['role'] not in ROLE_LIST:
                    # If invalid role, set to first role in list as fallback
                    cleaned_hero['role'] = ROLE_LIST[0] if ROLE_LIST else 'Unknown'
            
            # Ensure numeric fields are valid
            numeric_fields = ['pick_rate', 'ban_rate']
            for field in numeric_fields:
                if field in cleaned_hero:
                    try:
                        val = float(cleaned_hero[field])
                        # Clamp between 0 and 1
                        cleaned_hero[field] = max(0.0, min(1.0, val))
                    except (ValueError, TypeError):
                        cleaned_hero[field] = 0.0
            
            cleaned_data.append(cleaned_hero)
        
        return cleaned_data
    
    def clean_counter_data(self, raw_data: list) -> list:
        """
        Validate counter_score is between 0 and 1
        """
        cleaned_data = []
        
        for counter in raw_data:
            # Skip if not a dictionary
            if not isinstance(counter, dict):
                continue
                
            cleaned_counter = counter.copy()
            
            # Clean string fields
            string_fields = ['hero_name', 'countered_by_name', 'patch']
            for field in string_fields:
                if field in cleaned_counter and isinstance(cleaned_counter[field], str):
                    cleaned_counter[field] = cleaned_counter[field].strip()
            
            # Validate counter_score
            if 'counter_score' in cleaned_counter:
                try:
                    score = float(cleaned_counter['counter_score'])
                    # Clamp between 0 and 1
                    cleaned_counter['counter_score'] = max(0.0, min(1.0, score))
                except (ValueError, TypeError):
                    cleaned_counter['counter_score'] = 0.0
            
            # Ensure sample_size is valid integer
            if 'sample_size' in cleaned_counter:
                try:
                    size = int(cleaned_counter['sample_size'])
                    # Ensure non-negative
                    cleaned_counter['sample_size'] = max(0, size)
                except (ValueError, TypeError):
                    cleaned_counter['sample_size'] = 0
            
            cleaned_data.append(cleaned_counter)
        
        return cleaned_data
    
    def clean_synergy_data(self, raw_data: list) -> list:
        """
        Validate synergy_score is between 0 and 1
        """
        cleaned_data = []
        
        for synergy in raw_data:
            # Skip if not a dictionary
            if not isinstance(synergy, dict):
                continue
                
            cleaned_synergy = synergy.copy()
            
            # Clean string fields
            string_fields = ['hero_a_name', 'hero_b_name', 'patch']
            for field in string_fields:
                if field in cleaned_synergy and isinstance(cleaned_synergy[field], str):
                    cleaned_synergy[field] = cleaned_synergy[field].strip()
            
            # Validate synergy_score
            if 'synergy_score' in cleaned_synergy:
                try:
                    score = float(cleaned_synergy['synergy_score'])
                    # Clamp between 0 and 1
                    cleaned_synergy['synergy_score'] = max(0.0, min(1.0, score))
                except (ValueError, TypeError):
                    cleaned_synergy['synergy_score'] = 0.0
            
            # Validate combined_wr
            if 'combined_wr' in cleaned_synergy:
                try:
                    wr = float(cleaned_synergy['combined_wr'])
                    # Clamp between 0 and 1
                    cleaned_synergy['combined_wr'] = max(0.0, min(1.0, wr))
                except (ValueError, TypeError):
                    cleaned_synergy['combined_wr'] = 0.5
            
            # Ensure sample_size is valid integer
            if 'sample_size' in cleaned_synergy:
                try:
                    size = int(cleaned_synergy['sample_size'])
                    # Ensure non-negative
                    cleaned_synergy['sample_size'] = max(0, size)
                except (ValueError, TypeError):
                    cleaned_synergy['sample_size'] = 0
            
            cleaned_data.append(cleaned_synergy)
        
        return cleaned_data

# Example usage (for testing)
if __name__ == "__main__":
    cleaner = DataCleaner()
    
    # Test hero data cleaning
    dirty_heroes = [
        {
            "name": "  Gatotkaca  ",
            "role": "Tank",
            "base_win_rate": 0.8,  # Too high, should be clamped to 0.7
            "pick_rate": 0.15,
            "ban_rate": 0.08
        },
        {
            "name": "Invalid Hero",
            "role": "InvalidRole",  # Should be changed to first role in list
            "base_win_rate": 0.5
        }
    ]
    
    cleaned_heroes = cleaner.clean_hero_data(dirty_heroes)
    print("Cleaned heroes:", cleaned_heroes)