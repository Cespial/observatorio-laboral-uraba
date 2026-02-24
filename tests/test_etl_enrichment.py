"""Tests for ETL enrichment functions: skill extraction, sector classification, salary parsing, deduplication."""
import sys
from pathlib import Path

# Make etl module importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "etl"))

from etl_sync import (
    extract_skills,
    classify_sector,
    parse_salary,
    get_dane_code,
    extract_enrichment,
    compute_dedup_hash,
)


class TestExtractSkills:
    def test_detects_excel(self):
        skills = extract_skills("Asistente administrativo", "Manejo de Excel avanzado y Word")
        assert "Excel" in skills
        assert "Word" in skills

    def test_detects_agro_skills(self):
        skills = extract_skills("Operario de campo", "Experiencia en cultivo de banano y cosecha")
        assert "Cultivo banano/plátano" in skills
        assert "Cosecha" in skills

    def test_detects_soft_skills(self):
        skills = extract_skills("Líder de ventas", "Se requiere liderazgo y trabajo en equipo")
        assert "Liderazgo" in skills
        assert "Trabajo en equipo" in skills

    def test_empty_input(self):
        skills = extract_skills(None, None)
        assert skills == []

    def test_no_duplicates(self):
        skills = extract_skills("Excel Excel", "Excel")
        assert skills.count("Excel") == 1


class TestClassifySector:
    def test_agroindustria(self):
        assert classify_sector("Operario agrícola", "Finca bananera") == "Agroindustria"

    def test_salud(self):
        assert classify_sector("Enfermera", "Hospital regional") == "Salud"

    def test_tecnologia(self):
        assert classify_sector("Desarrollador", "Software Python") == "Tecnología"

    def test_educacion(self):
        assert classify_sector("Docente de matemáticas", "Colegio") == "Educación"

    def test_otro_fallback(self):
        assert classify_sector("Cargo genérico", "Descripción vaga") == "Otro"


class TestParseSalary:
    def test_colombian_format(self):
        assert parse_salary("1.300.000") == 1300000

    def test_plain_number(self):
        assert parse_salary("2000000") == 2000000

    def test_with_prefix(self):
        assert parse_salary("$1.500.000 + comisiones") == 1500000

    def test_too_low(self):
        assert parse_salary("50000") is None

    def test_none_input(self):
        assert parse_salary(None) is None

    def test_garbage(self):
        assert parse_salary("A convenir") is None


class TestGetDaneCode:
    def test_apartado_with_accent(self):
        assert get_dane_code("Apartadó") == "05045"

    def test_apartado_without_accent(self):
        assert get_dane_code("apartado") == "05045"

    def test_turbo(self):
        assert get_dane_code("Turbo") == "05837"

    def test_none_input(self):
        assert get_dane_code(None) is None

    def test_unknown_city(self):
        assert get_dane_code("Bogotá") is None


class TestExtractEnrichment:
    def test_experience_detection(self):
        result = extract_enrichment("Vendedor", "Se requiere 2 años de experiencia en ventas")
        assert result["nivel_experiencia"] == "2 anos"

    def test_contract_type(self):
        result = extract_enrichment("Operario", "Contrato a término indefinido")
        assert result["tipo_contrato"] == "Indefinido"

    def test_education_level(self):
        result = extract_enrichment("Contador", "Profesional en contaduría")
        assert result["nivel_educativo"] == "Profesional"

    def test_modality_remote(self):
        result = extract_enrichment("Programador", "Trabajo remoto desde casa")
        assert result["modalidad"] == "Remoto"

    def test_no_enrichment(self):
        result = extract_enrichment("Cargo", "Sin detalles")
        assert result["nivel_experiencia"] is None
        assert result["tipo_contrato"] is None


class TestDedupHash:
    def test_same_offer_same_hash(self):
        h1 = compute_dedup_hash("Operario", "Unibán", "Apartadó")
        h2 = compute_dedup_hash("Operario", "Unibán", "Apartadó")
        assert h1 == h2

    def test_different_offers_different_hash(self):
        h1 = compute_dedup_hash("Operario", "Unibán", "Apartadó")
        h2 = compute_dedup_hash("Vendedor", "Almacén", "Turbo")
        assert h1 != h2

    def test_case_insensitive(self):
        h1 = compute_dedup_hash("OPERARIO", "UNIBÁN", "APARTADÓ")
        h2 = compute_dedup_hash("operario", "unibán", "apartadó")
        assert h1 == h2

    def test_handles_none(self):
        h1 = compute_dedup_hash("Operario", None, "Apartadó")
        h2 = compute_dedup_hash("Operario", None, "Apartadó")
        assert h1 == h2
