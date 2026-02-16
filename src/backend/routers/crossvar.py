"""
Motor de Cruces Multivariable — el corazón analítico del observatorio
Permite cruzar cualquier par de variables y obtener scatter plots, correlaciones,
mapas bivariados y análisis espaciales.
"""
from fastapi import APIRouter, Query, HTTPException
from ..database import engine, cached
from sqlalchemy import text
import json

router = APIRouter(prefix="/api/crossvar", tags=["Cruces Multivariable"])


# Variables disponibles para cruce
VARIABLES = {
    "poblacion": {
        "name": "Población por Manzana",
        "sql": "SELECT cod_dane_manzana as geo_id, CAST(total_personas AS FLOAT) as valor, geom FROM cartografia.manzanas_censales WHERE total_personas ~ '^[0-9]+$'",
        "unit": "personas",
        "geo_level": "manzana",
    },
    "icfes_global": {
        "name": "Puntaje ICFES Global (promedio por colegio)",
        "sql": """
            SELECT cole_nombre_establecimiento as geo_id,
                   AVG(CAST(punt_global AS FLOAT)) as valor
            FROM socioeconomico.icfes_raw
            WHERE punt_global IS NOT NULL
            GROUP BY cole_nombre_establecimiento
        """,
        "unit": "puntos",
        "geo_level": "colegio",
    },
    "icfes_matematicas": {
        "name": "Puntaje ICFES Matemáticas (promedio)",
        "sql": """
            SELECT cole_nombre_establecimiento as geo_id,
                   AVG(CAST(punt_matematicas AS FLOAT)) as valor
            FROM socioeconomico.icfes_raw
            WHERE punt_matematicas IS NOT NULL
            GROUP BY cole_nombre_establecimiento
        """,
        "unit": "puntos",
        "geo_level": "colegio",
    },
    "icfes_lectura": {
        "name": "Puntaje ICFES Lectura Crítica (promedio)",
        "sql": """
            SELECT cole_nombre_establecimiento as geo_id,
                   AVG(CAST(punt_lectura_critica AS FLOAT)) as valor
            FROM socioeconomico.icfes_raw
            WHERE punt_lectura_critica IS NOT NULL
            GROUP BY cole_nombre_establecimiento
        """,
        "unit": "puntos",
        "geo_level": "colegio",
    },
    "matricula": {
        "name": "Matrícula Total por Establecimiento",
        "sql": """
            SELECT nombre_establecimiento as geo_id,
                   CAST(total_matricula AS FLOAT) as valor
            FROM socioeconomico.establecimientos_educativos_raw
            WHERE total_matricula IS NOT NULL
        """,
        "unit": "estudiantes",
        "geo_level": "colegio",
    },
    "homicidios_anual": {
        "name": "Homicidios por Año",
        "sql": """
            SELECT EXTRACT(YEAR FROM fecha_hecho)::text as geo_id,
                   SUM(CAST(cantidad AS FLOAT)) as valor
            FROM seguridad.homicidios_raw
            WHERE fecha_hecho IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fecha_hecho)
        """,
        "unit": "casos",
        "geo_level": "anual",
    },
    "hurtos_anual": {
        "name": "Hurtos por Año",
        "sql": """
            SELECT EXTRACT(YEAR FROM fecha_hecho)::text as geo_id,
                   SUM(CAST(cantidad AS FLOAT)) as valor
            FROM seguridad.hurtos_raw
            WHERE fecha_hecho IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fecha_hecho)
        """,
        "unit": "casos",
        "geo_level": "anual",
    },
    "vif_anual": {
        "name": "Violencia Intrafamiliar por Año",
        "sql": """
            SELECT EXTRACT(YEAR FROM fecha_hecho)::text as geo_id,
                   SUM(CAST(cantidad AS FLOAT)) as valor
            FROM seguridad.violencia_intrafamiliar_raw
            WHERE fecha_hecho IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fecha_hecho)
        """,
        "unit": "casos",
        "geo_level": "anual",
    },
    "delitos_sexuales_anual": {
        "name": "Delitos Sexuales por Año",
        "sql": """
            SELECT EXTRACT(YEAR FROM fecha_hecho)::text as geo_id,
                   SUM(CAST(cantidad AS FLOAT)) as valor
            FROM seguridad.delitos_sexuales_raw
            WHERE fecha_hecho IS NOT NULL
            GROUP BY EXTRACT(YEAR FROM fecha_hecho)
        """,
        "unit": "casos",
        "geo_level": "anual",
    },
    "victimas_hecho": {
        "name": "Víctimas por Hecho Victimizante",
        "sql": """
            SELECT hecho as geo_id,
                   SUM(CAST(per_ocu AS FLOAT)) as valor
            FROM seguridad.victimas_raw
            WHERE per_ocu IS NOT NULL
            GROUP BY hecho
        """,
        "unit": "personas",
        "geo_level": "hecho",
    },
    "places_categoria": {
        "name": "Negocios por Categoría",
        "sql": """
            SELECT category as geo_id,
                   COUNT(*)::float as valor
            FROM servicios.google_places
            GROUP BY category
        """,
        "unit": "establecimientos",
        "geo_level": "categoria",
    },
    "places_rating": {
        "name": "Rating Promedio de Negocios por Categoría",
        "sql": """
            SELECT category as geo_id,
                   AVG(rating) as valor
            FROM servicios.google_places
            WHERE rating IS NOT NULL
            GROUP BY category
        """,
        "unit": "estrellas (1-5)",
        "geo_level": "categoria",
    },
}


@router.get("/variables")
@cached(ttl_seconds=3600)
def list_variables():
    """Listar todas las variables disponibles para cruces."""
    return [
        {"id": k, "name": v["name"], "unit": v["unit"], "geo_level": v["geo_level"]}
        for k, v in VARIABLES.items()
    ]


@router.get("/scatter")
def scatter_analysis(
    var_x: str = Query(..., description="Variable eje X"),
    var_y: str = Query(..., description="Variable eje Y"),
):
    """
    Cruce scatter plot entre dos variables.
    Retorna puntos (x, y) con labels, coeficiente de correlación y línea de regresión.
    """
    if var_x not in VARIABLES:
        raise HTTPException(status_code=400, detail=f"Variable '{var_x}' no existe. Usa /api/crossvar/variables")
    if var_y not in VARIABLES:
        raise HTTPException(status_code=400, detail=f"Variable '{var_y}' no existe. Usa /api/crossvar/variables")

    vx = VARIABLES[var_x]
    vy = VARIABLES[var_y]

    # Get data for both variables
    with engine.connect() as conn:
        rows_x = conn.execute(text(vx["sql"])).fetchall()
        rows_y = conn.execute(text(vy["sql"])).fetchall()

    # Create dictionaries for join
    dict_x = {str(r[0]): float(r[1]) for r in rows_x if r[1] is not None}
    dict_y = {str(r[0]): float(r[1]) for r in rows_y if r[1] is not None}

    # Join on geo_id
    common_keys = set(dict_x.keys()) & set(dict_y.keys())
    points = [
        {"label": k, "x": dict_x[k], "y": dict_y[k]}
        for k in common_keys
    ]

    # Calculate correlation (pure Python — no numpy needed)
    correlation = None
    regression = None
    if len(points) >= 3:
        xs = [p["x"] for p in points]
        ys = [p["y"] for p in points]
        n = len(xs)
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        var_x = sum((x - mean_x) ** 2 for x in xs)
        var_y = sum((y - mean_y) ** 2 for y in ys)
        cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        if var_x > 0 and var_y > 0:
            correlation = cov / (var_x * var_y) ** 0.5
            slope = cov / var_x
            intercept = mean_y - slope * mean_x
            regression = {
                "slope": slope,
                "intercept": intercept,
                "r_squared": correlation ** 2,
            }

    return {
        "var_x": {"id": var_x, "name": vx["name"], "unit": vx["unit"]},
        "var_y": {"id": var_y, "name": vy["name"], "unit": vy["unit"]},
        "points": points,
        "n": len(points),
        "correlation": correlation,
        "regression": regression,
    }


@router.get("/timeseries")
def timeseries_comparison(
    variables: str = Query(
        "homicidios_anual,hurtos_anual,vif_anual",
        description="Variables separadas por coma (deben ser de nivel anual)",
    ),
):
    """
    Comparación de múltiples series temporales en un solo gráfico.
    """
    var_list = [v.strip() for v in variables.split(",")]
    series = {}

    for var_id in var_list:
        if var_id not in VARIABLES:
            continue
        v = VARIABLES[var_id]
        if v["geo_level"] != "anual":
            continue
        with engine.connect() as conn:
            rows = conn.execute(text(v["sql"])).fetchall()
        series[var_id] = {
            "name": v["name"],
            "unit": v["unit"],
            "data": [{"year": int(float(r[0])), "value": float(r[1])} for r in rows if r[0] and r[1]],
        }
        series[var_id]["data"].sort(key=lambda x: x["year"])

    return {"series": series}


@router.get("/security-matrix")
@cached(ttl_seconds=600)
def security_matrix():
    """
    Matriz completa de seguridad: todos los tipos de delito por año.
    Ideal para gráficos de área apilada o heatmaps temporales.
    """
    types = {
        "Homicidios": "seguridad.homicidios_raw",
        "Hurtos": "seguridad.hurtos_raw",
        "Delitos Sexuales": "seguridad.delitos_sexuales_raw",
        "Violencia Intrafamiliar": "seguridad.violencia_intrafamiliar_raw",
    }

    sql = """
        SELECT 'Homicidios' as tipo, EXTRACT(YEAR FROM fecha_hecho)::int as anio, SUM(CAST(cantidad AS INT)) as total
        FROM seguridad.homicidios_raw WHERE fecha_hecho IS NOT NULL GROUP BY anio
        UNION ALL
        SELECT 'Hurtos', EXTRACT(YEAR FROM fecha_hecho)::int, SUM(CAST(cantidad AS INT))
        FROM seguridad.hurtos_raw WHERE fecha_hecho IS NOT NULL GROUP BY EXTRACT(YEAR FROM fecha_hecho)::int
        UNION ALL
        SELECT 'Delitos Sexuales', EXTRACT(YEAR FROM fecha_hecho)::int, SUM(CAST(cantidad AS INT))
        FROM seguridad.delitos_sexuales_raw WHERE fecha_hecho IS NOT NULL GROUP BY EXTRACT(YEAR FROM fecha_hecho)::int
        UNION ALL
        SELECT 'Violencia Intrafamiliar', EXTRACT(YEAR FROM fecha_hecho)::int, SUM(CAST(cantidad AS INT))
        FROM seguridad.violencia_intrafamiliar_raw WHERE fecha_hecho IS NOT NULL GROUP BY EXTRACT(YEAR FROM fecha_hecho)::int
        UNION ALL
        SELECT 'Lesiones Personales', EXTRACT(YEAR FROM fecha_hecho)::int, SUM(CAST(cantidad AS INT))
        FROM seguridad.lesiones_personales_raw WHERE fecha_hecho IS NOT NULL GROUP BY EXTRACT(YEAR FROM fecha_hecho)::int
        UNION ALL
        SELECT 'Masacres', a_o::int, SUM(CAST(total_de_v_ctimas_del_caso AS INT))
        FROM seguridad.masacres_raw WHERE a_o IS NOT NULL GROUP BY a_o::int
        ORDER BY tipo, anio
    """
    with engine.connect() as conn:
        rows = conn.execute(text(sql)).fetchall()

    return {"data": [{"tipo": r[0], "anio": r[1], "total": r[2]} for r in rows]}


@router.get("/education-vs-security")
def education_vs_security():
    """
    Cruce especial: evolución de puntajes ICFES vs indicadores de seguridad por año.
    """
    with engine.connect() as conn:
        # ICFES by year
        icfes = conn.execute(text("""
            SELECT SUBSTRING(periodo, 1, 4)::int as anio,
                   AVG(CAST(punt_global AS FLOAT)) as prom_global,
                   COUNT(*) as estudiantes
            FROM socioeconomico.icfes_raw
            WHERE punt_global IS NOT NULL
            GROUP BY SUBSTRING(periodo, 1, 4)
            ORDER BY anio
        """)).fetchall()

        # Homicidios by year
        homicidios = conn.execute(text("""
            SELECT EXTRACT(YEAR FROM fecha_hecho)::int as anio,
                   SUM(CAST(cantidad AS INT)) as total
            FROM seguridad.homicidios_raw
            WHERE fecha_hecho IS NOT NULL
            GROUP BY anio ORDER BY anio
        """)).fetchall()

    return {
        "icfes": [{"anio": r[0], "prom_global": float(r[1]), "estudiantes": r[2]} for r in icfes],
        "homicidios": [{"anio": r[0], "total": r[1]} for r in homicidios],
    }
