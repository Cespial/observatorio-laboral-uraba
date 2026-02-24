"""
Módulo de Analítica Avanzada — Inteligencia Territorial y Laboral para Urabá
"""
from fastapi import APIRouter, Query, HTTPException
from ..database import cached, query_dicts

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
    ofertas = query_dicts("""
        SELECT municipio, dane_code, COUNT(*) as vacantes
        FROM empleo.ofertas_laborales
        WHERE dane_code IS NOT NULL
        GROUP BY municipio, dane_code
        ORDER BY vacantes DESC
    """)

    poblacion = query_dicts("""
        SELECT DISTINCT ON (dane_code)
            dane_code, entidad as municipio, dato_numerico as poblacion, anio
        FROM socioeconomico.terridata
        WHERE indicador = :ind
        ORDER BY dane_code, anio DESC
    """, {"ind": "Población total"})

    # Build lookup
    pop_map = {p["dane_code"]: p for p in poblacion}
    result = []
    for o in ofertas:
        p = pop_map.get(o["dane_code"])
        pob = p["poblacion"] if p else 0
        result.append({
            "municipio": o["municipio"],
            "dane_code": o["dane_code"],
            "vacantes": o["vacantes"],
            "poblacion": pob,
            "vacantes_por_1000_hab": round(o["vacantes"] / pob * 1000, 2) if pob and pob > 0 else 0,
            "anio_poblacion": p["anio"] if p else None,
        })
    return sorted(result, key=lambda x: x["vacantes_por_1000_hab"], reverse=True)


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

    # Use query_dicts for short-lived connections (Supabase transaction pooler)
    skills = query_dicts(f"""
        SELECT skill, COUNT(*) as demanda
        FROM empleo.ofertas_laborales, UNNEST(skills) AS skill
        WHERE {where}
        GROUP BY skill
        ORDER BY demanda DESC
        LIMIT 20
    """, params)

    sectores = query_dicts(f"""
        SELECT sector, COUNT(*) as ofertas,
               COUNT(DISTINCT empresa) as empresas
        FROM empleo.ofertas_laborales
        WHERE {where}
        GROUP BY sector
        ORDER BY ofertas DESC
    """, params)

    edu = query_dicts("""
        SELECT
            ROUND(AVG(punt_global)::numeric, 1) as icfes_promedio,
            COUNT(DISTINCT cole_nombre) as colegios,
            COUNT(*) as total_estudiantes
        FROM socioeconomico.icfes
        WHERE punt_global IS NOT NULL
    """)
    edu_row = edu[0] if edu else {}

    total_demanda = sum(s["demanda"] for s in skills)

    return {
        "skills_demandadas": [
            {"skill": s["skill"], "demanda": s["demanda"], "pct": round(s["demanda"] / total_demanda * 100, 1) if total_demanda > 0 else 0}
            for s in skills
        ],
        "sectores_con_demanda": [
            {"sector": s["sector"], "ofertas": s["ofertas"], "empresas": s["empresas"]}
            for s in sectores
        ],
        "capital_humano": {
            "icfes_promedio": float(edu_row.get("icfes_promedio")) if edu_row.get("icfes_promedio") else None,
            "colegios": edu_row.get("colegios", 0),
            "estudiantes_evaluados": edu_row.get("total_estudiantes", 0),
        },
        "insights": _generate_skill_insights(skills, sectores),
    }


def _generate_skill_insights(skills, sectores):
    insights = []
    if skills:
        top = skills[0]
        name = top["skill"] if isinstance(top, dict) else top[0]
        count = top["demanda"] if isinstance(top, dict) else top[1]
        insights.append(f"La habilidad más demandada es {name} con {count} menciones en ofertas.")
    if sectores:
        top_sector = sectores[0]
        s_name = top_sector["sector"] if isinstance(top_sector, dict) else top_sector[0]
        s_ofertas = top_sector["ofertas"] if isinstance(top_sector, dict) else top_sector[1]
        s_empresas = top_sector["empresas"] if isinstance(top_sector, dict) else top_sector[2]
        insights.append(f"El sector con más demanda es {s_name} con {s_ofertas} ofertas de {s_empresas} empresas.")

    # Check for tech skills
    tech_names = ('Python', 'SQL', 'SAP', 'Excel')
    tech_skills = [s for s in skills if (s["skill"] if isinstance(s, dict) else s[0]) in tech_names]
    if tech_skills:
        total_tech = sum(s["demanda"] if isinstance(s, dict) else s[1] for s in tech_skills)
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


@router.get("/laboral/cadenas-productivas")
@cached(ttl_seconds=3600)
def get_cadenas_productivas():
    """Análisis por cadenas productivas de Urabá: ofertas, empresas y salario por cadena."""
    CADENAS = {
        "Banano y Plátano": {
            "sectores": ["Agroindustria"],
            "skills": ["Cosecha", "Empaque", "Fitosanidad", "Riego y drenaje",
                        "Certificaciones agrícolas", "Certificacion organica",
                        "Cultivo banano/plátano", "Agricultura", "BPM", "HACCP",
                        "Cadena de frio"],
        },
        "Ganadería y Lácteos": {
            "sectores": ["Agroindustria", "Mantenimiento"],
            "skills": ["Ganadería", "Veterinaria", "Porcicultura", "Acuicultura"],
        },
        "Turismo y Gastronomía": {
            "sectores": ["Turismo y Gastronomía"],
            "skills": ["Hotelería", "Guía turístico", "Servicio de habitación",
                        "Barista/Bartender", "Atención al cliente"],
        },
        "Comercio y Logística Portuaria": {
            "sectores": ["Transporte y Logística", "Comercio y Ventas"],
            "skills": ["Logística", "Montacargas", "Comercio exterior", "Cadena de frio",
                        "Aduanas", "Contenedores", "Estiba", "Zona franca",
                        "Logística marítima"],
        },
        "Construcción e Infraestructura": {
            "sectores": ["Construcción", "Mantenimiento"],
            "skills": ["AutoCAD", "Soldadura", "Electricidad", "Mecánica",
                        "Construcción", "Maquinaria pesada", "SST"],
        },
        "Servicios y Administrativo": {
            "sectores": ["Administrativo", "Contabilidad y Finanzas", "Salud",
                         "Educación", "Recursos Humanos", "Jurídico"],
            "skills": ["Excel", "SAP", "Contabilidad", "Software contable",
                        "Facturación", "Inventarios", "Power BI"],
        },
    }

    # Fetch base data: ofertas grouped by sector
    sector_data = query_dicts("""
        SELECT sector, municipio, COUNT(*) as ofertas,
               COUNT(DISTINCT empresa) as empresas,
               ROUND(AVG(salario_numerico)) as salario_promedio
        FROM empleo.ofertas_laborales
        WHERE sector IS NOT NULL
        GROUP BY sector, municipio
    """)

    # Fetch top skills per sector
    skills_data = query_dicts("""
        SELECT sector, skill, COUNT(*) as demanda
        FROM empleo.ofertas_laborales, UNNEST(skills) AS skill
        WHERE sector IS NOT NULL
        GROUP BY sector, skill
        ORDER BY sector, demanda DESC
    """)

    # Build sector→skills lookup
    sector_skills = {}
    for row in skills_data:
        s = row["sector"]
        if s not in sector_skills:
            sector_skills[s] = []
        sector_skills[s].append({"skill": row["skill"], "demanda": row["demanda"]})

    result = []
    for cadena_name, cfg in CADENAS.items():
        cadena_ofertas = 0
        cadena_empresas = set()
        salarios = []
        municipios = {}
        matched_skills = {}

        for row in sector_data:
            if row["sector"] in cfg["sectores"]:
                cadena_ofertas += row["ofertas"]
                # Approximate unique empresas by municipality
                cadena_empresas.add(f"{row.get('municipio', '')}_{row['empresas']}")
                if row.get("salario_promedio"):
                    salarios.append((row["salario_promedio"], row["ofertas"]))
                muni = row.get("municipio", "Otro")
                if muni not in municipios:
                    municipios[muni] = {"municipio": muni, "ofertas": 0}
                municipios[muni]["ofertas"] += row["ofertas"]

        # Aggregate skills relevant to this chain
        for sector in cfg["sectores"]:
            for sk in sector_skills.get(sector, []):
                if sk["skill"] in cfg["skills"] or not cfg["skills"]:
                    sname = sk["skill"]
                    if sname not in matched_skills:
                        matched_skills[sname] = 0
                    matched_skills[sname] += sk["demanda"]

        # Weighted salary average
        sal_prom = None
        if salarios:
            total_w = sum(w for _, w in salarios)
            sal_prom = int(sum(s * w for s, w in salarios) / total_w) if total_w > 0 else None

        empresas_total = sum(row["empresas"] for row in sector_data if row["sector"] in cfg["sectores"])

        top_skills = sorted(matched_skills.items(), key=lambda x: x[1], reverse=True)[:10]
        top_municipios = sorted(municipios.values(), key=lambda x: x["ofertas"], reverse=True)

        result.append({
            "cadena": cadena_name,
            "sectores": cfg["sectores"],
            "ofertas": cadena_ofertas,
            "empresas": empresas_total,
            "salario_promedio": sal_prom,
            "top_skills": [{"skill": s, "demanda": d} for s, d in top_skills],
            "municipios": top_municipios,
        })

    return sorted(result, key=lambda x: x["ofertas"], reverse=True)


@router.get("/laboral/estacionalidad")
@cached(ttl_seconds=3600)
def get_estacionalidad_laboral():
    """Perfil estacional: ofertas y salario promedio por mes del año (1-12) y sector."""
    sql = """
        SELECT EXTRACT(MONTH FROM fecha_publicacion)::int as mes,
               sector, COUNT(*) as ofertas,
               ROUND(AVG(salario_numerico)) as salario_promedio
        FROM empleo.ofertas_laborales
        WHERE fecha_publicacion IS NOT NULL
        GROUP BY mes, sector
        ORDER BY mes, ofertas DESC
    """
    rows = query_dicts(sql)

    # Also compute general monthly profile
    general_sql = """
        SELECT EXTRACT(MONTH FROM fecha_publicacion)::int as mes,
               COUNT(*) as ofertas,
               ROUND(AVG(salario_numerico)) as salario_promedio
        FROM empleo.ofertas_laborales
        WHERE fecha_publicacion IS NOT NULL
        GROUP BY mes
        ORDER BY mes
    """
    general = query_dicts(general_sql)

    # Compute average to detect peaks and valleys
    total_ofertas = sum(r["ofertas"] for r in general)
    avg_mensual = total_ofertas / 12 if total_ofertas > 0 else 0

    MES_NOMBRES = {
        1: "Ene", 2: "Feb", 3: "Mar", 4: "Abr", 5: "May", 6: "Jun",
        7: "Jul", 8: "Ago", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dic",
    }

    perfil_general = []
    for r in general:
        ofertas = r["ofertas"]
        ratio = ofertas / avg_mensual if avg_mensual > 0 else 1
        clasificacion = "pico" if ratio > 1.2 else ("valle" if ratio < 0.8 else "normal")
        perfil_general.append({
            "mes": r["mes"],
            "mes_nombre": MES_NOMBRES.get(r["mes"], str(r["mes"])),
            "ofertas": ofertas,
            "salario_promedio": int(r["salario_promedio"]) if r.get("salario_promedio") else None,
            "ratio": round(ratio, 2),
            "clasificacion": clasificacion,
        })

    # Build sector × month matrix
    sector_meses = {}
    for r in rows:
        s = r["sector"]
        if s not in sector_meses:
            sector_meses[s] = {"sector": s, "meses": {}, "total": 0}
        sector_meses[s]["meses"][r["mes"]] = r["ofertas"]
        sector_meses[s]["total"] += r["ofertas"]

    # Detect peaks/valleys per sector
    sectores_estacionales = []
    for s_name, s_data in sorted(sector_meses.items(), key=lambda x: x[1]["total"], reverse=True)[:10]:
        meses_vals = s_data["meses"]
        s_avg = s_data["total"] / max(len(meses_vals), 1)
        picos = [m for m, v in meses_vals.items() if s_avg > 0 and v / s_avg > 1.2]
        valles = [m for m, v in meses_vals.items() if s_avg > 0 and v / s_avg < 0.8]
        row_data = {"sector": s_name, "total": s_data["total"], "picos": picos, "valles": valles}
        for mes_num in range(1, 13):
            row_data[MES_NOMBRES[mes_num]] = meses_vals.get(mes_num, 0)
        sectores_estacionales.append(row_data)

    return {
        "perfil_general": perfil_general,
        "sectores_estacionales": sectores_estacionales,
        "promedio_mensual": round(avg_mensual),
    }


@router.get("/laboral/informalidad")
@cached(ttl_seconds=3600)
def get_informalidad_laboral():
    """Indicador de informalidad laboral por municipio combinando IPM, ofertas y TerriData."""
    # 1. IPM: empleo_informal
    ipm_data = query_dicts("""
        SELECT municipio, dane_code, empleo_informal as tasa_ipm
        FROM socioeconomico.ipm
        WHERE empleo_informal IS NOT NULL
        ORDER BY empleo_informal DESC
    """)

    # 2. Proxy from ofertas: % contratos no-indefinidos
    proxy_data = query_dicts("""
        SELECT municipio, dane_code,
               COUNT(*) as total_ofertas,
               COUNT(CASE WHEN tipo_contrato IN ('Prestacion de servicios', 'Obra o labor') THEN 1 END) as no_indefinido,
               COUNT(CASE WHEN tipo_contrato = 'Indefinido' THEN 1 END) as indefinido
        FROM empleo.ofertas_laborales
        WHERE tipo_contrato IS NOT NULL AND dane_code IS NOT NULL
        GROUP BY municipio, dane_code
    """)

    # 3. Pobreza monetaria from TerriData
    pobreza_data = query_dicts("""
        SELECT DISTINCT ON (dane_code) dane_code, dato_numerico as pobreza_monetaria, anio
        FROM socioeconomico.terridata
        WHERE indicador = 'Incidencia de la pobreza monetaria'
        ORDER BY dane_code, anio DESC
    """)

    # Build lookups
    ipm_map = {r["dane_code"]: r for r in ipm_data}
    proxy_map = {r["dane_code"]: r for r in proxy_data}
    pobreza_map = {r["dane_code"]: r for r in pobreza_data}

    all_danes = set()
    for d in [ipm_map, proxy_map, pobreza_map]:
        all_danes.update(d.keys())

    result = []
    for dane in all_danes:
        if not dane:
            continue
        ipm = ipm_map.get(dane, {})
        proxy = proxy_map.get(dane, {})
        pob = pobreza_map.get(dane, {})

        tasa_ipm = ipm.get("tasa_ipm")
        total_ofertas = proxy.get("total_ofertas", 0)
        no_indef = proxy.get("no_indefinido", 0)
        proxy_pct = round(no_indef / total_ofertas * 100, 1) if total_ofertas > 0 else None
        pobreza_monetaria = pob.get("pobreza_monetaria")

        # Composite: weighted average of normalized values (0-100 scale)
        components = []
        if tasa_ipm is not None:
            components.append(float(tasa_ipm))
        if proxy_pct is not None:
            components.append(proxy_pct)
        if pobreza_monetaria is not None:
            components.append(float(pobreza_monetaria))

        indice_compuesto = round(sum(components) / len(components), 1) if components else None

        municipio = ipm.get("municipio") or proxy.get("municipio") or "Desconocido"
        result.append({
            "municipio": municipio,
            "dane_code": dane,
            "tasa_ipm": float(tasa_ipm) if tasa_ipm is not None else None,
            "proxy_informal_pct": proxy_pct,
            "ofertas_con_contrato": total_ofertas,
            "contratos_indefinido": proxy.get("indefinido", 0),
            "contratos_no_indefinido": no_indef,
            "pobreza_monetaria": float(pobreza_monetaria) if pobreza_monetaria is not None else None,
            "indice_compuesto": indice_compuesto,
        })

    return sorted(result, key=lambda x: x["indice_compuesto"] or 0, reverse=True)


@router.get("/laboral/salario-imputado")
@cached(ttl_seconds=3600)
def get_salario_imputado():
    """Tabla de referencia salarial y estadísticas de imputación."""
    referencia = query_dicts("""
        SELECT sector, municipio, nivel_educativo, nivel_experiencia,
               ROUND(AVG(salario_numerico)) as salario_estimado,
               COUNT(*) as muestra,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_numerico) as mediana
        FROM empleo.ofertas_laborales
        WHERE salario_numerico IS NOT NULL
        GROUP BY sector, municipio, nivel_educativo, nivel_experiencia
        HAVING COUNT(*) >= 3
    """)

    cobertura = query_dicts("""
        SELECT
            COUNT(*) as total,
            COUNT(CASE WHEN salario_numerico IS NOT NULL THEN 1 END) as con_salario,
            COUNT(CASE WHEN salario_imputado IS NOT NULL THEN 1 END) as con_imputado
        FROM empleo.ofertas_laborales
    """)

    cob = cobertura[0] if cobertura else {}
    total = cob.get("total", 0)
    con_sal = cob.get("con_salario", 0)
    con_imp = cob.get("con_imputado", 0)

    for r in referencia:
        if r.get("salario_estimado"):
            r["salario_estimado"] = int(r["salario_estimado"])
        if r.get("mediana"):
            r["mediana"] = int(r["mediana"])

    return {
        "tabla_referencia": referencia[:50],
        "cobertura": {
            "total_ofertas": total,
            "con_salario_real": con_sal,
            "con_salario_imputado": con_imp,
            "pct_salario_real": round(con_sal / total * 100, 1) if total > 0 else 0,
            "pct_cobertura_total": round((con_sal + con_imp) / total * 100, 1) if total > 0 else 0,
        },
    }


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
