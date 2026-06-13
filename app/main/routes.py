"""Blueprint principal: landing page e endpoints operacionais.

Inclui o *health check* consumido pelo Docker (`HEALTHCHECK`) e pela pipeline
de CI/CD para verificar se a aplicação subiu antes de rodar o DAST.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, redirect, url_for
from flask_login import current_user

from app import __version__
from app.extensions import db

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    """Raiz: envia o usuário autenticado ao painel; senão, ao login."""
    if current_user.is_authenticated:
        return redirect(url_for("tasks.list_tasks"))
    return redirect(url_for("auth.login"))


@main_bp.route("/health")
def health():
    """Health check leve para orquestradores e pipeline.

    Verifica a conectividade com o banco de dados executando uma query trivial.
    Retorna 200 quando saudável e 503 quando degradado.
    """
    try:
        db.session.execute(db.text("SELECT 1"))
        db_status = "up"
        http_status = 200
    except Exception:  # noqa: BLE001 - health check nunca deve lançar
        db_status = "down"
        http_status = 503

    payload = {
        "service": "taskguard",
        "version": __version__,
        "status": "healthy" if http_status == 200 else "unhealthy",
        "database": db_status,
    }
    return jsonify(payload), http_status
