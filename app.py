"""
app.py — Flask application factory + local entry point
======================================================
Local dev:     python app.py
Production:    gunicorn --preload -b 0.0.0.0:$PORT wsgi:app     (see wsgi.py)

Design notes
------------
• The DB URL is resolved at startup. If an external DB (MySQL/Postgres) is
  configured but unreachable, we log a clear warning and fall back to SQLite so
  the site still comes up instead of crash-looping.  (Important on free hosts
  where a database can expire.)
• ensure_ready() creates tables + seeds demo data when the DB is empty —
  safe to call on every boot.
"""
import os
from datetime import datetime, timezone

from flask import Flask, render_template, render_template_string, request, jsonify
from jinja2 import TemplateNotFound
from sqlalchemy import create_engine, text
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_wtf.csrf import CSRFError

from config import Config, SQLITE_FALLBACK
from extensions import db, login_manager, csrf
from models import (User, Product, Category, Address, Order, OrderItem,
                    OrderStatusHistory, CartItem, WishlistItem,
                    STATUS_META, ORDER_STATUSES, utcnow)


# ----------------------------------------------------------------------
# Crash-proof error page
# ----------------------------------------------------------------------
# Ella error handler-um ithai use pannum. Template file (errors/404.html)
# missing-a irundhaalo, 0-byte-a irundhaalo — app CRASH aagaadhu; intha
# clean inline page-ah kaattum.  (Files missing aanaalum site nikkadhu!)
FALLBACK_ERROR_HTML = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__CODE__ — __TITLE__</title>
<style>
  body{font-family:-apple-system,'Segoe UI',Roboto,Arial,sans-serif;margin:0;
       min-height:100vh;display:grid;place-items:center;
       background:linear-gradient(160deg,#fdf2f8,#f5f3ff 55%,#eff6ff)}
  .box{background:#fff;border-radius:18px;padding:34px 30px;max-width:520px;width:92%;
       box-shadow:0 18px 44px rgba(16,24,40,.14);text-align:center}
  .ico{font-size:2.6rem}
  h1{font-size:2rem;margin:.4rem 0 .2rem;color:#111827}
  h2{font-size:1.02rem;margin:0 0 .7rem;color:#374151;font-weight:600}
  p{color:#6b7280;font-size:.92rem;line-height:1.55;margin:0 0 1.2rem}
  .btn{display:inline-block;background:linear-gradient(135deg,#f43397,#a855f7);
       color:#fff;text-decoration:none;font-weight:700;border-radius:999px;
       padding:.62rem 1.5rem;margin:0 .25rem}
  .btn.alt{background:#fff;color:#d01f7c;border:2px solid #f43397}
  small{display:block;margin-top:1.1rem;color:#9ca3af;font-size:.74rem}
</style></head><body>
  <div class="box">
    <div class="ico">__EMOJI__</div>
    <h1>__CODE__</h1>
    <h2>__TITLE__</h2>
    <p>__MESSAGE__</p>
    <a class="btn" href="/">Go Home</a>
    <a class="btn alt" href="/products">Browse Products</a>
    <small>ShopKart — fallback page (error template file missing • CHECK_FILES.bat run pannunga)</small>
  </div>
</body></html>"""


def _fallback_page(code: int, title: str, message: str) -> str:
    """Simple inline error page — template file thevai illa."""
    emoji = {404: "🧭", 403: "🔒", 401: "🔒", 500: "🛠️"}.get(code, "⚠️")
    return (FALLBACK_ERROR_HTML
            .replace("__CODE__", str(code))
            .replace("__TITLE__", str(title))
            .replace("__MESSAGE__", str(message))
            .replace("__EMOJI__", emoji))


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------
def _connect_args(url: str) -> dict:
    """Short connect timeout so a dead DB doesn't hang the boot."""
    if url.startswith("mysql"):
        return {"connect_timeout": 5}
    if url.startswith("postgresql"):
        return {"connect_timeout": 5}
    return {}


def _resolve_db_url(app: Flask) -> None:
    """Use the configured DB; fall back to SQLite if it's unreachable."""
    url = app.config["SQLALCHEMY_DATABASE_URI"]

    if url.startswith("sqlite"):
        app.config["DB_LABEL"] = "SQLite"
        return

    try:
        probe = create_engine(url, connect_args=_connect_args(url))
        with probe.connect() as conn:
            conn.execute(text("SELECT 1"))
        probe.dispose()
        app.config["DB_LABEL"] = url.split("://")[0].split("+")[0]
        app.logger.info("Database reachable: %s", app.config["DB_LABEL"])
    except Exception as exc:                       # noqa: BLE001  (broad on purpose)
        app.logger.warning(
            "Configured database unreachable (%s: %s) — falling back to SQLite. "
            "The site will still work; data just won't persist across restarts.",
            exc.__class__.__name__, str(exc)[:180],
        )
        app.config["SQLALCHEMY_DATABASE_URI"] = SQLITE_FALLBACK
        app.config["DB_LABEL"] = "SQLite (fallback)"


def ensure_ready(app: Flask) -> None:
    """Create tables and seed demo data if the database is empty."""
    with app.app_context():
        try:
            db.create_all()
            if not User.query.first():
                from seed import seed_all
                seed_all(app)
                app.logger.info("Database seeded with demo data.")
            else:
                app.logger.info("Database already contains data — seed skipped.")
        except Exception as exc:                   # noqa: BLE001
            app.logger.error("Database initialisation failed: %s", exc)
            db.session.rollback()


# ----------------------------------------------------------------------
# Application factory
# ----------------------------------------------------------------------
def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # folders
    os.makedirs(os.path.join(app.root_path, "instance"), exist_ok=True)
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # database (with safe fallback)
    _resolve_db_url(app)
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # behind a reverse proxy (Render / nginx) trust one hop of headers
    if not app.config["DEBUG"]:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # ---------------- blueprints ----------------
    from blueprints.main import main_bp
    from blueprints.auth import auth_bp
    from blueprints.cart import cart_bp
    from blueprints.orders import orders_bp
    from blueprints.admin import admin_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)

    # ---------------- template globals ----------------
    @app.context_processor
    def inject_globals():
        from cart_utils import get_cart
        _, _, _, cart_count = get_cart()
        return dict(
            nav_categories=Category.query.order_by(Category.name).all(),
            STORE_NAME=app.config["STORE_NAME"],
            FREE_SHIPPING_ABOVE=app.config["FREE_SHIPPING_ABOVE"],
            SHIPPING_FEE=app.config["SHIPPING_FEE"],
            cart_count=cart_count,
            now=utcnow(),
            status_meta=STATUS_META,
        )

    # ---------------- template filters ----------------
    @app.template_filter("money")
    def money(value):
        try:
            return "₹" + f"{int(value):,}"
        except (TypeError, ValueError):
            return "₹0"

    @app.template_filter("datef")
    def datef(value, fmt="%d %b %Y"):
        return value.strftime(fmt) if value else ""

    @app.template_filter("datetimef")
    def datetimef(value, fmt="%d %b %Y, %I:%M %p"):
        return value.strftime(fmt) if value else ""

    # ---------------- health check (Render pings this) ----------------
    @app.route("/healthz")
    def healthz():
        db_state = "up"
        try:
            db.session.execute(text("SELECT 1"))
        except Exception as exc:                   # noqa: BLE001
            db_state = f"degraded ({exc.__class__.__name__})"
            db.session.rollback()
        return jsonify(status="ok", database=db_state,
                       db_label=app.config.get("DB_LABEL", "?"),
                       debug=app.config["DEBUG"],
                       time=datetime.now(timezone.utc).isoformat(timespec="seconds"))

    # ---------------- error pages (crash-proof) ----------------
    def _safe_page(template, code, title, message, **ctx):
        """Try the real template; missing/empty file -> inline fallback.
        Ithanaala TemplateNotFound error-vay CRASH aagaadhu."""
        try:
            return render_template(template, code=code, title=title,
                                   message=message, **ctx)
        except TemplateNotFound:
            return render_template_string(_fallback_page(code, title, message))

    @app.errorhandler(404)
    def not_found(e):
        return _safe_page("errors/404.html", 404, "Page not found",
                          "Neenga thedra page kidaikkala. Home-ku poy paarunga 😊"), 404

    @app.errorhandler(403)
    def forbidden(e):
        return _safe_page("errors/403.html", 403, "Access denied",
                          "Indha page-ku access illa. Admin account venum."), 403

    @app.errorhandler(401)
    def unauthorized(e):
        return _safe_page("errors/403.html", 401, "Login needed",
                          "Indha page-ku login pannanum."), 401

    @app.errorhandler(405)
    def method_not_allowed(e):
        return _safe_page("errors/generic.html", 405, "Method not allowed",
                          "Indha page-ku indha action allowed illa."), 405

    @app.errorhandler(CSRFError)
    def handle_csrf(e):
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(ok=False, msg="Session expired — page-ah refresh pannunga"), 400
        return _safe_page("errors/generic.html", 400, "Session expired",
                          "Security token expire aagidhu. Page-ah refresh panni "
                          "marubadiyum try pannunga."), 400

    @app.errorhandler(413)
    def request_too_large(e):
        limit = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(ok=False, msg=f"File too big — max {limit} MB"), 413
        return _safe_page("errors/generic.html", 413, "File too large",
                          f"Upload pannina file romba periyadhu. "
                          f"Maximum size: {limit} MB."), 413

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return _safe_page("errors/500.html", 500, "Server error",
                          "Konjam neram kazhichu try pannunga."), 500

    # ---------------- CLI ----------------
    @app.cli.command("init-db")
    def init_db():
        """flask --app app init-db  → create tables + demo data"""
        db.create_all()
        print("✅ Tables created.")
        from seed import seed_all
        seed_all(app)
        print("✅ Seed data inserted.")

    return app


# ----------------------------------------------------------------------
# Local development entry point
# ----------------------------------------------------------------------
app = create_app()

if __name__ == "__main__":
    ensure_ready(app)          # tables + demo data on first run
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=True)