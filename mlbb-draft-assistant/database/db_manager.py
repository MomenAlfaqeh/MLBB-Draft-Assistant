import sqlite3
import json
import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)

        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def initialize_db(self):
        schema_path = Path(__file__).parent / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Schema file not found at {schema_path}")

        with open(schema_path, 'r') as f:
            schema_sql = f.read()

        conn = self.connect()
        conn.executescript(schema_sql)
        conn.commit()
        self.disconnect()

    def get_all_heroes(self) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM heroes ORDER BY name")
        heroes = [dict(row) for row in cursor.fetchall()]
        self.disconnect()
        return heroes

    def get_hero_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.execute("SELECT * FROM heroes WHERE name = ?", (name,))
        row = cursor.fetchone()
        self.disconnect()
        return dict(row) if row else None

    def upsert_hero(self, hero_data: Dict[str, Any]):
        conn = self.connect()
        conn.execute("""
            INSERT INTO heroes (name, role, specialty, base_win_rate, pick_rate, ban_rate, tier, last_updated)
            VALUES (:name, :role, :specialty, :base_win_rate, :pick_rate, :ban_rate, :tier, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                role = excluded.role,
                specialty = excluded.specialty,
                base_win_rate = excluded.base_win_rate,
                pick_rate = excluded.pick_rate,
                ban_rate = excluded.ban_rate,
                tier = excluded.tier,
                last_updated = CURRENT_TIMESTAMP
        """, hero_data)
        conn.commit()
        self.disconnect()

    def get_counters(self, hero_id: int) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.execute("""
            SELECT hc.*, h.name as countered_by_name
            FROM hero_counters hc
            JOIN heroes h ON hc.countered_by_id = h.id
            WHERE hc.hero_id = ?
        """, (hero_id,))
        counters = [dict(row) for row in cursor.fetchall()]
        self.disconnect()
        return counters

    def get_synergies(self, hero_id: int) -> List[Dict[str, Any]]:
        conn = self.connect()
        cursor = conn.execute("""
            SELECT hs.*,
                   CASE
                       WHEN hs.hero_a_id = ? THEN hb.name
                       ELSE ha.name
                   END as synergy_with_name
            FROM hero_synergies hs
            JOIN heroes ha ON hs.hero_a_id = ha.id
            JOIN heroes hb ON hs.hero_b_id = hb.id
            WHERE hs.hero_a_id = ? OR hs.hero_b_id = ?
        """, (hero_id, hero_id, hero_id))
        synergies = [dict(row) for row in cursor.fetchall()]
        self.disconnect()
        return synergies

    def save_counter(self, hero_id: int, countered_by_id: int, score: float,
                     sample_size: int = None, patch: str = None):
        conn = self.connect()
        conn.execute("""
            INSERT INTO hero_counters (hero_id, countered_by_id, counter_score, sample_size, patch_date)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(hero_id, countered_by_id) DO UPDATE SET
                counter_score = excluded.counter_score,
                sample_size = excluded.sample_size,
                patch_date = excluded.patch_date
        """, (hero_id, countered_by_id, score, sample_size, patch))
        conn.commit()
        self.disconnect()

    def save_synergy(self, hero_a: int, hero_b: int, score: float,
                     combined_wr: float = None, sample_size: int = None, patch: str = None):
        conn = self.connect()
        if hero_a > hero_b:
            hero_a, hero_b = hero_b, hero_a

        conn.execute("""
            INSERT INTO hero_synergies (hero_a_id, hero_b_id, synergy_score, combined_wr, sample_size, patch_date)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(hero_a_id, hero_b_id) DO UPDATE SET
                synergy_score = excluded.synergy_score,
                combined_wr = excluded.combined_wr,
                sample_size = excluded.sample_size,
                patch_date = excluded.patch_date
        """, (hero_a, hero_b, score, combined_wr, sample_size, patch))
        conn.commit()
        self.disconnect()

    def clear_table(self, table_name: str):
        conn = self.connect()
        conn.execute(f"DELETE FROM {table_name}")
        conn.commit()
        self.disconnect()

    def bulk_insert_heroes(self, heroes: List[Dict[str, Any]]):
        conn = self.connect()
        conn.executemany("""
            INSERT OR REPLACE INTO heroes (id, name, role, specialty, base_win_rate, pick_rate, ban_rate, tier, last_updated)
            VALUES (:id, :name, :role, :specialty, :base_win_rate, :pick_rate, :ban_rate, :tier, :last_updated)
        """, heroes)
        conn.commit()
        self.disconnect()

    def bulk_insert_counters(self, counters: List[Dict[str, Any]]):
        conn = self.connect()
        conn.executemany("""
            INSERT OR REPLACE INTO hero_counters (hero_id, countered_by_id, counter_score, sample_size, patch_date)
            VALUES (:hero_id, :countered_by_id, :counter_score, :sample_size, :patch)
        """, counters)
        conn.commit()
        self.disconnect()

    def bulk_insert_synergies(self, synergies: List[Dict[str, Any]]):
        conn = self.connect()
        conn.executemany("""
            INSERT OR REPLACE INTO hero_synergies (hero_a_id, hero_b_id, synergy_score, combined_wr, sample_size, patch_date)
            VALUES (:hero_a_id, :hero_b_id, :synergy_score, :combined_wr, :sample_size, :patch)
        """, synergies)
        conn.commit()
        self.disconnect()

    def get_cache_timestamp(self) -> Optional[str]:
        conn = self.connect()
        cursor = conn.execute("SELECT last_updated FROM heroes ORDER BY last_updated DESC LIMIT 1")
        row = cursor.fetchone()
        self.disconnect()
        return row["last_updated"] if row else None


class BigQueryManager:
    def __init__(self, project_id: str, dataset: str, db_path: str = None):
        self.project_id = project_id
        self.dataset = dataset
        self.client = None
        self.sqlite = DatabaseManager(db_path or "database/mlbb.db")
        self._init_bigquery_client()

    def _init_bigquery_client(self):
        try:
            from google.cloud import bigquery
            self.client = bigquery.Client(project=self.project_id)
            logger.info(f"BigQuery client initialized for project {self.project_id}")
        except Exception as e:
            logger.warning(f"Failed to initialize BigQuery client: {e}")
            self.client = None

    def _query(self, query_str: str) -> List[Dict[str, Any]]:
        if self.client is None:
            raise ConnectionError("BigQuery client not available")
        query_job = self.client.query(query_str)
        return [dict(row) for row in query_job.result()]

    def get_all_heroes(self) -> List[Dict[str, Any]]:
        query = f"SELECT * FROM `{self.project_id}.{self.dataset}.heroes` ORDER BY name"
        return self._query(query)

    def get_hero_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        query = f"SELECT * FROM `{self.project_id}.{self.dataset}.heroes` WHERE name = @name"
        job_config = bigquery.QueryJobConfig(
            query_params=[bigquery.ScalarQueryParameter("name", "STRING", name)]
        )
        query_job = self.client.query(query, job_config=job_config)
        rows = [dict(row) for row in query_job.result()]
        return rows[0] if rows else None

    def get_counters(self, hero_id: int = None) -> List[Dict[str, Any]]:
        if hero_id is not None:
            query = f"""
                SELECT hc.*, h.name as countered_by_name
                FROM `{self.project_id}.{self.dataset}.hero_counters` hc
                JOIN `{self.project_id}.{self.dataset}.heroes` h ON hc.countered_by_id = h.id
                WHERE hc.hero_id = @hero_id
            """
            job_config = bigquery.QueryJobConfig(
                query_params=[bigquery.ScalarQueryParameter("hero_id", "INTEGER", hero_id)]
            )
        else:
            query = f"SELECT * FROM `{self.project_id}.{self.dataset}.hero_counters`"
            job_config = None

        query_job = self.client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]

    def get_synergies(self, hero_id: int = None) -> List[Dict[str, Any]]:
        if hero_id is not None:
            query = f"""
                SELECT hs.*,
                       CASE
                           WHEN hs.hero_a_id = @hero_id THEN hb.name
                           ELSE ha.name
                       END as synergy_with_name
                FROM `{self.project_id}.{self.dataset}.hero_synergies` hs
                JOIN `{self.project_id}.{self.dataset}.heroes` ha ON hs.hero_a_id = ha.id
                JOIN `{self.project_id}.{self.dataset}.heroes` hb ON hs.hero_b_id = hb.id
                WHERE hs.hero_a_id = @hero_id OR hs.hero_b_id = @hero_id
            """
            job_config = bigquery.QueryJobConfig(
                query_params=[bigquery.ScalarQueryParameter("hero_id", "INTEGER", hero_id)]
            )
        else:
            query = f"SELECT * FROM `{self.project_id}.{self.dataset}.hero_synergies`"
            job_config = None

        query_job = self.client.query(query, job_config=job_config)
        return [dict(row) for row in query_job.result()]

    def get_current_patch(self) -> Optional[Dict[str, Any]]:
        query = f"""
            SELECT * FROM `{self.project_id}.{self.dataset}.patches`
            ORDER BY release_date DESC LIMIT 1
        """
        rows = self._query(query)
        return rows[0] if rows else None

    def sync_to_sqlite(self) -> bool:
        try:
            if self.client is None:
                logger.warning("BigQuery client not available, skipping sync")
                return False

            logger.info("Syncing BigQuery data to SQLite cache...")

            heroes = self.get_all_heroes()
            self.sqlite.clear_table("heroes")
            if heroes:
                sqlite_heroes = []
                for h in heroes:
                    last_updated = h.get("last_updated")
                    if last_updated and hasattr(last_updated, "isoformat"):
                        last_updated = last_updated.isoformat()
                    sqlite_heroes.append({
                        "id": h.get("id"),
                        "name": h.get("name"),
                        "role": h.get("role"),
                        "specialty": h.get("specialty"),
                        "base_win_rate": h.get("base_win_rate"),
                        "pick_rate": h.get("pick_rate"),
                        "ban_rate": h.get("ban_rate"),
                        "tier": h.get("tier"),
                        "last_updated": last_updated or datetime.now().isoformat(),
                    })
                self.sqlite.bulk_insert_heroes(sqlite_heroes)
                logger.info(f"Synced {len(heroes)} heroes to SQLite cache")

            counters = self.get_counters()
            self.sqlite.clear_table("hero_counters")
            if counters:
                sqlite_counters = []
                for c in counters:
                    sqlite_counters.append({
                        "hero_id": c.get("hero_id"),
                        "countered_by_id": c.get("countered_by_id"),
                        "counter_score": c.get("counter_score"),
                        "sample_size": c.get("sample_size"),
                        "patch": c.get("patch"),
                    })
                self.sqlite.bulk_insert_counters(sqlite_counters)
                logger.info(f"Synced {len(counters)} counters to SQLite cache")

            synergies = self.get_synergies()
            self.sqlite.clear_table("hero_synergies")
            if synergies:
                sqlite_synergies = []
                for s in synergies:
                    sqlite_synergies.append({
                        "hero_a_id": s.get("hero_a_id"),
                        "hero_b_id": s.get("hero_b_id"),
                        "synergy_score": s.get("synergy_score"),
                        "combined_wr": s.get("combined_wr"),
                        "sample_size": s.get("sample_size"),
                        "patch": s.get("patch"),
                    })
                self.sqlite.bulk_insert_synergies(sqlite_synergies)
                logger.info(f"Synced {len(synergies)} synergies to SQLite cache")

            return True

        except Exception as e:
            logger.error(f"Failed to sync BigQuery to SQLite: {e}")
            return False

    def is_cache_fresh(self, expiry_hours: int = 24) -> bool:
        timestamp = self.sqlite.get_cache_timestamp()
        if not timestamp:
            return False
        try:
            if isinstance(timestamp, str):
                if "T" in timestamp:
                    cache_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                    if cache_time.tzinfo:
                        cache_time = cache_time.replace(tzinfo=None)
                else:
                    cache_time = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            else:
                cache_time = timestamp

            expiry = timedelta(hours=expiry_hours)
            return (datetime.now() - cache_time) < expiry
        except Exception:
            return False

    def get_data(self) -> Dict[str, List[Dict[str, Any]]]:
        if self.client is not None:
            try:
                if not self.is_cache_fresh():
                    self.sync_to_sqlite()
                else:
                    logger.info("Using fresh SQLite cache")
            except Exception as e:
                logger.warning(f"BigQuery sync failed, falling back to cache: {e}")
        return {
            "heroes": self.sqlite.get_all_heroes(),
        }


try:
    from google.cloud import bigquery
except ImportError:
    bigquery = None
