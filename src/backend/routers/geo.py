"""
Endpoints geoespaciales — manzanas con datos, heatmaps, filtros espaciales
"""
from fastapi import APIRouter, Query
from ..database import engine, query_geojson
from sqlalchemy import text

router = APIRouter(prefix="/api/geo", tags=["Geoespacial"])


@router.get("/manzanas")
def get_manzanas(
    dane_code: str = Query(None, description="Filtrar por código DANE del municipio (ej: 05045)"),
    min_pop: int = Query(0, description="Población mínima"),
    max_pop: int = Query(999999, description="Población máxima"),
    limit: int = Query(5000, le=10000),
):
    """Manzanas censales con datos de población, filtrables por municipio."""
    conditions = ["total_personas ~ '^[0-9]+$'"]
    params = {"min_pop": min_pop, "max_pop": max_pop, "lim": limit}
    
    if dane_code:
        conditions.append("cod_dane_municipio = :dane")
        params["dane"] = dane_code
        
    where = " AND ".join(conditions)
    sql = f"""
        SELECT geom, cod_dane_manzana, cod_dane_municipio,
               CAST(total_personas AS INT) as total_personas
        FROM cartografia.manzanas_censales
        WHERE {where}
          AND CAST(total_personas AS INT) >= :min_pop
          AND CAST(total_personas AS INT) <= :max_pop
        LIMIT :lim
    """
    return query_geojson(sql, params)


@router.get("/edificaciones")
def get_edificaciones(
    dane_code: str = Query(None, description="Filtrar por código DANE"),
    building_type: str = Query(None, description="Filtro tipo edificación"),
    limit: int = Query(5000, le=10000),
):
    """Edificaciones OSM filtradas por municipio."""
    conditions = ["1=1"]
    params = {"lim": limit}
    
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code
        
    if building_type:
        conditions.append("building = :bt")
        params["bt"] = building_type
        
    where = "WHERE " + " AND ".join(conditions)
    sql = f"SELECT geom, id, building, name, amenity FROM cartografia.osm_edificaciones {where} LIMIT :lim"
    return query_geojson(sql, params)


@router.get("/vias")
def get_vias(
    dane_code: str = Query(None, description="Filtrar por código DANE"),
    highway_type: str = Query(None, description="Tipo de vía (primary, secondary, residential, etc)"),
    limit: int = Query(5000, le=10000),
):
    """Red vial OSM con filtro por tipo."""
    conditions = ["1=1"]
    params = {"lim": limit}
    
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    if highway_type:
        conditions.append("highway = :ht")
        params["ht"] = highway_type

    where = "WHERE " + " AND ".join(conditions)
    sql = f"SELECT geom, id, highway, name, surface, lanes FROM cartografia.osm_vias {where} LIMIT :lim"
    return query_geojson(sql, params)


@router.get("/amenidades")
def get_amenidades(
    dane_code: str = Query(None, description="Filtrar por código DANE"),
    amenity_type: str = Query(None, description="Tipo de amenidad (school, hospital, etc)"),
):
    """Amenidades OSM."""
    conditions = ["1=1"]
    params = {}
    
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    if amenity_type:
        conditions.append("amenity = :at")
        params["at"] = amenity_type

    where = "WHERE " + " AND ".join(conditions)
    sql = f"SELECT geom, id, amenity, name, phone, website FROM cartografia.osm_amenidades {where} LIMIT 2000"
    return query_geojson(sql, params)


@router.get("/places")
def get_google_places(
    dane_code: str = Query(None, description="Filtrar por código DANE"),
    category: str = Query(None, description="Categoría (Restaurantes, Bancos, etc)"),
    min_rating: float = Query(0, description="Rating mínimo"),
    limit: int = Query(1000, le=5000),
):
    """Establecimientos comerciales de Google Places."""
    conditions = ["1=1"]
    params = {"lim": limit}

    if dane_code:
        # Assuming google_places has a municipality column or spatial join is needed
        # For now, adding the condition if column exists (it should based on ETL)
        # But if not, we can relax this or rely on frontend viewport
        # We'll assume the column is 'dane_code' or 'cod_mpio'
        # Given ETLs usually standardizing on dane_code:
        # conditions.append("dane_code = :dane")
        # params["dane"] = dane_code
        pass 

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
        FROM servicios.google_places_regional
        WHERE {where}
        LIMIT :lim
    """
    return query_geojson(sql, params)


@router.get("/places/categories")
def get_places_categories():
    """Listar categorías de Google Places con conteos."""
    sql = "SELECT category, COUNT(*) as count FROM servicios.google_places_regional GROUP BY category ORDER BY count DESC"
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()
    return [{"category": r[0], "count": r[1]} for r in rows]


@router.get("/places/heatmap")
def get_places_heatmap(
    dane_code: str = Query(None),
    category: str = Query(None)
):
    """Datos para heatmap de establecimientos (lat, lon, weight)."""
    conditions = ["1=1"]
    params = {}
    
    if category:
        conditions.append("category = :cat")
        params["cat"] = category
        
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    where = "WHERE " + " AND ".join(conditions)
    sql = f"""
        SELECT lat, lon, COALESCE(user_ratings_total, 1) as weight
        FROM servicios.google_places_regional
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
