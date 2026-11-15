"""Application configuration.

Zero-configuration Flask application configuration:
- No API keys or secret keys required.
- Automatically handles serverless environments (Vercel / Lambda).
- Copies pre-seeded SQLite database to /tmp in read-only environments.
- Optional: Can connect to external MySQL if DATABASE_URL is provided.
"""
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))


def get_sqlite_uri():
    """Returns a writable SQLite URI.
    
    In serverless environments (Vercel, AWS Lambda, Linux containers with read-only root),
    the SQLite database is copied to /tmp so it has full read-write permissions.
    """
    is_serverless = (
        bool(
            os.getenv("VERCEL")
            or os.getenv("VERCEL_ENV")
            or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
            or os.getenv("LAMBDA_TASK_ROOT")
            or os.getenv("NOW_REGION")
        )
        or (os.name != "nt" and os.path.exists("/tmp"))
        or not os.access(basedir, os.W_OK)
    )

    if is_serverless:
        tmp_db = "/tmp/hostel_db.sqlite3"
        # Seed /tmp database from bundled database if not yet present
        if not os.path.exists(tmp_db):
            bundled_db = os.path.join(basedir, "hostel_db.sqlite3")
            if os.path.exists(bundled_db):
                try:
                    shutil.copy2(bundled_db, tmp_db)
                except Exception:
                    pass
        return f"sqlite:///{tmp_db}"

    # Local development
    return f"sqlite:///{os.path.join(basedir, 'hostel_db.sqlite3')}"


SQLITE_URL = get_sqlite_uri()


class Config:
    """Application configuration with zero-config defaults."""

    # Built-in session signing key (no environment variable or API key needed)
    SECRET_KEY = os.getenv("SECRET_KEY", "college-hostel-system-default-key-2026")

    # Uses SQLite by default. If an optional DATABASE_URL is provided, it uses that instead.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", SQLITE_URL)
    SQLITE_FALLBACK_URL = SQLITE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # Session & CSRF Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
