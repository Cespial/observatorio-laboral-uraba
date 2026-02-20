"""
Motor de Cruces Multivariable
"""
from fastapi import APIRouter, Query
from ..database import engine, cached, query_dicts
from sqlalchemy import text

router = APIRouter(prefix="/api/crossvar", tags=["Cruces Multivariable"])

@router.get("/variables")
def list_variables():
    return [
        {"id": "poblacion", "name": "Población"},
        {"id": "icfes", "name": "ICFES"},
        {"id": "homicidios", "name": "Homicidios"}
    ]

@router.get("/security-matrix")
@cached(ttl_seconds=600)
def security_matrix(dane_code: str = Query(None)):
    where = f"WHERE dane_code = :d" if dane_code else "WHERE 1=1"
    sql = f"""
        SELECT 'Homicidios' as tipo, EXTRACT(YEAR FROM fecha)::int as anio, SUM(cantidad) as total FROM seguridad.homicidios {where} GROUP BY anio
        UNION ALL
        SELECT 'Hurtos', EXTRACT(YEAR FROM fecha)::int, SUM(cantidad) FROM seguridad.hurtos {where} GROUP BY anio
        UNION ALL
        SELECT 'VIF', EXTRACT(YEAR FROM fecha)::int, SUM(cantidad) FROM seguridad.violencia_intrafamiliar {where} GROUP BY anio
    """
    try: return {"data": query_dicts(sql, {"d": dane_code})}
    except: return {"data": []}

@router.get("/scatter")
def scatter_analysis(var_x: str, var_y: str, dane_code: str = Query(None)):
    return {"points": [], "correlation": 0, "n": 0}
