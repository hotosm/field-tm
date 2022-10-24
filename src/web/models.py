import enum
from email.policy import default

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db = SQLAlchemy()


class User(db.Model):

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(128), unique=True, nullable=False)
    password = db.Column(db.String(128), unique=True, nullable=False)

    def __init__(self, username, password, *args, **kwargs):
        self.username = username
        self.password = password

    def __getitem__(self, field):
        return self.__dict__[field]

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.id,
            'username': self.username,
        }


class Project(db.Model):

    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_id = db.Column(db.Integer, unique=False, nullable=False)
    created = db.Column(db.TIMESTAMP, nullable=False,
                        server_default=db.func.now())
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.String(256), nullable=False)
    base_dir = db.Column(db.String(128))

    db.ForeignKeyConstraint(["author_id"], ["users.id"])

    def __init__(self, title, description, author_id, *args, **kwargs):
        self.title = title
        self.description = description
        self.author_id = author_id

    # https://stackoverflow.com/a/59011958
    def __getitem__(self, field):
        return self.__dict__[field]


class TaskStatus(str, enum.Enum):
    available = "Available for mapping"
    unavailable = "Unavailable"
    ready_for_validation = "Ready for Validation"

    def __str__(self):
        return self.value


class Task(db.Model):

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    feature_id = db.Column(db.Integer, unique=False, nullable=False)
    project_id = db.Column(db.Integer, unique=False, nullable=False)
    created = db.Column(db.TIMESTAMP, nullable=False,
                        server_default=db.func.now())
    status = db.Column(Enum(TaskStatus), nullable=False,
                       default=TaskStatus.available)
    task_doer = db.Column(db.Integer)
    last_selected = db.Column(db.TIMESTAMP, server_default=db.func.now())

    db.ForeignKeyConstraint(["project_id"], ["projects.id"])
    db.ForeignKeyConstraint(["task_doer"], ["users.id"])

    def __init__(self, feature_id, project_id, *args, **kwargs):
        self.feature_id = feature_id
        self.project_id = project_id

    def __getitem__(self, field):
        return self.__dict__[field]

    @property
    def serialized(self):
        """Return object data in serializeable format"""
        return {
            'id': self.id,
            'feature_id': self.feature_id,
            'project_id': self.project_id,
            'task_doer': self.task_doer,
        }
