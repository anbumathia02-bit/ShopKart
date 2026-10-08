"""
config.py — Application configuration
=====================================
Same code runs on different databases WITHOUT any change:

  • SQLite   → local dev / Render free demo (default, zero setup)
  • MySQL    → your own server   (DATABASE_URL in .env)
  • Postgres → Render managed DB (DATABASE_URL from Render dashboard)

`.env` examples:
  DATABASE_URL=mysql+pymysql://user:pass@localhost/shopkart_db?charset=utf8mb4
  DATABASE_URL=postgresql+psycopg2://user:pass@host/dbname
"""
import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

SQLITE_FALLBACK = "sqlite:///" + os.path.join(BASE_DIR, "instance", "shopkart.db")


def _fix_db_url(url: str) -> str:
    """Normalise URLs given by hosting platforms.

    Render/Heroku hand out `postgres://...` which SQLAlchemy no longer accepts,
    and we make sure a driver prefix is present.
    """
    if not url:
        return url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg2://", 1)
    elif url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    elif url.startswith("mysql://"):
        url = url.replace("mysql://", "mysql+pymysql://", 1)
    return url


class Config:
    # ---------- Core ----------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")

    # FLASK_DEBUG defaults to 1 for local dev; Render sets it to 0.
    DEBUG = os.environ.get("FLASK_DEBUG", "1") == "1"

    # ---------- Database ----------
    # No DATABASE_URL  → SQLite (zero setup, perfect for demos)
    # DATABASE_URL set → MySQL / Postgres
    SQLALCHEMY_DATABASE_URI = _fix_db_url(
        os.environ.get("DATABASE_URL") or SQLITE_FALLBACK
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,      # reconnects if the DB dropped the connection
        "pool_recycle": 280,        # avoids "server has gone away" on MySQL
    }

    # ---------- Uploads ----------
    UPLOAD_FOLDER = os.path.join(BASE_DIR, "static", "uploads", "products")
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024        # 5 MB per upload

    # ---------- Shop settings ----------
    STORE_NAME = os.environ.get("STORE_NAME", "ShopKart")
    FREE_SHIPPING_ABOVE = int(os.environ.get("FREE_SHIPPING_ABOVE", 499))
    SHIPPING_FEE = int(os.environ.get("SHIPPING_FEE", 49))
    CURRENCY = "₹"

    # ---------- Security / cookies ----------
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    # Secure cookies only when we are actually served over HTTPS.
    # Render sets RENDER=true, so this turns on automatically in production
    # and stays off for plain-http local runs (otherwise login would break).
    SESSION_COOKIE_SECURE = (
        os.environ.get("RENDER") is not None or os.environ.get("HTTPS") == "1"
    )
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE

    # ---------- Misc ----------
    TEMPLATES_AUTO_RELOAD = DEBUG
    JSON_SORT_KEYS = False
