"""
Resumen ejecutivo del municipio — dashboard summary
"""
from fastapi import APIRouter, Query
from ..database import engine, cached
from sqlalchemy import text

router = APIRouter(prefix="/api/stats", tags=["Resumen"])

MUNICIPIOS = {
    "05045": "Apartadó",
    "05837": "Turbo",
    "05147": "Carepa",
    "05172": "Chigorodó",
    "05490": "Necoclí",
    "05051": "Arboletes",
    "05665": "San Pedro de Urabá",
    "05659": "San Juan de Urabá",
    "05480": "Mutatá",
    "05475": "Murindó",
    "05873": "Vigía del Fuerte"
}

@router.get("/summary")
@cached(ttl_seconds=600)
def get_summary(
    dane_code: str = Query(None, description="Filtrar por código DANE del municipio")
):
    """
    Resumen ejecutivo regional o por municipio.
    """
    stats = {
        "region": "Urabá",
        "municipio": MUNICIPIOS.get(dane_code, "Toda la Región"),
        "departamento": "Antioquia",
        "divipola": dane_code or "REGIONAL",
    }

    where_terridata = "WHERE codigo_municipio = :dane" if dane_code else ""
    where_icfes = "WHERE cole_cod_mcpio_ubicacion = :dane" if dane_code else ""
    where_seguridad = "WHERE codigo_dane = :dane" if dane_code else ""
    where_manzanas = "WHERE cod_dane_municipio = :dane" if dane_code else ""
    
    params = {"dane": dane_code} if dane_code else {}

    with engine.connect() as conn:
        # 1. Población
        try:
            pop_sql = f"SELECT dato_numerico, anio FROM socioeconomico.terridata {where_terridata} {'AND' if dane_code else 'WHERE'} indicador = 'Población total' ORDER BY anio DESC LIMIT 1"
            pop_row = conn.execute(text(pop_sql), params).fetchone()
            stats["poblacion_total"] = int(float(pop_row[0])) if pop_row else None
            stats["poblacion_anio"] = pop_row[1] if pop_row else None
        except: stats["poblacion_total"] = None

        # 2. Manzanas
        try:
            stats["manzanas_censales"] = conn.execute(text(f"SELECT COUNT(*) FROM cartografia.manzanas_censales {where_manzanas}"), params).scalar()
        except: stats["manzanas_censales"] = 0

        # 3. Negocios (Google Places Regional)
        try:
            stats["establecimientos_comerciales"] = conn.execute(text(f"SELECT COUNT(*) FROM servicios.google_places_regional {where_seguridad.replace('codigo_dane', 'dane_code')}"), params).scalar()
        except: stats["establecimientos_comerciales"] = 0

        # 4. Educación
        try:
            icfes = conn.execute(text(f"SELECT COUNT(DISTINCT cole_nombre_establecimiento), AVG(CAST(punt_global AS FLOAT)) FROM socioeconomico.icfes_raw {where_icfes} {'AND' if dane_code else 'WHERE'} punt_global IS NOT NULL"), params).fetchone()
            stats["establecimientos_educativos"] = icfes[0]
            stats["icfes"] = {"promedio_global": round(float(icfes[1]), 1) if icfes[1] else None}
        except:
            stats["establecimientos_educativos"] = 0
            stats["icfes"] = {"promedio_global": None}

        # 5. Matrícula
        try:
            mat_sql = f"SELECT SUM(dato_numerico) FROM socioeconomico.terridata {where_terridata} {'AND' if dane_code else 'WHERE'} indicador = 'Matrícula total'"
            stats["matricula_total"] = int(float(conn.execute(text(mat_sql), params).scalar() or 0))
        except: stats["matricula_total"] = 0

        # 6. Salud (IPS)
        try:
            stats["ips_salud"] = conn.execute(text(f"SELECT COUNT(*) FROM socioeconomico.ips_raw {where_seguridad.replace('codigo_dane', 'municipioprestadordesc')}"), params).scalar()
        except: stats["ips_salud"] = 0

        # 7. Seguridad
        for table, key in [("homicidios_raw", "total_homicidios"), ("hurtos_raw", "total_hurtos"), ("violencia_intrafamiliar_raw", "total_vif")]:
            try:
                val = conn.execute(text(f"SELECT SUM(CAST(cantidad AS INT)) FROM seguridad.{table} {where_seguridad}"), params).scalar()
                stats[key] = int(val) if val else 0
            except: stats[key] = 0

        # 8. Víctimas
        try:
            stats["total_victimas_conflicto"] = conn.execute(text(f"SELECT SUM(CAST(per_ocu AS INT)) FROM seguridad.victimas_raw {where_seguridad.replace('codigo_dane', 'cod_municipio')}"), params).scalar()
        except: stats["total_victimas_conflicto"] = 0

        # 9. Prestadores Servicios
        try:
            stats["prestadores_servicios"] = conn.execute(text(f"SELECT COUNT(*) FROM servicios.prestadores_raw {where_seguridad.replace('codigo_dane', 'municipio')}"), params).scalar()
        except: stats["prestadores_servicios"] = 0

    return stats
