"""
blueprints/orders.py — Checkout, Order placement (COD), History, Tracking, Cancel
"""
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect, url_for,
                   flash, abort, current_app)
from flask_login import login_required, current_user
from extensions import db
from models import (utcnow, Address, Order, OrderItem, OrderStatusHistory, Product,
                    ORDER_STATUSES, STATUS_META)
from cart_utils import get_cart, clear_cart
from utils import generate_order_number

orders_bp = Blueprint("orders", __name__)


# ---------------------------------------------------------------- CHECKOUT
@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    items, subtotal, mrp_total, count = get_cart()

    if not items:
        flash("Cart empty! Products add pannunga 😊", "warning")
        return redirect(url_for("main.products"))

    shipping = 0 if subtotal >= current_app.config["FREE_SHIPPING_ABOVE"] \
        else current_app.config["SHIPPING_FEE"]
    total = subtotal + shipping

    if request.method == "POST":
        addr_id = request.form.get("address_id", type=int)
        address = Address.query.filter_by(id=addr_id, user_id=current_user.id).first()
        if not address:
            flash("Delivery address select pannunga.", "danger")
            return redirect(url_for("orders.checkout"))

        payment = request.form.get("payment_method", "COD")
        if payment not in ("COD",):        # Phase 9 will add RAZORPAY here
            payment = "COD"

        # ---- stock check for the whole cart (all-or-nothing) ----
        for it in items:
            if it["qty"] > it["product"].stock:
                flash(f"Sorry! '{it['product'].name}' has only "
                      f"{it['product'].stock} left. Cart-ah adjust pannunga.", "danger")
                return redirect(url_for("cart.view_cart"))

        # ---- create the order ----
        order = Order(
            order_number="TEMP",                     # replaced below
            user_id=current_user.id,
            ship_name=address.full_name,
            ship_phone=address.phone,
            ship_line1=address.line1,
            ship_line2=address.line2,
            ship_city=address.city,
            ship_state=address.state,
            ship_pincode=address.pincode,
            subtotal=subtotal,
            shipping_fee=shipping,
            total=total,
            payment_method=payment,
            status="PLACED",
        )
        db.session.add(order)
        db.session.flush()                            # get order.id

        order.order_number = generate_order_number(order.id)

        for it in items:
            p = it["product"]
            db.session.add(OrderItem(
                order_id=order.id,
                product_id=p.id,
                product_name=p.name,
                product_image=p.image,
                emoji=p.emoji,
                color=p.color,
                seller=p.seller,
                price=p.price,
                qty=it["qty"],
                line_total=p.price * it["qty"],
            ))
            p.stock -= it["qty"]                      # reduce stock
            p.review_count += 1

        db.session.add(OrderStatusHistory(
            order_id=order.id, status="PLACED",
            note="Order placed successfully (Cash on Delivery)"))

        db.session.commit()
        clear_cart()

        return redirect(url_for("orders.success", order_number=order.order_number))

    return render_template("checkout.html",
                           items=items, subtotal=subtotal, shipping=shipping,
                           total=total, savings=mrp_total - subtotal,
                           addresses=current_user.addresses)


# ---------------------------------------------------------------- SUCCESS
@orders_bp.route("/order/success/<order_number>")
@login_required
def success(order_number):
    order = Order.query.filter_by(order_number=order_number,
                                  user_id=current_user.id).first_or_404()
    return render_template("order_success.html", order=order)


# ---------------------------------------------------------------- HISTORY
@orders_bp.route("/orders")
@login_required
def history():
    orders = (Order.query.filter_by(user_id=current_user.id)
              .order_by(Order.placed_at.desc()).all())
    return render_template("orders.html", orders=orders, statuses=ORDER_STATUSES,
                           meta=STATUS_META)


# ---------------------------------------------------------------- ORDER DETAIL
@orders_bp.route("/orders/<order_number>")
@login_required
def detail(order_number):
    order = Order.query.filter_by(order_number=order_number,
                                  user_id=current_user.id).first_or_404()
    return render_template("order_detail.html", order=order, meta=STATUS_META,
                           statuses=ORDER_STATUSES)


# ---------------------------------------------------------------- TRACK (public)
@orders_bp.route("/track", methods=["GET"])
def track():
    order = None
    number = request.args.get("order", "").strip().upper()[:40]

    if number:
        order = Order.query.filter_by(order_number=number).first()
        if not order:
            flash(f"No order found with number {number}.", "warning")

    return render_template("track.html", order=order, number=number, meta=STATUS_META,
                           statuses=ORDER_STATUSES)


# ---------------------------------------------------------------- CANCEL
@orders_bp.route("/orders/<order_number>/cancel", methods=["POST"])
@login_required
def cancel(order_number):
    order = Order.query.filter_by(order_number=order_number,
                                  user_id=current_user.id).first_or_404()

    if not order.can_cancel:
        flash("Indha order-ah ippo cancel panna mudiyaadhu. Support-ku call pannunga.", "warning")
        return redirect(url_for("orders.detail", order_number=order_number))

    # put stock back
    for it in order.items:
        if it.product_id:
            p = db.session.get(Product, it.product_id)
            if p:
                p.stock += it.qty

    order.status = "CANCELLED"
    db.session.add(OrderStatusHistory(order_id=order.id, status="CANCELLED",
                                      note="Cancelled by customer"))
    db.session.commit()

    flash("Order cancelled. Refund (COD) — nothing to refund 🎉", "info")
    return redirect(url_for("orders.detail", order_number=order_number))
