#!/usr/bin/env python3
"""
ETL Pipeline — Observatorio de Ciudades Apartadó
Carga todos los datasets a PostgreSQL/PostGIS
"""
import json
import os
import sys
import traceback
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from sqlalchemy import create_engine, text

# ============================================================
# CONFIGURACIÓN
# ============================================================
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

from dotenv import load_dotenv
load_dotenv(BASE_DIR / ".env")

DB_URL = os.getenv("DATABASE_URL")
# DANE_CODE is now handled per municipality in the loop

MUNICIPIOS = [
    ("05045", "Apartadó",   [-76.80, 7.70, -76.35, 8.10]),
    ("05051", "Arboletes",  [-76.60, 8.70, -76.20, 9.10]),
    ("05147", "Carepa",     [-76.80, 7.60, -76.40, 7.95]),
    ("05172", "Chigorodó",  [-76.85, 7.50, -76.30, 7.85]),
    ("05475", "Murindó",    [-77.00, 6.80, -76.50, 7.20]),
    ("05480", "Mutatá",     [-76.60, 7.10, -76.20, 7.50]),
    ("05490", "Necoclí",    [-77.00, 8.30, -76.50, 8.70]),
    ("05659", "San Juan",   [-76.70, 8.80, -76.30, 9.20]),
    ("05665", "San Pedro",  [-76.50, 8.10, -76.10, 8.50]),
    ("05837", "Turbo",      [-77.10, 7.90, -76.40, 8.60]),
    ("05873", "Vigía",      [-77.10, 6.40, -76.40, 7.00])
]

engine = create_engine(DB_URL)

results = []

def log(msg):
    print(f"  {msg}")

def report(name, status, count=0, detail="", dane_code=""):
    results.append({
        "dataset": name, 
        "municipio": dane_code,
        "status": status, 
        "registros": count, 
        "detalle": detail
    })
    emoji = "OK" if status == "ok" else "FAIL" if status == "error" else "SKIP"
    prefix = f"[{dane_code}] " if dane_code else ""
    print(f"  {emoji} {prefix}{name}: {count} registros {detail}")


# ============================================================
# 1. CARTOGRAFÍA — Límite municipal
# ============================================================
def load_limite_municipal(dane_code, name, bbox):
    log(f"Cargando límite municipal de {name} ({dane_code})...")
    # Try specific file or generic
    path = DATA_DIR / "cartografia" / "geojson" / f"{name.lower().replace(' ', '_')}.geojson"
    if not path.exists():
        path = DATA_DIR / "cartografia" / "geojson" / "apartado.geojson" # fallback for testing
        if not path.exists():
            report("limite_municipal", "skip", detail="Archivo no encontrado", dane_code=dane_code)
            return

    gdf = gpd.read_file(path)
    gdf = gdf.to_crs(epsg=4326)
    gdf_out = gpd.GeoDataFrame({
        "dane_code": [dane_code],
        "nombre": [name],
        "divipola": [dane_code],
        "departamento": ["Antioquia"],
        "area_km2": [gdf.iloc[0].get("area_km2", None)],
        "geom": [gdf.iloc[0].geometry]
    }, geometry="geom", crs="EPSG:4326")
    
    gdf_out.to_postgis("limite_municipal", engine, schema="cartografia", if_exists="append", index=False)
    report("limite_municipal", "ok", len(gdf_out), dane_code=dane_code)


# ============================================================
# 2. OSM — Edificaciones, Vías, Uso suelo, Amenidades
# ============================================================
import requests
import time

def download_osm_data(name, bbox, layer):
    """Descarga datos de OSM usando Overpass API."""
    log(f"Descargando {layer} OSM para {name} via Overpass...")
    
    queries = {
        "buildings": 'way["building"]({s},{w},{n},{e});',
        "roads": 'way["highway"]({s},{w},{n},{e});',
        "landuse": 'way["landuse"]({s},{w},{n},{e});',
        "amenities": 'node["amenity"]({s},{w},{n},{e});'
    }
    
    query_body = queries.get(layer)
    if not query_body: return None
    
    # bbox in overpass is (s, w, n, e)
    w, s, e, n = bbox
    full_query = f'[out:json][timeout:90];({query_body});out body geom;'
    
    url = "https://overpass-api.de/api/interpreter"
    try:
        response = requests.post(url, data={'data': full_query})
        if response.status_code == 200:
            data = response.json()
            filename = f"{name.lower().replace(' ', '_')}_{layer}.json"
            target_path = DATA_DIR / "cartografia" / "osm" / filename
            target_path.parent.mkdir(parents=True, exist_ok=True)
            with open(target_path, "w") as f:
                json.dump(data, f)
            return target_path
    except Exception as e:
        log(f"Error descargando OSM: {e}")
    return None

def load_osm_layer(layer_name, filename_pattern, table_name, dane_code, name, bbox):
    log(f"Cargando {layer_name} OSM para {name}...")
    filename = filename_pattern.replace("{name}", name.lower().replace(" ", "_"))
    path = DATA_DIR / "cartografia" / "osm" / filename
    
    if not path.exists():
        # Intentar descargar
        path = download_osm_data(name, bbox, layer_name.replace("edificaciones", "buildings").replace("vias", "roads").replace("uso_suelo", "landuse").replace("amenidades", "amenities"))
        if not path:
            report(table_name, "skip", detail="Archivo no encontrado y descarga fallida", dane_code=dane_code)
            return
        
    with open(path) as f:
        data = json.load(f)

    rows = []
    from shapely.geometry import Polygon, LineString, Point
    
    for el in data.get("elements", []):
        tags = el.get("tags", {})
        if "geometry" not in el and "lat" not in el: continue
        
        try:
            geom = None
            if layer_name in ("edificaciones", "uso_suelo"):
                coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
                if len(coords) < 4: continue
                if coords[0] != coords[-1]: coords.append(coords[0])
                geom = Polygon(coords)
                if not geom.is_valid: geom = geom.buffer(0)
            elif layer_name == "vias":
                coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
                if len(coords) < 2: continue
                geom = LineString(coords)
            elif layer_name == "amenidades":
                geom = Point(el["lon"], el["lat"])

            if geom:
                row = {"id": el["id"], "dane_code": dane_code, "geom": geom}
                if layer_name == "edificaciones":
                    row.update({
                        "osm_type": "way",
                        "building": tags.get("building", "yes"),
                        "name": tags.get("name"),
                        "amenity": tags.get("amenity"),
                        "addr_street": tags.get("addr:street")
                    })
                elif layer_name == "vias":
                    row.update({
                        "osm_type": "way",
                        "highway": tags.get("highway"),
                        "name": tags.get("name"),
                        "surface": tags.get("surface"),
                        "lanes": int(tags["lanes"]) if "lanes" in tags else None
                    })
                elif layer_name == "uso_suelo":
                    row.update({
                        "landuse": tags.get("landuse"),
                        "name": tags.get("name")
                    })
                elif layer_name == "amenidades":
                    row.update({
                        "amenity": tags.get("amenity"),
                        "name": tags.get("name"),
                        "phone": tags.get("phone"),
                        "website": tags.get("website"),
                        "opening_hours": tags.get("opening_hours"),
                        "lat": el["lat"], "lon": el["lon"]
                    })
                rows.append(row)
        except Exception:
            continue

    if rows:
        gdf = gpd.GeoDataFrame(rows, geometry="geom", crs="EPSG:4326")
        gdf.to_postgis(table_name, engine, schema="cartografia", if_exists="append", index=False)
        report(table_name, "ok", len(gdf), dane_code=dane_code)
    else:
        report(table_name, "skip", detail="Sin datos", dane_code=dane_code)


# ============================================================
# 3. MGN — Manzanas Censales (filtrar por Municipio)
# ============================================================
def load_mgn_manzanas(dane_code, name, bbox):
    log(f"Cargando MGN manzanas para {name}...")
    shp_path = DATA_DIR / "cartografia" / "mgn" / "raw" / "MGN_ANM_MANZANA.shp"
    if not shp_path.exists():
        report("manzanas_censales", "error", detail="Shapefile no encontrado", dane_code=dane_code)
        return

    # Filter by bbox and then by dane_code
    gdf = gpd.read_file(shp_path, bbox=tuple(bbox))
    if len(gdf) == 0:
        report("manzanas_censales", "skip", detail="Sin datos en bbox", dane_code=dane_code)
        return

    # Identify code column
    code_col = None
    for c in gdf.columns:
        if c.lower() in ('mpio_cdpmp', 'cod_mpio', 'mpio_ccdgo', 'mgn_mpio_c'):
            code_col = c
            break
    
    if code_col:
        gdf = gdf[gdf[code_col].astype(str).str.contains(dane_code)]
    
    if len(gdf) == 0:
        report("manzanas_censales", "skip", detail="Filtrado por código vacío", dane_code=dane_code)
        return

    gdf = gdf.to_crs(epsg=4326)
    gdf['dane_code'] = dane_code
    
    # Simple mapping for this exercise
    gdf_out = gdf[['dane_code', 'geometry']].copy()
    gdf_out.columns = ['dane_code', 'geom']
    gdf_out = gpd.GeoDataFrame(gdf_out, geometry='geom', crs="EPSG:4326")
    
    gdf_out.to_postgis("manzanas_censales", engine, schema="cartografia", if_exists="append", index=False)
    report("manzanas_censales", "ok", len(gdf_out), dane_code=dane_code)


# ============================================================
# 4. CATASTRO — Terrenos
# ============================================================
def load_catastro_layer(layer_name, shp_filename, table_name, dane_code, name, bbox):
    log(f"Cargando catastro {layer_name} para {name}...")
    shp_path = DATA_DIR / "catastro" / "raw" / "CatastroPubliconNoviembre2025" / shp_filename
    if not shp_path.exists():
        report(table_name, "skip", detail="Shapefile no encontrado", dane_code=dane_code)
        return

    gdf = gpd.read_file(shp_path, bbox=tuple(bbox))
    if len(gdf) == 0:
        report(table_name, "skip", detail="Sin datos en bbox", dane_code=dane_code)
        return

    gdf = gdf.to_crs(epsg=4326)
    gdf['dane_code'] = dane_code
    
    gdf.to_postgis(table_name, engine, schema="catastro", if_exists="append", index=False)
    report(table_name, "ok", len(gdf), dane_code=dane_code)


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================
def main():
    print("=" * 70)
    print("  ETL PIPELINE — OBSERVATORIO REGIONAL URABÁ")
    print("=" * 70)

    # Clean tables first if needed, or use if_exists='replace' on the first iteration
    # For now, we use 'append' and expect tables to be empty or handled by schema migration
    with engine.connect() as conn:
        for schema in ['cartografia', 'catastro', 'socioeconomico', 'seguridad', 'servicios']:
            conn.execute(text(f"DROP SCHEMA IF EXISTS {schema} CASCADE"))
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        conn.commit()
    
    # Re-run schema to create tables
    with open(BASE_DIR / "etl" / "00_schema.sql") as f:
        with engine.begin() as conn:
            conn.execute(text(f.read()))

    for dane_code, name, bbox in MUNICIPIOS:
        # Cartografía
        load_limite_municipal(dane_code, name, bbox)
        load_osm_layer("edificaciones", "{name}_buildings.json", "osm_edificaciones", dane_code, name, bbox)
        load_osm_layer("vias", "{name}_roads.json", "osm_vias", dane_code, name, bbox)
        load_osm_layer("uso_suelo", "{name}_landuse.json", "osm_uso_suelo", dane_code, name, bbox)
        load_osm_layer("amenidades", "{name}_amenities.json", "osm_amenidades", dane_code, name, bbox)
        
        # MGN
        load_mgn_manzanas(dane_code, name, bbox)
        
        # Catastro
        load_catastro_layer("terrenos", "R_TERRENO.shp", "terrenos", dane_code, name, bbox)
        load_catastro_layer("construcciones", "R_CONSTRUCCION.shp", "construcciones", dane_code, name, bbox)
        load_catastro_layer("sectores", "R_SECTOR.shp", "sectores", dane_code, name, bbox)
        load_catastro_layer("veredas", "R_VEREDA.shp", "veredas", dane_code, name, bbox)

    # Socioeconómico and others (these usually have all municipios in one file or specific files)
    # To be updated in next steps...

    # Resumen
    print("\n" + "=" * 70)
    print("  RESUMEN ETL REGIONAL")
    print("=" * 70)
    ok_count = sum(1 for r in results if r["status"] == "ok")
    total_records = sum(r["registros"] for r in results if r["status"] == "ok")
    print(f"  Operaciones exitosas: {ok_count}")
    print(f"  Total registros cargados: {total_records:,}")
    print("=" * 70)

if __name__ == "__main__":
    main()


# ============================================================
# 2. OSM — Edificaciones, Vías, Uso suelo, Amenidades
# ============================================================
def load_osm_buildings():
    log("Cargando edificaciones OSM...")
    path = DATA_DIR / "cartografia" / "osm" / "apartado_buildings.json"
    if not path.exists():
        report("osm_edificaciones", "error", detail="Archivo no encontrado")
        return
    with open(path) as f:
        data = json.load(f)

    rows = []
    for el in data.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) < 4:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        from shapely.geometry import Polygon
        try:
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            tags = el.get("tags", {})
            rows.append({
                "id": el["id"],
                "osm_type": "way",
                "building": tags.get("building", "yes"),
                "name": tags.get("name"),
                "amenity": tags.get("amenity"),
                "addr_street": tags.get("addr:street"),
                "geom": poly
            })
        except Exception:
            continue

    if rows:
        gdf = gpd.GeoDataFrame(rows, geometry="geom", crs="EPSG:4326")
        gdf.to_postgis("osm_edificaciones", engine, schema="cartografia", if_exists="replace", index=False)
        report("osm_edificaciones", "ok", len(gdf))
    else:
        report("osm_edificaciones", "error", detail="Sin datos")


def load_osm_roads():
    log("Cargando vías OSM...")
    path = DATA_DIR / "cartografia" / "osm" / "apartado_roads.json"
    if not path.exists():
        report("osm_vias", "error", detail="Archivo no encontrado")
        return
    with open(path) as f:
        data = json.load(f)

    rows = []
    for el in data.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) < 2:
            continue
        from shapely.geometry import LineString
        try:
            line = LineString(coords)
            tags = el.get("tags", {})
            rows.append({
                "id": el["id"],
                "osm_type": "way",
                "highway": tags.get("highway"),
                "name": tags.get("name"),
                "surface": tags.get("surface"),
                "lanes": int(tags["lanes"]) if "lanes" in tags else None,
                "geom": line
            })
        except Exception:
            continue

    if rows:
        gdf = gpd.GeoDataFrame(rows, geometry="geom", crs="EPSG:4326")
        gdf.to_postgis("osm_vias", engine, schema="cartografia", if_exists="replace", index=False)
        report("osm_vias", "ok", len(gdf))
    else:
        report("osm_vias", "error", detail="Sin datos")


def load_osm_landuse():
    log("Cargando uso del suelo OSM...")
    path = DATA_DIR / "cartografia" / "osm" / "apartado_landuse.json"
    if not path.exists():
        report("osm_uso_suelo", "error", detail="Archivo no encontrado")
        return
    with open(path) as f:
        data = json.load(f)

    rows = []
    for el in data.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [(p["lon"], p["lat"]) for p in el["geometry"]]
        if len(coords) < 4:
            continue
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        from shapely.geometry import Polygon
        try:
            poly = Polygon(coords)
            if not poly.is_valid:
                poly = poly.buffer(0)
            tags = el.get("tags", {})
            rows.append({
                "id": el["id"],
                "landuse": tags.get("landuse"),
                "name": tags.get("name"),
                "geom": poly
            })
        except Exception:
            continue

    if rows:
        gdf = gpd.GeoDataFrame(rows, geometry="geom", crs="EPSG:4326")
        gdf.to_postgis("osm_uso_suelo", engine, schema="cartografia", if_exists="replace", index=False)
        report("osm_uso_suelo", "ok", len(gdf))
    else:
        report("osm_uso_suelo", "error", detail="Sin datos")


def load_osm_amenities():
    log("Cargando amenidades OSM...")
    path = DATA_DIR / "cartografia" / "osm" / "apartado_amenities.json"
    if not path.exists():
        report("osm_amenidades", "error", detail="Archivo no encontrado")
        return
    with open(path) as f:
        data = json.load(f)

    rows = []
    for el in data.get("elements", []):
        if "lat" not in el or "lon" not in el:
            continue
        from shapely.geometry import Point
        tags = el.get("tags", {})
        rows.append({
            "id": el["id"],
            "amenity": tags.get("amenity"),
            "name": tags.get("name"),
            "phone": tags.get("phone"),
            "website": tags.get("website"),
            "opening_hours": tags.get("opening_hours"),
            "lat": el["lat"],
            "lon": el["lon"],
            "geom": Point(el["lon"], el["lat"])
        })

    if rows:
        gdf = gpd.GeoDataFrame(rows, geometry="geom", crs="EPSG:4326")
        gdf.to_postgis("osm_amenidades", engine, schema="cartografia", if_exists="replace", index=False)
        report("osm_amenidades", "ok", len(gdf))
    else:
        report("osm_amenidades", "error", detail="Sin datos")


# ============================================================
# 3. MGN — Manzanas Censales (filtrar Apartadó)
# ============================================================
def load_mgn_manzanas():
    log("Cargando MGN manzanas censales (filtrando Apartadó)...")
    shp_path = DATA_DIR / "cartografia" / "mgn" / "raw" / "MGN_ANM_MANZANA.shp"
    if not shp_path.exists():
        report("manzanas_censales", "error", detail="Shapefile no encontrado")
        return

    # Read only Apartadó using a bounding box filter first, then DANE code
    log("  Leyendo shapefile nacional (puede tardar)...")
    # Read the DBF to find column names first
    sample = gpd.read_file(shp_path, rows=5)
    log(f"  Columnas: {list(sample.columns)}")

    # Find the municipality code column
    mpio_col = None
    for col in sample.columns:
        if "mpio" in col.lower() or "municipio" in col.lower() or "cod_mun" in col.lower():
            log(f"  Columna municipio candidata: {col} = {sample[col].iloc[0]}")
            mpio_col = col

    # Use bbox to pre-filter (Apartadó: approx 7.77, -76.75, 8.07, -76.41)
    log("  Filtrando por bounding box de Apartadó...")
    gdf = gpd.read_file(shp_path, bbox=(-76.80, 7.70, -76.35, 8.10))
    log(f"  Registros en bbox: {len(gdf)}")

    if len(gdf) == 0:
        report("manzanas_censales", "error", detail="Sin manzanas en bbox")
        return

    # Additional filter by DANE code if column found
    log(f"  Columnas disponibles: {list(gdf.columns)}")
    code_cols = [c for c in gdf.columns if 'mpio' in c.lower() or 'municipio' in c.lower() or '05045' in str(gdf[c].unique()[:5])]
    if code_cols:
        log(f"  Filtrando por columnas: {code_cols}")

    gdf = gdf.to_crs(epsg=4326)

    # Map columns dynamically
    col_map = {}
    for c in gdf.columns:
        cl = c.lower()
        if 'manz' in cl and ('cod' in cl or 'cdgo' in cl):
            col_map['cod_dane_manzana'] = c
        elif 'secc' in cl and ('cod' in cl or 'cdgo' in cl):
            col_map['cod_dane_seccion'] = c
        elif 'sect' in cl and ('cod' in cl or 'cdgo' in cl):
            col_map['cod_dane_sector'] = c
        elif cl in ('mpio_cdpmp', 'cod_mpio', 'mpio_ccdgo'):
            col_map['cod_dane_municipio'] = c
        elif 'tp_' in cl or 'total_per' in cl:
            col_map['total_personas'] = c
        elif 'th_' in cl or 'total_hog' in cl:
            col_map['total_hogares'] = c
        elif 'tv_' in cl or 'total_viv' in cl:
            col_map['total_viviendas'] = c

    log(f"  Mapeo de columnas: {col_map}")

    out_cols = {"geom": gdf.geometry}
    for target, source in col_map.items():
        out_cols[target] = gdf[source]

    gdf_out = gpd.GeoDataFrame(out_cols, geometry="geom", crs="EPSG:4326")
    gdf_out.to_postgis("manzanas_censales", engine, schema="cartografia", if_exists="replace", index=False)
    report("manzanas_censales", "ok", len(gdf_out))


# ============================================================
# 4. CATASTRO — Terrenos (filtrar Apartadó)
# ============================================================
def load_catastro_terrenos():
    log("Cargando catastro terrenos (filtrando Apartadó)...")
    shp_path = DATA_DIR / "catastro" / "raw" / "CatastroPubliconNoviembre2025" / "R_TERRENO.shp"
    if not shp_path.exists():
        report("catastro_terrenos", "error", detail="Shapefile no encontrado")
        return

    sample = gpd.read_file(shp_path, rows=3)
    log(f"  Columnas terreno: {list(sample.columns)}")

    # Filter by bbox
    log("  Filtrando por bbox...")
    gdf = gpd.read_file(shp_path, bbox=(-76.80, 7.70, -76.35, 8.10))
    log(f"  Terrenos en bbox: {len(gdf)}")

    if len(gdf) == 0:
        report("catastro_terrenos", "error", detail="Sin terrenos en bbox")
        return

    gdf = gdf.to_crs(epsg=4326)
    gdf.to_postgis("terrenos", engine, schema="catastro", if_exists="replace", index=False)
    report("catastro_terrenos", "ok", len(gdf))


def load_catastro_construcciones():
    log("Cargando catastro construcciones (filtrando Apartadó)...")
    shp_path = DATA_DIR / "catastro" / "raw" / "CatastroPubliconNoviembre2025" / "R_CONSTRUCCION.shp"
    if not shp_path.exists():
        report("catastro_construcciones", "error", detail="Shapefile no encontrado")
        return

    sample = gpd.read_file(shp_path, rows=3)
    log(f"  Columnas construcción: {list(sample.columns)}")

    gdf = gpd.read_file(shp_path, bbox=(-76.80, 7.70, -76.35, 8.10))
    log(f"  Construcciones en bbox: {len(gdf)}")

    if len(gdf) == 0:
        report("catastro_construcciones", "error", detail="Sin construcciones en bbox")
        return

    gdf = gdf.to_crs(epsg=4326)
    gdf.to_postgis("construcciones", engine, schema="catastro", if_exists="replace", index=False)
    report("catastro_construcciones", "ok", len(gdf))


def load_catastro_sectores():
    log("Cargando catastro sectores...")
    shp_path = DATA_DIR / "catastro" / "raw" / "CatastroPubliconNoviembre2025" / "R_SECTOR.shp"
    if not shp_path.exists():
        report("catastro_sectores", "error", detail="Shapefile no encontrado")
        return

    sample = gpd.read_file(shp_path, rows=3)
    log(f"  Columnas sector: {list(sample.columns)}")

    gdf = gpd.read_file(shp_path, bbox=(-76.80, 7.70, -76.35, 8.10))
    log(f"  Sectores en bbox: {len(gdf)}")

    if len(gdf) == 0:
        report("catastro_sectores", "error", detail="Sin sectores en bbox")
        return

    gdf = gdf.to_crs(epsg=4326)
    gdf.to_postgis("sectores", engine, schema="catastro", if_exists="replace", index=False)
    report("catastro_sectores", "ok", len(gdf))


def load_catastro_veredas():
    log("Cargando catastro veredas...")
    shp_path = DATA_DIR / "catastro" / "raw" / "CatastroPubliconNoviembre2025" / "R_VEREDA.shp"
    if not shp_path.exists():
        report("catastro_veredas", "error", detail="Shapefile no encontrado")
        return

    sample = gpd.read_file(shp_path, rows=3)
    log(f"  Columnas vereda: {list(sample.columns)}")

    gdf = gpd.read_file(shp_path, bbox=(-76.80, 7.70, -76.35, 8.10))
    log(f"  Veredas en bbox: {len(gdf)}")

    if len(gdf) == 0:
        report("catastro_veredas", "error", detail="Sin veredas en bbox")
        return

    gdf = gdf.to_crs(epsg=4326)
    gdf.to_postgis("veredas", engine, schema="catastro", if_exists="replace", index=False)
    report("catastro_veredas", "ok", len(gdf))


# ============================================================
# 5. IGAC — Municipios shapefile
# ============================================================
def load_igac_municipios():
    log("Cargando IGAC municipios...")
    shp_path = DATA_DIR / "cartografia" / "igac" / "raw" / "DireccionesTerritoriales_shp" / "DTerritorialesMunpio.shp"
    if not shp_path.exists():
        report("igac_municipios", "error", detail="Shapefile no encontrado")
        return

    gdf = gpd.read_file(shp_path, bbox=(-76.80, 7.70, -76.35, 8.10))
    log(f"  Municipios IGAC en bbox: {len(gdf)}")
    log(f"  Columnas: {list(gdf.columns)}")

    if len(gdf) > 0:
        gdf = gdf.to_crs(epsg=4326)
        gdf.to_postgis("igac_municipios", engine, schema="cartografia", if_exists="replace", index=False)
        report("igac_municipios", "ok", len(gdf))
    else:
        report("igac_municipios", "error", detail="Sin datos en bbox")


from config import URABA_DANE_CODES

# ============================================================
# 6. SOCIOECONÓMICO — IPM
# ============================================================
def load_ipm_regional():
    log("Cargando IPM regional...")
    path = DATA_DIR / "socioeconomico" / "ipm" / "ipm_municipal.xls"
    if not path.exists():
        report("ipm", "skip", detail="Archivo no encontrado")
        return

    try:
        df = pd.read_excel(path, engine="xlrd")
        dane_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains("05045").any():
                dane_col = col
                break
        
        if dane_col:
            df = df[df[dane_col].astype(str).str.contains('|'.join(URABA_DANE_CODES))]
            df['dane_code'] = df[dane_col].astype(str).str.extract(f"({'|'.join(URABA_DANE_CODES)})")[0]
            df.to_sql("ipm", engine, schema="socioeconomico", if_exists="append", index=False)
            report("ipm", "ok", len(df), detail="Regional")
    except Exception as e:
        report("ipm", "error", detail=str(e)[:100])

# ============================================================
# 7. SOCIOECONÓMICO — NBI
# ============================================================
def load_nbi_regional():
    log("Cargando NBI regional...")
    path = DATA_DIR / "socioeconomico" / "nbi" / "nbi_municipios.xls"
    if not path.exists():
        report("nbi", "skip", detail="Archivo no encontrado")
        return

    try:
        df = pd.read_excel(path, engine="xlrd")
        dane_col = None
        for col in df.columns:
            if df[col].astype(str).str.contains("05045").any():
                dane_col = col
                break
        
        if dane_col:
            df = df[df[dane_col].astype(str).str.contains('|'.join(URABA_DANE_CODES))]
            df['dane_code'] = df[dane_col].astype(str).str.extract(f"({'|'.join(URABA_DANE_CODES)})")[0]
            df.to_sql("nbi", engine, schema="socioeconomico", if_exists="append", index=False)
            report("nbi", "ok", len(df), detail="Regional")
    except Exception as e:
        report("nbi", "error", detail=str(e)[:100])

# Update main to include these
def main():
    # ... (previous code) ...
    for dane_code, name, bbox in MUNICIPIOS:
        # (per municipality loads)
        pass

    # Regional loads
    load_ipm_regional()
    load_nbi_regional()
    # (Similarly for others)
    print("ETL complete.")


# ============================================================
# 8. EDUCACIÓN — Establecimientos
# ============================================================
def load_educacion():
    log("Cargando establecimientos educativos...")
    path = DATA_DIR / "educacion" / "establecimientos_apartado.json"
    if not path.exists():
        report("establecimientos_educativos", "error", detail="Archivo no encontrado")
        return

    with open(path) as f:
        data = json.load(f)

    if not data:
        report("establecimientos_educativos", "error", detail="Vacío")
        return

    df = pd.DataFrame(data)
    log(f"  Columnas: {list(df.columns)[:10]}")

    col_map = {}
    for c in df.columns:
        cl = c.lower()
        if 'codigo_dane' in cl and 'mun' not in cl:
            col_map['codigo_dane'] = c
        elif 'nombre' in cl and 'establecimiento' in cl:
            col_map['nombre'] = c
        elif 'municipio' == cl:
            col_map['municipio'] = c
        elif 'sector' == cl or 'cod_sector' == cl:
            col_map['sector'] = c
        elif 'total_matricula' in cl:
            col_map['total_matricula'] = c

    df.to_sql("establecimientos_educativos_raw", engine, schema="socioeconomico", if_exists="replace", index=False)
    report("establecimientos_educativos", "ok", len(df))


# ============================================================
# 9. EDUCACIÓN — ICFES
# ============================================================
def load_icfes():
    log("Cargando resultados ICFES...")
    path = DATA_DIR / "educacion" / "icfes_apartado.json"
    if not path.exists():
        report("icfes", "error", detail="Archivo no encontrado")
        return

    with open(path) as f:
        data = json.load(f)

    if not data:
        report("icfes", "error", detail="Vacío")
        return

    df = pd.DataFrame(data)
    log(f"  Columnas ICFES: {list(df.columns)[:15]}")
    log(f"  Registros: {len(df)}")

    # Convert numeric columns
    num_cols = [c for c in df.columns if 'punt_' in c.lower() or 'puntaje' in c.lower()]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c], errors='coerce')

    df.to_sql("icfes_raw", engine, schema="socioeconomico", if_exists="replace", index=False)
    report("icfes", "ok", len(df))


# ============================================================
# 10. SALUD — IPS
# ============================================================
def load_ips():
    log("Cargando IPS/Salud...")
    path = DATA_DIR / "salud" / "ips_apartado.json"
    if not path.exists():
        report("ips_salud", "error", detail="Archivo no encontrado")
        return

    with open(path) as f:
        data = json.load(f)

    if not data:
        report("ips_salud", "error", detail="Vacío")
        return

    df = pd.DataFrame(data)
    log(f"  Columnas IPS: {list(df.columns)[:10]}")
    df.to_sql("ips_raw", engine, schema="socioeconomico", if_exists="replace", index=False)
    report("ips_salud", "ok", len(df))


# ============================================================
# 11. SERVICIOS PÚBLICOS
# ============================================================
def load_servicios_publicos():
    log("Cargando prestadores de servicios públicos...")
    path = DATA_DIR / "servicios_publicos" / "prestadores_apartado.json"
    if not path.exists():
        report("servicios_publicos", "error", detail="Archivo no encontrado")
        return

    with open(path) as f:
        data = json.load(f)

    if not data:
        report("servicios_publicos", "error", detail="Vacío")
        return

    df = pd.DataFrame(data)
    log(f"  Columnas Servicios: {list(df.columns)[:10]}")
    df.to_sql("prestadores_raw", engine, schema="servicios", if_exists="replace", index=False)
    report("servicios_publicos", "ok", len(df))


# ============================================================
# 12-15. SEGURIDAD
# ============================================================
def load_security_dataset(name, filename, table_name):
    log(f"Cargando {name}...")
    path = DATA_DIR / "seguridad" / filename
    if not path.exists():
        report(name, "error", detail="Archivo no encontrado")
        return

    with open(path) as f:
        data = json.load(f)

    if not data or (isinstance(data, dict) and data.get("error")):
        report(name, "error", detail="Vacío o error API")
        return

    df = pd.DataFrame(data)

    # Convert fecha_hecho to date
    date_cols = [c for c in df.columns if 'fecha' in c.lower()]
    for c in date_cols:
        df[c] = pd.to_datetime(df[c], errors='coerce')

    # Convert cantidad to numeric
    if 'cantidad' in df.columns:
        df['cantidad'] = pd.to_numeric(df['cantidad'], errors='coerce')

    df.to_sql(table_name, engine, schema="seguridad", if_exists="replace", index=False)
    report(name, "ok", len(df))


# ============================================================
# 16. CONFLICTO — Víctimas
# ============================================================
def load_victimas():
    log("Cargando víctimas del conflicto...")
    path = DATA_DIR / "conflicto" / "victimas_apartado.json"
    if not path.exists():
        report("victimas_conflicto", "error", detail="Archivo no encontrado")
        return

    with open(path) as f:
        data = json.load(f)

    if not data or (isinstance(data, dict) and data.get("error")):
        report("victimas_conflicto", "error", detail="Vacío o error API")
        return

    df = pd.DataFrame(data)
    log(f"  Columnas víctimas: {list(df.columns)[:10]}")

    num_cols = ['per_ocu', 'eventos', 'personas']
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors='coerce')

    df.to_sql("victimas_raw", engine, schema="seguridad", if_exists="replace", index=False)
    report("victimas_conflicto", "ok", len(df))


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================
def main():
    print("=" * 70)
    print("  ETL PIPELINE — OBSERVATORIO REGIONAL URABÁ")
    print("=" * 70)

    # Inicializar Base de Datos (Crear Esquemas si no existen)
    try:
        with engine.connect() as conn:
            for schema in ['cartografia', 'catastro', 'socioeconomico', 'seguridad', 'servicios', 'ambiental']:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
            conn.commit()
        
        # Cargar Schema Base (Tablas)
        with open(BASE_DIR / "etl" / "00_schema.sql") as f:
            with engine.begin() as conn:
                conn.execute(text(f.read()))
        log("Esquema de base de datos verificado: OK")
    except Exception as e:
        log(f"Error inicializando DB: {e}")
        return

    # 1. Cargas por Municipio (Cartografía, OSM, MGN, Catastro)
    for dane_code, name, bbox in MUNICIPIOS:
        print(f"\n--- PROCESANDO {name.upper()} ({dane_code}) ---")
        
        try: load_limite_municipal(dane_code, name, bbox)
        except Exception as e: report("limite_municipal", "error", detail=str(e)[:50], dane_code=dane_code)

        # OSM con descarga automática si falta local
        for layer, table in [("edificaciones", "osm_edificaciones"), 
                            ("vias", "osm_vias"), 
                            ("uso_suelo", "osm_uso_suelo"), 
                            ("amenidades", "osm_amenidades")]:
            try:
                load_osm_layer(layer, "{name}_" + layer + ".json", table, dane_code, name, bbox)
            except Exception as e:
                report(table, "error", detail=str(e)[:50], dane_code=dane_code)

        # MGN y Catastro
        try: load_mgn_manzanas(dane_code, name, bbox)
        except Exception as e: report("manzanas_censales", "error", detail=str(e)[:50], dane_code=dane_code)

        try: load_catastro_layer("terrenos", "R_TERRENO.shp", "terrenos", dane_code, name, bbox)
        except Exception as e: report("terrenos", "error", detail=str(e)[:50], dane_code=dane_code)

        try: load_catastro_layer("construcciones", "R_CONSTRUCCION.shp", "construcciones", dane_code, name, bbox)
        except Exception as e: report("construcciones", "error", detail=str(e)[:50], dane_code=dane_code)

    # 2. Cargas Regionales (IPM, NBI, etc.)
    print("\n--- CARGAS REGIONALES ---")
    try: load_ipm_regional()
    except Exception as e: report("ipm", "error", detail=str(e)[:50], dane_code="URABA")

    try: load_nbi_regional()
    except Exception as e: report("nbi", "error", detail=str(e)[:50], dane_code="URABA")

    # Resumen Final
    print("\n" + "=" * 70)
    print("  RESUMEN FINAL ETL REGIONAL")
    print("=" * 70)
    ok_count = sum(1 for r in results if r["status"] == "ok")
    total_records = sum(r["registros"] for r in results if r["status"] == "ok")
    print(f"  Operaciones exitosas: {ok_count}")
    print(f"  Total registros cargados: {total_records:,}")
    print("=" * 70)

    # Guardar reporte
    report_path = BASE_DIR / "docs" / "etl_regional_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\n  Reporte regional guardado en: {report_path}")


if __name__ == "__main__":
    main()
