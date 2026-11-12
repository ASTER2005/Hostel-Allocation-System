"""Application factory: builds and configures the Flask app."""
import os
from datetime import datetime
from flask import Flask, render_template, render_template_string
from config import Config
from .extensions import db, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # If the configured URI is MySQL, attempt a quick connectivity probe.
    # On Vercel (serverless) there is no MySQL unless DATABASE_URL is explicitly
    # set, so we fall back to SQLite immediately without hanging the cold-start.
    db_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if db_uri.startswith("mysql"):
        try:
            from sqlalchemy import create_engine, text
            test_engine = create_engine(
                db_uri,
                connect_args={"connect_timeout": 3},
                pool_timeout=3,
            )
            with test_engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            test_engine.dispose()
        except Exception:
            # MySQL unreachable → fall back to SQLite
            fallback_uri = app.config.get("SQLITE_FALLBACK_URL")
            app.config["SQLALCHEMY_DATABASE_URI"] = fallback_uri

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register Blueprints
    from .auth import bp as auth_bp
    from .student import bp as student_bp
    from .admin import bp as admin_bp
    from .warden import bp as warden_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp, url_prefix="/student")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(warden_bp, url_prefix="/warden")

    # Auto-create all tables on first request (safe for SQLite on Vercel /tmp).
    # For MySQL in production, run a proper migration instead.
    with app.app_context():
        db.create_all()

    # Error Handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template("shared/error.html", code=403, title="Access Denied", 
                               message="You do not have permission to view this page or resource."), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template("shared/error.html", code=404, title="Page Not Found", 
                               message="The requested page could not be located on the server."), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("shared/error.html", code=500, title="Server Error", 
                               message="An internal server error occurred. Please contact the administrator."), 500

    # Context Processors & Filters
    @app.context_processor
    def inject_global_vars():
        return {
            "current_year": datetime.utcnow().year,
            "system_name": "Hostel Allocation and Management System",
            "college_name": "Imperial College of Engineering & Technology"
        }

    @app.template_filter("status_badge")
    def status_badge_filter(status):
        status_map = {
            "Approved": "badge-approved",
            "Allocated": "badge-allocated",
            "Checked-In": "badge-checked-in",
            "Resolved": "badge-resolved",
            "Available": "badge-available",
            "Pending": "badge-pending",
            "In Progress": "badge-in-progress",
            "Open": "badge-open",
            "Rejected": "badge-rejected",
            "Cancelled": "badge-cancelled",
            "Full": "badge-full",
            "Maintenance": "badge-maintenance",
            "Checked-Out": "badge-checked-out"
        }
        badge_cls = status_map.get(str(status), "badge-neutral")
        return f'<span class="custom-badge {badge_cls}">{status}</span>'

    return app

@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return db.session.get(User, int(user_id))
