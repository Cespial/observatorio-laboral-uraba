"""Vercel serverless entry point — re-exports the FastAPI app."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.backend.main import app  # noqa: E402, F401
