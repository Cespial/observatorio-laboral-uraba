"""
Módulo de Analítica Avanzada — Inteligencia Territorial y Laboral para Urabá
"""
from fastapi import APIRouter, Query, HTTPException
from ..database import engine, cached, query_dicts
from sqlalchemy import text

router = APIRouter(prefix="/api/analytics", tags=["Analytics"])


@router.get("/gaps")
@cached(ttl_seconds=3600)
def get_gaps(
    dane_code: str = Query("05045", description="Código DANE del municipio"),
    indicador: str = Query("Población total", description="Indicador a comparar"),
):
    """Brecha entre un municipio y el promedio regional."""
    sql = """
        WITH regional_avg AS (
            SELECT indicador, AVG(dato_numerico) as avg_val, anio
            FROM socioeconomico.terridata
            WHERE indicador = :indicador
            GROUP BY indicador, anio
            ORDER BY anio DESC
            LIMIT 1
        ),
        muni_val AS (
            SELECT entidad, dato_numerico as muni_val, anio
            FROM socioeconomico.terridata
            WHERE indicador = :indicador AND dane_code = :dane_code
            ORDER BY anio DESC
            LIMIT 1
        )
        SELECT
            m.entidad as municipio,
            m.muni_val as valor_municipio,
            r.avg_val as promedio_regional,
            (m.muni_val - r.avg_val) as brecha_absoluta,
            CASE WHEN r.avg_val != 0 THEN ((m.muni_val - r.avg_val) / r.avg_val) * 100 ELSE 0 END as brecha_porcentual,
            m.anio
        FROM muni_val m, regional_avg r
    """
    results = query_dicts(sql, {"dane_code": dane_code, "indicador": indicador})
    if not results:
        raise HTTPException(status_code=404, detail="No se encontraron datos")
    return results[0]


@router.get("/ranking")
@cached(ttl_seconds=3600)
def get_ranking(
    indicador: str = Query("Población total"),
    order: str = Query("desc", enum=["asc", "desc"]),
):
    """Ranking de municipios por indicador TerriData."""
    safe_order = "DESC" if order == "desc" else "ASC"
    sql = f"""
        WITH latest_data AS (
            SELECT DISTINCT ON (entidad)
                entidad as municipio,
                dane_code,
                dato_numerico as valor,
                anio
            FROM socioeconomico.terridata
            WHERE indicador = :indicador
            ORDER BY entidad, anio DESC
        )
        SELECT * FROM latest_data
        ORDER BY valor {safe_order}
    """
    return query_dicts(sql, {"indicador": indicador})


@router.get("/laboral/termometro")
@cached(ttl_seconds=1800)
def get_termometro_laboral():
    """Termómetro Laboral: Intensidad de ofertas recientes por municipio."""
    sql = """
        SELECT
            municipio,
            COUNT(CASE WHEN fecha_publicacion >= CURRENT_DATE - INTERVAL '7 days' THEN 1 END) as ultimos_7_dias,
            COUNT(CASE WHEN fecha_publicacion < CURRENT_DATE - INTERVAL '7 days'
                       AND fecha_publicacion >= CURRENT_DATE - INTERVAL '14 days' THEN 1 END) as anteriores_7_dias,
            COUNT(CASE WHEN fecha_publicacion >= CURRENT_DATE - INTERVAL '30 days' THEN 1 END) as ultimos_30_dias,
            COUNT(*) as total
        FROM empleo.ofertas_laborales
        GROUP BY municipio
        ORDER BY total DESC
    """
    rows = query_dicts(sql)
    for r in rows:
        prev = r.get("anteriores_7_dias", 0) or 1
        r["tendencia"] = round(((r.get("ultimos_7_dias", 0) - r.get("anteriores_7_dias", 0)) / prev) * 100, 1)
    return rows


@router.get("/laboral/oferta-demanda")
@cached(ttl_seconds=3600)
def get_oferta_demanda():
    """Oferta laboral vs demanda potencial (población)."""
    sql = """
        WITH ofertas AS (
            SELECT municipio, dane_code, COUNT(*) as vacantes
            FROM empleo.ofertas_laborales
            WHERE dane_code IS NOT NULL
            GROUP BY municipio, dane_code
        ),
        poblacion AS (
            SELECT DISTINCT ON (dane_code)
                dane_code, entidad as municipio_pop, dato_numerico as poblacion, anio
            FROM socioeconomico.terridata
            WHERE indicador = 'Población total'
            ORDER BY dane_code, anio DESC
        )
        SELECT
            p.municipio_pop as municipio,
            o.dane_code,
            COALESCE(o.vacantes, 0) as vacantes,
            p.poblacion,
            CASE WHEN p.poblacion > 0
                THEN ROUND((COALESCE(o.vacantes, 0)::numeric / p.poblacion) * 1000, 2)
                ELSE 0
            END as vacantes_por_1000_hab,
            p.anio as anio_poblacion
        FROM poblacion p
        LEFT JOIN ofertas o ON p.dane_code = o.dane_code
        ORDER BY vacantes_por_1000_hab DESC
    """
    return query_dicts(sql)


@router.get("/laboral/brecha-skills")
@cached(ttl_seconds=3600)
def get_brecha_skills(dane_code: str = Query(None)):
    """Brecha de habilidades: skills demandadas vs formación disponible en la región."""
    conditions = ["1=1"]
    params = {}
    if dane_code:
        conditions.append("dane_code = :dane")
        params["dane"] = dane_code

    where = " AND ".join(conditions)

    with engine.connect() as conn:
        # Skills demand
        skills = conn.execute(text(f"""
            SELECT skill, COUNT(*) as demanda
            FROM empleo.ofertas_laborales, UNNEST(skills) AS skill
            WHERE {where}
            GROUP BY skill
            ORDER BY demanda DESC
            LIMIT 20
        """), params).fetchall()

        # Sector distribution of demand
        sectores = conn.execute(text(f"""
            SELECT sector, COUNT(*) as ofertas,
                   COUNT(DISTINCT empresa) as empresas
            FROM empleo.ofertas_laborales
            WHERE {where}
            GROUP BY sector
            ORDER BY ofertas DESC
        """), params).fetchall()

        # Education level indicators (from ICFES as proxy for human capital)
        edu = conn.execute(text("""
            SELECT
                ROUND(AVG(punt_global)::numeric, 1) as icfes_promedio,
                COUNT(DISTINCT cole_nombre) as colegios,
                SUM(estudiantes) as total_estudiantes
            FROM socioeconomico.icfes
            WHERE punt_global IS NOT NULL
        """)).fetchone()

    total_demanda = sum(s[1] for s in skills)

    return {
        "skills_demandadas": [
            {"skill": s[0], "demanda": s[1], "pct": round(s[1] / total_demanda * 100, 1) if total_demanda > 0 else 0}
            for s in skills
        ],
        "sectores_con_demanda": [
            {"sector": s[0], "ofertas": s[1], "empresas": s[2]}
            for s in sectores
        ],
        "capital_humano": {
            "icfes_promedio": float(edu[0]) if edu and edu[0] else None,
            "colegios": edu[1] if edu else 0,
            "estudiantes_evaluados": edu[2] if edu else 0,
        },
        "insights": _generate_skill_insights(skills, sectores),
    }


def _generate_skill_insights(skills, sectores):
    insights = []
    if skills:
        top = skills[0]
        insights.append(f"La habilidad más demandada es {top[0]} con {top[1]} menciones en ofertas.")
    if sectores:
        top_sector = sectores[0]
        insights.append(f"El sector con más demanda es {top_sector[0]} con {top_sector[1]} ofertas de {top_sector[2]} empresas.")

    # Check for tech skills
    tech_skills = [s for s in skills if s[0] in ('Python', 'SQL', 'SAP', 'Excel')]
    if tech_skills:
        total_tech = sum(s[1] for s in tech_skills)
        insights.append(f"Las habilidades tecnológicas (Excel, SAP, SQL, Python) aparecen en {total_tech} ofertas.")

    return insights


@router.get("/laboral/dinamismo")
@cached(ttl_seconds=3600)
def get_dinamismo_laboral():
    """Índice de dinamismo laboral: velocidad de publicación de nuevas ofertas."""
    sql = """
        WITH monthly AS (
            SELECT
                TO_CHAR(fecha_publicacion, 'YYYY-MM') as mes,
                COUNT(*) as ofertas,
                COUNT(DISTINCT empresa) as empresas,
                COUNT(DISTINCT municipio) as municipios,
                COUNT(DISTINCT sector) as sectores
            FROM empleo.ofertas_laborales
            WHERE fecha_publicacion IS NOT NULL
            GROUP BY TO_CHAR(fecha_publicacion, 'YYYY-MM')
            ORDER BY mes
        ),
        with_growth AS (
            SELECT
                mes,
                ofertas,
                empresas,
                municipios,
                sectores,
                LAG(ofertas) OVER (ORDER BY mes) as prev_ofertas
            FROM monthly
        )
        SELECT
            mes,
            ofertas,
            empresas,
            municipios,
            sectores,
            CASE WHEN prev_ofertas > 0
                THEN ROUND(((ofertas - prev_ofertas)::numeric / prev_ofertas) * 100, 1)
                ELSE NULL
            END as crecimiento_pct
        FROM with_growth
        ORDER BY mes
    """
    return query_dicts(sql)


@router.get("/laboral/concentracion")
@cached(ttl_seconds=3600)
def get_concentracion_laboral():
    """Concentración laboral: distribución geográfica de la actividad económica."""
    sql = """
        WITH muni_stats AS (
            SELECT
                o.municipio,
                o.dane_code,
                COUNT(*) as ofertas,
                COUNT(DISTINCT o.empresa) as empresas,
                COUNT(DISTINCT o.sector) as sectores,
                ROUND(AVG(o.salario_numerico)) as salario_promedio,
                STRING_AGG(DISTINCT o.sector, ', ' ORDER BY o.sector) as sectores_presentes
            FROM empleo.ofertas_laborales o
            WHERE o.dane_code IS NOT NULL
            GROUP BY o.municipio, o.dane_code
        ),
        total AS (
            SELECT SUM(ofertas) as total_ofertas FROM muni_stats
        )
        SELECT
            m.*,
            ROUND((m.ofertas::numeric / t.total_ofertas) * 100, 1) as pct_ofertas,
            ST_Y(ST_Centroid(lm.geom)) as lat,
            ST_X(ST_Centroid(lm.geom)) as lon
        FROM muni_stats m
        CROSS JOIN total t
        LEFT JOIN cartografia.limite_municipal lm ON m.dane_code = lm.dane_code
        ORDER BY ofertas DESC
    """
    rows = query_dicts(sql)
    for r in rows:
        if r.get("salario_promedio"):
            r["salario_promedio"] = int(r["salario_promedio"])
    return rows


@router.get("/laboral/sector-municipio")
@cached(ttl_seconds=3600)
def get_sector_municipio_matrix():
    """Matriz sector × municipio: cuántas ofertas hay por sector en cada municipio."""
    sql = """
        SELECT sector, municipio, COUNT(*) as ofertas
        FROM empleo.ofertas_laborales
        WHERE sector != 'Otro'
        GROUP BY sector, municipio
        ORDER BY sector, ofertas DESC
    """
    rows = query_dicts(sql)

    # Pivot to matrix format
    sectors = {}
    for r in rows:
        s = r["sector"]
        if s not in sectors:
            sectors[s] = {"sector": s, "total": 0}
        sectors[s][r["municipio"]] = r["ofertas"]
        sectors[s]["total"] += r["ofertas"]

    return sorted(sectors.values(), key=lambda x: x["total"], reverse=True)


@router.get("/clusters")
@cached(ttl_seconds=3600)
def get_territorial_clusters():
    """Agrupamiento de municipios por similitud socioeconómica."""
    sql = """
        SELECT
            entidad as municipio,
            indicador,
            dato_numerico as valor
        FROM socioeconomico.terridata
        WHERE indicador IN ('Población total', 'Incidencia de la pobreza monetaria', 'Valor agregado municipal')
        AND anio = (SELECT MAX(anio) FROM socioeconomico.terridata)
    """
    data = query_dicts(sql)
    if not data:
        return {"error": "Datos insuficientes para clustering"}

    import pandas as pd
    df = pd.DataFrame(data).pivot(index='municipio', columns='indicador', values='valor').reset_index()

    clusters = []
    for _, row in df.iterrows():
        poblacion = row.get('Población total', 0) or 0
        pobreza = row.get('Incidencia de la pobreza monetaria', 0) or 0
        pib = row.get('Valor agregado municipal', 0) or 0

        if poblacion > 100000:
            cluster = "Nodo Urbano Regional"
            desc = "Municipios con alta densidad poblacional y servicios centralizados."
        elif pib > 1000000:
            cluster = "Eje Agroindustrial"
            desc = "Municipios con fuerte base económica en banano/plátano y logística."
        elif pobreza > 50:
            cluster = "Territorio en Desarrollo"
            desc = "Municipios con altos retos sociales y brechas de infraestructura."
        else:
            cluster = "Ruralidad Emergente"
            desc = "Municipios con economías en transición y potencial turístico."

        clusters.append({
            "municipio": row['municipio'],
            "cluster": cluster,
            "descripcion": desc,
            "indicadores": {"poblacion": poblacion, "pobreza": pobreza, "pib": pib},
        })

    return clusters
