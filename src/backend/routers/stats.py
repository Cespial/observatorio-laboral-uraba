"""
Resumen ejecutivo regional y por municipio
"""
from fastapi import APIRouter, Query
from ..database import engine, cached, query_dicts
from sqlalchemy import text

router = APIRouter(prefix="/api/stats", tags=["Resumen"])

MUNICIPIOS = {
    "05045": "Apartadó", "05837": "Turbo", "05147": "Carepa", "05172": "Chigorodó",
    "05490": "Necoclí", "05051": "Arboletes", "05665": "San Pedro de Urabá",
    "05659": "San Juan de Urabá", "05480": "Mutatá", "05475": "Murindó",
    "05873": "Vigía del Fuerte"
}

@router.get("/summary")
@cached(ttl_seconds=600)
def get_summary(dane_code: str = Query(None)):
    stats = {
        "region": "Urabá",
        "municipio": MUNICIPIOS.get(dane_code, "Toda la Región"),
        "departamento": "Antioquia",
        "divipola": dane_code or "REGIONAL",
    }
    
    params = {"dane": dane_code} if dane_code else {}
    where = "WHERE dane_code = :dane" if dane_code else "WHERE 1=1"

    with engine.connect() as conn:
        # Población
        try:
            row = conn.execute(text(f"SELECT dato_numerico, anio FROM socioeconomico.terridata {where} AND indicador = 'Población total' ORDER BY anio DESC LIMIT 1"), params).fetchone()
            stats["poblacion_total"] = int(row[0]) if row else None
            stats["poblacion_anio"] = row[1] if row else None
        except: stats["poblacion_total"] = None

        # Homicidios
        try:
            stats["total_homicidios"] = conn.execute(text(f"SELECT SUM(cantidad) FROM seguridad.homicidios {where}"), params).scalar() or 0
        except: stats["total_homicidios"] = 0

        # Hurtos
        try:
            stats["total_hurtos"] = conn.execute(text(f"SELECT SUM(cantidad) FROM seguridad.hurtos {where}"), params).scalar() or 0
        except: stats["total_hurtos"] = 0

        # Educación
        try:
            stats["matricula_total"] = conn.execute(text(f"SELECT SUM(dato_numerico) FROM socioeconomico.terridata {where} AND indicador = 'Matrícula total'"), params).scalar() or 0
        except: stats["matricula_total"] = 0

        # Servicios (Google Places Regional)
        try:
            stats["establecimientos_comerciales"] = conn.execute(text(f"SELECT COUNT(*) FROM servicios.google_places_regional {where}"), params).scalar() or 0
        except: stats["establecimientos_comerciales"] = 0

    return stats

@router.get("/catalog-summary")
@cached(ttl_seconds=3600)
def get_catalog_summary():
    try:
        with engine.connect() as conn:
            row = conn.execute(text("SELECT COUNT(*), SUM(reltuples) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace WHERE n.nspname IN ('cartografia','socioeconomico','seguridad','servicios') AND c.relkind = 'r'")).fetchone()
            return {"tables": row[0] or 0, "records": int(row[1]) if row and row[1] else 0}
    except: return {"tables": 0, "records": 0}
