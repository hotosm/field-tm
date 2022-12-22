# Copyright (c) 2020, 2021, 2022 Humanitarian OpenStreetMap Team
# This file is part of FMTM.
#
#     FMTM is free software: you can redistribute it and/or modify
#     it under the terms of the GNU General Public License as published by
#     the Free Software Foundation, either version 3 of the License, or
#     (at your option) any later version.
#
#     FMTM is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU General Public License for more details.
#
#     You should have received a copy of the GNU General Public License
#     along with FMTM.  If not, see <https:#www.gnu.org/licenses/>.
#

import enum
import datetime
from email.policy import default

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Enum

db = SQLAlchemy()


class DisplayProject:
    id: int
    author_id: int
    created: datetime
    author_username: str
    description: str


class UITask:
    status: str
    feature_id: int
    name: str
    qr_code: bytes
    outline: str
    uid: int
    locked_by_uid: int


class User(db.Model):

    __tablename__ = "web_users"

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

    __tablename__ = "web_projects"

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


class FrontendTaskStatus(str, enum.Enum):
    available = "Available for mapping"
    unavailable = "Unavailable"
    ready_for_validation = "Ready for Validation"

    def __str__(self):
        return self.value


class Task(db.Model):

    __tablename__ = "web_tasks"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    feature_id = db.Column(db.Integer, unique=False, nullable=False)
    project_id = db.Column(db.Integer, unique=False, nullable=False)
    created = db.Column(db.TIMESTAMP, nullable=False,
                        server_default=db.func.now())
    status = db.Column(Enum(FrontendTaskStatus), nullable=False,
                       default=FrontendTaskStatus.available)
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
