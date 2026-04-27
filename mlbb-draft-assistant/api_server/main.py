from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import sys
import os

# Add project root to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import DatabaseManager
from data_pipeline.scraper import HeroScraper
from config import DB_PATH, SERVER_HOST, SERVER_PORT
from api_server.routes import router

# Create FastAPI app
app = FastAPI(
    title="MLBB AI Draft Assistant",
    description="API for Mobile Legends: Bang Bang AI Draft Assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost", "http://127.0.0.1", "http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include router
app.include_router(router)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and run initial scrape if needed"""
    # Initialize database
    db_manager = DatabaseManager(DB_PATH)
    db_manager.initialize_db()
    
    # Check if we have any heroes in the database
    heroes = db_manager.get_all_heroes()
    if len(heroes) == 0:
        print("No heroes found in database. Running initial scrape...")
        scraper = HeroScraper(DB_PATH)
        scraper.run_full_scrape()
    else:
        print(f"Database already contains {len(heroes)} heroes. Skipping initial scrape.")

# Root endpoint
@app.get("/")
async def root():
    return {"message": "MLBB AI Draft Assistant API", "version": "1.0.0"}

# Run the application
if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)