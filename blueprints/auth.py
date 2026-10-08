"""
blueprints/auth.py — Login / Signup / Logout / Account / Address book
"""
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   request, session)
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db
from models import User, Address, Order
from cart_utils import merge_guest_cart_into_db

auth_bp = Blueprint("auth", __name__)


# ---------------------------------------------------------------- SIGNUP
@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        name     = request.form.get("name", "").strip()
        email    = request.form.get("email", "").strip().lower()
        phone    = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        confirm  = request.form.get("confirm", "")

        errors = []
        if len(name) < 2:
            errors.append("Ellaam sari — please enter your full name.")
        if "@" not in email or "." not in email:
            errors.append("Valid email id kudunga.")
        if User.query.filter_by(email=email).first():
            errors.append("Indha email already registered. Login pannunga.")
        if len(password) < 6:
            errors.append("Password at least 6 characters venum.")
        if password != confirm:
            errors.append("Passwords match aagala.")

        if errors:
            for e in errors:
                flash(e, "danger")
            return render_template("auth/signup.html", form=request.form)

        user = User(name=name, email=email, phone=phone)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        merge_guest_cart_into_db(user)          # guest cart → DB cart
        flash(f"Welcome {user.name}! Account ready 🎉", "success")
        return redirect(url_for("main.home"))

    return render_template("auth/signup.html", form={})


# ---------------------------------------------------------------- LOGIN
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.home"))

    if request.method == "POST":
        email    = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            flash("Email or password wrong. Try again.", "danger")
            return render_template("auth/login.html", form=request.form)

        login_user(user, remember=remember)
        merge_guest_cart_into_db(user)

        flash(f"Welcome back, {user.name}! 👋", "success")

        nxt = request.args.get("next")
        if nxt and nxt.startswith("/"):          # open-redirect safe
            return redirect(nxt)
        if user.is_admin:
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("main.home"))

    return render_template("auth/login.html", form={})


# ---------------------------------------------------------------- LOGOUT
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out. See you soon! 👋", "info")
    return redirect(url_for("main.home"))


# ---------------------------------------------------------------- ACCOUNT
@auth_bp.route("/account")
@login_required
def account():
    orders = (Order.query.filter_by(user_id=current_user.id)
              .order_by(Order.placed_at.desc()).limit(3).all())
    total_orders = Order.query.filter_by(user_id=current_user.id).count()
    return render_template("auth/account.html", orders=orders, total_orders=total_orders)


# ---------------------------------------------------------------- ADDRESSES
@auth_bp.route("/account/addresses", methods=["GET", "POST"])
@login_required
def addresses():
    if request.method == "POST":
        a = Address(
            user_id=current_user.id,
            label=request.form.get("label", "Home").strip() or "Home",
            full_name=request.form.get("full_name", "").strip(),
            phone=request.form.get("phone", "").strip(),
            line1=request.form.get("line1", "").strip(),
            line2=request.form.get("line2", "").strip(),
            city=request.form.get("city", "").strip(),
            state=request.form.get("state", "").strip(),
            pincode=request.form.get("pincode", "").strip(),
        )
        if not all([a.full_name, a.phone, a.line1, a.city, a.state, a.pincode]):
            flash("All * fields venum.", "danger")
            return redirect(url_for("auth.addresses"))

        make_default = bool(request.form.get("is_default"))
        if make_default or not current_user.addresses:
            Address.query.filter_by(user_id=current_user.id).update({"is_default": False})
            a.is_default = True

        db.session.add(a)
        db.session.commit()
        flash("Address saved ✓", "success")
        return redirect(request.args.get("next") or url_for("auth.addresses"))

    return render_template("auth/addresses.html", addresses=current_user.addresses)


@auth_bp.route("/account/addresses/<int:aid>/delete", methods=["POST"])
@login_required
def delete_address(aid):
    a = Address.query.filter_by(id=aid, user_id=current_user.id).first_or_404()
    was_default = a.is_default
    db.session.delete(a)
    db.session.commit()
    if was_default and current_user.addresses:
        current_user.addresses[0].is_default = True
        db.session.commit()
    flash("Address removed.", "info")
    return redirect(url_for("auth.addresses"))


@auth_bp.route("/account/addresses/<int:aid>/default", methods=["POST"])
@login_required
def make_default_address(aid):
    a = Address.query.filter_by(id=aid, user_id=current_user.id).first_or_404()
    Address.query.filter_by(user_id=current_user.id).update({"is_default": False})
    a.is_default = True
    db.session.commit()
    flash("Default address updated ✓", "success")
    return redirect(url_for("auth.addresses"))
