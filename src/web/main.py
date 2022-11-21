from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from src.web import create_app

app = create_app()
db = SQLAlchemy(app)
migrate = Migrate(app, db)

if __name__ == "__main__":
    app.run(host='127.0.0.1', port=8080, debug=True)
