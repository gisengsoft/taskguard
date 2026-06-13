"""Ponto de entrada da aplicação TaskGuard.

Uso em desenvolvimento:
    python run.py

Uso em produção (via Gunicorn, definido no Dockerfile):
    gunicorn "run:app" --bind 0.0.0.0:8000
"""
from __future__ import annotations

import os

from app import create_app

# Instância exposta para o servidor WSGI (Gunicorn) e para o `flask` CLI.
app = create_app()


if __name__ == "__main__":
    # O modo debug é controlado pela configuração do ambiente, nunca fixado.
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", "5000"))
    app.run(host=host, port=port, debug=app.config.get("DEBUG", False))
