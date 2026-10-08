"""
blueprints/admin.py — Admin panel
Dashboard • Products CRUD (+ image upload) • Categories • Stock •
Orders + status updates • Customers
"""
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, abort)
from flask_login import login_required, current_user
from sqlalchemy import func
from extensions import db
from models import (utcnow, Product, Category, Order, OrderItem, User, Address,
                    OrderStatusHistory, ORDER_STATUSES, STATUS_META)
from utils import unique_slug, save_product_image, admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# =====================================================================
# DASHBOARD — sales analytics
# =====================================================================
@admin_bp.route("/")
@login_required
@admin_required
def dashboard():
    paid_statuses = [s for s in ORDER_STATUSES if s != "CANCELLED"]

    total_orders = Order.query.count()
    total_revenue = db.session.query(func.coalesce(func.sum(Order.total), 0)) \
        .filter(Order.status.in_(paid_statuses)).scalar() or 0
    total_customers = User.query.filter_by(is_admin=False).count()
    total_products = Product.query.filter_by(is_active=True).count()
    out_of_stock = Product.query.filter(Product.is_active, Product.stock <= 0).count()
    pending = Order.query.filter(Order.status.in_(["PLACED", "CONFIRMED", "PACKED"])).count()

    today = utcnow().date()
    today_revenue = db.session.query(func.coalesce(func.sum(Order.total), 0)) \
        .filter(Order.status.in_(paid_statuses),
                func.date(Order.placed_at) == today).scalar() or 0

    # ---- last 7 days chart data ----
    days, day_labels, day_values = [], [], []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        rev = db.session.query(func.coalesce(func.sum(Order.total), 0)) \
            .filter(Order.status.in_(paid_statuses),
                    func.date(Order.placed_at) == d).scalar() or 0
        day_labels.append(d.strftime("%d %b"))
        day_values.append(int(rev))
    max_day = max(day_values) if any(day_values) else 1

    # ---- order status breakdown ----
    status_rows = db.session.query(Order.status, func.count(Order.id)) \
        .group_by(Order.status).all()
    status_counts = {s: c for s, c in status_rows}

    # ---- top selling products ----
    top_products = db.session.query(
        OrderItem.product_name, OrderItem.emoji, OrderItem.color,
        func.sum(OrderItem.qty).label("sold"),
        func.sum(OrderItem.line_total).label("revenue")) \
        .join(Order, Order.id == OrderItem.order_id) \
        .filter(Order.status != "CANCELLED") \
        .group_by(OrderItem.product_name, OrderItem.emoji, OrderItem.color) \
        .order_by(func.sum(OrderItem.qty).desc()).limit(5).all()

    recent_orders = Order.query.order_by(Order.placed_at.desc()).limit(8).all()
    low_stock = Product.query.filter(Product.is_active, Product.stock <= 5) \
        .order_by(Product.stock.asc()).limit(6).all()

    return render_template("admin/dashboard.html",
                           total_orders=total_orders, total_revenue=total_revenue,
                           total_customers=total_customers, total_products=total_products,
                           out_of_stock=out_of_stock, pending=pending,
                           today_revenue=today_revenue,
                           day_labels=day_labels, day_values=day_values, max_day=max_day,
                           status_counts=status_counts, statuses=ORDER_STATUSES,
                           meta=STATUS_META, top_products=top_products,
                           recent_orders=recent_orders, low_stock=low_stock)


# =====================================================================
# PRODUCTS
# =====================================================================
@admin_bp.route("/products")
@login_required
@admin_required
def products():
    q = request.args.get("q", "").strip()[:120]
    cat_id = request.args.get("cat", type=int)

    query = Product.query
    if q:
        query = query.filter(Product.name.ilike(f"%{q}%"))
    if cat_id:
        query = query.filter(Product.category_id == cat_id)

    items = query.order_by(Product.created_at.desc()).all()
    return render_template("admin/products.html", products=items,
                           categories=Category.query.order_by(Category.name).all(),
                           q=q, cat_id=cat_id)


@admin_bp.route("/products/new", methods=["GET", "POST"])
@login_required
@admin_required
def product_new():
    if request.method == "POST":
        ok, msg = _save_product(None, request)
        flash(msg, "success" if ok else "danger")
        if ok:
            return redirect(url_for("admin.products"))
        return redirect(url_for("admin.product_new"))

    return render_template("admin/product_form.html", product=None,
                           categories=Category.query.order_by(Category.name).all())


@admin_bp.route("/products/<int:pid>/edit", methods=["GET", "POST"])
@login_required
@admin_required
def product_edit(pid):
    product = db.session.get(Product, pid) or abort(404)

    if request.method == "POST":
        ok, msg = _save_product(product, request)
        flash(msg, "success" if ok else "danger")
        return redirect(url_for("admin.product_edit", pid=pid))

    return render_template("admin/product_form.html", product=product,
                           categories=Category.query.order_by(Category.name).all())


def _save_product(product, req):
    """Shared create/update logic. Returns (ok, message)."""
    name = req.form.get("name", "").strip()
    try:
        price = int(req.form.get("price", 0))
        mrp = int(req.form.get("mrp", 0) or price)
        stock = int(req.form.get("stock", 0))
    except ValueError:
        return False, "Price / MRP / Stock — numbers mattum venum."

    if not name or price <= 0:
        return False, "Product name and a valid price are required."
    if mrp < price:
        return False, "MRP should be >= selling price."

    is_new = product is None
    if is_new:
        product = Product(name=name, slug=unique_slug(Product, name),
                          price=price, mrp=mrp, stock=stock)

    product.name = name
    product.slug = unique_slug(Product, name, current_id=product.id if not is_new else None)
    product.description = req.form.get("description", "").strip()
    product.price = price
    product.mrp = mrp
    product.stock = stock
    product.category_id = req.form.get("category_id", type=int)
    product.seller = req.form.get("seller", "").strip() or "ShopKart Retail"
    product.emoji = req.form.get("emoji", "").strip() or "📦"
    product.color = req.form.get("color", "").strip() or "#eef1f5"
    product.rating = float(req.form.get("rating", 4.0) or 4.0)
    product.is_active = bool(req.form.get("is_active"))

    uploaded = save_product_image(req.files.get("image"))
    if uploaded:
        product.image = uploaded
    elif req.form.get("remove_image"):
        product.image = None

    if is_new:
        db.session.add(product)
    db.session.commit()
    return True, f"Product '{name}' {'created' if is_new else 'updated'} ✓"


@admin_bp.route("/products/<int:pid>/delete", methods=["POST"])
@login_required
@admin_required
def product_delete(pid):
    product = db.session.get(Product, pid) or abort(404)
    product.is_active = False          # soft delete — old orders keep the reference
    db.session.commit()
    flash(f"'{product.name}' deactivated (hidden from shop).", "info")
    return redirect(url_for("admin.products"))


@admin_bp.route("/products/<int:pid>/stock", methods=["POST"])
@login_required
@admin_required
def product_stock(pid):
    product = db.session.get(Product, pid) or abort(404)
    new_stock = request.form.get("stock", type=int)
    if new_stock is not None and new_stock >= 0:
        product.stock = new_stock
        db.session.commit()
        flash(f"{product.name} → stock {new_stock} ✓", "success")
    return redirect(request.referrer or url_for("admin.products"))


# =====================================================================
# CATEGORIES
# =====================================================================
@admin_bp.route("/categories", methods=["GET", "POST"])
@login_required
@admin_required
def categories():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        icon = request.form.get("icon", "").strip() or "📦"
        if not name:
            flash("Category name venum.", "danger")
        elif Category.query.filter(func.lower(Category.name) == name.lower()).first():
            flash("Indha category already irukku.", "warning")
        else:
            db.session.add(Category(name=name, slug=unique_slug(Category, name), icon=icon))
            db.session.commit()
            flash(f"Category '{name}' added ✓", "success")
        return redirect(url_for("admin.categories"))

    cats = Category.query.order_by(Category.name).all()
    return render_template("admin/categories.html", categories=cats)


@admin_bp.route("/categories/<int:cid>/delete", methods=["POST"])
@login_required
@admin_required
def category_delete(cid):
    cat = db.session.get(Category, cid) or abort(404)
    if cat.products:
        flash(f"'{cat.name}' has {len(cat.products)} products. First move them, then delete.", "warning")
        return redirect(url_for("admin.categories"))
    db.session.delete(cat)
    db.session.commit()
    flash("Category deleted.", "info")
    return redirect(url_for("admin.categories"))


# =====================================================================
# ORDERS
# =====================================================================
@admin_bp.route("/orders")
@login_required
@admin_required
def orders():
    status = request.args.get("status", "").strip()
    q = request.args.get("q", "").strip()[:120]

    query = Order.query
    if status in ORDER_STATUSES:
        query = query.filter(Order.status == status)
    if q:
        query = query.filter(Order.order_number.ilike(f"%{q}%"))

    items = query.order_by(Order.placed_at.desc()).all()
    return render_template("admin/orders.html", orders=items, statuses=ORDER_STATUSES,
                           meta=STATUS_META, current_status=status, q=q)


@admin_bp.route("/orders/<int:oid>")
@login_required
@admin_required
def order_detail(oid):
    order = db.session.get(Order, oid) or abort(404)
    return render_template("admin/order_detail.html", order=order,
                           statuses=ORDER_STATUSES, meta=STATUS_META)


@admin_bp.route("/orders/<int:oid>/status", methods=["POST"])
@login_required
@admin_required
def order_status(oid):
    order = db.session.get(Order, oid) or abort(404)
    new_status = request.form.get("status", "")
    note = request.form.get("note", "").strip()

    if new_status not in ORDER_STATUSES:
        flash("Invalid status.", "danger")
        return redirect(url_for("admin.order_detail", oid=oid))

    if new_status == order.status:
        flash("Status already same-a irukku.", "info")
        return redirect(url_for("admin.order_detail", oid=oid))

    # if admin cancels, return stock
    if new_status == "CANCELLED" and order.status != "CANCELLED":
        for it in order.items:
            if it.product_id:
                p = db.session.get(Product, it.product_id)
                if p:
                    p.stock += it.qty

    order.status = new_status
    if new_status == "DELIVERED":
        order.delivered_at = utcnow()

    db.session.add(OrderStatusHistory(order_id=order.id, status=new_status,
                                      note=note or f"Updated by admin"))
    db.session.commit()
    flash(f"Order {order.order_number} → {STATUS_META[new_status]['text']} ✓", "success")
    return redirect(url_for("admin.order_detail", oid=oid))


# =====================================================================
# CUSTOMERS
# =====================================================================
@admin_bp.route("/customers")
@login_required
@admin_required
def customers():
    q = request.args.get("q", "").strip()[:120]
    query = User.query.filter_by(is_admin=False)
    if q:
        query = query.filter(db.or_(User.name.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    users = query.order_by(User.created_at.desc()).all()

    stats = {}
    for u in users:
        agg = db.session.query(func.count(Order.id),
                               func.coalesce(func.sum(Order.total), 0)) \
            .filter(Order.user_id == u.id, Order.status != "CANCELLED").first()
        stats[u.id] = {"orders": agg[0], "spent": int(agg[1])}

    return render_template("admin/customers.html", users=users, stats=stats, q=q)


@admin_bp.route("/customers/<int:uid>")
@login_required
@admin_required
def customer_detail(uid):
    user = db.session.get(User, uid) or abort(404)
    if user.is_admin:
        abort(404)
    orders = Order.query.filter_by(user_id=uid).order_by(Order.placed_at.desc()).all()
    spent = sum(o.total for o in orders if o.status != "CANCELLED")
    return render_template("admin/customer_detail.html", user=user, orders=orders,
                           spent=spent, meta=STATUS_META, addresses=user.addresses)
