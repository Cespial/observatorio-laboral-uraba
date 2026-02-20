"""
Router para el mercado laboral y ofertas de empleo en Urabá
============================================================
Fuente: empleo.ofertas_laborales (PostgreSQL / Supabase)
Fallback: SQLite ~/uraba_empleos/empleos_uraba.db
"""
from fastapi import APIRouter, Query
from ..database import engine, cached, query_dicts
from sqlalchemy import text

router = APIRouter(prefix="/api/empleo", tags=["Empleo"])


def _table_exists():
    """Check if the PG table exists."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1 FROM empleo.ofertas_laborales LIMIT 1"))
        return True
    except Exception:
        return False


@router.get("/ofertas")
@cached(ttl_seconds=3600)
def get_ofertas(
    municipio: str = Query(None, description="Filtrar por municipio"),
    fuente: str = Query(None, description="Filtrar por fuente"),
    sector: str = Query(None, description="Filtrar por sector"),
    dane_code: str = Query(None, description="Filtrar por código DANE"),
    busqueda: str = Query(None, description="Buscar en título o descripción"),
    limit: int = Query(100, le=1000),
):
    """Listado de ofertas laborales."""
    conditions = ["1=1"]
    params = {"lim": limit}
    if municipio:
        conditions.append("municipio ILIKE :muni")
        params["muni"] = f"%{municipio}%"
    if fuente:
        conditions.append("fuente = :fuente")
        params["fuente"] = fuente
    if sector:
        conditions.append("sector = :sector")
        params["sector"] = sector
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code
    if busqueda:
        conditions.append("(titulo ILIKE :q OR descripcion ILIKE :q)")
        params["q"] = f"%{busqueda}%"

    where = " AND ".join(conditions)
    sql = f"""
        SELECT id, titulo, empresa, salario_texto, salario_numerico,
               municipio, dane_code, fuente, sector, skills,
               fecha_publicacion, enlace
        FROM empleo.ofertas_laborales
        WHERE {where}
        ORDER BY fecha_publicacion DESC NULLS LAST
        LIMIT :lim
    """
    return query_dicts(sql, params)


@router.get("/stats")
@cached(ttl_seconds=3600)
def get_empleo_stats(dane_code: str = Query(None)):
    """Estadísticas generales del mercado laboral."""
    conditions = ["1=1"]
    params = {}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code
    where = " AND ".join(conditions)

    total_rows = query_dicts(
        f"SELECT COUNT(*) as total FROM empleo.ofertas_laborales WHERE {where}", params
    )
    total = total_rows[0]["total"] if total_rows else 0

    por_municipio = query_dicts(f"""
        SELECT municipio, COUNT(*) as total
        FROM empleo.ofertas_laborales WHERE {where}
        GROUP BY municipio ORDER BY total DESC
    """, params)

    por_fuente = query_dicts(f"""
        SELECT fuente, COUNT(*) as total
        FROM empleo.ofertas_laborales WHERE {where}
        GROUP BY fuente ORDER BY total DESC
    """, params)

    por_sector = query_dicts(f"""
        SELECT sector, COUNT(*) as total
        FROM empleo.ofertas_laborales WHERE {where}
        GROUP BY sector ORDER BY total DESC
    """, params)

    emp_cond = f"{where} AND empresa IS NOT NULL AND empresa != 'No especificada'"
    top_empresas = query_dicts(f"""
        SELECT empresa, COUNT(*) as total
        FROM empleo.ofertas_laborales WHERE {emp_cond}
        GROUP BY empresa ORDER BY total DESC LIMIT 15
    """, params)

    sal_cond = f"{where} AND salario_numerico IS NOT NULL"
    con_sal_rows = query_dicts(
        f"SELECT COUNT(*) as total FROM empleo.ofertas_laborales WHERE {sal_cond}", params
    )
    con_salario = con_sal_rows[0]["total"] if con_sal_rows else 0

    sal_rows = query_dicts(f"""
        SELECT
            ROUND(AVG(salario_numerico)) as promedio,
            MIN(salario_numerico) as minimo,
            MAX(salario_numerico) as maximo,
            PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_numerico) as mediana
        FROM empleo.ofertas_laborales
        WHERE {sal_cond}
    """, params)
    ss = sal_rows[0] if sal_rows else {}

    return {
        "total_ofertas": total,
        "con_salario": con_salario,
        "salario_promedio": int(ss["promedio"]) if ss.get("promedio") else None,
        "salario_minimo": int(ss["minimo"]) if ss.get("minimo") else None,
        "salario_maximo": int(ss["maximo"]) if ss.get("maximo") else None,
        "salario_mediana": int(ss["mediana"]) if ss.get("mediana") else None,
        "por_municipio": por_municipio,
        "por_fuente": por_fuente,
        "por_sector": por_sector,
        "top_empresas": top_empresas,
    }


@router.get("/serie-temporal")
@cached(ttl_seconds=3600)
def get_empleo_serie_temporal(
    dane_code: str = Query(None),
    municipio: str = Query(None),
):
    """Serie temporal de ofertas agrupadas por mes."""
    conditions = ["fecha_publicacion IS NOT NULL"]
    params = {}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code
    if municipio:
        conditions.append("municipio ILIKE :muni")
        params["muni"] = f"%{municipio}%"

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            TO_CHAR(fecha_publicacion, 'YYYY-MM') as periodo,
            COUNT(*) as ofertas,
            COUNT(DISTINCT empresa) as empresas,
            ROUND(AVG(salario_numerico)) as salario_promedio
        FROM empleo.ofertas_laborales
        WHERE {where}
        GROUP BY TO_CHAR(fecha_publicacion, 'YYYY-MM')
        ORDER BY periodo
    """
    rows = query_dicts(sql, params)
    for r in rows:
        if r.get("salario_promedio"):
            r["salario_promedio"] = int(r["salario_promedio"])
    return rows


@router.get("/skills")
@cached(ttl_seconds=3600)
def get_skills_demand(
    dane_code: str = Query(None),
    sector: str = Query(None),
    limit: int = Query(25, le=50),
):
    """Top habilidades demandadas (extraídas de ofertas)."""
    conditions = ["1=1"]
    params = {"lim": limit}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code
    if sector:
        conditions.append("sector = :sector")
        params["sector"] = sector

    where = " AND ".join(conditions)
    sql = f"""
        SELECT skill, COUNT(*) as demanda
        FROM empleo.ofertas_laborales, UNNEST(skills) AS skill
        WHERE {where}
        GROUP BY skill
        ORDER BY demanda DESC
        LIMIT :lim
    """
    return query_dicts(sql, params)


@router.get("/salarios")
@cached(ttl_seconds=3600)
def get_salary_analysis(
    dane_code: str = Query(None),
):
    """Análisis de salarios por sector y municipio."""
    conditions = ["salario_numerico IS NOT NULL"]
    params = {}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    where = " AND ".join(conditions)

    with engine.connect() as conn:
        por_sector = conn.execute(text(f"""
            SELECT sector,
                   COUNT(*) as ofertas,
                   ROUND(AVG(salario_numerico)) as promedio,
                   MIN(salario_numerico) as minimo,
                   MAX(salario_numerico) as maximo
            FROM empleo.ofertas_laborales
            WHERE {where}
            GROUP BY sector
            HAVING COUNT(*) >= 2
            ORDER BY promedio DESC
        """), params).fetchall()

        por_municipio = conn.execute(text(f"""
            SELECT municipio,
                   COUNT(*) as ofertas,
                   ROUND(AVG(salario_numerico)) as promedio,
                   MIN(salario_numerico) as minimo,
                   MAX(salario_numerico) as maximo
            FROM empleo.ofertas_laborales
            WHERE {where}
            GROUP BY municipio
            ORDER BY promedio DESC
        """), params).fetchall()

        rangos = conn.execute(text(f"""
            SELECT
                CASE
                    WHEN salario_numerico < 1300000 THEN '< SMMLV'
                    WHEN salario_numerico < 2000000 THEN '1-2 SMMLV'
                    WHEN salario_numerico < 3000000 THEN '2-3 SMMLV'
                    WHEN salario_numerico < 5000000 THEN '3-5 SMMLV'
                    ELSE '> 5 SMMLV'
                END as rango,
                COUNT(*) as ofertas
            FROM empleo.ofertas_laborales
            WHERE {where}
            GROUP BY rango
            ORDER BY MIN(salario_numerico)
        """), params).fetchall()

    return {
        "por_sector": [
            {"sector": r[0], "ofertas": r[1], "promedio": int(r[2]), "minimo": r[3], "maximo": r[4]}
            for r in por_sector
        ],
        "por_municipio": [
            {"municipio": r[0], "ofertas": r[1], "promedio": int(r[2]), "minimo": r[3], "maximo": r[4]}
            for r in por_municipio
        ],
        "rangos": [{"rango": r[0], "ofertas": r[1]} for r in rangos],
    }


@router.get("/sectores")
@cached(ttl_seconds=3600)
def get_sectores_detalle(
    dane_code: str = Query(None),
):
    """Desglose detallado por sector económico."""
    conditions = ["1=1"]
    params = {}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            sector,
            COUNT(*) as ofertas,
            COUNT(DISTINCT empresa) as empresas,
            COUNT(DISTINCT municipio) as municipios,
            ROUND(AVG(salario_numerico)) as salario_promedio,
            COUNT(CASE WHEN salario_numerico IS NOT NULL THEN 1 END) as con_salario
        FROM empleo.ofertas_laborales
        WHERE {where}
        GROUP BY sector
        ORDER BY ofertas DESC
    """
    rows = query_dicts(sql, params)
    for r in rows:
        if r.get("salario_promedio"):
            r["salario_promedio"] = int(r["salario_promedio"])
    return rows


@router.get("/empresas")
@cached(ttl_seconds=3600)
def get_empresas_ranking(
    dane_code: str = Query(None),
    limit: int = Query(20, le=50),
):
    """Ranking de empresas que más contratan."""
    conditions = ["empresa IS NOT NULL", "empresa != 'No especificada'"]
    params = {"lim": limit}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    where = " AND ".join(conditions)
    sql = f"""
        SELECT
            empresa,
            COUNT(*) as ofertas,
            COUNT(DISTINCT sector) as sectores,
            COUNT(DISTINCT municipio) as municipios,
            ROUND(AVG(salario_numerico)) as salario_promedio
        FROM empleo.ofertas_laborales
        WHERE {where}
        GROUP BY empresa
        ORDER BY ofertas DESC
        LIMIT :lim
    """
    rows = query_dicts(sql, params)
    for r in rows:
        if r.get("salario_promedio"):
            r["salario_promedio"] = int(r["salario_promedio"])
    return rows


@router.get("/mapa-calor")
@cached(ttl_seconds=3600)
def get_empleo_heatmap():
    """Datos para mapa de calor de ofertas por municipio (usando centroides)."""
    sql = """
        SELECT
            o.municipio,
            o.dane_code,
            COUNT(*) as ofertas,
            ST_Y(ST_Centroid(lm.geom)) as lat,
            ST_X(ST_Centroid(lm.geom)) as lon
        FROM empleo.ofertas_laborales o
        JOIN cartografia.limite_municipal lm ON o.dane_code = lm.dane_code
        WHERE o.dane_code IS NOT NULL
        GROUP BY o.municipio, o.dane_code, lm.geom
        ORDER BY ofertas DESC
    """
    return query_dicts(sql)


@router.get("/fuentes")
def list_fuentes():
    """Listar fuentes de empleo disponibles."""
    sql = """
        SELECT fuente, COUNT(*) as total
        FROM empleo.ofertas_laborales
        GROUP BY fuente ORDER BY total DESC
    """
    return query_dicts(sql)


@router.get("/kpis")
@cached(ttl_seconds=3600)
def get_empleo_kpis(dane_code: str = Query(None)):
    """KPIs principales del mercado laboral para el dashboard."""
    conditions = ["1=1"]
    params = {}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    where = " AND ".join(conditions)
    with engine.connect() as conn:
        row = conn.execute(text(f"""
            SELECT
                COUNT(*) as total_ofertas,
                COUNT(DISTINCT empresa) as total_empresas,
                COUNT(DISTINCT sector) as total_sectores,
                ROUND(AVG(salario_numerico)) as salario_promedio,
                (SELECT sector FROM empleo.ofertas_laborales WHERE {where}
                 GROUP BY sector ORDER BY COUNT(*) DESC LIMIT 1) as sector_top,
                (SELECT empresa FROM empleo.ofertas_laborales
                 WHERE {where} AND empresa IS NOT NULL AND empresa != 'No especificada'
                 GROUP BY empresa ORDER BY COUNT(*) DESC LIMIT 1) as empresa_top
            FROM empleo.ofertas_laborales
            WHERE {where}
        """), params).fetchone()

    return {
        "total_ofertas": row[0] if row else 0,
        "total_empresas": row[1] if row else 0,
        "total_sectores": row[2] if row else 0,
        "salario_promedio": int(row[3]) if row and row[3] else None,
        "sector_top": row[4] if row else None,
        "empresa_top": row[5] if row else None,
    }
