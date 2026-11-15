"""Application configuration.

Zero-configuration Flask application configuration:
- In-memory database by default: 100% file-free and in RAM.
  No SQLite files on disk, no permission issues, and zero disk write errors on Vercel/serverless.
- Automatically seeds all demo data (Admin, Wardens, Students, Rooms, Hostels) into RAM.
- Cloud DB ready: Simply set DATABASE_URL (MySQL / PostgreSQL) for permanent cloud persistence.
"""
import os
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()

# If DATABASE_URL is set in environment (e.g. Neon, Supabase, TiDB, Railway), use it.
# Otherwise, use a pure in-memory database with StaticPool (zero disk files, zero permission errors).
_cloud_db = os.getenv("DATABASE_URL")
if _cloud_db and _cloud_db.startswith("postgres://"):
    # SQLAlchemy requires postgresql:// instead of legacy postgres://
    _cloud_db = _cloud_db.replace("postgres://", "postgresql://", 1)

DATABASE_URI = _cloud_db or "sqlite://"


class Config:
    """Application configuration with zero-config in-memory defaults."""

    # Built-in session signing key (no environment variable or API key needed)
    SECRET_KEY = os.getenv("SECRET_KEY", "college-hostel-system-default-key-2026")

    SQLALCHEMY_DATABASE_URI = DATABASE_URI

    # Engine options: If running in-memory SQLite, use StaticPool so all connections share the memory DB
    if DATABASE_URI.startswith("sqlite"):
        SQLALCHEMY_ENGINE_OPTIONS = {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            "pool_recycle": 280,
            "pool_pre_ping": True,
        }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session & CSRF Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
