"""
utils.py — small shared helpers
"""
import os
import re
import uuid
from functools import wraps
from flask import abort, current_app
from flask_login import current_user


# ---------------------------------------------------------------- slugs
def slugify(text: str) -> str:
    text = (text or "").strip().lower()
    text = re.sub(r"[^a-z0-9\u0B80-\u0BFF]+", "-", text)   # keep Tamil chars
    return text.strip("-") or "item"


def unique_slug(model, name: str, current_id=None) -> str:
    """Make sure slug is unique across the table."""
    base = slugify(name)
    slug, n = base, 1
    while True:
        q = model.query.filter_by(slug=slug)
        if current_id:
            q = q.filter(model.id != current_id)
        if not q.first():
            return slug
        n += 1
        slug = f"{base}-{n}"


# ---------------------------------------------------------------- uploads
def allowed_file(filename: str) -> bool:
    return ("." in filename and
            filename.rsplit(".", 1)[1].lower() in current_app.config["ALLOWED_EXTENSIONS"])


def save_product_image(file_storage):
    """Saves an uploaded image, returns stored filename (or None)."""
    if not file_storage or not file_storage.filename:
        return None
    if not allowed_file(file_storage.filename):
        return None
    ext = file_storage.filename.rsplit(".", 1)[1].lower()
    fname = f"{uuid.uuid4().hex[:12]}.{ext}"
    folder = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(folder, exist_ok=True)
    file_storage.save(os.path.join(folder, fname))
    return fname


# ---------------------------------------------------------------- guards
def admin_required(f):
    """Blocks non-admin users from admin routes."""
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return wrapper


# ---------------------------------------------------------------- misc
def generate_order_number(order_id: int) -> str:
    """Human friendly order id, e.g. SK-2026-000123"""
    from models import utcnow
    return f"SK-{utcnow().year}-{order_id:06d}"
