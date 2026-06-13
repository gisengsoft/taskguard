"""Tratadores de erro HTTP centralizados.

Renderizam páginas amigáveis e padronizadas (sem vazar stack traces ao usuário)
e registram os eventos relevantes nos logs de segurança/aplicação.
"""
from __future__ import annotations

import logging

from flask import Flask, render_template

from app.logging_config import log_security_event


def register_error_handlers(app: Flask) -> None:
    """Registra os handlers de erro na aplicação."""

    @app.errorhandler(403)
    def forbidden(error):  # type: ignore[no-untyped-def]
        log_security_event(
            "access_forbidden", "Acesso negado a recurso protegido.",
            level=logging.WARNING,
        )
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):  # type: ignore[no-untyped-def]
        return render_template("errors/404.html"), 404

    @app.errorhandler(429)
    def too_many_requests(error):  # type: ignore[no-untyped-def]
        # Disparado pelo Flask-Limiter: forte indício de abuso/automação.
        log_security_event(
            "rate_limit_exceeded",
            f"Limite de requisições excedido: {getattr(error, 'description', '')}",
            level=logging.WARNING,
        )
        return render_template("errors/429.html"), 429

    @app.errorhandler(500)
    def internal_error(error):  # type: ignore[no-untyped-def]
        app.logger.exception("Erro interno não tratado: %s", error)
        return render_template("errors/500.html"), 500

    @app.errorhandler(400)
    def bad_request(error):  # type: ignore[no-untyped-def]
        return render_template("errors/400.html"), 400
