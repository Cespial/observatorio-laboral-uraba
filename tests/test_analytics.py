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


class TestCadenasProductivas:
    def test_cadenas_returns_list(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            # sector_data
            [
                {"sector": "Agroindustria", "municipio": "Apartadó", "ofertas": 40,
                 "empresas": 8, "salario_promedio": 1500000},
                {"sector": "Turismo y Gastronomía", "municipio": "Turbo", "ofertas": 15,
                 "empresas": 5, "salario_promedio": 1200000},
            ],
            # skills_data
            [
                {"sector": "Agroindustria", "skill": "Cosecha", "demanda": 12},
                {"sector": "Agroindustria", "skill": "Empaque", "demanda": 8},
                {"sector": "Turismo y Gastronomía", "skill": "Hotelería", "demanda": 5},
            ],
        ]
        resp = client.get("/api/analytics/laboral/cadenas-productivas")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0
        # First should be the one with most offers
        assert data[0]["ofertas"] >= data[-1]["ofertas"]
        # Check structure
        first = data[0]
        assert "cadena" in first
        assert "ofertas" in first
        assert "empresas" in first
        assert "top_skills" in first
        assert "municipios" in first

    def test_cadenas_empty_data(self, client, mock_query_dicts):
        mock_query_dicts.return_value = []
        resp = client.get("/api/analytics/laboral/cadenas-productivas")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


class TestEstacionalidad:
    def test_estacionalidad_returns_profile(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            # sector × month data
            [
                {"mes": 1, "sector": "Agroindustria", "ofertas": 20, "salario_promedio": 1500000},
                {"mes": 2, "sector": "Agroindustria", "ofertas": 25, "salario_promedio": 1600000},
                {"mes": 1, "sector": "Salud", "ofertas": 10, "salario_promedio": 2000000},
            ],
            # general monthly data
            [
                {"mes": 1, "ofertas": 30, "salario_promedio": 1600000},
                {"mes": 2, "ofertas": 25, "salario_promedio": 1600000},
            ],
        ]
        resp = client.get("/api/analytics/laboral/estacionalidad")
        assert resp.status_code == 200
        data = resp.json()
        assert "perfil_general" in data
        assert "sectores_estacionales" in data
        assert "promedio_mensual" in data
        assert len(data["perfil_general"]) == 2
        # Check classification
        for m in data["perfil_general"]:
            assert m["clasificacion"] in ("pico", "valle", "normal")
            assert "mes_nombre" in m

    def test_estacionalidad_empty(self, client, mock_query_dicts):
        mock_query_dicts.return_value = []
        resp = client.get("/api/analytics/laboral/estacionalidad")
        assert resp.status_code == 200
        data = resp.json()
        assert data["perfil_general"] == []
        assert data["promedio_mensual"] == 0


class TestInformalidad:
    def test_informalidad_returns_ranking(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            # IPM data
            [{"municipio": "Apartadó", "dane_code": "05045", "tasa_ipm": 65.2}],
            # Proxy data
            [{"municipio": "Apartadó", "dane_code": "05045", "total_ofertas": 50,
              "no_indefinido": 20, "indefinido": 30}],
            # Pobreza data
            [{"dane_code": "05045", "pobreza_monetaria": 45.0, "anio": 2023}],
        ]
        resp = client.get("/api/analytics/laboral/informalidad")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 1
        item = data[0]
        assert item["municipio"] == "Apartadó"
        assert item["tasa_ipm"] == 65.2
        assert item["proxy_informal_pct"] == 40.0  # 20/50 * 100
        assert item["pobreza_monetaria"] == 45.0
        assert item["indice_compuesto"] is not None

    def test_informalidad_empty(self, client, mock_query_dicts):
        mock_query_dicts.return_value = []
        resp = client.get("/api/analytics/laboral/informalidad")
        assert resp.status_code == 200
        assert resp.json() == []


class TestSalarioImputado:
    def test_salario_imputado_returns_cobertura(self, client, mock_query_dicts):
        mock_query_dicts.side_effect = [
            # Reference table
            [
                {"sector": "Agroindustria", "municipio": "Apartadó",
                 "nivel_educativo": "Bachiller", "nivel_experiencia": "1 ano",
                 "salario_estimado": 1300000, "muestra": 5, "mediana": 1300000},
            ],
            # Coverage stats
            [{"total": 200, "con_salario": 80, "con_imputado": 60}],
        ]
        resp = client.get("/api/analytics/laboral/salario-imputado")
        assert resp.status_code == 200
        data = resp.json()
        assert "tabla_referencia" in data
        assert "cobertura" in data
        assert data["cobertura"]["total_ofertas"] == 200
        assert data["cobertura"]["pct_salario_real"] == 40.0
        assert data["cobertura"]["pct_cobertura_total"] == 70.0
