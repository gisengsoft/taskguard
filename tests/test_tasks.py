"""Testes do CRUD de tarefas e do controle de autorização por proprietário."""
from __future__ import annotations

from app.models import Task, User


def _create_task(client, title="Tarefa de teste", priority="media", status="pendente"):
    return client.post(
        "/tarefas/nova",
        data={
            "title": title,
            "description": "descrição",
            "status": status,
            "priority": priority,
        },
        follow_redirects=True,
    )


class TestTaskAccessControl:
    def test_list_requires_authentication(self, client):
        resp = client.get("/tarefas/", follow_redirects=True)
        assert "Entrar no TaskGuard".encode() in resp.data

    def test_create_requires_authentication(self, client):
        resp = client.get("/tarefas/nova", follow_redirects=True)
        assert "Entrar no TaskGuard".encode() in resp.data


class TestTaskCrud:
    def test_create_task(self, auth_client, db):
        resp = _create_task(auth_client, title="Estudar DevSecOps")
        assert resp.status_code == 200
        assert "Estudar DevSecOps".encode() in resp.data
        assert Task.query.filter_by(title="Estudar DevSecOps").count() == 1

    def test_edit_task(self, auth_client, db):
        _create_task(auth_client, title="Título antigo")
        task = Task.query.filter_by(title="Título antigo").first()
        resp = auth_client.post(
            f"/tarefas/{task.id}/editar",
            data={
                "title": "Título novo",
                "description": "atualizada",
                "status": "em_andamento",
                "priority": "alta",
            },
            follow_redirects=True,
        )
        assert resp.status_code == 200
        refreshed = db.session.get(Task, task.id)
        assert refreshed.title == "Título novo"
        assert refreshed.status == "em_andamento"

    def test_delete_task(self, auth_client, db):
        _create_task(auth_client, title="Para excluir")
        task = Task.query.filter_by(title="Para excluir").first()
        resp = auth_client.post(
            f"/tarefas/{task.id}/excluir", follow_redirects=True
        )
        assert resp.status_code == 200
        assert db.session.get(Task, task.id) is None

    def test_toggle_done(self, auth_client, db):
        _create_task(auth_client, title="Alternar")
        task = Task.query.filter_by(title="Alternar").first()
        auth_client.post(f"/tarefas/{task.id}/concluir", follow_redirects=True)
        assert db.session.get(Task, task.id).status == "concluida"


class TestTaskSearch:
    def test_search_filters_results(self, auth_client, db):
        _create_task(auth_client, title="Comprar pão")
        _create_task(auth_client, title="Estudar Flask")
        resp = auth_client.get("/tarefas/?q=Flask")
        assert "Estudar Flask".encode() in resp.data
        assert "Comprar".encode() not in resp.data

    def test_filter_by_status(self, auth_client, db):
        _create_task(auth_client, title="Pendente A", status="pendente")
        _create_task(auth_client, title="Concluida B", status="concluida")
        resp = auth_client.get("/tarefas/?status=concluida")
        assert "Concluida B".encode() in resp.data
        assert "Pendente A".encode() not in resp.data


class TestOwnershipIsolation:
    def test_user_cannot_access_others_task(self, client, db, user):
        # Tarefa pertencente à 'alice' (fixture user).
        t = Task(title="Privada da Alice", user_id=user.id)
        db.session.add(t)
        db.session.commit()

        # Cria e autentica um segundo usuário, 'mallory'.
        mallory = User(username="mallory", email="mallory@example.com")
        mallory.set_password("Senha@123")
        db.session.add(mallory)
        db.session.commit()
        client.post(
            "/auth/login",
            data={"username": "mallory", "password": "Senha@123"},
            follow_redirects=True,
        )

        # Mallory tenta acessar a tarefa da Alice -> 404 (não vaza existência).
        resp = client.get(f"/tarefas/{t.id}/editar")
        assert resp.status_code == 404

        # E não consegue excluí-la.
        resp = client.post(f"/tarefas/{t.id}/excluir")
        assert resp.status_code == 404
        assert db.session.get(Task, t.id) is not None
