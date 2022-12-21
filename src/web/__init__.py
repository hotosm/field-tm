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

import os

from flask import Flask, render_template
# from flask_migrate import Migrate

from config import config

# migrate = Migrate()


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
    # migrate.init_app(app, db)

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
