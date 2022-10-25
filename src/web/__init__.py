import os

from flask import Flask, render_template
from flask_migrate import Migrate

from config import config

migrate = Migrate()


def create_app(config_name=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_mapping(SECRET_KEY="dev")

    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "development")

    # load the instance config, if it exists, when not testing
    app.config.from_object(config[config_name])

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    from .models import db

    db.init_app(app)
    migrate.init_app(app, db)

    # shell context for flask cli
    @app.shell_context_processor
    def ctx():
        return {"app": app, "db": db}

    with app.app_context():
        # Include our Routes
        @app.route("/map")
        @app.route("/map/<pname>")
        def map_select_page(pname=None):
            return render_template("map.html", pname=pname)

        db.create_all()

        # Register Blueprints
        from . import auth

        app.register_blueprint(auth.bp)

        from . import project

        app.register_blueprint(project.bp)
        app.add_url_rule("/", endpoint="index")

        return app
