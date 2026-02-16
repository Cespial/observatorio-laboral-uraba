import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / ".env")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cristianespinal@localhost:5433/observatorio_apartado")

# Auto-detect Neon and enforce SSL
if ".neon.tech" in DATABASE_URL and "sslmode" not in DATABASE_URL:
    sep = "&" if "?" in DATABASE_URL else "?"
    DATABASE_URL += f"{sep}sslmode=require"

GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
DANE_CODE = os.getenv("DANE_CODE", "05045")
MUNICIPALITY_NAME = os.getenv("MUNICIPALITY_NAME", "Apartadó")
