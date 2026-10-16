import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from app.config import Config

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
limiter = Limiter(key_func=get_remote_address, default_limits=[], storage_uri="memory://")


def create_app(config_object=None):
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "..", "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "..", "static"),
        instance_relative_config=True,
    )
    app.config.from_object(config_object or Config)

    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(os.path.dirname(__file__), "..", "instance"), exist_ok=True)

    db.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)
    limiter.enabled = bool(app.config.get("RATELIMIT_ENABLED", True))

    login_manager.init_app(app)
    login_manager.login_view = "login"
    login_manager.login_message = "Please log in to continue."
    login_manager.login_message_category = "error"

    from app import models  # noqa: F401
    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        try:
            return db.session.get(User, int(user_id))
        except (TypeError, ValueError):
            return None

    from app.routes import register_routes

    register_routes(app)

    from flask import render_template

    @app.errorhandler(400)
    def bad_request(_e):
        return render_template(
            "error.html",
            title="Bad request",
            message="The request could not be processed. Please try again.",
        ), 400

    @app.errorhandler(403)
    def forbidden(_e):
        return render_template(
            "error.html",
            title="Access denied",
            message="You do not have permission to view this page.",
        ), 403

    @app.errorhandler(404)
    def not_found(_e):
        return render_template(
            "error.html",
            title="Page not found",
            message="The page you are looking for does not exist.",
        ), 404

    @app.errorhandler(429)
    def too_many(_e):
        return render_template(
            "error.html",
            title="Too many attempts",
            message="Please wait a minute and try again.",
        ), 429

    @app.errorhandler(500)
    def server_error(_e):
        return render_template(
            "error.html",
            title="Something went wrong",
            message="An unexpected error occurred. Please try again later.",
        ), 500

    register_cli(app)

    with app.app_context():
        db.create_all()
        _add_missing_profile_columns()
        seed_on_start = os.getenv("SEED_ON_START", "true").lower() == "true"
        if not app.config.get("TESTING") and seed_on_start and User.query.count() == 0:
            from app.seed import seed_demo_data

            seed_demo_data()

    return app


def _add_missing_profile_columns():
    """Lightweight auto-migration.

    Adds newly introduced profile columns to an existing database without
    dropping data. Safe to run on every startup. For full schema history use a
    migration tool such as Alembic.
    """
    from sqlalchemy import inspect, text

    inspector = inspect(db.engine)
    if "profiles" not in inspector.get_table_names():
        return
    existing = {col["name"] for col in inspector.get_columns("profiles")}
    ddl_types = {
        "mobile": "VARCHAR(20)",
        "work": "VARCHAR(160)",
        "gotra": "VARCHAR(80)",
        "manglik": "VARCHAR(20)",
        "family_background": "TEXT",
        "father_name": "VARCHAR(120)",
        "father_occupation": "VARCHAR(120)",
        "mother_name": "VARCHAR(120)",
        "mother_occupation": "VARCHAR(120)",
        "brothers": "INTEGER DEFAULT 0",
        "sisters": "INTEGER DEFAULT 0",
        "family_village": "VARCHAR(120)",
        "district": "VARCHAR(80)",
        "current_address": "TEXT",
    }
    missing = [(name, ddl) for name, ddl in ddl_types.items() if name not in existing]
    for name, ddl in missing:
        db.session.execute(text(f'ALTER TABLE profiles ADD COLUMN "{name}" {ddl}'))
    if missing:
        db.session.commit()


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        db.create_all()
        print("Database tables created.")

    @app.cli.command("seed-demo")
    def seed_demo():
        from app.seed import seed_demo_data

        created = seed_demo_data()
        print(f"Demo data ready. New demo users created: {created}")

    @app.cli.command("reset-demo")
    def reset_demo():
        from app.seed import reset_demo_data

        removed = reset_demo_data()
        print(f"Removed {removed} demo users and related sample data.")
