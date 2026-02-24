#!/usr/bin/env python3
"""
ETL 15 — Backfill dedup_hash for existing ofertas_laborales rows.
Computes dedup_hash (SHA256 of titulo+empresa+municipio) and removes duplicates.
"""
import sys
from pathlib import Path
from sqlalchemy import create_engine, text

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import DB_URL
from etl_sync import compute_dedup_hash

def main():
    engine = create_engine(DB_URL, pool_size=1, max_overflow=0)

    with engine.connect() as conn:
        rows = conn.execute(text(
            "SELECT id, titulo, empresa, municipio FROM empleo.ofertas_laborales "
            "WHERE dedup_hash IS NULL ORDER BY id"
        )).fetchall()

    print(f"  {len(rows)} rows to backfill")
    if not rows:
        engine.dispose()
        return

    seen_hashes = {}
    duplicates = []
    updates = []

    for row_id, titulo, empresa, municipio in rows:
        h = compute_dedup_hash(titulo, empresa, municipio)
        if h in seen_hashes:
            duplicates.append(row_id)
        else:
            seen_hashes[h] = row_id
            updates.append((row_id, h))

    print(f"  {len(updates)} unique rows to update")
    print(f"  {len(duplicates)} duplicate rows to remove")

    with engine.begin() as conn:
        # Update unique rows
        for row_id, h in updates:
            conn.execute(
                text("UPDATE empleo.ofertas_laborales SET dedup_hash = :h WHERE id = :id"),
                {"h": h, "id": row_id},
            )

        # Delete duplicates
        if duplicates:
            conn.execute(
                text("DELETE FROM empleo.ofertas_laborales WHERE id = ANY(:ids)"),
                {"ids": duplicates},
            )

    engine.dispose()
    print(f"  Backfill complete. Updated: {len(updates)}, Removed: {len(duplicates)}")


if __name__ == "__main__":
    main()
