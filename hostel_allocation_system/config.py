"""Application configuration.

Priority order for the database URI:
  1. DATABASE_URL environment variable (set this on Vercel / Railway / etc.)
  2. If all MySQL env-vars are present → try MySQL
  3. Otherwise → SQLite in /tmp (writable on Vercel serverless) or project dir locally
"""
import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

# On Vercel the project filesystem is read-only; /tmp is the only writable location.
# Locally /tmp also works, but we fall back to the project dir so the DB file is easy
# to find during development.
_tmp_sqlite = "sqlite:////tmp/hostel_db.sqlite3"
_local_sqlite = f"sqlite:///{os.path.join(basedir, 'hostel_db.sqlite3')}"
SQLITE_URL = _tmp_sqlite if os.getenv("VERCEL") or os.getenv("VERCEL_ENV") else _local_sqlite


class Config:
    """Shared configuration for all environments."""

    # -------------------------------------------------------------------
    # Security
    # -------------------------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY", "hostel-system-secure-key-college-2026")

    # -------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------
    # Build MySQL URL from individual env-vars if they are all present.
    _DB_USER = os.getenv("DB_USER", "")
    _DB_PASS = os.getenv("DB_PASSWORD", "")
    _DB_HOST = os.getenv("DB_HOST", "localhost")
    _DB_PORT = os.getenv("DB_PORT", "3306")
    _DB_NAME = os.getenv("DB_NAME", "hostel_db")

    _MYSQL_AVAILABLE = bool(_DB_USER and _DB_PASS and _DB_NAME)
    _MYSQL_URL = (
        f"mysql+pymysql://{_DB_USER}:{_DB_PASS}@{_DB_HOST}:{_DB_PORT}/{_DB_NAME}"
        if _MYSQL_AVAILABLE
        else None
    )

    # Explicit DATABASE_URL wins over everything else.
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL") or _MYSQL_URL or SQLITE_URL

    # Store fallback separately so create_app() can reference it.
    SQLITE_FALLBACK_URL = SQLITE_URL

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }

    # -------------------------------------------------------------------
    # Session & CSRF
    # -------------------------------------------------------------------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
