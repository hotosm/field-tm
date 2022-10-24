import os
import tempfile

import pytest

from src import create_app
from src.auth import generate_password_hash
from src.db import get_db, init_db
from src.models import Project, Task, User

with open(os.path.join(os.path.dirname(__file__), 'data.sql'), 'rb') as f:
    _data_sql = f.read().decode('utf8')


@pytest.fixture
def app():
    db_fd, db_path = tempfile.mkstemp()

    app = create_app('testing')
    db = None
    with app.app_context():
        init_db(app)
        db = get_db()
        db.create_all()
        db.session.query(User).delete()
        db.session.query(Project).delete()

        user = User(
            username='test',
            password=generate_password_hash('test')
        )
        db.session.add(user)

        user = User(
            username='other',
            password=generate_password_hash('other')
        )
        db.session.add(user)

        project = Project(
            title='test title',
            description='test\nbody',
            author_id=1,
            created='2022-01-01 00:00:00',
        )
        db.session.add(project)

        task = Task(
            task_number=1,
            project_id=1,
            created='2022-01-01 00:00:00',
        )
        db.session.add(task)

        db.session.commit()

    yield app

    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def runner(app):
    return app.test_cli_runner()


class AuthActions(object):
    def __init__(self, client):
        self._client = client

    def login(self, username='test', password='test'):
        return self._client.post('/auth/login', data={'username': username, 'password': password})

    def logout(self):
        return self._client.get('/auth/logout')


@pytest.fixture
def auth(client):
    return AuthActions(client)
