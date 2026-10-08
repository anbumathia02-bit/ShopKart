"""
blueprints/cart.py — Cart page + AJAX endpoints
Works for BOTH guests (session cart) and logged-in users (DB cart).
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from cart_utils import (get_cart, add_to_cart, update_qty,
                        remove_from_cart, clear_cart)

cart_bp = Blueprint("cart", __name__, url_prefix="/cart")


@cart_bp.route("/")
def view_cart():
    items, subtotal, mrp_total, count = get_cart()
    shipping = 0 if (subtotal >= current_app.config["FREE_SHIPPING_ABOVE"] or subtotal == 0) \
        else current_app.config["SHIPPING_FEE"]
    return render_template("cart.html",
                           items=items, subtotal=subtotal, mrp_total=mrp_total,
                           count=count, shipping=shipping, total=subtotal + shipping,
                           savings=mrp_total - subtotal)


@cart_bp.route("/add/<int:pid>", methods=["POST"])
def add(pid):
    qty = request.form.get("qty", 1, type=int)
    ok, msg = add_to_cart(pid, qty)

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        _, _, _, count = get_cart()
        return jsonify(ok=ok, msg=msg, cart_count=count)

    flash(msg, "success" if ok else "warning")
    return redirect(request.form.get("next") or request.referrer or url_for("cart.view_cart"))


@cart_bp.route("/update/<int:pid>", methods=["POST"])
def update(pid):
    update_qty(pid, request.form.get("qty", 1, type=int))
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        items, subtotal, _, count = get_cart()
        return jsonify(ok=True, cart_count=count, subtotal=subtotal)
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/remove/<int:pid>", methods=["POST"])
def remove(pid):
    remove_from_cart(pid)
    flash("Item removed from cart.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/clear", methods=["POST"])
def clear():
    clear_cart()
    flash("Cart cleared.", "info")
    return redirect(url_for("cart.view_cart"))


@cart_bp.route("/buy-now/<int:pid>", methods=["POST"])
def buy_now(pid):
    """Straight to checkout: add item then jump."""
    ok, msg = add_to_cart(pid, request.form.get("qty", 1, type=int))
    if not ok:
        flash(msg, "warning")
        return redirect(url_for("main.product_detail", pid=pid))
    return redirect(url_for("orders.checkout"))
