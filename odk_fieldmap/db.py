from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

import click
from flask import current_app, g

from .models import db


def get_db():
    return db


def init_db(app):
    db = get_db()
    migrate = Migrate(app, db)


@click.command('init-db')
def init_db_command():
    """Clears existing data and creates new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.cli.add_command(init_db_command)
