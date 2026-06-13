"""Rotas de autenticação: registro, login e logout.

Aplica rate limiting agressivo no login, proteção contra brute force por conta
(bloqueio temporário) e registra todos os eventos relevantes no log de
segurança consumido pelo Fail2Ban.
"""
from __future__ import annotations

import logging

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from app.auth.forms import LoginForm, RegisterForm
from app.extensions import db, limiter
from app.logging_config import log_security_event
from app.models import User
from app.security import sanitize_text

auth_bp = Blueprint("auth", __name__)


def _is_safe_next(target: str | None) -> bool:
    """Evita *open redirect*: só aceita destinos relativos ao próprio host."""
    if not target:
        return False
    return target.startswith("/") and not target.startswith("//")


@auth_bp.route("/register", methods=["GET", "POST"])
@limiter.limit("10 per hour")
def register():
    """Cadastro de novo usuário."""
    if current_user.is_authenticated:
        return redirect(url_for("tasks.list_tasks"))

    form = RegisterForm()
    if form.validate_on_submit():
        username = sanitize_text(form.username.data, max_length=64)
        email = sanitize_text(form.email.data, max_length=120).lower()

        # Unicidade verificada via ORM (parametrizado, sem SQL manual).
        if User.query.filter_by(username=username).first():
            flash("Este nome de usuário já está em uso.", "danger")
            return render_template("auth/register.html", form=form)
        if User.query.filter_by(email=email).first():
            flash("Este e-mail já está cadastrado.", "danger")
            return render_template("auth/register.html", form=form)

        user = User(username=username, email=email)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        log_security_event(
            "user_registered", f"Novo usuário cadastrado: {username}",
            username=username,
        )
        flash("Conta criada com sucesso! Faça login para continuar.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("10 per minute; 50 per hour")
def login():
    """Autenticação com proteção contra brute force."""
    if current_user.is_authenticated:
        return redirect(url_for("tasks.list_tasks"))

    form = LoginForm()
    if form.validate_on_submit():
        username = sanitize_text(form.username.data, max_length=64)
        user = User.query.filter_by(username=username).first()

        # 1) Conta bloqueada por excesso de tentativas.
        if user and user.is_locked():
            log_security_event(
                "login_blocked_locked",
                f"Login bloqueado: conta '{username}' temporariamente travada.",
                username=username, level=logging.WARNING,
            )
            flash(
                "Conta temporariamente bloqueada por excesso de tentativas. "
                "Tente novamente mais tarde.",
                "danger",
            )
            return render_template("auth/login.html", form=form)

        # 2) Credenciais válidas.
        if user and user.check_password(form.password.data):
            user.reset_failed_attempts()
            db.session.commit()
            login_user(user, remember=form.remember_me.data)
            log_security_event(
                "login_success", f"Login bem-sucedido: {username}",
                username=username,
            )
            flash("Bem-vindo(a) de volta!", "success")

            next_page = request.args.get("next")
            if _is_safe_next(next_page):
                return redirect(next_page)
            return redirect(url_for("tasks.list_tasks"))

        # 3) Falha de autenticação. Registra tentativa e, se a conta existir,
        #    incrementa o contador de brute force. A mensagem ao usuário é
        #    genérica de propósito (não revela se o usuário existe).
        if user:
            user.register_failed_attempt(
                max_attempts=current_app_config("LOGIN_MAX_ATTEMPTS"),
                lockout_minutes=current_app_config("LOGIN_LOCKOUT_MINUTES"),
            )
            db.session.commit()
            if user.is_locked():
                log_security_event(
                    "account_locked",
                    f"Conta '{username}' bloqueada após múltiplas falhas.",
                    username=username, level=logging.WARNING,
                )

        log_security_event(
            "login_failed",
            f"Falha de autenticação para usuário '{username}'.",
            username=username, level=logging.WARNING,
        )
        flash("Usuário ou senha inválidos.", "danger")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """Encerra a sessão do usuário (somente via POST, evita logout por CSRF/GET)."""
    username = getattr(current_user, "username", "-")
    logout_user()
    log_security_event("logout", f"Sessão encerrada: {username}", username=username)
    flash("Você saiu com segurança.", "info")
    return redirect(url_for("auth.login"))


def current_app_config(key: str):
    """Atalho para ler config do app atual sem import circular no topo."""
    from flask import current_app

    return current_app.config[key]
