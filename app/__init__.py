from flask import Flask


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)

    if config:
        app.config.update(config)

    from app.routes import main
    app.register_blueprint(main)

    return app
