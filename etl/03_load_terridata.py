#!/usr/bin/env python3
"""
ETL 03 - Load TerriData Excel into PostgreSQL (Regional Urabá)
Exhaustive version: loads all files in the directory.
Ensures .env is loaded.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Load env before importing DB_URL if possible, or just re-read it here
load_dotenv()
DB_URL = os.getenv("DATABASE_URL")

# -- Configuration -----------------------------------------------------------
DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "terridata"
SHEET_NAME = "Datos"
SCHEMA = "socioeconomico"
TABLE = "terridata"
FULL_TABLE = SCHEMA + "." + TABLE

# -- Column mapping: original Spanish -> snake_case --------------------------
COL_MAP = {
    "Código Departamento": "codigo_departamento",
    "Departamento": "departamento",
    "Código Entidad": "codigo_entidad",
    "Entidad": "entidad",
    "Dimensión": "dimension",
    "Subcategoría": "subcategoria",
    "Indicador": "indicador",
    "Dato Numérico": "dato_numerico",
    "Dato Cualitativo": "dato_cualitativo",
    "Año": "anio",
    "Mes": "mes",
    "Fuente": "fuente",
    "Unidad de Medida": "unidad_de_medida",
}

def parse_spanish_number(val):
    if pd.isna(val): return np.nan
    if isinstance(val, (int, float)): return float(val)
    s = str(val).strip().replace(".", "").replace(",", ".")
    try: return float(s)
    except ValueError: return np.nan

def load_file(engine, file_path):
    import re
    filename = file_path.name
    match = re.search(r'(\d{5})', filename)
    dane_code = match.group(1) if match else "00000"
    
    print(f"Processing {filename} (DANE: {dane_code})...")
    try:
        df = pd.read_excel(file_path, sheet_name=SHEET_NAME)
    except Exception as e:
        print(f"  Warning: failed to read sheet '{SHEET_NAME}', trying first sheet. {e}")
        df = pd.read_excel(file_path)
    
    df = df[df["Código Entidad"].notna()].reset_index(drop=True)
    df.rename(columns=COL_MAP, inplace=True)
    
    df["dato_numerico"] = df["dato_numerico"].apply(parse_spanish_number)
    df["dane_code"] = str(dane_code).zfill(5)
    
    cols_to_keep = list(COL_MAP.values()) + ["dane_code"]
    df = df[[c for c in df.columns if c in cols_to_keep]]

    df.to_sql(
        TABLE, engine, schema=SCHEMA, if_exists="append", index=False,
        method="multi", chunksize=500
    )
    print(f"  Inserted {len(df)} rows.")

def main():
    if not DB_URL:
        print("Error: DATABASE_URL not set in .env")
        return
        
    engine = create_engine(DB_URL)
    
    ddl = f"""
    CREATE SCHEMA IF NOT EXISTS {SCHEMA};
    DROP TABLE IF EXISTS {FULL_TABLE} CASCADE;
    CREATE TABLE {FULL_TABLE} (
        id                  SERIAL,
        dane_code           VARCHAR(5),
        codigo_departamento INTEGER,
        departamento        TEXT,
        codigo_entidad      INTEGER,
        entidad             TEXT,
        dimension           TEXT,
        subcategoria        TEXT,
        indicador           TEXT,
        dato_numerico       DOUBLE PRECISION,
        dato_cualitativo    TEXT,
        anio                INTEGER,
        mes                 INTEGER,
        fuente              TEXT,
        unidad_de_medida    TEXT,
        PRIMARY KEY (id, dane_code)
    );
    CREATE INDEX idx_terridata_dane ON {FULL_TABLE} (dane_code);
    CREATE INDEX idx_terridata_ind ON {FULL_TABLE} (indicador);
    CREATE INDEX idx_terridata_dim ON {FULL_TABLE} (dimension);
    """
    with engine.begin() as conn:
        conn.execute(text(ddl))

    files = list(DATA_DIR.glob("*.xls*"))
    print(f"Found {len(files)} files in {DATA_DIR}")
    
    for f in files:
        try:
            load_file(engine, f)
        except Exception as e:
            print(f"  [ERROR] Loading {f}: {e}")

    print("\n" + "=" * 70)
    print("  TERRIDATA LOAD COMPLETE")
    print("=" * 70)
    try:
        with engine.connect() as conn:
            count = conn.execute(text(f"SELECT COUNT(*) FROM {FULL_TABLE}")).scalar()
            print(f"  Total records loaded to Supabase: {count}")
    except Exception as e:
        print(f"Summary failed: {e}")
    print("=" * 70)

if __name__ == "__main__":
    main()
