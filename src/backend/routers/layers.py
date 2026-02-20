"""
Gestión de capas — catálogo de todas las capas disponibles
"""
from fastapi import APIRouter, HTTPException, Query
from ..database import engine, cached, query_geojson
from sqlalchemy import text

router = APIRouter(prefix="/api/layers", tags=["Capas"])

# Registro de capas disponibles
LAYERS_CATALOG = [
    {
        "id": "limite_municipal",
        "name": "Límite Municipal",
        "schema": "cartografia",
        "table": "limite_municipal",
        "description": "Polígono del municipio de Apartadó",
        "geometry_type": "Polygon",
        "category": "cartografia",
    },
    {
        "id": "veredas_mgn",
        "name": "Veredas y Secciones Rurales (MGN 2019)",
        "schema": "cartografia",
        "table": "veredas_mgn",
        "description": "Límites de veredas y secciones rurales de Urabá",
        "geometry_type": "MultiPolygon",
        "category": "cartografia",
    },
    {
        "id": "manzanas_censales",
        "name": "Manzanas Censales (MGN 2018)",
        "schema": "cartografia",
        "table": "manzanas_censales",
        "description": "Manzanas del censo 2018 con datos de población",
        "geometry_type": "MultiPolygon",
        "category": "cartografia",
    },
    {
        "id": "igac_apartado",
        "name": "Municipio IGAC",
        "schema": "cartografia",
        "table": "igac_municipios",
        "description": "Polígono oficial IGAC de Apartadó",
        "geometry_type": "MultiPolygon",
        "category": "cartografia",
        "geom_col": "geometry",
    },
    {
        "id": "igac_uraba",
        "name": "Municipios de Urabá",
        "schema": "cartografia",
        "table": "igac_uraba",
        "description": "8 municipios de la región de Urabá",
        "geometry_type": "MultiPolygon",
        "category": "cartografia",
        "geom_col": "geometry",
    },
    {
        "id": "osm_edificaciones",
        "name": "Edificaciones (OSM)",
        "schema": "cartografia",
        "table": "osm_edificaciones",
        "description": "Edificaciones de OpenStreetMap",
        "geometry_type": "Polygon",
        "category": "osm",
    },
    {
        "id": "osm_vias",
        "name": "Red Vial (OSM)",
        "schema": "cartografia",
        "table": "osm_vias",
        "description": "Vías y calles de OpenStreetMap",
        "geometry_type": "LineString",
        "category": "osm",
    },
    {
        "id": "osm_uso_suelo",
        "name": "Uso del Suelo (OSM)",
        "schema": "cartografia",
        "table": "osm_uso_suelo",
        "description": "Clasificación de uso del suelo OSM",
        "geometry_type": "Polygon",
        "category": "osm",
    },
    {
        "id": "osm_amenidades",
        "name": "Amenidades (OSM)",
        "schema": "cartografia",
        "table": "osm_amenidades",
        "description": "Puntos de interés de OpenStreetMap",
        "geometry_type": "Point",
        "category": "osm",
    },
    {
        "id": "google_places",
        "name": "Negocios y Servicios (Google)",
        "schema": "servicios",
        "table": "google_places_regional",
        "description": "Establecimientos comerciales y servicios identificados en toda la región de Urabá",
        "geometry_type": "Point",
        "category": "economia",
    },
]


@router.get("")
@cached(ttl_seconds=600)
def list_layers():
    """Listar todas las capas disponibles con conteo de registros."""
    parts = [
        f"SELECT '{layer['id']}' AS id, COUNT(*) AS cnt FROM {layer['schema']}.{layer['table']}"
        for layer in LAYERS_CATALOG
    ]
    sql = " UNION ALL ".join(parts)
    counts = {}
    with engine.connect() as conn:
        for row in conn.execute(text(sql)).fetchall():
            counts[row[0]] = row[1]
    return [{**layer, "record_count": counts.get(layer["id"], 0)} for layer in LAYERS_CATALOG]


@router.get("/{layer_id}/geojson")
def get_layer_geojson(
    layer_id: str,
    dane_code: str = Query(None, description="Filtrar por código DANE"),
    limit: int = 5000
):
    """Obtener GeoJSON completo de una capa."""
    layer = next((l for l in LAYERS_CATALOG if l["id"] == layer_id), None)
    if not layer:
        raise HTTPException(status_code=404, detail=f"Capa '{layer_id}' no encontrada")

    gc = layer.get("geom_col", "geom")
    conditions = ["1=1"]
    params = {"lim": limit}
    
    # Try to filter by dane_code if the table likely has it
    if dane_code:
        # Check if column exists in the catalog definition? No, we don't store columns there.
        # We'll just assume for standard tables.
        if layer_id in ["limite_municipal", "manzanas_censales", "osm_edificaciones", 
                        "osm_vias", "osm_uso_suelo", "osm_amenidades"]:
            conditions.append("dane_code = :dane")
            params["dane"] = dane_code
    
    where = "WHERE " + " AND ".join(conditions)
    sql = f"SELECT * FROM {layer['schema']}.{layer['table']} {where} LIMIT :lim"
    return query_geojson(sql, params, geom_col=gc)


@router.get("/{layer_id}/stats")
def get_layer_stats(layer_id: str):
    """Estadísticas básicas de una capa (bbox, conteo, columnas)."""
    layer = next((l for l in LAYERS_CATALOG if l["id"] == layer_id), None)
    if not layer:
        raise HTTPException(status_code=404, detail=f"Capa '{layer_id}' no encontrada")

    gc = layer.get("geom_col", "geom")
    with engine.connect() as conn:
        count = conn.execute(
            text(f"SELECT COUNT(*) FROM {layer['schema']}.{layer['table']}")
        ).scalar()
        bbox = conn.execute(
            text(f"SELECT ST_Extent({gc})::text FROM {layer['schema']}.{layer['table']}")
        ).scalar()
        cols = conn.execute(
            text(
                "SELECT column_name, data_type FROM information_schema.columns "
                "WHERE table_schema = :s AND table_name = :t ORDER BY ordinal_position"
            ),
            {"s": layer["schema"], "t": layer["table"]},
        ).fetchall()

    return {
        "layer_id": layer_id,
        "name": layer["name"],
        "record_count": count,
        "bbox": bbox,
        "columns": [{"name": c[0], "type": c[1]} for c in cols],
    }
