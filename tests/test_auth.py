"""Testes do fluxo de autenticação e proteção contra brute force."""
from __future__ import annotations

from app.models import User


class TestRegistration:
    def test_register_page_loads(self, client):
        resp = client.get("/auth/register")
        assert resp.status_code == 200
        assert "Criar conta".encode() in resp.data

    def test_successful_registration(self, client, db):
        resp = client.post(
            "/auth/register",
            data={
                "username": "bob",
                "email": "bob@example.com",
                "password": "Senha@123",
                "confirm_password": "Senha@123",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert User.query.filter_by(username="bob").first() is not None

    def test_password_is_hashed_not_plaintext(self, client, db):
        client.post(
            "/auth/register",
            data={
                "username": "carol",
                "email": "carol@example.com",
                "password": "Senha@123",
                "confirm_password": "Senha@123",
            },
        )
        u = User.query.filter_by(username="carol").first()
        assert u is not None
        assert u.password_hash != "Senha@123"
        assert u.check_password("Senha@123")

    def test_weak_password_rejected(self, client, db):
        resp = client.post(
            "/auth/register",
            data={
                "username": "dave",
                "email": "dave@example.com",
                "password": "fraca",  # sem maiúscula, número e curta
                "confirm_password": "fraca",
            },
        )
        assert resp.status_code == 200
        assert User.query.filter_by(username="dave").first() is None

    def test_duplicate_username_rejected(self, client, db, user):
        resp = client.post(
            "/auth/register",
            data={
                "username": "alice",  # já existe (fixture)
                "email": "outro@example.com",
                "password": "Senha@123",
                "confirm_password": "Senha@123",
            },
        )
        assert "já está em uso".encode() in resp.data


class TestLogin:
    def test_login_success(self, client, user):
        resp = client.post(
            "/auth/login",
            data={"username": "alice", "password": "Senha@123"},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert "Minhas tarefas".encode() in resp.data

    def test_login_wrong_password(self, client, user):
        resp = client.post(
            "/auth/login",
            data={"username": "alice", "password": "errada"},
            follow_redirects=True,
        )
        assert "inválidos".encode() in resp.data

    def test_logout_requires_login(self, client):
        # Logout é POST e protegido; sem sessão redireciona ao login.
        resp = client.post("/auth/logout", follow_redirects=True)
        assert resp.status_code == 200
        assert "Entrar no TaskGuard".encode() in resp.data


class TestBruteForceProtection:
    def test_account_locks_after_max_attempts(self, client, db, user):
        # TestingConfig define LOGIN_MAX_ATTEMPTS = 3.
        for _ in range(3):
            client.post(
                "/auth/login",
                data={"username": "alice", "password": "errada"},
            )
        refreshed = User.query.filter_by(username="alice").first()
        assert refreshed.is_locked()

    def test_locked_account_blocks_valid_password(self, client, db, user):
        for _ in range(3):
            client.post(
                "/auth/login",
                data={"username": "alice", "password": "errada"},
            )
        # Mesmo com a senha correta, a conta segue bloqueada.
        resp = client.post(
            "/auth/login",
            data={"username": "alice", "password": "Senha@123"},
            follow_redirects=True,
        )
        assert "bloqueada".encode() in resp.data
