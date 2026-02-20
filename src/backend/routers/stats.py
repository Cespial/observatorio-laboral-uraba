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
    # Standardize dane_code to 5 digits if present
    dane = dane_code.zfill(5) if dane_code and dane_code.isdigit() else dane_code
    
    stats = {
        "region": "Urabá",
        "municipio": MUNICIPIOS.get(dane, "Toda la Región"),
        "departamento": "Antioquia",
        "divipola": dane or "REGIONAL",
    }
    
    params = {"dane": dane} if dane else {}
    where = "WHERE dane_code = :dane" if dane else "WHERE 1=1"

    with engine.connect() as conn:
        # 1. Población (Desde TerriData - Ya cargado para todos)
        try:
            row = conn.execute(text(f"SELECT dato_numerico, anio FROM socioeconomico.terridata {where} AND indicador = 'Población total' ORDER BY anio DESC LIMIT 1"), params).fetchone()
            stats["poblacion_total"] = int(row[0]) if row else None
            stats["poblacion_anio"] = row[1] if row else None
        except: stats["poblacion_total"] = None

        # 2. Homicidios (Intentar tabla seguridad, fallback a TerriData)
        try:
            h_val = conn.execute(text(f"SELECT SUM(cantidad) FROM seguridad.homicidios {where}"), params).scalar()
            if not h_val and dane:
                # Fallback to TerriData
                h_val = conn.execute(text(f"SELECT dato_numerico FROM socioeconomico.terridata {where} AND indicador = 'Número de homicidios' ORDER BY anio DESC LIMIT 1"), params).scalar()
            stats["total_homicidios"] = int(h_val) if h_val else 0
        except: stats["total_homicidios"] = 0

        # 3. Hurtos
        try:
            hu_val = conn.execute(text(f"SELECT SUM(cantidad) FROM seguridad.hurtos {where}"), params).scalar()
            stats["total_hurtos"] = int(hu_val) if hu_val else 0
        except: stats["total_hurtos"] = 0

        # 4. Educación (Matrícula)
        try:
            m_val = conn.execute(text(f"SELECT SUM(dato_numerico) FROM socioeconomico.terridata {where} AND indicador = 'Matrícula total'"), params).scalar()
            stats["matricula_total"] = int(m_val) if m_val else 0
        except: stats["matricula_total"] = 0

        # 5. Negocios (Google Places Regional - Ya cargado para todos)
        try:
            stats["establecimientos_comerciales"] = conn.execute(text(f"SELECT COUNT(*) FROM servicios.google_places_regional {where}"), params).scalar() or 0
        except: stats["establecimientos_comerciales"] = 0

    return stats

@router.get("/catalog-summary")
@cached(ttl_seconds=3600)
def get_catalog_summary():
    try:
        with engine.connect() as conn:
            # Safer query for record count
            sql = """
                SELECT COUNT(*) as tables, 
                       COALESCE(SUM(n_live_tup), 0) as records 
                FROM pg_stat_user_tables 
                WHERE schemaname IN ('cartografia','socioeconomico','seguridad','servicios','catastro')
            """
            row = conn.execute(text(sql)).fetchone()
            return {"tables": row[0] or 0, "records": int(row[1]) if row and row[1] else 0}
    except Exception as e: 
        print(f"Catalog summary error: {e}")
        return {"tables": 0, "records": 0}
