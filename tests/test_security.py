"""Testes das defesas de segurança: headers, CSRF, sanitização e health check."""
from __future__ import annotations

import pytest

from app import create_app
from app.security import sanitize_text


class TestSecurityHeaders:
    def test_security_headers_present(self, client):
        resp = client.get("/auth/login")
        headers = resp.headers
        assert "Content-Security-Policy" in headers
        assert headers.get("X-Frame-Options") == "DENY"
        assert headers.get("X-Content-Type-Options") == "nosniff"
        assert "Referrer-Policy" in headers
        assert "Permissions-Policy" in headers

    def test_csp_restricts_default_src(self, client):
        resp = client.get("/auth/login")
        assert "default-src 'self'" in resp.headers.get("Content-Security-Policy", "")


class TestCsrfProtection:
    def test_csrf_blocks_post_without_token(self):
        # App separado com CSRF ATIVADO (a config de teste o desliga).
        app = create_app("development")
        app.config.update(WTF_CSRF_ENABLED=True, SECRET_KEY="test", TESTING=True)
        with app.test_client() as c:
            resp = c.post(
                "/auth/login",
                data={"username": "x", "password": "y"},
            )
            # Sem token CSRF a requisição é rejeitada (400).
            assert resp.status_code == 400


class TestInputSanitization:
    @pytest.mark.parametrize(
        "raw,expected_absent",
        [
            ("<script>alert(1)</script>", "<script>"),
            ("<img src=x onerror=alert(1)>", "<img"),
            ("texto & <b>negrito</b>", "<b>"),
        ],
    )
    def test_sanitize_escapes_html(self, raw, expected_absent):
        cleaned = sanitize_text(raw)
        assert expected_absent not in cleaned

    def test_sanitize_handles_none(self):
        assert sanitize_text(None) == ""

    def test_sanitize_truncates(self):
        assert len(sanitize_text("a" * 500, max_length=100)) == 100

    def test_stored_xss_is_escaped_in_response(self, auth_client):
        payload = "<script>alert('xss')</script>"
        auth_client.post(
            "/tarefas/nova",
            data={
                "title": payload,
                "description": "x",
                "status": "pendente",
                "priority": "media",
            },
            follow_redirects=True,
        )
        resp = auth_client.get("/tarefas/")
        # O script bruto não pode aparecer executável na resposta.
        assert b"<script>alert('xss')</script>" not in resp.data


class TestHealthEndpoint:
    def test_health_returns_200_and_json(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "taskguard"
        assert data["database"] == "up"
