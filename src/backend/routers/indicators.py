"""
Endpoints de indicadores socioeconómicos, educativos, seguridad
"""
from fastapi import APIRouter, Query, HTTPException
from ..database import engine, query_dicts
from sqlalchemy import text

router = APIRouter(prefix="/api/indicators", tags=["Indicadores"])

# Nombres de tablas estandarizados (sin _raw)
TABLES = {
    "icfes": "socioeconomico.icfes",
    "homicidios": "seguridad.homicidios",
    "hurtos": "seguridad.hurtos",
    "delitos_sexuales": "seguridad.delitos_sexuales",
    "vif": "seguridad.violencia_intrafamiliar",
    "victimas": "seguridad.victimas_conflicto",
    "colegios": "socioeconomico.establecimientos_educativos",
    "ips": "socioeconomico.ips_salud",
    "places": "servicios.google_places_regional"
}

INDICATORS_CATALOG = [
    {"id": "icfes_global", "name": "Puntaje ICFES Global", "category": "educacion"},
    {"id": "homicidios", "name": "Homicidios", "category": "seguridad"},
    {"id": "hurtos", "name": "Hurtos", "category": "seguridad"},
    {"id": "victimas_conflicto", "name": "Víctimas del Conflicto", "category": "seguridad"},
    {"id": "establecimientos_educativos", "name": "Colegios", "category": "educacion"},
    {"id": "ips_salud", "name": "IPS / Salud", "category": "salud"},
    {"id": "places_economia", "name": "Comercio y Servicios", "category": "economia"},
]

@router.get("")
def list_indicators():
    return INDICATORS_CATALOG

@router.get("/icfes")
def get_icfes(
    dane_code: str = Query(None),
    aggregate: str = Query("colegio")
):
    table = TABLES["icfes"]
    cond = ["1=1"]
    params = {"dane": dane_code}
    if dane_code: cond.append("dane_code = :dane")
    
    where = " AND ".join(cond)
    
    if aggregate == "periodo":
        sql = f"SELECT periodo, COUNT(*) as estudiantes, AVG(punt_global) as prom_global FROM {table} WHERE {where} GROUP BY periodo ORDER BY periodo"
    else:
        sql = f"SELECT cole_nombre as colegio, periodo, AVG(punt_global) as prom_global FROM {table} WHERE {where} GROUP BY cole_nombre, periodo ORDER BY prom_global DESC"
    
    try: return query_dicts(sql, params)
    except: return []

@router.get("/seguridad/serie")
def get_seguridad_serie(tipo: str = "homicidios", dane_code: str = Query(None)):
    table = TABLES.get(tipo, TABLES["homicidios"])
    cond = ["1=1"]
    params = {"dane": dane_code}
    if dane_code: cond.append("dane_code = :dane")
    
    sql = f"SELECT EXTRACT(YEAR FROM fecha)::int as anio, SUM(cantidad) as total FROM {table} WHERE {' AND '.join(cond)} GROUP BY anio ORDER BY anio"
    try: return query_dicts(sql, params)
    except: return []

@router.get("/terridata")
def get_terridata(dane_code: str = Query(None), dimension: str = Query(None)):
    cond = ["1=1"]
    params = {"dane": dane_code, "dim": dimension}
    if dane_code: cond.append("dane_code = :dane")
    if dimension: cond.append("dimension = :dim")
    
    sql = f"SELECT indicador, dato_numerico, anio, unidad_de_medida FROM socioeconomico.terridata WHERE {' AND '.join(cond)} ORDER BY anio DESC"
    try: return query_dicts(sql, params)
    except: return []

@router.get("/victimas")
def get_victimas(dane_code: str = Query(None)):
    params = {"dane": dane_code}
    where = "WHERE dane_code = :dane" if dane_code else ""
    sql = f"SELECT hecho as dimension, SUM(personas) as personas FROM seguridad.victimas_conflicto {where} GROUP BY hecho ORDER BY personas DESC"
    try: return query_dicts(sql, params)
    except: return []
