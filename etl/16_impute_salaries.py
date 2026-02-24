"""
ETL 16: Imputación Salarial
============================
Estima salarios para ofertas sin salario_numerico usando la mediana
por sector + municipio + nivel_educativo + nivel_experiencia.

Fallback chain:
  1. sector + municipio + nivel_educativo + nivel_experiencia (≥3 muestra)
  2. sector + municipio (≥3 muestra)
  3. sector alone (≥3 muestra)

Writes result to empleo.ofertas_laborales.salario_imputado.
"""
import os
import sys
from pathlib import Path

# Allow imports from etl/
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import create_engine, text

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

engine = create_engine(DATABASE_URL)


def ensure_column():
    """Add salario_imputado column if it doesn't exist."""
    with engine.begin() as conn:
        conn.execute(text(
            "ALTER TABLE empleo.ofertas_laborales "
            "ADD COLUMN IF NOT EXISTS salario_imputado INTEGER"
        ))
    print("[OK] Column salario_imputado ensured.")


def build_reference_table(conn):
    """Build salary reference medians at different granularity levels."""
    # Level 1: Full granularity
    level1 = conn.execute(text("""
        SELECT sector, municipio, nivel_educativo, nivel_experiencia,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_numerico) as mediana,
               COUNT(*) as muestra
        FROM empleo.ofertas_laborales
        WHERE salario_numerico IS NOT NULL
        GROUP BY sector, municipio, nivel_educativo, nivel_experiencia
        HAVING COUNT(*) >= 3
    """)).fetchall()

    # Level 2: sector + municipio
    level2 = conn.execute(text("""
        SELECT sector, municipio,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_numerico) as mediana,
               COUNT(*) as muestra
        FROM empleo.ofertas_laborales
        WHERE salario_numerico IS NOT NULL
        GROUP BY sector, municipio
        HAVING COUNT(*) >= 3
    """)).fetchall()

    # Level 3: sector only
    level3 = conn.execute(text("""
        SELECT sector,
               PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY salario_numerico) as mediana,
               COUNT(*) as muestra
        FROM empleo.ofertas_laborales
        WHERE salario_numerico IS NOT NULL
        GROUP BY sector
        HAVING COUNT(*) >= 3
    """)).fetchall()

    # Build lookup dicts
    ref1 = {}
    for r in level1:
        key = (r[0], r[1], r[2], r[3])
        ref1[key] = int(r[4])

    ref2 = {}
    for r in level2:
        key = (r[0], r[1])
        ref2[key] = int(r[4])

    ref3 = {}
    for r in level3:
        ref3[r[0]] = int(r[4])

    print(f"  Reference tables: L1={len(ref1)} | L2={len(ref2)} | L3={len(ref3)}")
    return ref1, ref2, ref3


def impute(conn, ref1, ref2, ref3):
    """Impute salaries for offers missing salario_numerico."""
    # Reset previous imputations
    conn.execute(text("UPDATE empleo.ofertas_laborales SET salario_imputado = NULL"))

    # Fetch offers without salary
    rows = conn.execute(text("""
        SELECT id, sector, municipio, nivel_educativo, nivel_experiencia
        FROM empleo.ofertas_laborales
        WHERE salario_numerico IS NULL
    """)).fetchall()

    print(f"  Offers without salary: {len(rows)}")

    updates = []
    l1_hits = l2_hits = l3_hits = misses = 0

    for row in rows:
        oid, sector, muni, edu, exp = row

        # Try level 1
        key1 = (sector, muni, edu, exp)
        if key1 in ref1:
            updates.append({"oid": oid, "sal": ref1[key1]})
            l1_hits += 1
            continue

        # Try level 2
        key2 = (sector, muni)
        if key2 in ref2:
            updates.append({"oid": oid, "sal": ref2[key2]})
            l2_hits += 1
            continue

        # Try level 3
        if sector in ref3:
            updates.append({"oid": oid, "sal": ref3[sector]})
            l3_hits += 1
            continue

        misses += 1

    # Batch update
    if updates:
        for batch_start in range(0, len(updates), 500):
            batch = updates[batch_start:batch_start + 500]
            for u in batch:
                conn.execute(text(
                    "UPDATE empleo.ofertas_laborales SET salario_imputado = :sal WHERE id = :oid"
                ), u)

    print(f"  Imputed: L1={l1_hits} | L2={l2_hits} | L3={l3_hits} | Misses={misses}")
    print(f"  Total imputed: {len(updates)} / {len(rows)} ({round(len(updates)/max(len(rows),1)*100, 1)}%)")


def main():
    print("=" * 60)
    print("ETL 16: Salary Imputation")
    print("=" * 60)

    ensure_column()

    with engine.begin() as conn:
        ref1, ref2, ref3 = build_reference_table(conn)
        impute(conn, ref1, ref2, ref3)

    print("[DONE] Salary imputation complete.")


if __name__ == "__main__":
    main()
