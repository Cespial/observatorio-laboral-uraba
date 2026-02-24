"""Tests for the rate limiting middleware."""
from src.backend.middleware.rate_limit import RateLimitMiddleware


class TestRateLimit:
    def test_normal_request_includes_headers(self, client, mock_query_dicts):
        mock_query_dicts.return_value = [{"skill": "Excel", "demanda": 10}]
        resp = client.get("/api/empleo/skills")
        assert resp.status_code == 200
        assert "X-RateLimit-Limit" in resp.headers
        assert "X-RateLimit-Remaining" in resp.headers

    def test_health_check_not_rate_limited(self, client):
        for _ in range(100):
            resp = client.get("/")
            assert resp.status_code == 200

    def test_docs_not_rate_limited(self, client):
        for _ in range(100):
            resp = client.get("/docs")
            assert resp.status_code == 200

    def test_rate_limit_exceeded_with_low_limit(self, mock_engine, mock_query_dicts):
        """Create a dedicated app with a very low rate limit to test 429."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        app = FastAPI()
        app.add_middleware(RateLimitMiddleware, requests_per_minute=5, burst_per_second=100)

        @app.get("/test")
        def test_endpoint():
            return {"ok": True}

        client = TestClient(app)
        statuses = []
        for _ in range(10):
            resp = client.get("/test")
            statuses.append(resp.status_code)

        assert 429 in statuses
        # The 429 response should have proper format
        resp_429 = client.get("/test")
        if resp_429.status_code == 429:
            body = resp_429.json()
            assert "detail" in body
            assert "retry_after_seconds" in body
            assert "Retry-After" in resp_429.headers
