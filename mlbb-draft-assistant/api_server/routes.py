from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import BigQueryManager
from scoring_engine.scorer import get_top_recommendations, get_recommendations_by_lane, calculate_elo_win_probability
from vision_engine.hero_detector import HeroDetector
from config import BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, DB_PATH, SERVER_HOST, SERVER_PORT

router = APIRouter()

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

bq_manager = BigQueryManager(BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, DB_PATH)
hero_detector = HeroDetector()


def get_db():
    heroes = bq_manager.sqlite.get_all_heroes()
    if not heroes:
        try:
            bq_manager.sync_to_sqlite()
            heroes = bq_manager.sqlite.get_all_heroes()
        except Exception:
            pass
    return bq_manager.sqlite, heroes


@router.get("/health")
async def health_check():
    bq_available = bq_manager.client is not None
    cache_fresh = bq_manager.is_cache_fresh()
    return {
        "status": "ok",
        "version": "2.0.0",
        "bigquery_connected": bq_available,
        "cache_fresh": cache_fresh
    }

@router.get("/heroes", response_model=List[Dict[str, Any]])
async def get_heroes():
    try:
        db, heroes = get_db()
        return heroes
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve heroes: {str(e)}"
        )

@router.get("/heroes/{name}", response_model=Dict[str, Any])
async def get_hero(name: str):
    try:
        db, _ = get_db()
        hero = db.get_hero_by_name(name)
        if not hero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Hero '{name}' not found"
            )

        counters = db.get_counters(hero["id"])
        synergies = db.get_synergies(hero["id"])

        return {
            "hero": hero,
            "counters": counters,
            "synergies": synergies
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve hero details: {str(e)}"
        )

@router.get("/patch/current", response_model=Dict[str, Any])
async def get_current_patch():
    try:
        patch_info = bq_manager.get_current_patch()
        if not patch_info:
            return {"patch": None, "message": "No patch information available"}

        return {
            "patch": patch_info,
            "cache_fresh": bq_manager.is_cache_fresh()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve patch info: {str(e)}"
        )

@router.post("/draft/update", response_model=Dict[str, Any])
async def draft_update(request: DraftRequest):
    try:
        db, all_heroes = get_db()

        banned_set = set(request.banned)
        available_heroes = [h for h in all_heroes if h["name"] not in banned_set]

        top_picks, matchup_prob = get_top_recommendations(
            available_heroes=available_heroes,
            enemy_picks=request.enemy_picks,
            ally_picks=request.ally_picks,
            top_n=5,
            db=db
        )

        lane_recs = get_recommendations_by_lane(
            available_heroes=available_heroes,
            enemy_picks=request.enemy_picks,
            ally_picks=request.ally_picks,
            top_n=2,
            db=db
        )

        top_picks_result = []
        for rec in top_picks:
            top_picks_result.append({
                "hero_id": rec.hero_id,
                "name": rec.name,
                "total_score": rec.total_score,
                "lane": rec.lane,
                "breakdown": rec.breakdown
            })

        return {
            "top_picks": top_picks_result,
            "lane_recommendations": lane_recs["lane_recommendations"],
            "matchup_probability": matchup_prob,
            "scoring_method": "bayesian_elo"
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}"
        )

@router.post("/analyze")
async def analyze_screenshot(request: AnalyzeRequest):
    try:
        # 1. Detect heroes from the screenshot using the Vision Engine
        draft_result = hero_detector.detect_draft(request.screenshot_b64)
        
        # 2. Clean up the lists (remove None values if a slot is empty)
        ally_picks =[h for h in draft_result.get("ally_picks", []) if h is not None]
        enemy_picks = [h for h in draft_result.get("enemy_picks", []) if h is not None]
        
        print(f"🎯 Vision Detected - Allies: {ally_picks} | Enemies: {enemy_picks}")

        # 3. Get recommendations and win probability from the Scoring Engine
        db, all_heroes = get_db()
        
        # Get the top 1 recommendation per lane to fit the Android UI
        lane_recs = get_recommendations_by_lane(
            available_heroes=all_heroes,
            enemy_picks=enemy_picks,
            ally_picks=ally_picks,
            top_n=1,
            db=db
        )
        
        # Get overall win probability
        _, matchup_prob = get_top_recommendations(
            available_heroes=all_heroes,
            enemy_picks=enemy_picks,
            ally_picks=ally_picks,
            top_n=1, 
            db=db
        )

        # 4. Format the recommendations string with newlines for the Android Overlay
        recs_dict = lane_recs.get("lane_recommendations", {})
        recs_text =[]
        for lane, picks in recs_dict.items():
            if picks:
                top_hero = picks[0].name
                recs_text.append(f"{lane.upper()}: {top_hero}")
        
        final_recs_string = "\n".join(recs_text) if recs_text else "Awaiting draft..."

        # 5. Return exact JSON format expected by the Android app
        return {
            "win_probability": matchup_prob,
            "recommendations": final_recs_string
        }

    except Exception as e:
        print(f"Analysis error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze screenshot: {str(e)}"
        )

        detections = {"ally": [], "enemy": []}

        db, all_heroes = get_db()

        recommendations = get_top_recommendations(
            available_heroes=all_heroes,
            enemy_picks=detections["enemy"],
            ally_picks=detections["ally"],
            top_n=5,
            db=db
        )

        result = []
        for rec in recommendations[0]:
            result.append({
                "hero_id": rec.hero_id,
                "name": rec.name,
                "total_score": rec.total_score,
                "breakdown": rec.breakdown
            })

        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze screenshot: {str(e)}"
        )

# Android app endpoints
@router.get("/api/recommendations")
async def get_recommendations():
    try:
        db, all_heroes = get_db()

        top_picks, matchup_prob = get_top_recommendations(
            available_heroes=all_heroes,
            enemy_picks=[],
            ally_picks=[],
            top_n=5,
            db=db
        )

        recommendations = []
        for rec in top_picks:
            recommendations.append({
                "hero": rec.name,
                "lane": rec.lane,
                "confidence": int(rec.total_score * 100),
                "winRate": rec.total_score
            })

        return recommendations
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendations: {str(e)}"
        )

@router.post("/api/analyze-screenshot")
async def analyze_screenshot_android(request: AnalyzeRequest):
    try:
        img_bytes = hero_detector.decode_base64_image(request.screenshot_b64)
        if img_bytes is None or img_bytes.size == 0:
            return {"allies": [], "enemies": [], "currentTurn": "", "isComplete": False}

        draft_result = hero_detector.detect_draft(request.screenshot_b64)

        return {
            "allies": draft_result.get("ally_picks", []),
            "enemies": draft_result.get("enemy_picks", []),
            "currentTurn": "ally",
            "isComplete": False
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze screenshot: {str(e)}"
        )
