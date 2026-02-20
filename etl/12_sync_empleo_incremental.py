#!/usr/bin/env python3
"""
ETL 12 — Sync incremental de ofertas laborales SQLite → Supabase
=================================================================
Lee nuevas ofertas desde ~/uraba_empleos/empleos_uraba.db
y las inserta en empleo.ofertas_laborales (PostgreSQL/Supabase).
Solo inserta ofertas que no existen ya (por content_hash).

Uso:
  python etl/12_sync_empleo_incremental.py
  # O con cron / GitHub Actions para sync automático
"""

import sqlite3
import sys
import re
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_URL

SQLITE_PATH = Path.home() / "uraba_empleos" / "empleos_uraba.db"

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
    combined = f"{titulo or ''} {descripcion or ''}".lower()
    return [name for pattern, name in SKILL_PATTERNS if re.search(pattern, combined, re.IGNORECASE)]


def classify_sector(titulo, descripcion):
    combined = f"{titulo or ''} {descripcion or ''}".lower()
    for pattern, sector in SECTOR_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return sector
    return 'Otro'


def parse_salary(salario_str):
    if not salario_str:
        return None
    cleaned = re.sub(r'[^\d.]', '', salario_str.split('+')[0].split('-')[0].strip())
    parts = cleaned.split('.')
    if len(parts) > 2:
        cleaned = ''.join(parts)
    elif len(parts) == 2 and len(parts[1]) == 3:
        cleaned = ''.join(parts)
    try:
        val = int(cleaned)
        return val if val > 100000 else None
    except (ValueError, OverflowError):
        return None


def get_dane_code(municipio):
    return MUNICIPIO_DANE.get((municipio or '').lower().strip()) if municipio else None


def main():
    if not SQLITE_PATH.exists():
        print(f"ERROR: No se encontró {SQLITE_PATH}")
        sys.exit(1)

    engine = create_engine(DB_URL, pool_size=1, max_overflow=0)

    # Get existing hashes from PG
    with engine.connect() as conn:
        existing = set()
        try:
            rows = conn.execute(text("SELECT content_hash FROM empleo.ofertas_laborales WHERE content_hash IS NOT NULL")).fetchall()
            existing = {r[0] for r in rows}
        except Exception:
            print("WARN: Table empleo.ofertas_laborales may not exist, will try to create")

    print(f"  {len(existing)} ofertas existentes en Supabase")

    # Read SQLite
    conn_sqlite = sqlite3.connect(str(SQLITE_PATH))
    conn_sqlite.row_factory = sqlite3.Row
    all_rows = conn_sqlite.execute("SELECT * FROM ofertas ORDER BY id").fetchall()
    print(f"  {len(all_rows)} ofertas en SQLite")

    new_rows = [r for r in all_rows if r['content_hash'] not in existing]
    print(f"  {len(new_rows)} nuevas ofertas para sincronizar")

    if not new_rows:
        print("Nada nuevo para sincronizar.")
        conn_sqlite.close()
        engine.dispose()
        return

    with engine.begin() as conn:
        # Ensure table exists
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS empleo"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS empleo.ofertas_laborales (
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

        inserted = 0
        for row in new_rows:
            titulo = row['titulo']
            desc = row['descripcion']
            skills = extract_skills(titulo, desc)
            sector = classify_sector(titulo, desc)
            salario_num = parse_salary(row['salario'])
            dane = get_dane_code(row['municipio'])

            fecha_pub = row['fecha_pub']
            if fecha_pub and '/' in fecha_pub:
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

        print(f"  Insertadas: {inserted} nuevas ofertas")

    conn_sqlite.close()
    engine.dispose()
    print("Sync completado!")


if __name__ == "__main__":
    main()
