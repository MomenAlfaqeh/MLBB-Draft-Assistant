import pytest
import tempfile
import os
import sys

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from data_pipeline.scraper import HeroScraper
from database.db_manager import DatabaseManager

def test_scrape_win_rates_returns_10_heroes():
    """Test that scrape_win_rates returns 10 heroes"""
    scraper = HeroScraper()
    heroes = scraper.scrape_win_rates()
    
    # Assert we got 10 heroes
    assert len(heroes) == 10
    
    # Assert each hero has required fields
    for hero in heroes:
        assert "name" in hero
        assert "role" in hero
        assert "base_win_rate" in hero
        assert isinstance(hero["base_win_rate"], (int, float))
        assert 0.0 <= hero["base_win_rate"] <= 1.0

def test_run_full_scrape_saves_to_db():
    """Test that run_full_scrape saves heroes to the database"""
    # Create a temporary database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
        db_path = tmp_file.name
    
    try:
        # Create scraper with temporary database
        scraper = HeroScraper(db_path)
        
        # Run full scrape
        scraper.run_full_scrape()
        
        # Check that heroes were saved to database
        db_manager = DatabaseManager(db_path)
        heroes = db_manager.get_all_heroes()
        
        # Assert we got 10 heroes
        assert len(heroes) == 10
        
        # Assert hero names match what we expect from mock data
        hero_names = [hero["name"] for hero in heroes]
        expected_names = [
            "Gatotkaca", "Franco", "Alucard", "Hayabusa", "Harley",
            "Lyla", "Claude", "Karrie", "Rafaela", "Estes"
        ]
        
        for name in expected_names:
            assert name in hero_names
        
    finally:
        # Clean up temporary file
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    pytest.main([__file__])