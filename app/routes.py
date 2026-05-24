import sqlite3

from flask import Blueprint, abort, current_app, render_template

from app.databases import list_databases, list_tables

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
    db_dir = current_app.config["DB_DIR"]
    if name not in list_databases(db_dir):
        abort(404)

    try:
        tables = list_tables(db_dir / name)
    except sqlite3.DatabaseError as exc:
        return render_template("database.html", name=name, error=str(exc))

    return render_template("database.html", name=name, tables=tables)
