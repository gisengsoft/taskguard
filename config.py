"""
Configuração final blindada TaskGuard (DevSecOps ready)
"""
from __future__ import annotations

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# Carrega .env apenas se existir
env_path = BASE_DIR / ".env"
if env_path.exists():
    load_dotenv(env_path)


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


class BaseConfig:
    """Configuração base segura"""

    # ---------------- SECURITY CORE ----------------
    SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE-ME-PRODUCTION")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", False)

    PERMANENT_SESSION_LIFETIME = timedelta(
        minutes=int(os.getenv("SESSION_LIFETIME_MINUTES", "30"))
    )

    # ---------------- DATABASE ----------------
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        f"sqlite:///{BASE_DIR / 'taskguard.db'}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # ---------------- CSRF ----------------
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = 3600

    # ---------------- RATE LIMIT ----------------
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "200 per hour")
    RATELIMIT_HEADERS_ENABLED = True

    # ---------------- LOGIN SECURITY ----------------
    LOGIN_MAX_ATTEMPTS = int(os.getenv("LOGIN_MAX_ATTEMPTS", "5"))
    LOGIN_LOCKOUT_MINUTES = int(os.getenv("LOGIN_LOCKOUT_MINUTES", "15"))

    # ---------------- LOGGING ----------------
    LOG_DIR = BASE_DIR / "logs"
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    SYSLOG_ENABLED = _env_bool("SYSLOG_ENABLED", False)
    SYSLOG_HOST = os.getenv("SYSLOG_HOST", "localhost")
    SYSLOG_PORT = int(os.getenv("SYSLOG_PORT", "514"))

    # ---------------- SECURITY HEADERS ----------------
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
    DEBUG = True
    ENV = "development"


class TestingConfig(BaseConfig):
    DEBUG = False
    TESTING = True
    ENV = "testing"

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False
    RATELIMIT_STORAGE_URI = "memory://"
    LOGIN_MAX_ATTEMPTS = 3
    SYSLOG_ENABLED = False


class ProductionConfig(BaseConfig):
    DEBUG = False
    ENV = "production"

    SESSION_COOKIE_SECURE = True
    FORCE_HTTPS = True


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}


def get_config(name: str | None = None) -> type[BaseConfig]:
    name = name or os.getenv("FLASK_CONFIG", "default")
    return config_by_name.get(name, DevelopmentConfig)
