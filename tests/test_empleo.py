"""Tests for the empleo router endpoints."""
from unittest.mock import patch, MagicMock
from sqlalchemy import text


class TestOfertasEndpoint:
    def test_get_ofertas_basic(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            [{"total": 2}],  # count query
            [  # data query
                {
                    "id": 1, "titulo": "Operario de banano", "empresa": "Unibán",
                    "salario_texto": "1.300.000", "salario_numerico": 1300000,
                    "descripcion": "Cosecha", "municipio": "Apartadó",
                    "dane_code": "05045", "fuente": "computrabajo",
                    "sector": "Agroindustria", "skills": ["Cosecha"],
                    "fecha_publicacion": "2025-01-15", "enlace": "https://example.com",
                    "nivel_experiencia": "1 ano", "tipo_contrato": "Fijo",
                    "nivel_educativo": "Bachiller", "modalidad": "Presencial",
                },
                {
                    "id": 2, "titulo": "Vendedor", "empresa": "Almacén",
                    "salario_texto": None, "salario_numerico": None,
                    "descripcion": "Ventas", "municipio": "Turbo",
                    "dane_code": "05837", "fuente": "elempleo",
                    "sector": "Comercio y Ventas", "skills": ["Ventas"],
                    "fecha_publicacion": "2025-01-14", "enlace": "https://example.com/2",
                    "nivel_experiencia": None, "tipo_contrato": None,
                    "nivel_educativo": None, "modalidad": None,
                },
            ],
        ]
        resp = client.get("/api/empleo/ofertas")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["page"] == 1

    def test_get_ofertas_with_filters(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            [{"total": 1}],
            [{"id": 1, "titulo": "Enfermera", "empresa": "IPS", "municipio": "Apartadó",
              "dane_code": "05045", "fuente": "sena", "sector": "Salud",
              "salario_texto": None, "salario_numerico": None, "descripcion": "",
              "skills": [], "fecha_publicacion": None, "enlace": "",
              "nivel_experiencia": None, "tipo_contrato": None,
              "nivel_educativo": None, "modalidad": None}],
        ]
        resp = client.get("/api/empleo/ofertas?municipio=Apartadó&sector=Salud&page=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    def test_get_ofertas_pagination(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            [{"total": 50}],
            [],
        ]
        resp = client.get("/api/empleo/ofertas?page=3&page_size=10")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 50
        assert data["page"] == 3
        assert data["total_pages"] == 5


class TestEmpleoStats:
    def test_stats_basic(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            [{"total": 100}],
            [{"municipio": "Apartadó", "total": 60}, {"municipio": "Turbo", "total": 40}],
            [{"fuente": "computrabajo", "total": 70}],
            [{"sector": "Agroindustria", "total": 50}],
            [{"empresa": "Unibán", "total": 20}],
            [{"total": 30}],
            [{"promedio": 1500000, "minimo": 1000000, "maximo": 5000000, "mediana": 1300000}],
        ]
        resp = client.get("/api/empleo/stats")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_ofertas"] == 100
        assert len(data["por_municipio"]) == 2


class TestEmpleoSkills:
    def test_skills_demand(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [
            {"skill": "Excel", "demanda": 30},
            {"skill": "Ventas", "demanda": 25},
        ]
        resp = client.get("/api/empleo/skills")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["skill"] == "Excel"


class TestEmpleoKpis:
    def test_kpis_endpoint(self, client, mock_query_dicts):
        mock_conn = MagicMock()
        mock_row = (100, 25, 8, 1500000, "Agroindustria", "Unibán")
        mock_conn.__enter__ = MagicMock(return_value=mock_conn)
        mock_conn.__exit__ = MagicMock(return_value=False)
        mock_conn.execute.return_value.fetchone.return_value = mock_row

        with patch("src.backend.routers.empleo.engine") as mock_eng:
            mock_eng.connect.return_value = mock_conn
            resp = client.get("/api/empleo/kpis")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_ofertas"] == 100
        assert data["sector_top"] == "Agroindustria"


class TestEmpleoSerie:
    def test_serie_temporal(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [
            {"periodo": "2025-01", "ofertas": 45, "empresas": 12, "salario_promedio": 1500000},
            {"periodo": "2025-02", "ofertas": 52, "empresas": 15, "salario_promedio": 1600000},
        ]
        resp = client.get("/api/empleo/serie-temporal")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["periodo"] == "2025-01"
