"""Rotas do CRUD de tarefas.

Todas exigem autenticação (`@login_required`). Cada operação valida que a
tarefa pertence ao usuário logado — um usuário nunca acessa ou altera tarefas
de outro (controle de autorização / *broken access control*).
"""
from __future__ import annotations

import logging

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from sqlalchemy import or_

from app.extensions import db
from app.logging_config import log_security_event
from app.models import Task
from app.security import sanitize_text
from app.tasks.forms import SearchForm, TaskForm

tasks_bp = Blueprint("tasks", __name__)


def _get_owned_task_or_404(task_id: int) -> Task:
    """Retorna a tarefa se pertencer ao usuário atual; senão aborta.

    Devolve 404 (e não 403) para não revelar a existência de tarefas de
    terceiros — boa prática contra enumeração de IDs.
    """
    task = db.session.get(Task, task_id)
    if task is None or task.user_id != current_user.id:
        log_security_event(
            "idor_attempt",
            f"Acesso negado à tarefa id={task_id} pelo usuário "
            f"'{current_user.username}'.",
            username=current_user.username, level=logging.WARNING,
        )
        abort(404)
    return task


@tasks_bp.route("/")
@login_required
def list_tasks():
    """Lista, busca e filtra as tarefas do usuário."""
    form = SearchForm(request.args, meta={"csrf": False})
    query = Task.query.filter_by(user_id=current_user.id)

    term = sanitize_text(request.args.get("q", ""), max_length=120)
    status = request.args.get("status", "")

    if term:
        # `ilike` é seguro: o ORM parametriza o valor (sem SQL Injection).
        like = f"%{term}%"
        query = query.filter(
            or_(Task.title.ilike(like), Task.description.ilike(like))
        )
    if status in Task.VALID_STATUSES:
        query = query.filter_by(status=status)

    tasks = query.order_by(Task.created_at.desc()).all()

    stats = {
        "total": Task.query.filter_by(user_id=current_user.id).count(),
        "pending": Task.query.filter_by(
            user_id=current_user.id, status=Task.STATUS_PENDING
        ).count(),
        "in_progress": Task.query.filter_by(
            user_id=current_user.id, status=Task.STATUS_IN_PROGRESS
        ).count(),
        "done": Task.query.filter_by(
            user_id=current_user.id, status=Task.STATUS_DONE
        ).count(),
    }
    return render_template(
        "tasks/list.html", tasks=tasks, form=form, stats=stats,
        active_term=term, active_status=status,
    )


@tasks_bp.route("/nova", methods=["GET", "POST"])
@login_required
def create_task():
    """Cria uma nova tarefa."""
    form = TaskForm()
    if form.validate_on_submit():
        task = Task(
            title=sanitize_text(form.title.data, max_length=120),
            description=sanitize_text(form.description.data, max_length=2000),
            status=form.status.data,
            priority=form.priority.data,
            user_id=current_user.id,
        )
        db.session.add(task)
        db.session.commit()
        log_security_event(
            "task_created",
            f"Tarefa id={task.id} criada por '{current_user.username}'.",
            username=current_user.username,
        )
        flash("Tarefa criada com sucesso.", "success")
        return redirect(url_for("tasks.list_tasks"))
    return render_template("tasks/form.html", form=form, mode="create")


@tasks_bp.route("/<int:task_id>/editar", methods=["GET", "POST"])
@login_required
def edit_task(task_id: int):
    """Edita uma tarefa existente do próprio usuário."""
    task = _get_owned_task_or_404(task_id)
    form = TaskForm(obj=task)
    if form.validate_on_submit():
        task.title = sanitize_text(form.title.data, max_length=120)
        task.description = sanitize_text(form.description.data, max_length=2000)
        task.status = form.status.data
        task.priority = form.priority.data
        db.session.commit()
        log_security_event(
            "task_updated",
            f"Tarefa id={task.id} atualizada por '{current_user.username}'.",
            username=current_user.username,
        )
        flash("Tarefa atualizada.", "success")
        return redirect(url_for("tasks.list_tasks"))
    return render_template("tasks/form.html", form=form, mode="edit", task=task)


@tasks_bp.route("/<int:task_id>/excluir", methods=["POST"])
@login_required
def delete_task(task_id: int):
    """Exclui uma tarefa (somente via POST + CSRF token)."""
    task = _get_owned_task_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    log_security_event(
        "task_deleted",
        f"Tarefa id={task_id} excluída por '{current_user.username}'.",
        username=current_user.username,
    )
    flash("Tarefa excluída.", "info")
    return redirect(url_for("tasks.list_tasks"))


@tasks_bp.route("/<int:task_id>/concluir", methods=["POST"])
@login_required
def toggle_done(task_id: int):
    """Alterna rapidamente o status concluída/pendente."""
    task = _get_owned_task_or_404(task_id)
    if task.status == Task.STATUS_DONE:
        task.status = Task.STATUS_PENDING
    else:
        task.status = Task.STATUS_DONE
    db.session.commit()
    return redirect(url_for("tasks.list_tasks"))
