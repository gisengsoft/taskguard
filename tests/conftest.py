"""Fixtures compartilhadas dos testes (pytest).

Cada teste recebe uma aplicação isolada em modo `testing`, com banco SQLite em
memória recriado do zero, garantindo independência total entre os casos.
"""
from __future__ import annotations

import pytest

from app import create_app
from app.extensions import db as _db
from app.models import User


@pytest.fixture()
def app():
    """Aplicação Flask configurada para testes."""
    application = create_app("testing")
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Cliente de teste HTTP."""
    return app.test_client()


@pytest.fixture()
def db(app):
    """Sessão do banco de dados dentro do contexto da aplicação."""
    return _db


@pytest.fixture()
def user(app):
    """Usuário de teste já persistido."""
    u = User(username="alice", email="alice@example.com")
    u.set_password("Senha@123")
    _db.session.add(u)
    _db.session.commit()
    return u


@pytest.fixture()
def auth_client(client, user):
    """Cliente já autenticado como o usuário de teste."""
    client.post(
        "/auth/login",
        data={"username": "alice", "password": "Senha@123"},
        follow_redirects=True,
    )
    return client
