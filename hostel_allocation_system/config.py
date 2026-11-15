"""Application configuration.

Zero-configuration Flask application configuration:
- No API keys or secret keys required.
- No external database setup required.
- Runs with automatic SQLite storage (/tmp on Vercel, project dir locally).
- Optional: Can connect to external MySQL if DATABASE_URL is provided.
"""
import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# On Vercel serverless runtime, /tmp is the writable storage directory.
# Locally in development, hostel_db.sqlite3 is stored in the project folder.
_tmp_sqlite = "sqlite:////tmp/hostel_db.sqlite3"
_local_sqlite = f"sqlite:///{os.path.join(basedir, 'hostel_db.sqlite3')}"
SQLITE_URL = _tmp_sqlite if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") else _local_sqlite


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
