"""Tests for the analytics router endpoints."""
from unittest.mock import patch


class TestGaps:
    def test_gaps_returns_brecha(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [{
            "municipio": "Apartadó",
            "valor_municipio": 200000,
            "promedio_regional": 150000,
            "brecha_absoluta": 50000,
            "brecha_porcentual": 33.3,
            "anio": 2023,
        }]
        resp = client.get("/api/analytics/gaps?dane_code=05045&indicador=Población total")
        assert resp.status_code == 200
        data = resp.json()
        assert data["municipio"] == "Apartadó"
        assert data["brecha_absoluta"] == 50000

    def test_gaps_not_found(self, client, mock_query_dicts):
        mock_query_dicts.return_value = []
        resp = client.get("/api/analytics/gaps?dane_code=99999")
        assert resp.status_code == 404


class TestRanking:
    def test_ranking_returns_ordered_list(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [
            {"municipio": "Apartadó", "dane_code": "05045", "valor": 200000, "anio": 2023},
            {"municipio": "Turbo", "dane_code": "05837", "valor": 180000, "anio": 2023},
        ]
        resp = client.get("/api/analytics/ranking?indicador=Población total&order=desc")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["valor"] >= data[1]["valor"]


class TestTermometro:
    def test_termometro_laboral(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [
            {"municipio": "Apartadó", "ultimos_7_dias": 10, "anteriores_7_dias": 8,
             "ultimos_30_dias": 40, "total": 100},
        ]
        resp = client.get("/api/analytics/laboral/termometro")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert "tendencia" in data[0]
        assert data[0]["tendencia"] == 25.0  # (10-8)/8*100


class TestOfertaDemanda:
    def test_oferta_demanda(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            [{"municipio": "Apartadó", "dane_code": "05045", "vacantes": 50}],
            [{"dane_code": "05045", "municipio": "Apartadó", "poblacion": 200000, "anio": 2023}],
        ]
        resp = client.get("/api/analytics/laboral/oferta-demanda")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["vacantes_por_1000_hab"] == 0.25


class TestBrechaSkills:
    def test_brecha_skills(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            [{"skill": "Excel", "demanda": 30}, {"skill": "Ventas", "demanda": 20}],
            [{"sector": "Agroindustria", "ofertas": 50, "empresas": 10}],
            [{"icfes_promedio": 240.5, "colegios": 15, "total_estudiantes": 1200}],
        ]
        resp = client.get("/api/analytics/laboral/brecha-skills")
        assert resp.status_code == 200
        data = resp.json()
        assert "skills_demandadas" in data
        assert "capital_humano" in data
        assert "insights" in data
        assert len(data["skills_demandadas"]) == 2


class TestDinamismo:
    def test_dinamismo_laboral(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [
            {"mes": "2025-01", "ofertas": 40, "empresas": 10, "municipios": 5,
             "sectores": 4, "crecimiento_pct": None},
            {"mes": "2025-02", "ofertas": 52, "empresas": 12, "municipios": 6,
             "sectores": 5, "crecimiento_pct": 30.0},
        ]
        resp = client.get("/api/analytics/laboral/dinamismo")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[1]["crecimiento_pct"] == 30.0


class TestSectorMunicipio:
    def test_sector_municipio_matrix(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [
            {"sector": "Agroindustria", "municipio": "Apartadó", "ofertas": 30},
            {"sector": "Agroindustria", "municipio": "Turbo", "ofertas": 20},
            {"sector": "Salud", "municipio": "Apartadó", "ofertas": 15},
        ]
        resp = client.get("/api/analytics/laboral/sector-municipio")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2  # 2 sectors
        agro = next(s for s in data if s["sector"] == "Agroindustria")
        assert agro["Apartadó"] == 30
        assert agro["total"] == 50
