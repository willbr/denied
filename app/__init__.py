from flask import Flask

from app.config import get_db_dir


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config["DB_DIR"] = get_db_dir()

    if config:
        app.config.update(config)

    from app.routes import main
    app.register_blueprint(main)

    return app
