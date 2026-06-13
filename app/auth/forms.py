"""Formulários de autenticação (Flask-WTF / WTForms).

O uso do Flask-WTF garante, de forma transparente, a inclusão e validação do
token CSRF em cada formulário. As validações de servidor abaixo são a fonte de
verdade — nunca confiamos apenas em validação no navegador.
"""
from __future__ import annotations

import re

from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, StringField, SubmitField
from wtforms.validators import (
    DataRequired,
    Email,
    EqualTo,
    Length,
    Regexp,
    ValidationError,
)

# Usuário: letras, números, ponto, hífen e underscore.
USERNAME_PATTERN = r"^[A-Za-z0-9._-]+$"


class LoginForm(FlaskForm):
    """Formulário de autenticação."""

    username = StringField(
        "Usuário",
        validators=[
            DataRequired(message="Informe o usuário."),
            Length(min=3, max=64),
        ],
    )
    password = PasswordField(
        "Senha", validators=[DataRequired(message="Informe a senha.")]
    )
    remember_me = BooleanField("Manter conectado")
    submit = SubmitField("Entrar")


class RegisterForm(FlaskForm):
    """Formulário de cadastro de novo usuário com política de senha forte."""

    username = StringField(
        "Usuário",
        validators=[
            DataRequired(message="Informe um nome de usuário."),
            Length(min=3, max=64),
            Regexp(
                USERNAME_PATTERN,
                message="Use apenas letras, números e os símbolos . _ -",
            ),
        ],
    )
    email = StringField(
        "E-mail",
        validators=[
            DataRequired(message="Informe um e-mail."),
            Email(message="E-mail inválido."),
            Length(max=120),
        ],
    )
    password = PasswordField(
        "Senha",
        validators=[
            DataRequired(message="Defina uma senha."),
            Length(min=8, max=128, message="A senha deve ter ao menos 8 caracteres."),
        ],
    )
    confirm_password = PasswordField(
        "Confirmar senha",
        validators=[
            DataRequired(message="Confirme a senha."),
            EqualTo("password", message="As senhas não conferem."),
        ],
    )
    submit = SubmitField("Criar conta")

    @staticmethod
    def validate_password(_form, field) -> None:  # type: ignore[no-untyped-def]
        """Exige complexidade mínima: maiúscula, minúscula e dígito."""
        value = field.data or ""
        if not re.search(r"[A-Z]", value):
            raise ValidationError("A senha precisa de ao menos uma letra maiúscula.")
        if not re.search(r"[a-z]", value):
            raise ValidationError("A senha precisa de ao menos uma letra minúscula.")
        if not re.search(r"\d", value):
            raise ValidationError("A senha precisa de ao menos um número.")
