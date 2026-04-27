# MLBB AI Draft Assistant

An AI-powered assistant for Mobile Legends: Bang Bang (MLBB) draft phase that provides hero recommendations based on meta data, counter-picks, synergies, and team composition.

## Architecture Diagram

```
Android Overlay App
        ↓ (HTTP POST /analyze)
FastAPI Server (localhost:8080)
        ↓
┌─────────────────────────────────────┐
│           API Server                │
│  ├─ GET /health                     │
│  ├─ GET /heroes                     │
│  ├─ POST /draft/update              │
│  └─ POST /analyze                   │
└─────────────────────┬───────────────┘
                      ↓
┌─────────────────────┴───────────────┐
│         Core Engines                │
│  ├─ Scoring Engine                  │
│  │  ├─ scorer.py                     │
│  │  ├─ counter_logic.py              │
│  │  └─ synergy_logic.py              │
│  ├─ Vision Engine                   │
│  │  ├─ template_matcher.py           │
│  │  ├─ screen_capture.py             │
│  │  └─ hero_detector.py              │
│  └─ Database Layer                  │
│     ├─ db_manager.py                │
│     └─ schema.sql                   │
└─────────────────────┬───────────────┘
                      ↓
┌─────────────────────┴───────────────┐
│       Data Pipeline                 │
│  ├─ scraper.py                      │
│  ├─ cleaner.py                      │
│  └─ scheduler.py                    │
└─────────────────────────────────────┘
                      ↓
              SQLite Database
                    (mlbb.db)
```

## Setup Instructions

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Initialize database and scrape initial data**:
   ```bash
   python -c "from data_pipeline.scraper import HeroScraper; HeroScraper().run_full_scrape()"
   ```

3. **Run the server**:
   ```bash
   python -m uvicorn api_server.main:app --host localhost --port 8080
   ```

4. **Run tests**:
   ```bash
   pytest tests/ -v
   ```

## API Endpoints

| Method | Endpoint         | Description                                     |
|--------|------------------|-------------------------------------------------|
| GET    | `/health`        | Health check                                    |
| GET    | `/heroes`        | Get all heroes from database                    |
| POST   | `/draft/update`  | Get recommendations based on current draft state|
| POST   | `/analyze`       | Analyze screenshot and return recommendations   |

## Configuration

Modify `config.py` to adjust:
- Database path
- Server host and port
- Vision engine settings
- Scraping sources
- Scoring algorithm weights

## Development Notes

- The vision engine components are scaffolded and require hero icon images in `vision_engine/hero_icons/`
- The scraper currently uses mock data; implement actual web scraping for production
- For Android deployment, see `android_app/README_android.md` for Termux setup instructions

## Future Enhancements

- Implement actual web scraping from MLBB.gg and Liquipedia
- Add real template matching with hero icons
- Implement screen capture for automatic draft detection
- Add caching layer for improved performance
- Implement user feedback loop to improve recommendations