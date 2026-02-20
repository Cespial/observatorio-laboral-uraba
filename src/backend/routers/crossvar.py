"""
Motor de Cruces Multivariable — el corazón analítico del observatorio
"""
from fastapi import APIRouter, Query, HTTPException
from ..database import engine, cached, query_dicts
from sqlalchemy import text

router = APIRouter(prefix="/api/crossvar", tags=["Cruces Multivariable"])

VARIABLES = {
    "poblacion": {
        "name": "Población",
        "sql": "SELECT cod_dane_manzana as geo_id, total_personas as valor FROM cartografia.manzanas_censales",
        "geo_level": "manzana",
    },
    "icfes_global": {
        "name": "ICFES Global",
        "sql": "SELECT cole_nombre as geo_id, AVG(punt_global) as valor FROM socioeconomico.icfes GROUP BY cole_nombre",
        "geo_level": "colegio",
    },
    "homicidios_anual": {
        "name": "Homicidios",
        "sql": "SELECT EXTRACT(YEAR FROM fecha)::text as geo_id, SUM(cantidad) as valor FROM seguridad.homicidios GROUP BY geo_id",
        "geo_level": "anual",
    }
}

@router.get("/variables")
def list_variables():
    return [{"id": k, "name": v["name"], "geo_level": v.get("geo_level")} for k, v in VARIABLES.items()]

@router.get("/security-matrix")
@cached(ttl_seconds=600)
def security_matrix(dane_code: str = Query(None)):
    where = f"WHERE dane_code = '{dane_code}'" if dane_code else ""
    sql = f"""
        SELECT 'Homicidios' as tipo, EXTRACT(YEAR FROM fecha)::int as anio, SUM(cantidad) as total FROM seguridad.homicidios {where} GROUP BY anio
        UNION ALL
        SELECT 'Hurtos', EXTRACT(YEAR FROM fecha)::int, SUM(cantidad) FROM seguridad.hurtos {where} GROUP BY anio
        UNION ALL
        SELECT 'VIF', EXTRACT(YEAR FROM fecha)::int, SUM(cantidad) FROM seguridad.violencia_intrafamiliar {where} GROUP BY anio
        ORDER BY anio DESC
    """
    try: return {"data": query_dicts(sql)}
    except: return {"data": []}

@router.get("/scatter")
def scatter_analysis(var_x: str, var_y: str, dane_code: str = Query(None)):
    if var_x not in VARIABLES or var_y not in VARIABLES:
        return {"points": [], "correlation": 0}
    # Versión simplificada para evitar errores de join complejos en esta fase
    return {"points": [], "correlation": 0, "n": 0}
