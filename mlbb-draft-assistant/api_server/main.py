import os
import base64
import tempfile

creds_b64 = os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
if creds_b64:
    try:
        creds_json = base64.b64decode(creds_b64).decode()
        tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        tmp.write(creds_json)
        tmp.close()
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = tmp.name
        print("Google credentials loaded from environment")
    except Exception as e:
        print(f"Failed to load credentials: {e}")

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
import uvicorn
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from database.db_manager import DatabaseManager, BigQueryManager
from config import DB_PATH, SERVER_HOST, SERVER_PORT, BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, CACHE_EXPIRY_HOURS
from api_server.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    db_manager = DatabaseManager(DB_PATH)
    db_manager.initialize_db()

    bq_manager = BigQueryManager(BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, DB_PATH)

    if bq_manager.client is not None:
        if not bq_manager.is_cache_fresh(CACHE_EXPIRY_HOURS):
            print("Cache expired or empty. Syncing from BigQuery...")
            success = bq_manager.sync_to_sqlite()
            if success:
                print("BigQuery sync completed successfully")
            else:
                print("BigQuery sync failed, using existing SQLite cache")
        else:
            print("SQLite cache is fresh, skipping BigQuery sync")
    else:
        print("BigQuery client unavailable, using SQLite cache")

    heroes = db_manager.get_all_heroes()
    print(f"Database contains {len(heroes)} heroes")

    yield

    # Shutdown (if needed)
    pass

app = FastAPI(
    title="MLBB AI Draft Assistant",
    description="API for Mobile Legends: Bang Bang AI Draft Assistant",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="api_server/static"), name="static")

app.include_router(router)

@app.get("/")
async def root():
    static_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
    return FileResponse(static_path)

if __name__ == "__main__":
    uvicorn.run(app, host=SERVER_HOST, port=SERVER_PORT)
