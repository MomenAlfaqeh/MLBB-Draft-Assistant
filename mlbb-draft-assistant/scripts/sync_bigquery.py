#!/usr/bin/env python3
"""
Sync BigQuery data to SQLite database.
This script is designed to run in GitHub Actions with Google credentials from environment variables.
"""

import os
import sys
import base64
import tempfile

# Load Google credentials from environment variable
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
        sys.exit(1)
else:
    print("GOOGLE_APPLICATION_CREDENTIALS_JSON not set")
    sys.exit(1)

# Add mlbb-draft-assistant directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from database.db_manager import BigQueryManager
from config import BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, DB_PATH

def main():
    print(f"Starting BigQuery sync to SQLite...")
    print(f"Project ID: {BIGQUERY_PROJECT_ID}")
    print(f"Dataset: {BIGQUERY_DATASET}")
    print(f"SQLite DB: {DB_PATH}")

    bq_manager = BigQueryManager(BIGQUERY_PROJECT_ID, BIGQUERY_DATASET, DB_PATH)

    if bq_manager.client is None:
        print("Failed to initialize BigQuery client")
        sys.exit(1)

    success = bq_manager.sync_to_sqlite()

    if success:
        print("Sync completed successfully")
        # Verify the database was created/updated
        if os.path.exists(DB_PATH):
            print(f"SQLite database exists at {DB_PATH}")
        else:
            print(f"Warning: SQLite database not found at {DB_PATH}")
    else:
        print("Sync failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
