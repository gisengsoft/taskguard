"""TaskGuard — fábrica da aplicação Flask.

Implementa o padrão *application factory*: `create_app` constrói e configura
uma instância da aplicação sob demanda, o que facilita testes (cada teste cria
seu próprio app isolado) e múltiplos ambientes.
"""
from __future__ import annotations

import logging

from flask import Flask, render_template
from flask_login import current_user
from werkzeug.middleware.proxy_fix import ProxyFix

from app.extensions import csrf, db, limiter, login_manager
from app.logging_config import configure_logging, log_security_event
from app.security import init_security
from config import BaseConfig, get_config

__version__ = "1.0.0"


def create_app(config_name: str | None = None) -> Flask:
    """Cria, configura e retorna a aplicação Flask.

    Parameters
    ----------
    config_name:
        Nome do ambiente (``development`` | ``testing`` | ``production``).
        Quando omitido, usa a variável de ambiente ``FLASK_CONFIG``.
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    config_class: type[BaseConfig] = get_config(config_name)
    app.config.from_object(config_class)

    # Confia em 1 nível de proxy reverso (Nginx/Traefik) para obter o IP real
    # do cliente e o esquema HTTPS. Essencial para rate limiting e logs corretos.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Logging deve vir antes do resto para capturar a inicialização.
    configure_logging(app)

    _register_extensions(app)
    _register_blueprints(app)
    _register_shell_context(app)
    _register_jinja_globals(app)

    # Tratadores de erro.
    from app.errors import register_error_handlers

    register_error_handlers(app)

    app.logger.info("Aplicação TaskGuard v%s inicializada (%s).",
                    __version__, app.config.get("ENV"))
    return app


def _register_extensions(app: Flask) -> None:
    """Vincula as extensões à aplicação."""
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    init_security(app)  # Flask-Talisman + headers extras

    # Carregador de usuário para o Flask-Login.
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id: str):  # type: ignore[no-untyped-def]
        return db.session.get(User, int(user_id))

    @login_manager.unauthorized_handler
    def _unauthorized():  # type: ignore[no-untyped-def]
        # Acesso a área protegida sem sessão válida é registrado.
        log_security_event(
            "unauthorized_access",
            "Tentativa de acesso a recurso protegido sem autenticação.",
            level=logging.WARNING,
        )
        from flask import flash, redirect, url_for

        flash("Faça login para acessar esta página.", "warning")
        return redirect(url_for("auth.login"))

    # Cria as tabelas automaticamente (idempotente) — funciona tanto com
    # SQLite quanto com PostgreSQL. Em produção, o ideal é evoluir o schema
    # com migrações (ex.: Alembic); aqui mantemos simples para o estudo de caso.
    with app.app_context():
        db.create_all()


def _register_blueprints(app: Flask) -> None:
    """Registra os blueprints (módulos de rotas)."""
    from app.auth.routes import auth_bp
    from app.main.routes import main_bp
    from app.tasks.routes import tasks_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(tasks_bp, url_prefix="/tarefas")

    # O endpoint de health check não deve sofrer rate limit nem CSRF.
    limiter.exempt(main_bp)


def _register_shell_context(app: Flask) -> None:
    """Disponibiliza objetos úteis no `flask shell`."""
    from app.models import Task, User

    @app.shell_context_processor
    def _ctx():  # type: ignore[no-untyped-def]
        return {"db": db, "User": User, "Task": Task}


def _register_jinja_globals(app: Flask) -> None:
    """Expõe variáveis globais aos templates."""

    @app.context_processor
    def _inject_globals():  # type: ignore[no-untyped-def]
        return {"app_version": __version__, "current_user": current_user}
