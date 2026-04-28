from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import DatabaseManager
from config import SCORING_WEIGHTS, ROLE_LIST

# Lane definitions - map roles/specialty to lanes
LANE_MAPPING = {
    "EXP Lane": ["Fighter", "Tank"],  # Tanks with fighter specialty also go EXP
    "Jungle": ["Assassin"],  # Fighters with burst can also jungle
    "Mid": ["Mage"],  # Some assassins with magic damage can mid
    "Gold Lane": ["Marksman"],  # Primary gold lane heroes
    "Roam/Utility": ["Support", "Tank"],  # Tanks and supports roam
}

# Heroes that can flex to jungle (fighter assassins)
JUNGLE_FIGHTERS = ["Lancelot", "Gusion", "Fanny", "Hayabusa", "Ling", "Joy", "Julian", "Yin", "Benedetta", "Zilong"]

@dataclass
class HeroScore:
    hero_id: int
    name: str
    total_score: float
    breakdown: Dict[str, float]
    lane: str = "Flex"  # Primary lane for this hero

def get_hero_lane(hero_name: str, role: str) -> str:
    """
    Determine the primary lane for a hero based on role and name.
    """
    # Check junglers first (specific fighters/assassins that jungle)
    if role == "Assassin" or hero_name in JUNGLE_FIGHTERS:
        return "Jungle"
    
    # Check by role
    if role == "Marksman":
        return "Gold Lane"
    if role == "Mage":
        return "Mid"
    if role == "Support":
        return "Roam/Utility"
    if role == "Tank":
        return "Roam/Utility"
    if role == "Fighter":
        return "EXP Lane"
    
    return "Flex"


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
    
    # Determine lane
    lane = get_hero_lane(candidate["name"], role)
    
    # 1. Meta win rate score (normalized to 0-1)
    meta_wr_score = (base_win_rate - 0.4) / 0.2
    meta_wr_score = max(0.0, min(1.0, meta_wr_score))
    
    # 2. Counter score (how well candidate counters enemy picks)
    counter_score = 0.0
    if enemy_picks:
        total_counter = 0.0
        valid_enemies = 0
        for enemy_name in enemy_picks:
            enemy_hero = db_manager.get_hero_by_name(enemy_name)
            if enemy_hero:
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
    ideal_composition = {
        "Tank": 1,
        "Fighter": 2,
        "Mage": 1,
        "Marksman": 1,
        "Support": 1
    }
    
    ally_role_count = {r: 0 for r in ROLE_LIST}
    for ally_name in ally_picks:
        ally_hero = db_manager.get_hero_by_name(ally_name)
        if ally_hero:
            ally_role = ally_hero["role"]
            if ally_role in ally_role_count:
                ally_role_count[ally_role] += 1
    
    role_needed = ideal_composition.get(role, 0)
    current_count = ally_role_count.get(role, 0)
    if role_needed > 0:
        if current_count < role_needed:
            comp_bonus = 1.0 - (current_count / role_needed)
        else:
            comp_bonus = 0.0
    else:
        comp_bonus = 0.5
    
    # Calculate weighted total score
    weights = SCORING_WEIGHTS
    total_score = (
        weights["meta_wr"] * meta_wr_score +
        weights["counter_score"] * counter_score +
        weights["synergy_score"] * synergy_score +
        weights["comp_bonus"] * comp_bonus
    )
    
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
        breakdown=breakdown,
        lane=lane
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

def calculate_matchup_probability(ally_picks: List[str], enemy_picks: List[str], 
                               db_manager: DatabaseManager) -> float:
    """
    Calculate matchup probability (ally win chance %) based on:
    - Average win rate of ally picks vs enemy picks
    - Counter score advantage
    - Synergy bonus
    Formula: base 50% + (ally_avg_wr - enemy_avg_wr)*100 + counter_advantage*10 + synergy_bonus*5
    """
    # Calculate average win rates
    ally_wr = []
    for name in ally_picks:
        hero = db_manager.get_hero_by_name(name)
        if hero:
            ally_wr.append(hero["base_win_rate"])
    
    enemy_wr = []
    for name in enemy_picks:
        hero = db_manager.get_hero_by_name(name)
        if hero:
            enemy_wr.append(hero["base_win_rate"])
    
    ally_avg_wr = sum(ally_wr) / len(ally_wr) if ally_wr else 0.5
    enemy_avg_wr = sum(enemy_wr) / len(enemy_wr) if enemy_wr else 0.5
    
    # Calculate counter advantage (how well allies counter enemies)
    counter_advantage = 0.0
    counter_count = 0
    for ally_name in ally_picks:
        ally_hero = db_manager.get_hero_by_name(ally_name)
        if ally_hero:
            for enemy_name in enemy_picks:
                enemy_hero = db_manager.get_hero_by_name(enemy_name)
                if enemy_hero:
                    counters = db_manager.get_counters(enemy_hero["id"])
                    for counter in counters:
                        if counter["countered_by_id"] == ally_hero["id"]:
                            counter_advantage += counter["counter_score"]
                            counter_count += 1
                            break
    counter_advantage = counter_advantage / max(counter_count, 1)
    
    # Calculate synergy bonus
    synergy_bonus = 0.0
    synergy_count = 0
    for i, ally1 in enumerate(ally_picks):
        for ally2 in ally_picks[i+1:]:
            hero_a = db_manager.get_hero_by_name(ally1)
            hero_b = db_manager.get_hero_by_name(ally2)
            if hero_a and hero_b:
                synergies = db_manager.get_synergies(hero_a["id"])
                for synergy in synergies:
                    if (synergy["hero_a_id"] == hero_b["id"] and synergy["hero_b_id"] == hero_a["id"]) or \
                       (synergy["hero_b_id"] == hero_b["id"] and synergy["hero_a_id"] == hero_a["id"]):
                        synergy_bonus += synergy["synergy_score"]
                        synergy_count += 1
                        break
    synergy_bonus = synergy_bonus / max(synergy_count, 1)
    
    # Apply formula
    probability = 50.0 + (ally_avg_wr - enemy_avg_wr) * 100 + counter_advantage * 10 + synergy_bonus * 5
    
    # Clamp to 0-100
    return max(0.0, min(100.0, probability))


def get_recommendations_by_lane(available_heroes: List[Dict[str, Any]], 
                                enemy_picks: List[str], 
                                ally_picks: List[str], 
                                top_n: int = 2,
                                db_path: str = None) -> Dict[str, List[HeroScore]]:
    """
    Get top N hero recommendations PER LANE (EXP Lane, Jungle, Mid, Gold Lane, Roam/Utility).
    Returns dict with lanes as keys and list of HeroScore objects as values.
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    # Score all heroes
    scored_heroes = []
    for hero in available_heroes:
        score = calculate_hero_score(hero, enemy_picks, ally_picks, db_path)
        scored_heroes.append(score)
    
    # Group by lane
    lane_recommendations = {lane: [] for lane in LANE_MAPPING.keys()}
    
    for score in scored_heroes:
        lane = score.lane
        if lane in lane_recommendations:
            lane_recommendations[lane].append(score)
    
    # Sort each lane by score and take top N
    for lane in lane_recommendations:
        lane_recommendations[lane].sort(key=lambda x: x.total_score, reverse=True)
        lane_recommendations[lane] = lane_recommendations[lane][:top_n]
    
    return lane_recommendations


def get_top_recommendations(available_heroes: List[Dict[str, Any]], 
                           enemy_picks: List[str], 
                           ally_picks: List[str], 
                           top_n: int = 5,
                           db_path: str = None) -> Tuple[List[HeroScore], float]:
    """
    Get top N hero recommendations based on scoring algorithm.
    Returns: (list of HeroScore, matchup_probability)
    """
    if db_path is None:
        from config import DB_PATH
        db_path = DB_PATH
    
    db_manager = DatabaseManager(db_path)
    
    scored_heroes = []
    for hero in available_heroes:
        score = calculate_hero_score(hero, enemy_picks, ally_picks, db_path)
        scored_heroes.append(score)
    
    # Sort by total score descending
    scored_heroes.sort(key=lambda x: x.total_score, reverse=True)
    
    # Calculate matchup probability
    matchup_prob = calculate_matchup_probability(ally_picks, enemy_picks, db_manager)
    
    # Return top N and probability
    return scored_heroes[:top_n], matchup_prob

# Example usage (for testing)
if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from config import DB_PATH
    
    db = DatabaseManager(DB_PATH)
    heroes = db.get_all_heroes()
    
    # Test lane recommendations
    print("=== LANE RECOMMENDATIONS ===")
    result = get_recommendations_by_lane(heroes, 
                                        enemy_picks=['Gusion', 'Lancelot'], 
                                        ally_picks=['Tigreal'], 
                                        top_n=2)
    for lane, recs in result.items():
        print(f"\n{lane}:")
        for rec in recs:
            print(f"  - {rec.name} (Score: {rec.total_score:.3f}, Lane: {rec.lane})")
    
    # Test top recommendations with probability
    print("\n=== TOP PICKS WITH MATCHUP PROBABILITY ===")
    top_picks, matchup_prob = get_top_recommendations(heroes, 
                                                      enemy_picks=['Gusion', 'Lancelot'], 
                                                      ally_picks=['Tigreal'], 
                                                      top_n=5)
    print(f"Matchup Probability: {matchup_prob:.1f}%")
    print("Top 5 Picks:")
    for i, rec in enumerate(top_picks, 1):
        print(f"  {i}. {rec.name} (Score: {rec.total_score:.3f})")
        print(f"     Breakdown: {rec.breakdown}")