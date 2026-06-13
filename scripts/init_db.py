#!/usr/bin/env python3
"""init_db.py — Inicializa o banco de dados e (opcionalmente) cria dados demo.

Uso:
    python scripts/init_db.py            # cria tabelas
    python scripts/init_db.py --seed     # cria tabelas + usuário e tarefas demo

O usuário demo tem credenciais previsíveis e destina-se APENAS a ambientes de
desenvolvimento/demonstração — jamais use em produção.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Permite executar o script a partir da raiz do projeto.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app  # noqa: E402
from app.extensions import db  # noqa: E402
from app.models import Task, User  # noqa: E402

DEMO_USERNAME = "demo"
DEMO_EMAIL = "demo@taskguard.local"
DEMO_PASSWORD = "Demo@1234"


def seed_demo_data() -> None:
    """Cria um usuário de demonstração com algumas tarefas de exemplo."""
    if User.query.filter_by(username=DEMO_USERNAME).first():
        print(f"[init_db] Usuário '{DEMO_USERNAME}' já existe; pulando seed.")
        return

    user = User(username=DEMO_USERNAME, email=DEMO_EMAIL)
    user.set_password(DEMO_PASSWORD)
    db.session.add(user)
    db.session.flush()  # garante user.id

    exemplos = [
        ("Revisar relatório de segurança", "Conferir achados do último scan DAST.",
         Task.STATUS_IN_PROGRESS, Task.PRIORITY_HIGH),
        ("Atualizar dependências", "Aplicar correções do Dependency-Check.",
         Task.STATUS_PENDING, Task.PRIORITY_MEDIUM),
        ("Configurar alertas do Fail2Ban", "Validar filtro de brute force.",
         Task.STATUS_PENDING, Task.PRIORITY_HIGH),
        ("Escrever testes de integração", "Cobrir o fluxo de login.",
         Task.STATUS_DONE, Task.PRIORITY_LOW),
    ]
    for title, desc, status, priority in exemplos:
        db.session.add(Task(
            title=title, description=desc, status=status,
            priority=priority, user_id=user.id,
        ))

    db.session.commit()
    print(f"[init_db] Usuário demo criado: {DEMO_USERNAME} / {DEMO_PASSWORD}")
    print(f"[init_db] {len(exemplos)} tarefas de exemplo adicionadas.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Inicializa o banco do TaskGuard.")
    parser.add_argument("--seed", action="store_true",
                        help="popula dados de demonstração")
    args = parser.parse_args()

    app = create_app()
    with app.app_context():
        db.create_all()
        print("[init_db] Tabelas criadas/garantidas.")
        if args.seed:
            seed_demo_data()


if __name__ == "__main__":
    main()
