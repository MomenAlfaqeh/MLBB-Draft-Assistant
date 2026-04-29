from pandas import DataFrame
import re
from datetime import datetime

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


VALID_ROLES = ['Tank', 'Fighter', 'Assassin', 'Mage', 'Marksman', 'Support']


@transformer
def clean_hero_data(df: DataFrame, **kwargs) -> DataFrame:
    """
    Clean and validate MLBB hero data:
    - Validate win_rate is between 0.4-0.65
    - Normalize role names
    - Add current patch date
    - Remove duplicates
    - Ensure correct column names for BigQuery
    """
    if df.empty:
        print("DataFrame is empty, returning as is")
        return df
    
    df = df.copy()
    
    # Rename win_rate to base_win_rate for BigQuery
    if 'win_rate' in df.columns and 'base_win_rate' not in df.columns:
        df = df.rename(columns={'win_rate': 'base_win_rate'})
    
    if 'base_win_rate' in df.columns:
        df['base_win_rate'] = df['base_win_rate'].apply(validate_win_rate)
        invalid_count = df['base_win_rate'].isna().sum()
        if invalid_count > 0:
            print(f"Removed {invalid_count} heroes with invalid win rates")
            df = df.dropna(subset=['base_win_rate'])
    
    if 'role' in df.columns:
        df['role'] = df['role'].apply(normalize_role)
        invalid_roles = df[~df['role'].isin(VALID_ROLES)]['role'].unique()
        if len(invalid_roles) > 0:
            print(f"Warning: Invalid roles found after normalization: {invalid_roles}")
    
    today = datetime.now().strftime('%Y-%m-%d')
    df['patch'] = today
    
    if 'id' not in df.columns:
        df['id'] = range(1, len(df) + 1)
    
    required_cols = ['id', 'name', 'role', 'specialty', 'base_win_rate', 
                    'pick_rate', 'ban_rate', 'tier', 'patch']
    for col in required_cols:
        if col not in df.columns:
            df[col] = None
    
    df = df[required_cols]
    
    before = len(df)
    df = df.drop_duplicates(subset=['name'], keep='first')
    after = len(df)
    if before != after:
        print(f"Removed {before - after} duplicate heroes")
    
    print(f"Cleaned data: {len(df)} heroes")
    return df


def validate_win_rate(value):
    if value is None:
        return None
    try:
        val = float(value)
        if 0.4 <= val <= 0.65:
            return val
        else:
            print(f"Win rate {val} out of range [0.4, 0.65], setting to None")
            return None
    except:
        return None


def normalize_role(role):
    if role is None:
        return None
    
    role_str = str(role).strip()
    
    role_mapping = {
        'tank': 'Tank',
        'fighter': 'Fighter',
        'assassin': 'Assassin',
        'mage': 'Mage',
        'marksman': 'Marksman',
        'support': 'Support',
        'roam': 'Support',
        'gold lane': 'Marksman',
        'exp lane': 'Fighter',
        'jungle': 'Assassin',
        'mid lane': 'Mage',
    }
    
    role_lower = role_str.lower()
    for key, value in role_mapping.items():
        if key in role_lower:
            return value
    
    for valid_role in VALID_ROLES:
        if valid_role.lower() in role_lower:
            return valid_role
    
    return role_str


@test
def test_output(df) -> None:
    assert df is not None, 'The output is undefined'
    if not df.empty:
        assert 'name' in df.columns, 'Missing name column'

        if 'win_rate' in df.columns:
            invalid = df[~df['win_rate'].between(0.4, 0.65)]
            assert len(invalid) == 0, f'Found {len(invalid)} heroes with invalid win rates'
