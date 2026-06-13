"""Formulários do CRUD de tarefas (Flask-WTF / WTForms)."""
from __future__ import annotations

from flask_wtf import FlaskForm
from wtforms import SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from app.models import Task


class TaskForm(FlaskForm):
    """Criação e edição de tarefas (mesmo formulário para ambos)."""

    title = StringField(
        "Título",
        validators=[
            DataRequired(message="O título é obrigatório."),
            Length(min=1, max=120),
        ],
    )
    description = TextAreaField(
        "Descrição",
        validators=[Optional(), Length(max=2000)],
    )
    status = SelectField(
        "Status",
        choices=[
            (Task.STATUS_PENDING, "Pendente"),
            (Task.STATUS_IN_PROGRESS, "Em andamento"),
            (Task.STATUS_DONE, "Concluída"),
        ],
        validators=[DataRequired()],
    )
    priority = SelectField(
        "Prioridade",
        choices=[
            (Task.PRIORITY_LOW, "Baixa"),
            (Task.PRIORITY_MEDIUM, "Média"),
            (Task.PRIORITY_HIGH, "Alta"),
        ],
        validators=[DataRequired()],
    )
    submit = SubmitField("Salvar")


class SearchForm(FlaskForm):
    """Busca por texto e filtro de status. Usa GET, então dispensa CSRF."""

    class Meta:
        csrf = False

    q = StringField("Buscar", validators=[Optional(), Length(max=120)])
    status = SelectField(
        "Status",
        choices=[
            ("", "Todos os status"),
            (Task.STATUS_PENDING, "Pendente"),
            (Task.STATUS_IN_PROGRESS, "Em andamento"),
            (Task.STATUS_DONE, "Concluída"),
        ],
        validators=[Optional()],
    )
    submit = SubmitField("Filtrar")
