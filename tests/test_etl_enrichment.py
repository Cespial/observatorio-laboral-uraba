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
    categorize_skills,
    SKILL_CATEGORIES,
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


class TestNewSkillPatterns:
    """Tests for newly added Urabá-specific skill patterns."""

    def test_detects_portuario_skills(self):
        skills = extract_skills("Operador portuario", "Experiencia en aduanas y manejo de contenedores")
        assert "Aduanas" in skills
        assert "Contenedores" in skills

    def test_detects_estiba(self):
        skills = extract_skills("Estibador", "Trabajo de estiba en puerto")
        assert "Estiba" in skills

    def test_detects_ganaderia(self):
        skills = extract_skills("Trabajador ganadero", "Experiencia en ganadería bovina")
        assert "Ganadería" in skills

    def test_detects_veterinaria(self):
        skills = extract_skills("Profesional veterinario", "Conocimientos en veterinaria")
        assert "Veterinaria" in skills

    def test_detects_palma(self):
        skills = extract_skills("Operario", "Trabajo en cultivo de palma de aceite")
        assert "Palma" in skills

    def test_detects_acuicultura(self):
        skills = extract_skills("Técnico", "Experiencia en acuicultura y piscicultura")
        assert "Acuicultura" in skills

    def test_detects_hoteleria(self):
        skills = extract_skills("Recepcionista", "Experiencia en hotelería")
        assert "Hotelería" in skills

    def test_detects_guia_turistico(self):
        skills = extract_skills("Guía turístico", "Servicio de guía turístico en Urabá")
        assert "Guía turístico" in skills

    def test_detects_transporte_fluvial(self):
        skills = extract_skills("Motorista", "Transporte fluvial por el río Atrato")
        assert "Transporte fluvial" in skills

    def test_detects_maquinaria_pesada(self):
        skills = extract_skills("Operador", "Manejo de maquinaria pesada y retroexcavadora")
        assert "Maquinaria pesada" in skills

    def test_detects_logistica_maritima(self):
        skills = extract_skills("Agente", "Logística naviera y marítima")
        assert "Logística marítima" in skills

    def test_detects_porcicultura(self):
        skills = extract_skills("Técnico", "Trabajo en porcicultura y cría de cerdos")
        assert "Porcicultura" in skills


class TestCategorizeSkills:
    """Tests for the skill categorization function."""

    def test_categorizes_tech_skills(self):
        result = categorize_skills(["Excel", "Python", "SAP"])
        assert "Tecnológica" in result
        assert "Excel" in result["Tecnológica"]
        assert "Python" in result["Tecnológica"]

    def test_categorizes_agro_skills(self):
        result = categorize_skills(["Cosecha", "Fitosanidad", "Ganadería"])
        assert "Agroindustrial" in result
        assert len(result["Agroindustrial"]) == 3

    def test_categorizes_soft_skills(self):
        result = categorize_skills(["Liderazgo", "Comunicación"])
        assert "Blanda" in result
        assert "Liderazgo" in result["Blanda"]

    def test_uncategorized_goes_to_otra(self):
        result = categorize_skills(["Unknown Skill XYZ"])
        assert "Otra" in result
        assert "Unknown Skill XYZ" in result["Otra"]

    def test_empty_input(self):
        result = categorize_skills([])
        assert result == {}

    def test_mixed_categories(self):
        result = categorize_skills(["Excel", "Cosecha", "Liderazgo", "Soldadura"])
        assert "Tecnológica" in result
        assert "Agroindustrial" in result
        assert "Blanda" in result
        assert "Industrial" in result

    def test_skill_categories_has_all_categories(self):
        expected = {"Tecnológica", "Agroindustrial", "Blanda", "Industrial",
                    "Administrativa", "Logística y Transporte", "Turismo y Gastronomía"}
        assert set(SKILL_CATEGORIES.keys()) == expected
