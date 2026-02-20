"""
Endpoints de indicadores socioeconómicos, educativos, salud, economía y seguridad
"""
from fastapi import APIRouter, Query, HTTPException
from ..database import engine, query_dicts
from sqlalchemy import text

router = APIRouter(prefix="/api/indicators", tags=["Indicadores"])

# Mapeo de tablas estandarizadas
TABLES = {
    "icfes": "socioeconomico.icfes",
    "homicidios": "seguridad.homicidios",
    "hurtos": "seguridad.hurtos",
    "vif": "seguridad.violencia_intrafamiliar",
    "delitos_sexuales": "seguridad.delitos_sexuales",
    "victimas": "seguridad.victimas_conflicto",
    "terridata": "socioeconomico.terridata",
    "ips": "socioeconomico.ips_salud",
    "establecimientos": "socioeconomico.establecimientos_educativos",
    "servicios": "socioeconomico.prestadores_servicios",
    "places": "servicios.google_places_regional"
}

@router.get("/icfes")
def get_icfes(dane_code: str = Query(None), aggregate: str = Query("colegio")):
    cond = ["1=1"]
    if dane_code: cond.append("dane_code = :dane")
    where = " AND ".join(cond)
    if aggregate == "periodo":
        sql = f"SELECT periodo, COUNT(*) as estudiantes, AVG(punt_global) as prom_global FROM {TABLES['icfes']} WHERE {where} GROUP BY periodo ORDER BY periodo"
    else:
        sql = f"SELECT cole_nombre as colegio, periodo, AVG(punt_global) as prom_global FROM {TABLES['icfes']} WHERE {where} GROUP BY cole_nombre, periodo ORDER BY prom_global DESC"
    return query_dicts(sql, {"dane": dane_code})

@router.get("/terridata")
def get_terridata(dane_code: str = Query(None), dimension: str = Query(None)):
    cond = ["1=1"]
    if dane_code: cond.append("dane_code = :dane")
    if dimension: cond.append("dimension = :dim")
    sql = f"SELECT dimension, indicador, dato_numerico, anio, unidad_de_medida FROM {TABLES['terridata']} WHERE {' AND '.join(cond)} ORDER BY anio DESC"
    return query_dicts(sql, {"dane": dane_code, "dim": dimension})

@router.get("/seguridad/serie")
def get_seguridad_serie(tipo: str = "homicidios", dane_code: str = Query(None)):
    table = TABLES.get(tipo, TABLES["homicidios"])
    cond = ["1=1"]
    if dane_code: cond.append("dane_code = :dane")
    sql = f"SELECT EXTRACT(YEAR FROM fecha)::int as anio, SUM(cantidad) as total FROM {table} WHERE {' AND '.join(cond)} GROUP BY anio ORDER BY anio"
    return query_dicts(sql, {"dane": dane_code})

@router.get("/victimas")
def get_victimas(dane_code: str = Query(None)):
    cond = ["1=1"]
    if dane_code: cond.append("dane_code = :dane")
    sql = f"SELECT hecho as dimension, SUM(personas) as personas FROM {TABLES['victimas']} WHERE {' AND '.join(cond)} GROUP BY hecho ORDER BY personas DESC"
    return query_dicts(sql, {"dane": dane_code})

@router.get("/salud/ips")
def get_ips(dane_code: str = Query(None)):
    cond = ["1=1"]
    if dane_code: cond.append("dane_code = :dane")
    sql = f"SELECT nombre, nivel_atencion, direccion, telefono FROM {TABLES['ips']} WHERE {' AND '.join(cond)} LIMIT 100"
    return query_dicts(sql, {"dane": dane_code})

# Endpoints de compatibilidad para evitar 404s
@router.get("/salud/irca")
def get_irca(dane_code: str = Query(None)):
    # Fallback to terridata if specific irca table doesn't exist
    sql = f"SELECT anio, dato_numerico as irca_total FROM {TABLES['terridata']} WHERE indicador ILIKE '%IRCA%' {'AND dane_code = :d' if dane_code else ''} ORDER BY anio"
    return query_dicts(sql, {"d": dane_code})

@router.get("/salud/sivigila/resumen")
def get_sivigila_resumen(dane_code: str = Query(None)):
    return [] # Placeholder

@router.get("/economia/internet/serie")
def get_internet_serie(dane_code: str = Query(None)):
    sql = f"SELECT anio, dato_numerico as total_accesos FROM {TABLES['terridata']} WHERE indicador ILIKE '%Internet%' {'AND dane_code = :d' if dane_code else ''} ORDER BY anio"
    return query_dicts(sql, {"d": dane_code})

@router.get("/economia/secop")
def get_secop_resumen(dane_code: str = Query(None)):
    return []

@router.get("/economia/turismo")
def get_turismo(dane_code: str = Query(None)):
    return {"total": 0, "detalle": []}

@router.get("/gobierno/finanzas")
def get_finanzas(dane_code: str = Query(None)):
    return get_terridata(dane_code, "Finanzas públicas")

@router.get("/gobierno/desempeno")
def get_desempeno(dane_code: str = Query(None)):
    return get_terridata(dane_code, "Medición de desempeño municipal")

@router.get("/gobierno/digital")
def get_gobierno_digital(dane_code: str = Query(None)):
    return []

@router.get("/gobierno/pobreza")
def get_pobreza(dane_code: str = Query(None)):
    return {"terridata": get_terridata(dane_code, "Pobreza"), "ipm_detalle": []}

@router.get("/cultura/espacios")
def get_espacios_culturales(dane_code: str = Query(None)):
    return []

@router.get("/cultura/turismo-detalle")
def get_turismo_detalle(dane_code: str = Query(None)):
    return {"total": 0, "por_categoria": {}}
