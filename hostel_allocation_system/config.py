"""Application configuration for local development and managed cloud SQL."""
import os
from dotenv import load_dotenv
from sqlalchemy.pool import StaticPool

load_dotenv()

def _database_uri():
    """Resolve a supported SQLAlchemy URL without hiding connection failures."""
    database_url = os.getenv("DATABASE_URL") or os.getenv("POSTGRES_URL")
    if not database_url:
        if os.getenv("VERCEL"):
            raise RuntimeError(
                "Set DATABASE_URL (PostgreSQL or MySQL) in Vercel Project Settings "
                "to use the application with persistent storage."
            )
        return "sqlite://"
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+psycopg2://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    if database_url.startswith("mysql://"):
        return database_url.replace("mysql://", "mysql+pymysql://", 1)
    if database_url.startswith(("postgresql+psycopg2://", "mysql+pymysql://", "sqlite:")):
        return database_url
    raise RuntimeError("DATABASE_URL must use PostgreSQL (postgresql://) or MySQL (mysql://).")


DATABASE_URI = _database_uri()
SECRET_KEY = os.getenv("SECRET_KEY")
if os.getenv("VERCEL") and not SECRET_KEY:
    raise RuntimeError("Set SECRET_KEY in Vercel Project Settings before deployment.")


class Config:
    """Application configuration with zero-config in-memory defaults."""

    # Built-in session signing key (no environment variable or API key needed)
    SECRET_KEY = SECRET_KEY or "college-hostel-system-default-key-2026"

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
