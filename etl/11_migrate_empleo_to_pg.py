"""
ETL 11 — Migrar ofertas laborales de SQLite a PostgreSQL (Supabase)
===================================================================
Lee de ~/uraba_empleos/empleos_uraba.db y carga en el schema empleo.ofertas_laborales.
Extrae habilidades (skills) básicas del titulo y descripcion usando regex.
"""

import sqlite3
import sys
import re
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_URL

SQLITE_PATH = Path.home() / "uraba_empleos" / "empleos_uraba.db"

# Mapping municipio names to DANE codes
MUNICIPIO_DANE = {
    "apartadó": "05045", "apartado": "05045",
    "turbo": "05837",
    "carepa": "05147",
    "chigorodó": "05172", "chigorodo": "05172",
    "necoclí": "05490", "necocli": "05490",
    "arboletes": "05051",
    "san pedro de urabá": "05665", "san pedro": "05665",
    "san juan de urabá": "05659", "san juan": "05659",
    "mutatá": "05480", "mutata": "05480",
    "murindó": "05475", "murindo": "05475",
    "vigía del fuerte": "05873", "vigia del fuerte": "05873", "vigia": "05873",
    "urabá": None, "uraba": None,
}

# Skills extraction patterns
SKILL_PATTERNS = [
    (r'\bexcel\b', 'Excel'),
    (r'\bword\b', 'Word'),
    (r'\bsap\b', 'SAP'),
    (r'\bpython\b', 'Python'),
    (r'\bsql\b', 'SQL'),
    (r'\bingl[eé]s\b', 'Inglés'),
    (r'\bcontabilidad\b', 'Contabilidad'),
    (r'\bfacturaci[oó]n\b', 'Facturación'),
    (r'\batenci[oó]n al cliente\b', 'Atención al cliente'),
    (r'\bservicio al cliente\b', 'Servicio al cliente'),
    (r'\bventas\b', 'Ventas'),
    (r'\bliderazgo\b', 'Liderazgo'),
    (r'\btrabajo en equipo\b', 'Trabajo en equipo'),
    (r'\bcomunicaci[oó]n\b', 'Comunicación'),
    (r'\bnegociaci[oó]n\b', 'Negociación'),
    (r'\bmanejo de personal\b', 'Manejo de personal'),
    (r'\blogística\b|\blogistica\b', 'Logística'),
    (r'\bpresupuesto\b', 'Presupuesto'),
    (r'\bmarketing\b|\bmercadeo\b', 'Marketing'),
    (r'\bredes sociales\b|\bsocial media\b', 'Redes sociales'),
    (r'\blicencia\s+(de\s+)?conducci[oó]n\b|\blicencia\s+[bc]\d\b', 'Licencia de conducción'),
    (r'\bmoto\b', 'Moto propia'),
    (r'\bsalud ocupacional\b|\bsst\b|\bseguridad y salud\b', 'SST'),
    (r'\bagricultura\b|\bagrícola\b|\bagricola\b|\bcultivo\b', 'Agricultura'),
    (r'\bbanano\b|\bplátano\b|\bplatano\b', 'Cultivo banano/plátano'),
    (r'\bglobalg\.?a\.?p\.?\b|\brainforest\b', 'Certificaciones agrícolas'),
    (r'\benfermería\b|\benfermeria\b|\benfermero\b', 'Enfermería'),
    (r'\bmedicina\b|\bmédico\b|\bmedico\b', 'Medicina'),
    (r'\bpedagog\b|\beducaci[oó]n\b|\bdocente\b|\bprofesor\b', 'Educación'),
    (r'\bconstrucci[oó]n\b|\bobra\b|\bingeniería civil\b', 'Construcción'),
    (r'\belectricidad\b|\beléctric\b|\belectric\b', 'Electricidad'),
    (r'\bmecánic\b|\bmecanica\b', 'Mecánica'),
    (r'\bsoldadura\b', 'Soldadura'),
]

# Sector classification based on title keywords
SECTOR_PATTERNS = [
    (r'\bagrícol|\bagricol|\bbanano|\bplátano|\bcultivo|\bagrono|\bfinca\b', 'Agroindustria'),
    (r'\bsalud|\benferm|\bmédic|\bhospital|\bIPS\b|\bEPS\b|\bfarmac', 'Salud'),
    (r'\beduca|\bdocente|\bprofesor|\bcolegio|\binstruct', 'Educación'),
    (r'\bcontabl|\bcontador|\bfinanci|\baudit|\btribut|\bimpuest', 'Contabilidad y Finanzas'),
    (r'\bvend|\bcomercial|\btienda|\bmercad|\bTAT\b', 'Comercio y Ventas'),
    (r'\bconstrucc|\bobra|\bingenier.*civil|\bmaestro.*obra|\barquitect', 'Construcción'),
    (r'\btecnolog|\bsistema|\bdesarroll|\bsoftware|\bIT\b|\bprogramad', 'Tecnología'),
    (r'\btransport|\blogíst|\bconductor|\bchof', 'Transporte y Logística'),
    (r'\bseguridad|\bvigilant|\bcustodia|\bguarda', 'Seguridad'),
    (r'\bturism|\bhotel|\brestaurant|\bcocin|\bchef\b|\bmesero', 'Turismo y Gastronomía'),
    (r'\badministrativ|\bsecretari|\brecepcion|\basistente.*admin', 'Administrativo'),
    (r'\bderecho|\bjuríd|\babogad|\blegal', 'Jurídico'),
    (r'\brecursos humanos|\btalento humano|\bRRHH\b|\bnómin', 'Recursos Humanos'),
    (r'\bmantenimiento|\bmecánic|\belectric|\btécnic', 'Mantenimiento'),
]


def extract_skills(titulo, descripcion):
    text = f"{titulo or ''} {descripcion or ''}".lower()
    skills = []
    for pattern, skill_name in SKILL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            skills.append(skill_name)
    return skills


def classify_sector(titulo, descripcion):
    text = f"{titulo or ''} {descripcion or ''}".lower()
    for pattern, sector in SECTOR_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return sector
    return 'Otro'


def parse_salary(salario_str):
    """Extract numeric salary value from strings like '$1.600.000' or '$1.400.000 + comisiones'"""
    if not salario_str:
        return None
    cleaned = re.sub(r'[^\d.]', '', salario_str.split('+')[0].split('-')[0].strip())
    # Remove dots used as thousands separators (common in Colombian format)
    parts = cleaned.split('.')
    if len(parts) > 2:
        # e.g. "1.600.000" -> "1600000"
        cleaned = ''.join(parts)
    elif len(parts) == 2 and len(parts[1]) == 3:
        cleaned = ''.join(parts)
    try:
        val = int(cleaned)
        if val > 100000:  # Sanity check for Colombian pesos
            return val
    except (ValueError, OverflowError):
        pass
    return None


def get_dane_code(municipio):
    if not municipio:
        return None
    return MUNICIPIO_DANE.get(municipio.lower().strip())


def main():
    if not SQLITE_PATH.exists():
        print(f"ERROR: No se encontró {SQLITE_PATH}")
        sys.exit(1)

    print(f"Leyendo ofertas de {SQLITE_PATH} ...")
    conn_sqlite = sqlite3.connect(str(SQLITE_PATH))
    conn_sqlite.row_factory = sqlite3.Row
    rows = conn_sqlite.execute("SELECT * FROM ofertas ORDER BY id").fetchall()
    print(f"  {len(rows)} ofertas encontradas")

    engine = create_engine(DB_URL)

    with engine.begin() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS empleo"))
        conn.execute(text("DROP TABLE IF EXISTS empleo.ofertas_laborales CASCADE"))
        conn.execute(text("""
            CREATE TABLE empleo.ofertas_laborales (
                id SERIAL PRIMARY KEY,
                titulo TEXT NOT NULL,
                empresa TEXT,
                salario_texto TEXT,
                salario_numerico INTEGER,
                descripcion TEXT,
                fecha_publicacion DATE,
                enlace TEXT,
                municipio TEXT NOT NULL,
                dane_code TEXT,
                fuente TEXT NOT NULL,
                sector TEXT,
                skills TEXT[],
                fecha_scraping TIMESTAMP,
                content_hash TEXT
            )
        """))
        print("  CREATE TABLE empleo.ofertas_laborales OK")

        inserted = 0
        for row in rows:
            titulo = row['titulo']
            desc = row['descripcion']
            skills = extract_skills(titulo, desc)
            sector = classify_sector(titulo, desc)
            salario_num = parse_salary(row['salario'])
            dane = get_dane_code(row['municipio'])

            # Normalize date format
            fecha_pub = row['fecha_pub']
            if fecha_pub and '/' in fecha_pub:
                # Convert DD/MM/YYYY to YYYY-MM-DD
                parts = fecha_pub.split('/')
                if len(parts) == 3:
                    fecha_pub = f"{parts[2]}-{parts[1]}-{parts[0]}"

            conn.execute(text("""
                INSERT INTO empleo.ofertas_laborales
                    (titulo, empresa, salario_texto, salario_numerico, descripcion,
                     fecha_publicacion, enlace, municipio, dane_code, fuente,
                     sector, skills, fecha_scraping, content_hash)
                VALUES
                    (:titulo, :empresa, :salario_texto, :salario_num, :descripcion,
                     :fecha_pub, :enlace, :municipio, :dane, :fuente,
                     :sector, :skills, :fecha_scraping, :hash)
            """), {
                "titulo": titulo,
                "empresa": row['empresa'],
                "salario_texto": row['salario'],
                "salario_num": salario_num,
                "descripcion": desc,
                "fecha_pub": fecha_pub if fecha_pub else None,
                "enlace": row['enlace'],
                "municipio": row['municipio'],
                "dane": dane,
                "fuente": row['fuente'],
                "sector": sector,
                "skills": skills,
                "fecha_scraping": row['fecha_scraping'],
                "hash": row['content_hash'],
            })
            inserted += 1

        # Create indexes
        conn.execute(text("CREATE INDEX idx_ofertas_municipio ON empleo.ofertas_laborales(municipio)"))
        conn.execute(text("CREATE INDEX idx_ofertas_dane ON empleo.ofertas_laborales(dane_code)"))
        conn.execute(text("CREATE INDEX idx_ofertas_fuente ON empleo.ofertas_laborales(fuente)"))
        conn.execute(text("CREATE INDEX idx_ofertas_sector ON empleo.ofertas_laborales(sector)"))
        conn.execute(text("CREATE INDEX idx_ofertas_fecha ON empleo.ofertas_laborales(fecha_publicacion)"))

        print(f"  Insertadas: {inserted} ofertas")

        # Print summary stats
        stats = conn.execute(text("""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT municipio) as municipios,
                COUNT(DISTINCT fuente) as fuentes,
                COUNT(DISTINCT sector) as sectores,
                COUNT(CASE WHEN salario_numerico IS NOT NULL THEN 1 END) as con_salario,
                COUNT(CASE WHEN array_length(skills, 1) > 0 THEN 1 END) as con_skills
            FROM empleo.ofertas_laborales
        """)).fetchone()
        print(f"\n  Resumen:")
        print(f"    Total ofertas:      {stats[0]}")
        print(f"    Municipios:         {stats[1]}")
        print(f"    Fuentes:            {stats[2]}")
        print(f"    Sectores:           {stats[3]}")
        print(f"    Con salario parsed: {stats[4]}")
        print(f"    Con skills:         {stats[5]}")

        # Print sector breakdown
        sectores = conn.execute(text("""
            SELECT sector, COUNT(*) as n
            FROM empleo.ofertas_laborales
            GROUP BY sector ORDER BY n DESC
        """)).fetchall()
        print(f"\n  Distribución por sector:")
        for s in sectores:
            print(f"    {s[0]:30s} {s[1]:>4d}")

    conn_sqlite.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
