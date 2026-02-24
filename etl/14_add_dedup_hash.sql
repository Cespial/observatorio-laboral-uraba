-- ============================================================
-- Migration: Add dedup_hash column for cross-portal deduplication
-- ============================================================
-- The dedup_hash is computed as SHA256(normalize(titulo)|normalize(empresa)|normalize(municipio))[:16]
-- This catches the same job posted on multiple portals (e.g., Computrabajo + ElEmpleo)

-- 1. Add the column
ALTER TABLE empleo.ofertas_laborales ADD COLUMN IF NOT EXISTS dedup_hash TEXT;

-- 2. Create a unique partial index (only for non-null values)
CREATE UNIQUE INDEX IF NOT EXISTS idx_ofertas_dedup_hash
ON empleo.ofertas_laborales (dedup_hash)
WHERE dedup_hash IS NOT NULL;

-- 3. Index on content_hash for fast lookups during sync
CREATE INDEX IF NOT EXISTS idx_ofertas_content_hash
ON empleo.ofertas_laborales (content_hash)
WHERE content_hash IS NOT NULL;

-- NOTE: To backfill dedup_hash for existing rows, run:
--   python etl/15_backfill_dedup_hash.py
