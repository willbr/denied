from flask import Blueprint, abort, current_app, render_template

from app.databases import list_databases

main = Blueprint("main", __name__)


@main.route("/")
def index():
    db_dir = current_app.config["DB_DIR"]
    return render_template(
        "index.html",
        databases=list_databases(db_dir),
        db_dir=db_dir,
    )


@main.route("/db/<name>/")
def database(name: str):
    # Stub — real implementation lands in Task 7.
    abort(501)
