import json
import time
import sqlite3
import os
from functools import wraps
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from .config import DATABASE_URL

# Database Engine — supports both PostgreSQL (production) and SQLite (testing)
_engine_kwargs = {"pool_pre_ping": True}
if DATABASE_URL.startswith("sqlite"):
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs.update(pool_size=2, max_overflow=3, pool_recycle=120)

engine = create_engine(DATABASE_URL, **_engine_kwargs)

# SQLite Connection (Employment Data)
# Assuming it's in a known path relative to the project
SQLITE_DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../uraba_empleos/empleos_uraba.db"))

def get_sqlite_conn():
    """Returns a connection to the jobs SQLite database, or None if unavailable."""
    if not os.path.exists(SQLITE_DB_PATH):
        return None
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

_cache = {}

def cached(ttl_seconds: int = 600):
    """Simple in-memory TTL cache decorator for endpoint functions."""
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Create a cache key from function name and arguments
            key = (fn.__name__, args, tuple(sorted(kwargs.items())))
            entry = _cache.get(key)
            if entry and time.time() - entry[0] < ttl_seconds:
                return entry[1]
            result = fn(*args, **kwargs)
            _cache[key] = (time.time(), result)
            return result
        return wrapper
    return decorator

SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def query_dicts(sql: str, params: dict = None) -> list[dict]:
    """Execute SQL once and return list of dicts."""
    with engine.connect() as conn:
        result = conn.execute(text(sql), params or {})
        if result.returns_rows:
            columns = list(result.keys())
            return [dict(zip(columns, row)) for row in result.fetchall()]
        return []


def query_dicts_batch(queries: list[tuple[str, dict | None]]) -> list[list[dict]]:
    """Execute multiple SQL queries on a single connection, returning a list of results.

    Each item in *queries* is a (sql, params) tuple.
    Returns a list of list[dict] in the same order.
    This avoids opening multiple connections from the pool, which can
    exhaust Vercel serverless connection limits.
    Uses SAVEPOINTs so a failed query doesn't abort the transaction for
    subsequent queries.
    """
    results: list[list[dict]] = []
    with engine.connect() as conn:
        for i, (sql, params) in enumerate(queries):
            try:
                conn.execute(text(f"SAVEPOINT sp_{i}"))
                result = conn.execute(text(sql), params or {})
                if result.returns_rows:
                    columns = list(result.keys())
                    results.append([dict(zip(columns, row)) for row in result.fetchall()])
                else:
                    results.append([])
                conn.execute(text(f"RELEASE SAVEPOINT sp_{i}"))
            except Exception:
                results.append([])
                try:
                    conn.execute(text(f"ROLLBACK TO SAVEPOINT sp_{i}"))
                except Exception:
                    pass
    return results

def query_geojson(sql: str, params: dict = None, geom_col: str = "geom") -> dict:
    """Execute SQL and return a GeoJSON FeatureCollection built server-side
    by PostGIS. *geom_col* must match the geometry column name in the query."""
    wrapped = f"""
        SELECT json_build_object(
            'type', 'FeatureCollection',
            'features', COALESCE(json_agg(
                json_build_object(
                    'type', 'Feature',
                    'geometry', ST_AsGeoJSON(sub.{geom_col})::json,
                    'properties', to_jsonb(sub) - '{geom_col}'
                )
            ), '[]'::json)
        ) AS fc
        FROM ({sql}) sub
    """
    with engine.connect() as conn:
        row = conn.execute(text(wrapped), params or {}).fetchone()
    return row[0] if row and row[0] else {"type": "FeatureCollection", "features": []}
