from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import DatabaseManager, BigQueryManager
from config import SCORING_WEIGHTS, ROLE_LIST, BAYESIAN_PRIOR, GLOBAL_AVG_WR

LANE_MAPPING = {
    "EXP Lane": ["Fighter", "Tank"],
    "Jungle": ["Assassin"],
    "Mid": ["Mage"],
    "Gold Lane": ["Marksman"],
    "Roam/Utility": ["Support", "Tank"],
}

JUNGLE_FIGHTERS = ["Lancelot", "Gusion", "Fanny", "Hayabusa", "Ling", "Joy", "Julian", "Yin", "Benedetta", "Zilong"]

@dataclass
class HeroScore:
    hero_id: int
    name: str
    total_score: float
    breakdown: Dict[str, float]
    lane: str = "Flex"

def get_hero_lane(hero_name: str, role: str) -> str:
    if role == "Assassin" or hero_name in JUNGLE_FIGHTERS:
        return "Jungle"
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


def bayesian_win_rate(win_rate: float, sample_size: int, prior: int = BAYESIAN_PRIOR, global_avg: float = GLOBAL_AVG_WR) -> float:
    if sample_size is None or sample_size <= 0:
        sample_size = 100
    return (win_rate * sample_size + global_avg * prior) / (sample_size + prior)


def calculate_counter_advantage(ally_picks: List[Dict[str, Any]], enemy_picks: List[Dict[str, Any]], db) -> float:
    if not ally_picks or not enemy_picks:
        return 0.0

    total_advantage = 0.0
    count = 0

    for ally in ally_picks:
        if isinstance(ally, str):
            ally_hero = db.get_hero_by_name(ally)
        else:
            ally_hero = ally
        if not ally_hero:
            continue

        for enemy in enemy_picks:
            if isinstance(enemy, str):
                enemy_hero = db.get_hero_by_name(enemy)
            else:
                enemy_hero = enemy
            if not enemy_hero:
                continue

            counters = db.get_counters(enemy_hero["id"])
            for counter in counters:
                if counter["countered_by_id"] == ally_hero["id"]:
                    total_advantage += counter["counter_score"]
                    count += 1
                    break

    return total_advantage / max(count, 1)


def calculate_synergy_bonus(picks: List[Dict[str, Any]], db) -> float:
    if len(picks) < 2:
        return 0.0

    total_synergy = 0.0
    count = 0

    pick_heroes = []
    for p in picks:
        if isinstance(p, str):
            hero = db.get_hero_by_name(p)
        else:
            hero = p
        if hero:
            pick_heroes.append(hero)

    for i, hero_a in enumerate(pick_heroes):
        for hero_b in pick_heroes[i+1:]:
            synergies = db.get_synergies(hero_a["id"])
            for synergy in synergies:
                if (synergy["hero_a_id"] == hero_b["id"] and synergy["hero_b_id"] == hero_a["id"]) or \
                   (synergy["hero_b_id"] == hero_b["id"] and synergy["hero_a_id"] == hero_a["id"]):
                    total_synergy += synergy["synergy_score"]
                    count += 1
                    break

    return total_synergy / max(count, 1)


def calculate_elo_win_probability(ally_picks: List[str], enemy_picks: List[str], db) -> float:
    ally_heroes = []
    for name in ally_picks:
        hero = db.get_hero_by_name(name)
        if hero:
            ally_heroes.append(hero)

    enemy_heroes = []
    for name in enemy_picks:
        hero = db.get_hero_by_name(name)
        if hero:
            enemy_heroes.append(hero)

    ally_strength = sum(h["base_win_rate"] for h in ally_heroes) / len(ally_heroes) if ally_heroes else 0.5
    enemy_strength = sum(h["base_win_rate"] for h in enemy_heroes) / len(enemy_heroes) if enemy_heroes else 0.5

    counter_advantage = calculate_counter_advantage(ally_heroes, enemy_heroes, db)
    synergy_bonus = calculate_synergy_bonus(ally_heroes, db)

    ally_elo = (ally_strength * 400) + (counter_advantage * 50) + (synergy_bonus * 30)
    enemy_elo = enemy_strength * 400

    win_prob = 1 / (1 + 10 ** ((enemy_elo - ally_elo) / 400))
    return round(win_prob * 100, 1)


def calculate_hero_score(candidate: Dict[str, Any],
                        enemy_picks: List[str],
                        ally_picks: List[str],
                        db = None) -> HeroScore:
    if db is None:
        from config import DB_PATH
        db = DatabaseManager(DB_PATH)

    hero = db.get_hero_by_name(candidate["name"])
    if not hero:
        hero_id = candidate.get("id", 0)
        base_win_rate = candidate.get("base_win_rate", 0.5)
        role = candidate.get("role", "Unknown")
        sample_size = candidate.get("sample_size", 100)
    else:
        hero_id = hero["id"]
        base_win_rate = hero["base_win_rate"]
        role = hero["role"]
        sample_size = hero.get("sample_size", 100)

    lane = get_hero_lane(candidate["name"], role)

    bayesian_wr = bayesian_win_rate(base_win_rate, sample_size)
    meta_wr_score = (bayesian_wr - 0.4) / 0.2
    meta_wr_score = max(0.0, min(1.0, meta_wr_score))

    counter_score = 0.0
    if enemy_picks:
        total_counter = 0.0
        valid_enemies = 0
        for enemy_name in enemy_picks:
            enemy_hero = db.get_hero_by_name(enemy_name)
            if enemy_hero:
                counters = db.get_counters(enemy_hero["id"])
                for counter in counters:
                    if counter["countered_by_id"] == hero_id:
                        total_counter += counter["counter_score"]
                        valid_enemies += 1
                        break
        if valid_enemies > 0:
            counter_score = total_counter / valid_enemies

    synergy_score = 0.0
    if ally_picks:
        total_synergy = 0.0
        valid_allies = 0
        for ally_name in ally_picks:
            ally_hero = db.get_hero_by_name(ally_name)
            if ally_hero:
                synergies = db.get_synergies(ally_hero["id"])
                for synergy in synergies:
                    if (synergy["hero_a_id"] == hero_id and synergy["hero_b_id"] == ally_hero["id"]) or \
                       (synergy["hero_b_id"] == hero_id and synergy["hero_a_id"] == ally_hero["id"]):
                        total_synergy += synergy["synergy_score"]
                        valid_allies += 1
                        break
        if valid_allies > 0:
            synergy_score = total_synergy / valid_allies

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
        ally_hero = db.get_hero_by_name(ally_name)
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


def get_recommendations_by_lane(available_heroes: List[Dict[str, Any]],
                                enemy_picks: List[str],
                                ally_picks: List[str],
                                top_n: int = 2,
                                db = None) -> Dict[str, Any]:
    if db is None:
        from config import DB_PATH
        db = DatabaseManager(DB_PATH)

    scored_heroes = []
    for hero in available_heroes:
        score = calculate_hero_score(hero, enemy_picks, ally_picks, db)
        scored_heroes.append(score)

    lane_recommendations = {lane: [] for lane in LANE_MAPPING.keys()}

    for score in scored_heroes:
        lane = score.lane
        if lane in lane_recommendations:
            lane_recommendations[lane].append(score)

    for lane in lane_recommendations:
        lane_recommendations[lane].sort(key=lambda x: x.total_score, reverse=True)
        lane_recommendations[lane] = lane_recommendations[lane][:top_n]

    result = {}
    for lane, recs in lane_recommendations.items():
        result[lane] = []
        for rec in recs:
            result[lane].append({
                "hero_id": rec.hero_id,
                "name": rec.name,
                "total_score": rec.total_score,
                "lane": rec.lane,
                "breakdown": rec.breakdown
            })

    return {"lane_recommendations": result}


def get_top_recommendations(available_heroes: List[Dict[str, Any]],
                           enemy_picks: List[str],
                           ally_picks: List[str],
                           top_n: int = 5,
                           db = None) -> Tuple[List[HeroScore], float]:
    if db is None:
        from config import DB_PATH
        db = DatabaseManager(DB_PATH)

    scored_heroes = []
    for hero in available_heroes:
        score = calculate_hero_score(hero, enemy_picks, ally_picks, db)
        scored_heroes.append(score)

    scored_heroes.sort(key=lambda x: x.total_score, reverse=True)

    matchup_prob = calculate_elo_win_probability(ally_picks, enemy_picks, db)

    return scored_heroes[:top_n], matchup_prob


if __name__ == "__main__":
    from database.db_manager import DatabaseManager
    from config import DB_PATH

    db = DatabaseManager(DB_PATH)
    heroes = db.get_all_heroes()

    print("=== LANE RECOMMENDATIONS ===")
    result = get_recommendations_by_lane(heroes,
                                        enemy_picks=['Gusion', 'Lancelot'],
                                        ally_picks=['Tigreal'],
                                        top_n=2)
    for lane, recs in result["lane_recommendations"].items():
        print(f"\n{lane}:")
        for rec in recs:
            print(f"  - {rec['name']} (Score: {rec['total_score']:.3f}, Lane: {rec['lane']})")

    print("\n=== TOP PICKS WITH ELO PROBABILITY ===")
    top_picks, matchup_prob = get_top_recommendations(heroes,
                                                       enemy_picks=['Gusion', 'Lancelot'],
                                                       ally_picks=['Tigreal'],
                                                       top_n=5)
    print(f"ELO Win Probability: {matchup_prob:.1f}%")
    print("Top 5 Picks:")
    for i, rec in enumerate(top_picks, 1):
        print(f"  {i}. {rec.name} (Score: {rec.total_score:.3f})")
        print(f"     Breakdown: {rec.breakdown}")
