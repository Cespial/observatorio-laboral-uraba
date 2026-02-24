"""Tests for the main FastAPI app: root endpoint, CORS, error handlers."""
from unittest.mock import patch


def test_root_endpoint(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Observatorio Laboral de Urabá"
    assert data["version"] == "4.0.0"
    assert "Apartadó" in data["municipios"]
    assert len(data["municipios"]) == 11
    assert "endpoints" in data


def test_root_has_security_headers(client):
    resp = client.get("/")
    assert resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert resp.headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert resp.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_cors_headers_on_options(client):
    resp = client.options(
        "/",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert resp.status_code == 200


def test_docs_endpoint_available(client):
    resp = client.get("/docs")
    assert resp.status_code == 200


def test_404_for_unknown_route(client):
    resp = client.get("/api/nonexistent")
    assert resp.status_code == 404
