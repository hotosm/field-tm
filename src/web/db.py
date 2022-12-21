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

import click
from flask import current_app, g
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from src.web.models import db


def get_db():
    return db


def init_db(app):
    db = get_db()
    migrate = Migrate(app, db)


@click.command("init-db")
def init_db_command():
    """Clears existing data and creates new tables."""
    init_db()
    click.echo("Initialized the database.")


def init_app(app):
    app.cli.add_command(init_db_command)
