"""Configuração da aplicação TaskGuard.

Centraliza todas as configurações em classes por ambiente. Nenhum segredo é
embutido em código: valores sensíveis são lidos de variáveis de ambiente
(carregadas de um arquivo .env em desenvolvimento). Consulte `.env.example`.
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# Diretório raiz do projeto (…/taskguard)
BASE_DIR = Path(__file__).resolve().parent

# Carrega o .env em desenvolvimento. Em produção as variáveis vêm do ambiente
# do container/orquestrador, e o arquivo simplesmente não existe.
load_dotenv(BASE_DIR / ".env")


def _env_bool(name: str, default: bool = False) -> bool:
    """Lê uma variável de ambiente booleana de forma tolerante."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Configuração comum a todos os ambientes."""

    # ------------------------------------------------------------------ #
    # Núcleo / sessão
    # ------------------------------------------------------------------ #
    SECRET_KEY = os.getenv("SECRET_KEY", "altere-esta-chave-em-producao")

    # Cookies de sessão endurecidos contra roubo/CSRF.
    SESSION_COOKIE_HTTPONLY = True          # Bloqueia leitura via JavaScript (anti-XSS)
    SESSION_COOKIE_SAMESITE = "Lax"         # Mitiga CSRF cross-site
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))
    )

    # ------------------------------------------------------------------ #
    # Banco de dados
    # ------------------------------------------------------------------ #
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL", f"sqlite:///{BASE_DIR / 'logs' / 'taskguard.db'}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ------------------------------------------------------------------ #
    # Proteção CSRF (Flask-WTF)
    # ------------------------------------------------------------------ #
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600              # Token válido por 1 hora

    # ------------------------------------------------------------------ #
    # Rate limiting (Flask-Limiter)
    # ------------------------------------------------------------------ #
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per hour")
    RATELIMIT_HEADERS_ENABLED = True

    # ------------------------------------------------------------------ #
    # Proteção contra brute force no login
    # ------------------------------------------------------------------ #
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))

    # ------------------------------------------------------------------ #
    # Logging / Syslog
    # ------------------------------------------------------------------ #
    LOG_DIR = BASE_DIR / "logs"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    SYSLOG_ENABLED = _env_bool("SYSLOG_ENABLED", False)
    SYSLOG_HOST = os.getenv("SYSLOG_HOST", "localhost")
    SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", "514"))

    # ------------------------------------------------------------------ #
    # Flask-Talisman (headers de segurança / CSP)
    # ------------------------------------------------------------------ #
    # CSP restritiva: nada de inline-script de origem desconhecida. Os poucos
    # scripts próprios usam nonce gerado por requisição (ver app/security.py).
    FORCE_HTTPS = _env_bool("FORCE_HTTPS", False)
    CONTENT_SECURITY_POLICY = {
        "default-src": "'self'",
        "script-src": "'self'",
        "style-src": "'self'",
        "img-src": "'self' data:",
        "font-src": "'self'",
        "object-src": "'none'",
        "base-uri": "'self'",
        "frame-ancestors": "'none'",
        "form-action": "'self'",
    }


class DevelopmentConfig(BaseConfig):
    """Ambiente local de desenvolvimento."""

    DEBUG = True
    ENV = "development"


class TestingConfig(BaseConfig):
    """Ambiente de testes automatizados (pytest)."""

    TESTING = True
    DEBUG = False
    ENV = "testing"
    # Banco em memória, isolado e descartável a cada execução de teste.
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False                # Facilita asserts nos testes de form
    RATELIMIT_ENABLED = False               # Evita falsos negativos por limite
    LOGIN_MAX_ATTEMPTS = 3
    SYSLOG_ENABLED = False


class ProductionConfig(BaseConfig):
    """Ambiente de produção / staging."""

    DEBUG = False
    ENV = "production"
    SESSION_COOKIE_SECURE = False
    FORCE_HTTPS = False

    # Evita fallback silencioso para SQLite em produção caso a variável
    # não seja lida corretamente do ambiente.
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"postgresql+psycopg://{os.getenv('POSTGRES_USER', 'taskguard')}:{os.getenv('POSTGRES_PASSWORD', 'taskguard')}@db:5432/{os.getenv('POSTGRES_DB', 'taskguard')}"
    )
    if SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_DATABASE_URI = f"postgresql+psycopg://{os.getenv('POSTGRES_USER', 'taskguard')}:{os.getenv('POSTGRES_PASSWORD', 'taskguard')}@db:5432/{os.getenv('POSTGRES_DB', 'taskguard')}"


# Mapa de seleção por nome (usado em create_app).
config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    """Resolve a classe de config a partir de FLASK_CONFIG ou do nome dado."""
    name = name or os.getenv("FLASK_CONFIG", "default")
    return config_by_name.get(name, DevelopmentConfig)
