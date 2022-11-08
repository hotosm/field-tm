from flask.cli import FlaskGroup

import os
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

from src.web.main import app, db

cli = FlaskGroup(app)


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


if __name__ == "__main__":
    cli()
