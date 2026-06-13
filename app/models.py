"""Modelos de dados (SQLAlchemy ORM).

Define as entidades `User` e `Task`. Toda a interação com o banco passa por
estes modelos e pelo ORM, o que elimina a construção manual de SQL e, por
consequência, a superfície de ataque de SQL Injection.
"""
from __future__ import annotations

from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from app.extensions import db


def _utcnow() -> datetime:
    """Horário atual em UTC (timezone-aware)."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Usuário autenticável do sistema.

    A senha jamais é armazenada em texto puro: guardamos apenas o hash gerado
    pelo Werkzeug (PBKDF2-SHA256 por padrão). Campos de controle de brute force
    permitem bloquear temporariamente a conta após tentativas falhas.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    # Controle de brute force
    failed_login_attempts = db.Column(db.Integer, default=0, nullable=False)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Relacionamento 1:N com tarefas; remoção em cascata.
    tasks = db.relationship(
        "Task",
        backref="owner",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    # ------------------------------------------------------------------ #
    # Senha
    # ------------------------------------------------------------------ #
    def set_password(self, password: str) -> None:
        """Gera e armazena o hash da senha."""
        self.password_hash = generate_password_hash(
            password, method="pbkdf2:sha256", salt_length=16
        )

    def check_password(self, password: str) -> bool:
        """Compara a senha informada com o hash de forma segura."""
        return check_password_hash(self.password_hash, password)

    # ------------------------------------------------------------------ #
    # Bloqueio por brute force
    # ------------------------------------------------------------------ #
    def is_locked(self) -> bool:
        """Indica se a conta está temporariamente bloqueada."""
        if self.locked_until is None:
            return False
        locked_until = self.locked_until
        if locked_until.tzinfo is None:  # Normaliza valores vindos do SQLite
            locked_until = locked_until.replace(tzinfo=timezone.utc)
        return _utcnow() < locked_until

    def register_failed_attempt(self, max_attempts: int, lockout_minutes: int) -> None:
        """Incrementa o contador de falhas e bloqueia ao atingir o limite."""
        from datetime import timedelta

        self.failed_login_attempts += 1
        if self.failed_login_attempts >= max_attempts:
            self.locked_until = _utcnow() + timedelta(minutes=lockout_minutes)

    def reset_failed_attempts(self) -> None:
        """Zera o contador de falhas após um login bem-sucedido."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def __repr__(self) -> str:  # pragma: no cover - apenas depuração
        return f"<User {self.username}>"


class Task(db.Model):
    """Tarefa pessoal pertencente a um usuário."""

    __tablename__ = "tasks"

    # Estados possíveis de uma tarefa.
    STATUS_PENDING = "pendente"
    STATUS_IN_PROGRESS = "em_andamento"
    STATUS_DONE = "concluida"
    VALID_STATUSES = (STATUS_PENDING, STATUS_IN_PROGRESS, STATUS_DONE)

    # Níveis de prioridade.
    PRIORITY_LOW = "baixa"
    PRIORITY_MEDIUM = "media"
    PRIORITY_HIGH = "alta"
    VALID_PRIORITIES = (PRIORITY_LOW, PRIORITY_MEDIUM, PRIORITY_HIGH)

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default=STATUS_PENDING, nullable=False)
    priority = db.Column(db.String(20), default=PRIORITY_MEDIUM, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=_utcnow, onupdate=_utcnow, nullable=False
    )

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id"), nullable=False, index=True
    )

    @property
    def status_label(self) -> str:
        """Rótulo legível para exibição na interface."""
        return {
            self.STATUS_PENDING: "Pendente",
            self.STATUS_IN_PROGRESS: "Em andamento",
            self.STATUS_DONE: "Concluída",
        }.get(self.status, self.status)

    @property
    def priority_label(self) -> str:
        """Rótulo legível de prioridade."""
        return {
            self.PRIORITY_LOW: "Baixa",
            self.PRIORITY_MEDIUM: "Média",
            self.PRIORITY_HIGH: "Alta",
        }.get(self.priority, self.priority)

    def __repr__(self) -> str:  # pragma: no cover - apenas depuração
        return f"<Task {self.id} {self.title!r}>"
