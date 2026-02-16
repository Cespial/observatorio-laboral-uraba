"""
Endpoints geoespaciales — manzanas con datos, heatmaps, filtros espaciales
"""
from fastapi import APIRouter, Query
from ..database import engine, query_geojson
from sqlalchemy import text

router = APIRouter(prefix="/api/geo", tags=["Geoespacial"])


@router.get("/manzanas")
def get_manzanas(
    min_pop: int = Query(0, description="Población mínima"),
    max_pop: int = Query(999999, description="Población máxima"),
    limit: int = Query(5000, le=10000),
):
    """Manzanas censales con datos de población, filtrables."""
    sql = """
        SELECT geom, cod_dane_manzana, cod_dane_municipio,
               CAST(total_personas AS INT) as total_personas
        FROM cartografia.manzanas_censales
        WHERE total_personas ~ '^[0-9]+$'
          AND CAST(total_personas AS INT) >= :min_pop
          AND CAST(total_personas AS INT) <= :max_pop
        LIMIT :lim
    """
    return query_geojson(sql, {"min_pop": min_pop, "max_pop": max_pop, "lim": limit})


@router.get("/edificaciones")
def get_edificaciones(
    building_type: str = Query(None, description="Filtro tipo edificación (ej: 'residential', 'commercial')"),
    limit: int = Query(5000, le=10000),
):
    """Edificaciones OSM con filtro por tipo."""
    where = ""
    params = {"lim": limit}
    if building_type:
        where = "WHERE building = :bt"
        params["bt"] = building_type
    sql = f"SELECT geom, id, building, name, amenity FROM cartografia.osm_edificaciones {where} LIMIT :lim"
    return query_geojson(sql, params)


@router.get("/vias")
def get_vias(
    highway_type: str = Query(None, description="Tipo de vía (primary, secondary, residential, etc)"),
    limit: int = Query(5000, le=10000),
):
    """Red vial OSM con filtro por tipo."""
    where = ""
    params = {"lim": limit}
    if highway_type:
        where = "WHERE highway = :ht"
        params["ht"] = highway_type
    sql = f"SELECT geom, id, highway, name, surface, lanes FROM cartografia.osm_vias {where} LIMIT :lim"
    return query_geojson(sql, params)


@router.get("/amenidades")
def get_amenidades(
    amenity_type: str = Query(None, description="Tipo de amenidad (school, hospital, etc)"),
):
    """Amenidades OSM."""
    where = ""
    params = {}
    if amenity_type:
        where = "WHERE amenity = :at"
        params["at"] = amenity_type
    sql = f"SELECT geom, id, amenity, name, phone, website FROM cartografia.osm_amenidades {where} LIMIT 2000"
    return query_geojson(sql, params)


@router.get("/places")
def get_google_places(
    category: str = Query(None, description="Categoría (Restaurantes, Bancos, etc)"),
    min_rating: float = Query(0, description="Rating mínimo"),
    limit: int = Query(1000, le=5000),
):
    """Establecimientos comerciales de Google Places."""
    conditions = ["1=1"]
    params = {"lim": limit}
    if category:
        conditions.append("category = :cat")
        params["cat"] = category
    if min_rating > 0:
        conditions.append("COALESCE(rating, 0) >= :mr")
        params["mr"] = min_rating

    where = " AND ".join(conditions)
    sql = f"""
        SELECT geom, place_id, name, category, address, rating,
               user_ratings_total, price_level, lat, lon
        FROM servicios.google_places
        WHERE {where}
        LIMIT :lim
    """
    return query_geojson(sql, params)


@router.get("/places/categories")
def get_places_categories():
    """Listar categorías de Google Places con conteos."""
    sql = "SELECT category, COUNT(*) as count FROM servicios.google_places GROUP BY category ORDER BY count DESC"
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
    return [{"category": r[0], "count": r[1]} for r in rows]


@router.get("/places/heatmap")
def get_places_heatmap(category: str = Query(None)):
    """Datos para heatmap de establecimientos (lat, lon, weight)."""
    where = ""
    params = {}
    if category:
        where = "WHERE category = :cat"
        params["cat"] = category
    sql = f"""
        SELECT lat, lon, COALESCE(user_ratings_total, 1) as weight
        FROM servicios.google_places
        {where}
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).fetchall()
    return [{"lat": float(r[0]), "lon": float(r[1]), "weight": int(r[2])} for r in rows]


@router.get("/uraba")
def get_uraba_region():
    """Municipios de la región de Urabá para contexto regional."""
    sql = """
        SELECT geometry, "MpCodigo" as codigo, "MpNombre" as nombre,
               "MpArea" as area_km2, "Depto" as departamento
        FROM cartografia.igac_uraba
    """
    return query_geojson(sql, geom_col="geometry")
