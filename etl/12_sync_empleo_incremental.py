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
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_URL

SQLITE_PATH = Path.home() / "uraba_empleos" / "empleos_uraba.db"

from etl_sync import (
    extract_skills,
    classify_sector,
    extract_enrichment,
    parse_salary,
    get_dane_code,
    compute_dedup_hash,
)


def main():
    if not SQLITE_PATH.exists():
        print(f"ERROR: No se encontró {SQLITE_PATH}")
        sys.exit(1)

    engine = create_engine(DB_URL, pool_size=1, max_overflow=0)

    # Get existing hashes from PG (both content_hash and dedup_hash)
    with engine.connect() as conn:
        existing_content = set()
        existing_dedup = set()
        try:
            rows = conn.execute(text(
                "SELECT content_hash, dedup_hash FROM empleo.ofertas_laborales "
                "WHERE content_hash IS NOT NULL OR dedup_hash IS NOT NULL"
            )).fetchall()
            existing_content = {r[0] for r in rows if r[0]}
            existing_dedup = {r[1] for r in rows if r[1]}
        except Exception:
            print("WARN: Table empleo.ofertas_laborales may not exist, will try to create")

    print(f"  {len(existing_content)} ofertas existentes (content_hash)")
    print(f"  {len(existing_dedup)} ofertas existentes (dedup_hash)")

    # Read SQLite
    conn_sqlite = sqlite3.connect(str(SQLITE_PATH))
    conn_sqlite.row_factory = sqlite3.Row
    all_rows = conn_sqlite.execute("SELECT * FROM ofertas ORDER BY id").fetchall()
    print(f"  {len(all_rows)} ofertas en SQLite")

    new_rows = [r for r in all_rows if r['content_hash'] not in existing_content]
    print(f"  {len(new_rows)} nuevas ofertas (por content_hash) para sincronizar")

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
                content_hash TEXT,
                nivel_experiencia TEXT,
                tipo_contrato TEXT,
                nivel_educativo TEXT,
                modalidad TEXT
            )
        """))
        # Add new columns if table already exists (idempotent)
        for col in ['nivel_experiencia', 'tipo_contrato', 'nivel_educativo', 'modalidad', 'dedup_hash']:
            conn.execute(text(f"ALTER TABLE empleo.ofertas_laborales ADD COLUMN IF NOT EXISTS {col} TEXT"))

        # Create unique index on dedup_hash for cross-portal deduplication
        conn.execute(text("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_ofertas_dedup_hash
            ON empleo.ofertas_laborales (dedup_hash)
            WHERE dedup_hash IS NOT NULL
        """))

        inserted = 0
        skipped_dedup = 0
        for row in new_rows:
            titulo = row['titulo']
            desc = row['descripcion']
            municipio = row['municipio']
            empresa = row['empresa']

            # Cross-portal dedup: skip if same title+company+municipality already exists
            dedup = compute_dedup_hash(titulo, empresa, municipio)
            if dedup in existing_dedup:
                skipped_dedup += 1
                continue

            skills = extract_skills(titulo, desc)
            sector = classify_sector(titulo, desc)
            salario_num = parse_salary(row['salario'])
            dane = get_dane_code(municipio)
            enrich = extract_enrichment(titulo, desc)

            fecha_pub = row['fecha_pub']
            if fecha_pub and '/' in fecha_pub:
                parts = fecha_pub.split('/')
                if len(parts) == 3:
                    fecha_pub = f"{parts[2]}-{parts[1]}-{parts[0]}"

            conn.execute(text("""
                INSERT INTO empleo.ofertas_laborales
                    (titulo, empresa, salario_texto, salario_numerico, descripcion,
                     fecha_publicacion, enlace, municipio, dane_code, fuente,
                     sector, skills, fecha_scraping, content_hash, dedup_hash,
                     nivel_experiencia, tipo_contrato, nivel_educativo, modalidad)
                VALUES
                    (:titulo, :empresa, :salario_texto, :salario_num, :descripcion,
                     :fecha_pub, :enlace, :municipio, :dane, :fuente,
                     :sector, :skills, :fecha_scraping, :hash, :dedup_hash,
                     :nivel_experiencia, :tipo_contrato, :nivel_educativo, :modalidad)
                ON CONFLICT (dedup_hash) WHERE dedup_hash IS NOT NULL DO NOTHING
            """), {
                "titulo": titulo,
                "empresa": empresa,
                "salario_texto": row['salario'],
                "salario_num": salario_num,
                "descripcion": desc,
                "fecha_pub": fecha_pub if fecha_pub else None,
                "enlace": row['enlace'],
                "municipio": municipio,
                "dane": dane,
                "fuente": row['fuente'],
                "sector": sector,
                "skills": skills,
                "fecha_scraping": row['fecha_scraping'],
                "hash": row['content_hash'],
                "dedup_hash": dedup,
                "nivel_experiencia": enrich['nivel_experiencia'],
                "tipo_contrato": enrich['tipo_contrato'],
                "nivel_educativo": enrich['nivel_educativo'],
                "modalidad": enrich['modalidad'],
            })
            existing_dedup.add(dedup)
            inserted += 1

        print(f"  Insertadas: {inserted} nuevas ofertas")
        print(f"  Omitidas por deduplicación cross-portal: {skipped_dedup}")

    conn_sqlite.close()
    engine.dispose()
    print("Sync completado!")


if __name__ == "__main__":
    main()
