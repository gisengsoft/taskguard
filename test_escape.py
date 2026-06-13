from app import create_app
from app.extensions import db
from app.models import Task, User

app = create_app('testing')
with app.app_context():
    db.create_all()
    user = User(username='test', email='test@test.com')
    user.set_password('Senha@123')
    db.session.add(user)
    db.session.commit()

    with app.test_client() as client:
        client.post('/auth/login', data={'username': 'test', 'password': 'Senha@123'})
        client.post('/tarefas/nova', data={
            'title': 'A & B',
            'description': 'description',
            'status': 'pendente',
            'priority': 'media'
        })
        resp = client.get('/tarefas/')
        print(resp.data.decode('utf-8'))
