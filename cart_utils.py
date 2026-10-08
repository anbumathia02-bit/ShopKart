"""
cart_utils.py — Cart logic in ONE place.
========================================
Guest  → cart lives in Flask session  (session['guest_cart'] = {"12": 2})
Logged → cart lives in MySQL/SQLite   (cart_items table)

On login we MERGE the guest cart into the DB cart, so nothing is lost.
"""
from flask import session
from flask_login import current_user
from extensions import db
from models import Product, CartItem


def _guest_cart() -> dict:
    return session.setdefault("guest_cart", {})


def get_cart():
    """Returns (items, subtotal, mrp_total, count). Items = list of dicts."""
    items, subtotal, mrp_total, count = [], 0, 0, 0

    if current_user.is_authenticated:
        rows = CartItem.query.filter_by(user_id=current_user.id).all()
        for row in rows:
            if not row.product or not row.product.is_active:
                continue
            p = row.product
            line = p.price * row.qty
            subtotal += line
            mrp_total += p.mrp * row.qty
            count += row.qty
            items.append({"product": p, "qty": row.qty, "line_total": line})
    else:
        guest = _guest_cart()
        for pid, qty in list(guest.items()):
            p = db.session.get(Product, int(pid))
            if not p or not p.is_active:
                guest.pop(pid, None)
                continue
            line = p.price * qty
            subtotal += line
            mrp_total += p.mrp * qty
            count += qty
            items.append({"product": p, "qty": qty, "line_total": line})
        session.modified = True

    return items, subtotal, mrp_total, count


def add_to_cart(product_id: int, qty: int = 1):
    """Returns (ok, message). Respects available stock."""
    p = db.session.get(Product, product_id)
    if not p or not p.is_active:
        return False, "Product not available."

    qty = max(1, int(qty))

    if current_user.is_authenticated:
        row = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        have = row.qty if row else 0
        if have + qty > p.stock:
            return False, f"Only {p.stock} left in stock."
        if row:
            row.qty = have + qty
        else:
            db.session.add(CartItem(user_id=current_user.id, product_id=product_id, qty=qty))
        db.session.commit()
    else:
        guest = _guest_cart()
        have = guest.get(str(product_id), 0)
        if have + qty > p.stock:
            return False, f"Only {p.stock} left in stock."
        guest[str(product_id)] = have + qty
        session.modified = True

    return True, f"{p.name[:40]} added to cart ✓"


def update_qty(product_id: int, qty: int):
    qty = int(qty)
    p = db.session.get(Product, product_id)
    max_qty = p.stock if p else 1

    if current_user.is_authenticated:
        row = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if row:
            if qty <= 0:
                db.session.delete(row)
            else:
                row.qty = min(qty, max_qty)
            db.session.commit()
    else:
        guest = _guest_cart()
        if qty <= 0:
            guest.pop(str(product_id), None)
        else:
            guest[str(product_id)] = min(qty, max_qty)
        session.modified = True


def remove_from_cart(product_id: int):
    if current_user.is_authenticated:
        row = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if row:
            db.session.delete(row)
            db.session.commit()
    else:
        _guest_cart().pop(str(product_id), None)
        session.modified = True


def clear_cart():
    if current_user.is_authenticated:
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    else:
        session["guest_cart"] = {}
        session.modified = True


def merge_guest_cart_into_db(user):
    """Called right after successful login/signup."""
    guest = session.get("guest_cart") or {}
    for pid, qty in guest.items():
        p = db.session.get(Product, int(pid))
        if not p or not p.is_active:
            continue
        row = CartItem.query.filter_by(user_id=user.id, product_id=p.id).first()
        if row:
            row.qty = min(row.qty + qty, p.stock)
        else:
            db.session.add(CartItem(user_id=user.id, product_id=p.id, qty=min(qty, p.stock)))
    db.session.commit()
    session["guest_cart"] = {}
    session.modified = True
