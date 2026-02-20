"""
ETL 10 — Cargar limites municipales correctos desde DAGRAN GeoJSON
=================================================================
Fuente: DAGRAN (Departamento Administrativo de Gestión del Riesgo de Antioquia)
        125 municipios de Antioquia — filtramos solo los 11 de Urabá.

Tablas destino:
  - cartografia.limite_municipal  (TRUNCATE + INSERT)
  - cartografia.igac_uraba        (DROP + CREATE + INSERT)

Los datos vienen en EPSG:4326 (WGS 84), el mismo SRID que usamos.
"""

import json
import sys
import os
from pathlib import Path
from shapely.geometry import shape
from sqlalchemy import create_engine, text

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_URL

GEOJSON_PATH = next(
    (p for p in [
        Path.home() / "Downloads" / "HISTÓRICO_DE_EVENTOS_DAGRAN_-3501919587579481384.geojson",
        Path.home() / "Downloads" / "HISTORICO_DE_EVENTOS_DAGRAN_-3501919587579481384.geojson",
    ] if p.exists()),
    None,
)

URABA_CODES = {
    "05045", "05051", "05147", "05172",
    "05475", "05480", "05490", "05659",
    "05665", "05837", "05873",
}

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if GEOJSON_PATH is None:
        print("ERROR: No se encontro el archivo GeoJSON DAGRAN en ~/Downloads")
        sys.exit(1)

    print(f"Leyendo {GEOJSON_PATH} ...")
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        fc = json.load(f)

    features = [
        feat for feat in fc["features"]
        if feat["properties"].get("COD_MPIO") in URABA_CODES
    ]
    print(f"  {len(features)} municipios de Urabá encontrados (esperados 11)")
    if len(features) != 11:
        print("WARN: Se esperaban 11 municipios")

    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        # --- Ensure schema exists ---
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS cartografia"))

        # ---------------------------------------------------------------
        # 1. cartografia.limite_municipal
        # ---------------------------------------------------------------
        print("\n--- cartografia.limite_municipal ---")
        conn.execute(text("DROP TABLE IF EXISTS cartografia.limite_municipal"))
        conn.execute(text("""
            CREATE TABLE cartografia.limite_municipal (
                gid SERIAL PRIMARY KEY,
                dane_code TEXT NOT NULL,
                nombre TEXT NOT NULL,
                subregion TEXT,
                area_km2 DOUBLE PRECISION,
                geom geometry(Geometry, 4326)
            )
        """))
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_limite_municipal_geom "
            "ON cartografia.limite_municipal USING gist(geom)"
        ))
        print("  DROP + CREATE TABLE OK")

        for feat in features:
            props = feat["properties"]
            geom_json = json.dumps(feat["geometry"])
            # Compute area in km² using geography cast (meters² → km²)
            conn.execute(text("""
                INSERT INTO cartografia.limite_municipal
                    (dane_code, nombre, subregion, area_km2, geom)
                VALUES (
                    :dane,
                    :nombre,
                    :subregion,
                    ST_Area(ST_GeomFromGeoJSON(:geom)::geography) / 1e6,
                    ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)
                )
            """), {
                "dane": props["COD_MPIO"],
                "nombre": props["MPIO_NOMBR"],
                "subregion": props.get("SUBREGION", "URABA"),
                "geom": geom_json,
            })

        cnt = conn.execute(text(
            "SELECT COUNT(*), COUNT(DISTINCT ST_AsText(geom)) FROM cartografia.limite_municipal"
        )).fetchone()
        print(f"  Insertados: {cnt[0]} filas, {cnt[1]} geometrias distintas")

        # ---------------------------------------------------------------
        # 2. cartografia.igac_uraba (compatible con endpoint /api/geo/uraba)
        # ---------------------------------------------------------------
        print("\n--- cartografia.igac_uraba ---")
        conn.execute(text("DROP TABLE IF EXISTS cartografia.igac_uraba"))
        conn.execute(text("""
            CREATE TABLE cartografia.igac_uraba (
                gid SERIAL PRIMARY KEY,
                "MpCodigo" TEXT NOT NULL,
                "MpNombre" TEXT NOT NULL,
                "MpArea"   DOUBLE PRECISION,
                "Depto"    TEXT DEFAULT 'ANTIOQUIA',
                geometry   geometry(Geometry, 4326)
            )
        """))
        print("  CREATE TABLE OK")

        for feat in features:
            props = feat["properties"]
            geom_json = json.dumps(feat["geometry"])
            conn.execute(text("""
                INSERT INTO cartografia.igac_uraba
                    ("MpCodigo", "MpNombre", "MpArea", "Depto", geometry)
                VALUES (
                    :code,
                    :name,
                    ST_Area(ST_GeomFromGeoJSON(:geom)::geography) / 1e6,
                    'ANTIOQUIA',
                    ST_SetSRID(ST_GeomFromGeoJSON(:geom), 4326)
                )
            """), {
                "code": props["COD_MPIO"],
                "name": props["MPIO_NOMBR"],
                "geom": geom_json,
            })

        cnt2 = conn.execute(text("SELECT COUNT(*) FROM cartografia.igac_uraba")).scalar()
        print(f"  Insertados: {cnt2} filas")

        # Spatial index
        conn.execute(text(
            "CREATE INDEX IF NOT EXISTS idx_igac_uraba_geom "
            "ON cartografia.igac_uraba USING gist(geometry)"
        ))
        print("  Indice espacial creado")

    print("\nDone!")


if __name__ == "__main__":
    main()
