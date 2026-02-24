"""
Shared fixtures for the Observatorio Laboral test suite.
Uses a SQLite in-memory database to avoid depending on PostgreSQL.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Set env before importing app modules
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SENTRY_DSN"] = ""
os.environ["RATE_LIMIT_RPM"] = "10000"  # Effectively disable rate limiting in tests
os.environ["RATE_LIMIT_BPS"] = "10000"


@pytest.fixture()
def mock_query_dicts():
    """Patch query_dicts everywhere it's imported."""
    with patch("src.backend.database.query_dicts") as db_mock, \
         patch("src.backend.routers.empleo.query_dicts", db_mock), \
         patch("src.backend.routers.analytics.query_dicts", db_mock):
        yield db_mock


@pytest.fixture()
def mock_engine():
    """Patch the SQLAlchemy engine so no real DB connection is attempted."""
    with patch("src.backend.database.engine") as mock:
        yield mock


@pytest.fixture()
def client(mock_engine):
    """FastAPI TestClient with mocked database engine."""
    from src.backend.main import app
    from src.backend.database import _cache

    _cache.clear()
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clear_cache():
    """Clear the in-memory cache between tests."""
    from src.backend.database import _cache
    _cache.clear()
    yield
    _cache.clear()
