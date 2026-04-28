from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import DatabaseManager
from scoring_engine.scorer import get_top_recommendations, get_recommendations_by_lane, HeroScore
from vision_engine.hero_detector import HeroDetector
from config import DB_PATH, SERVER_HOST, SERVER_PORT

router = APIRouter()

# Pydantic models for request/response
class DraftRequest(BaseModel):
    ally_picks: List[str]
    enemy_picks: List[str]
    banned: List[str] = []

class AnalyzeRequest(BaseModel):
    screenshot_b64: str

class HeroResponse(BaseModel):
    hero_id: int
    name: str
    total_score: float
    breakdown: Dict[str, float]

# Initialize components
db_manager = DatabaseManager(DB_PATH)
hero_detector = HeroDetector()

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "version": "1.0.0"}

@router.get("/heroes", response_model=List[Dict[str, Any]])
async def get_heroes():
    """Get all heroes from the database"""
    try:
        heroes = db_manager.get_all_heroes()
        return heroes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve heroes: {str(e)}"
        )

@router.post("/draft/update", response_model=Dict[str, Any])
async def draft_update(request: DraftRequest):
    """Get hero recommendations based on current draft state"""
    try:
        # Get all available heroes (excluding banned picks)
        all_heroes = db_manager.get_all_heroes()
        banned_set = set(request.banned)
        available_heroes = [h for h in all_heroes if h["name"] not in banned_set]
        
        # Get top recommendations with matchup probability
        top_picks, matchup_prob = get_top_recommendations(
            available_heroes=available_heroes,
            enemy_picks=request.enemy_picks,
            ally_picks=request.ally_picks,
            top_n=5
        )
        
        # Get lane-based recommendations
        lane_recs = get_recommendations_by_lane(
            available_heroes=available_heroes,
            enemy_picks=request.enemy_picks,
            ally_picks=request.ally_picks,
            top_n=2
        )
        
        # Convert HeroScore objects to dictionaries for response
        top_picks_result = []
        for rec in top_picks:
            top_picks_result.append({
                "hero_id": rec.hero_id,
                "name": rec.name,
                "total_score": rec.total_score,
                "lane": rec.lane,
                "breakdown": rec.breakdown
            })
        
        # Convert lane recommendations to dict format
        lane_result = {}
        for lane, recs in lane_recs.items():
            lane_result[lane] = []
            for rec in recs:
                lane_result[lane].append({
                    "hero_id": rec.hero_id,
                    "name": rec.name,
                    "total_score": rec.total_score,
                    "lane": rec.lane,
                    "breakdown": rec.breakdown
                })
        
        return {
            "top_picks": top_picks_result,
            "lane_recommendations": lane_result,
            "matchup_probability": matchup_prob
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.post("/analyze", response_model=List[HeroResponse])
async def analyze_screenshot(request: AnalyzeRequest):
    """Analyze a screenshot and return hero recommendations"""
    try:
        # Decode the base64 image
        img_bytes = hero_detector.decode_base64_image(request.screenshot_b64)
        if img_bytes is None or img_bytes.size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid image data"
            )
        
        # Process the screenshot to detect heroes
        # For now, we'll use empty lists since hero detection from screenshot is not fully implemented
        # In a real implementation, this would call hero_detector.process_screenshot()
        detections = {"ally": [], "enemy": []}
        
        # Get all available heroes
        all_heroes = db_manager.get_all_heroes()
        
        # Get top recommendations based on detected heroes
        recommendations = get_top_recommendations(
            available_heroes=all_heroes,
            enemy_picks=detections["enemy"],
            ally_picks=detections["ally"],
            top_n=5
        )
        
        # Convert HeroScore objects to dictionaries for response
        result = []
        for rec in recommendations:
            result.append({
                "hero_id": rec.hero_id,
                "name": rec.name,
                "total_score": rec.total_score,
                "breakdown": rec.breakdown
            })
        
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze screenshot: {str(e)}"
        )