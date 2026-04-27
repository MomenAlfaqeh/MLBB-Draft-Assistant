import pytest
import tempfile
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from scoring_engine.scorer import calculate_hero_score, get_top_recommendations, HeroScore
from database.db_manager import DatabaseManager

def test_calculate_hero_score_returns_valid_range():
    """Test that calculate_hero_score returns a score between 0 and 1"""
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Initialize database with schema
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_db()
        
        # Add a test hero
        test_hero = {
            "name": "Test Hero",
            "role": "Tank",
            "specialty": "Testing",
            "base_win_rate": 0.55,
            "pick_rate": 0.1,
            "ban_rate": 0.05,
            "tier": "B"
        }
        db_manager.upsert_hero(test_hero)
        
        # Test candidate hero
        candidate = {"name": "Test Hero", "role": "Tank", "base_win_rate": 0.55}
        
        # Calculate score with empty enemy and ally picks
        score = calculate_hero_score(candidate, [], [], db_path)
        
        # Assert score is between 0 and 1
        assert 0.0 <= score.total_score <= 1.0
        assert isinstance(score, HeroScore)
        assert score.name == "Test Hero"
        assert "meta_wr" in score.breakdown
        assert "counter_score" in score.breakdown
        assert "synergy_score" in score.breakdown
        assert "comp_bonus" in score.breakdown
        
    finally:
        # Clean up temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_get_top_recommendations_returns_correct_count():
    """Test that get_top_recommendations returns the correct number of recommendations"""
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Initialize database with schema
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_db()
        
        # Add test heroes
        test_heroes = [
            {
                "name": "Hero1",
                "role": "Tank",
                "specialty": "Testing",
                "base_win_rate": 0.55,
                "pick_rate": 0.1,
                "ban_rate": 0.05,
                "tier": "B"
            },
            {
                "name": "Hero2",
                "role": "Fighter",
                "specialty": "Testing",
                "base_win_rate": 0.50,
                "pick_rate": 0.1,
                "ban_rate": 0.05,
                "tier": "B"
            },
            {
                "name": "Hero3",
                "role": "Mage",
                "specialty": "Testing",
                "base_win_rate": 0.48,
                "pick_rate": 0.1,
                "ban_rate": 0.05,
                "tier": "B"
            }
        ]
        
        for hero in test_heroes:
            db_manager.upsert_hero(hero)
        
        # Available heroes
        available_heroes = db_manager.get_all_heroes()
        
        # Get top 2 recommendations
        recommendations = get_top_recommendations(
            available_heroes=available_heroes,
            enemy_picks=[],
            ally_picks=[],
            top_n=2
        )
        
        # Assert we got exactly 2 recommendations
        assert len(recommendations) == 2
        
        # Assert they are sorted by score descending
        assert recommendations[0].total_score >= recommendations[1].total_score
        
    finally:
        # Clean up temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)

def test_hero_score_breakdown_has_all_keys():
    """Test that HeroScore breakdown contains all expected keys"""
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Initialize database with schema
        db_manager = DatabaseManager(db_path)
        db_manager.initialize_db()
        
        # Add a test hero
        test_hero = {
            "name": "Test Hero",
            "role": "Tank",
            "specialty": "Testing",
            "base_win_rate": 0.55,
            "pick_rate": 0.1,
            "ban_rate": 0.05,
            "tier": "B"
        }
        db_manager.upsert_hero(test_hero)
        
        # Test candidate hero
        candidate = {"name": "Test Hero", "role": "Tank", "base_win_rate": 0.55}
        
        # Calculate score
        score = calculate_hero_score(candidate, [], [], db_path)
        
        # Assert breakdown has all expected keys
        expected_keys = {"meta_wr", "counter_score", "synergy_score", "comp_bonus"}
        assert set(score.breakdown.keys()) == expected_keys
        
        # Assert all values are floats
        for key, value in score.breakdown.items():
            assert isinstance(value, (int, float))
        
    finally:
        # Clean up temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    pytest.main([__file__])