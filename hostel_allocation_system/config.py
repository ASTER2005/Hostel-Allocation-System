import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Application configuration with primary MySQL support and seamless fallback."""
    SECRET_KEY = os.getenv("SECRET_KEY", "hostel-system-secure-key-college-2026")
    
    # Database configuration
    # Default MySQL URL (can be customized via .env or DATABASE_URL)
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASS = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "hostel_db")
    
    MYSQL_DEFAULT_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    SQLITE_FALLBACK_URL = f"sqlite:///{os.path.join(basedir, 'hostel_db.sqlite3')}"
    
    # If DATABASE_URL is explicitly set, use it; otherwise prefer MySQL
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", MYSQL_DEFAULT_URL)
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_recycle": 280,
        "pool_pre_ping": True,
    }
    
    # Session & Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
