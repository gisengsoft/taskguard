"""Instâncias singleton das extensões Flask.

Mantidas num módulo separado para evitar importações circulares: as extensões
são criadas aqui sem aplicação e vinculadas depois, dentro da fábrica
`create_app` (padrão *application factory*).
"""
from __future__ import annotations

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_talisman import Talisman
from flask_wtf import CSRFProtect

# ORM / banco de dados
db = SQLAlchemy()

# Gerenciamento de sessão de usuário
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Faça login para acessar esta página."
login_manager.login_message_category = "warning"
login_manager.session_protection = "strong"  # Invalida sessão se IP/UA mudarem

# Proteção CSRF global em todos os formulários
csrf = CSRFProtect()

# Headers de segurança / CSP / HSTS
talisman = Talisman()

# Rate limiting (chaveado por IP do cliente)
limiter = Limiter(key_func=get_remote_address)
