from dataclasses import dataclass
from typing import List, Dict, Any, Optional
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import DatabaseManager
from config import SCORING_WEIGHTS, ROLE_LIST

@dataclass
class HeroScore:
    hero_id: int
    name: str
    total_score: float
    breakdown: Dict[str, float]

def calculate_hero_score(candidate: Dict[str, Any], 
                        enemy_picks: List[str], 
                        ally_picks: List[str], 
                        db_path: str = None) -> HeroScore:
    """
    Calculate a comprehensive score for a hero based on:
    - Meta win rate (base_win_rate)
    - Counter score (how well it counters enemy picks)
    - Synergy score (how well it synergizes with ally picks)
    - Composition bonus (role balance)
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    db_manager = DatabaseManager(db_path)
    
    # Get candidate hero details
    hero = db_manager.get_hero_by_name(candidate["name"])
    if not hero:
        # If hero not found in DB, use candidate data
        hero_id = candidate.get("id", 0)
        base_win_rate = candidate.get("base_win_rate", 0.5)
        role = candidate.get("role", "Unknown")
    else:
        hero_id = hero["id"]
        base_win_rate = hero["base_win_rate"]
        role = hero["role"]
    
    # 1. Meta win rate score (normalized to 0-1)
    # Assuming win rates are between 0.4 and 0.6, normalize to 0-1 range
    meta_wr_score = (base_win_rate - 0.4) / 0.2  # 0.4 -> 0, 0.6 -> 1
    meta_wr_score = max(0.0, min(1.0, meta_wr_score))  # Clamp to 0-1
    
    # 2. Counter score (how well candidate counters enemy picks)
    counter_score = 0.0
    if enemy_picks:
        total_counter = 0.0
        valid_enemies = 0
        for enemy_name in enemy_picks:
            enemy_hero = db_manager.get_hero_by_name(enemy_name)
            if enemy_hero:
                # Get how well candidate counters this enemy
                counters = db_manager.get_counters(enemy_hero["id"])
                for counter in counters:
                    if counter["countered_by_id"] == hero_id:
                        total_counter += counter["counter_score"]
                        valid_enemies += 1
                        break
        if valid_enemies > 0:
            counter_score = total_counter / valid_enemies
    
    # 3. Synergy score (how well candidate synergizes with ally picks)
    synergy_score = 0.0
    if ally_picks:
        total_synergy = 0.0
        valid_allies = 0
        for ally_name in ally_picks:
            ally_hero = db_manager.get_hero_by_name(ally_name)
            if ally_hero:
                # Get synergy between candidate and this ally
                synergies = db_manager.get_synergies(ally_hero["id"])
                for synergy in synergies:
                    if (synergy["hero_a_id"] == hero_id and synergy["hero_b_id"] == ally_hero["id"]) or \
                       (synergy["hero_b_id"] == hero_id and synergy["hero_a_id"] == ally_hero["id"]):
                        total_synergy += synergy["synergy_score"]
                        valid_allies += 1
                        break
        if valid_allies > 0:
            synergy_score = total_synergy / valid_allies
    
    # 4. Composition bonus (role balance)
    comp_bonus = 0.0
    # Define ideal team composition (example: 1 Tank, 2 Fighters, 1 Mage, 1 Marksman, 1 Support)
    ideal_composition = {
        "Tank": 1,
        "Fighter": 2,
        "Mage": 1,
        "Marksman": 1,
        "Support": 1
    }
    
    # Count current allies by role
    ally_role_count = {role: 0 for role in ROLE_LIST}
    for ally_name in ally_picks:
        ally_hero = db_manager.get_hero_by_name(ally_name)
        if ally_hero:
            ally_role = ally_hero["role"]
            if ally_role in ally_role_count:
                ally_role_count[ally_role] += 1
    
    # Calculate how much this candidate improves role balance
    role_needed = ideal_composition.get(role, 0)
    current_count = ally_role_count.get(role, 0)
    if role_needed > 0:
        # Bonus if we need more of this role
        if current_count < role_needed:
            comp_bonus = 1.0 - (current_count / role_needed)
        else:
            comp_bonus = 0.0  # No bonus if we already have enough
    else:
        # For roles not in ideal composition, give small bonus for diversity
        comp_bonus = 0.5
    
    # Calculate weighted total score
    weights = SCORING_WEIGHTS
    total_score = (
        weights["meta_wr"] * meta_wr_score +
        weights["counter_score"] * counter_score +
        weights["synergy_score"] * synergy_score +
        weights["comp_bonus"] * comp_bonus
    )
    
    # Ensure score is between 0 and 1
    total_score = max(0.0, min(1.0, total_score))
    
    breakdown = {
        "meta_wr": meta_wr_score,
        "counter_score": counter_score,
        "synergy_score": synergy_score,
        "comp_bonus": comp_bonus
    }
    
    return HeroScore(
        hero_id=hero_id,
        name=candidate["name"],
        total_score=total_score,
        breakdown=breakdown
    )

def get_top_recommendations(available_heroes: List[Dict[str, Any]], 
                           enemy_picks: List[str], 
                           ally_picks: List[str], 
                           top_n: int = 5) -> List[HeroScore]:
    """
    Get top N hero recommendations based on scoring algorithm.
    """
    scored_heroes = []
    for hero in available_heroes:
        score = calculate_hero_score(hero, enemy_picks, ally_picks)
        scored_heroes.append(score)
    
    # Sort by total score descending
    scored_heroes.sort(key=lambda x: x.total_score, reverse=True)
    
    # Return top N
    return scored_heroes[:top_n]

# Example usage (for testing)
if __name__ == "__main__":
    # Mock data for testing
    mock_available_heroes = [
        {"name": "Gatotkaca", "role": "Tank", "base_win_rate": 0.52},
        {"name": "Franco", "role": "Tank", "base_win_rate": 0.50},
        {"name": "Alucard", "role": "Fighter", "base_win_rate": 0.51},
        {"name": "Hayabusa", "role": "Assassin", "base_win_rate": 0.49},
        {"name": "Harley", "role": "Mage", "base_win_rate": 0.47},
        {"name": "Lyla", "role": "Mage", "base_win_rate": 0.53},
        {"name": "Claude", "role": "Marksman", "base_win_rate": 0.50},
        {"name": "Karrie", "role": "Marksman", "base_win_rate": 0.48},
        {"name": "Rafaela", "role": "Support", "base_win_rate": 0.54},
        {"name": "Estes", "role": "Support", "base_win_rate": 0.51}
    ]
    
    enemy_picks = ["Hayabusa", "Claude"]
    ally_picks = ["Franco"]
    
    recommendations = get_top_recommendations(mock_available_heroes, enemy_picks, ally_picks, top_n=3)
    
    print("Top 3 Recommendations:")
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec.name} (Score: {rec.total_score:.3f})")
        print(f"   Breakdown: {rec.breakdown}")