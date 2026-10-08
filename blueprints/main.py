"""
blueprints/main.py — Customer facing catalog pages
Home • Products list + search + filters • Product detail • Wishlist
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, current_app
from flask_login import current_user, login_required
from sqlalchemy import or_
from extensions import db
from models import Product, Category, WishlistItem

main_bp = Blueprint("main", __name__)


# ---------------------------------------------------------------- HOME
@main_bp.route("/")
def home():
    categories = Category.query.order_by(Category.name).all()

    deal_products = (Product.query.filter(Product.is_active, Product.mrp > Product.price)
                     .order_by((Product.mrp - Product.price).desc()).limit(8).all())

    top_rated = (Product.query.filter_by(is_active=True)
                 .order_by(Product.rating.desc()).limit(8).all())

    new_arrivals = (Product.query.filter_by(is_active=True)
                    .order_by(Product.created_at.desc()).limit(8).all())

    return render_template("index.html",
                           categories=categories,
                           deal_products=deal_products,
                           top_rated=top_rated,
                           new_arrivals=new_arrivals)


# ---------------------------------------------------------------- PRODUCT LIST
@main_bp.route("/products")
def products():
    # .strip() + hard length cap — hostile input can't produce huge queries
    q        = request.args.get("q", "").strip()[:120]
    cat_slug = request.args.get("cat", "").strip()[:80]
    min_p    = request.args.get("min", type=int)
    max_p    = request.args.get("max", type=int)
    min_r    = request.args.get("rating", type=float)
    sort     = request.args.get("sort", "pop")
    page     = request.args.get("page", 1, type=int)

    query = Product.query.filter_by(is_active=True)

    if q:
        like = f"%{q}%"
        query = query.filter(or_(Product.name.ilike(like),
                                 Product.description.ilike(like),
                                 Product.seller.ilike(like)))
    active_cat = None
    if cat_slug and cat_slug != "all":
        active_cat = Category.query.filter_by(slug=cat_slug).first()
        if active_cat:
            query = query.filter(Product.category_id == active_cat.id)

    if min_p is not None:
        query = query.filter(Product.price >= min_p)
    if max_p is not None:
        query = query.filter(Product.price <= max_p)
    if min_r:
        query = query.filter(Product.rating >= min_r)

    if sort == "plow":
        query = query.order_by(Product.price.asc())
    elif sort == "phigh":
        query = query.order_by(Product.price.desc())
    elif sort == "rate":
        query = query.order_by(Product.rating.desc())
    elif sort == "new":
        query = query.order_by(Product.created_at.desc())
    elif sort == "disc":                     # highest discount first
        query = query.order_by((Product.mrp - Product.price).desc())
    else:  # popularity ≈ review count
        query = query.order_by(Product.review_count.desc())

    pagination = query.paginate(page=page, per_page=12, error_out=False)

    return render_template("products.html",
                           pagination=pagination,
                           products=pagination.items,
                           categories=Category.query.order_by(Category.name).all(),
                           active_cat=active_cat,
                           q=q, min_p=min_p, max_p=max_p,
                           min_r=min_r, sort=sort)


# ---------------------------------------------------------------- PRODUCT DETAIL
@main_bp.route("/product/<int:pid>")
def product_detail(pid):
    product = db.session.get(Product, pid)
    if not product or (not product.is_active and
                       not (current_user.is_authenticated and current_user.is_admin)):
        flash("Product not found.", "danger")
        return redirect(url_for("main.products"))

    related = (Product.query.filter(Product.is_active,
                                    Product.category_id == product.category_id,
                                    Product.id != product.id)
               .limit(4).all())

    in_wishlist = False
    if current_user.is_authenticated:
        in_wishlist = WishlistItem.query.filter_by(
            user_id=current_user.id, product_id=product.id).first() is not None

    return render_template("product_detail.html",
                           product=product, related=related, in_wishlist=in_wishlist)


# ---------------------------------------------------------------- WISHLIST
@main_bp.route("/wishlist")
@login_required
def wishlist():
    items = (WishlistItem.query.filter_by(user_id=current_user.id)
             .order_by(WishlistItem.added_at.desc()).all())
    return render_template("wishlist.html", items=items)


@main_bp.route("/wishlist/toggle/<int:pid>", methods=["POST"])
@login_required
def toggle_wishlist(pid):
    product = db.session.get(Product, pid)
    if not product:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify(ok=False, msg="Product not found"), 404
        flash("Product not found.", "danger")
        return redirect(url_for("main.products"))

    row = WishlistItem.query.filter_by(user_id=current_user.id, product_id=pid).first()
    if row:
        db.session.delete(row)
        db.session.commit()
        added = False
        msg = "Removed from wishlist"
    else:
        db.session.add(WishlistItem(user_id=current_user.id, product_id=pid))
        db.session.commit()
        added = True
        msg = "Added to wishlist ❤️"

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify(ok=True, added=added, msg=msg)

    flash(msg, "success")
    return redirect(request.referrer or url_for("main.home"))
