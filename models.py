"""
models.py — All database tables (SQLAlchemy ORM)
================================================
Yaaru table enna-ku:
  User            → customers + admins (is_admin flag)
  Address         → customer-oda delivery addresses
  Category        → product categories
  Product         → catalog
  CartItem        → logged-in user cart (guests use session)
  WishlistItem    → saved-for-later
  Order           → one placed order (address snapshot stored)
  OrderItem       → products inside that order
  OrderStatusHistory → order tracking timeline
"""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager


def utcnow():
    """Naive UTC timestamp — DB friendly and free of deprecation warnings."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


# =====================================================================
# USER
# =====================================================================
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(15))
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    addresses = db.relationship("Address", backref="user", lazy=True,
                                cascade="all, delete-orphan")
    cart_items = db.relationship("CartItem", backref="user", lazy=True,
                                 cascade="all, delete-orphan")
    wishlist_items = db.relationship("WishlistItem", backref="user", lazy=True,
                                     cascade="all, delete-orphan")
    orders = db.relationship("Order", backref="user", lazy=True)

    # ---- password helpers ----
    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    @property
    def default_address(self):
        for a in self.addresses:
            if a.is_default:
                return a
        return self.addresses[0] if self.addresses else None

    def __repr__(self):
        return f"<User {self.email}>"


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# =====================================================================
# ADDRESS
# =====================================================================
class Address(db.Model):
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label = db.Column(db.String(30), default="Home")      # Home / Work / Other
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    line1 = db.Column(db.String(200), nullable=False)
    line2 = db.Column(db.String(200))
    city = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.String(10), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    @property
    def one_line(self):
        parts = [self.line1, self.line2, self.city, self.state, self.pincode]
        return ", ".join(p for p in parts if p)


# =====================================================================
# CATEGORY
# =====================================================================
class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False, index=True)
    icon = db.Column(db.String(10), default="📦")
    products = db.relationship("Product", backref="category", lazy=True)

    @property
    def product_count(self):
        return Product.query.filter_by(category_id=self.id, is_active=True).count()


# =====================================================================
# PRODUCT
# =====================================================================
class Product(db.Model):
    __tablename__ = "products"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    description = db.Column(db.Text)
    price = db.Column(db.Integer, nullable=False)          # selling price ₹
    mrp = db.Column(db.Integer, nullable=False)            # strike-through ₹
    stock = db.Column(db.Integer, default=0, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"))
    seller = db.Column(db.String(100), default="ShopKart Retail")
    image = db.Column(db.String(255))                      # uploaded filename
    emoji = db.Column(db.String(10), default="📦")         # fallback visual
    color = db.Column(db.String(20), default="#eef1f5")    # fallback bg
    rating = db.Column(db.Float, default=4.0)
    review_count = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=utcnow)

    cart_items = db.relationship("CartItem", backref="product", lazy=True,
                                 cascade="all, delete-orphan")
    wishlist_items = db.relationship("WishlistItem", backref="product", lazy=True,
                                     cascade="all, delete-orphan")

    # ---- computed helpers used in templates ----
    @property
    def discount_percent(self):
        if self.mrp and self.mrp > self.price:
            return round((1 - self.price / self.mrp) * 100)
        return 0

    @property
    def in_stock(self):
        return self.stock > 0

    @property
    def image_url(self):
        if self.image:
            return f"/static/uploads/products/{self.image}"
        return None

    @property
    def stars(self):
        full = int(self.rating)
        half = 1 if (self.rating - full) >= 0.4 else 0
        return "★" * full + ("★" if half else "") + "☆" * (5 - full - half)

    @property
    def is_new(self):
        return (utcnow() - self.created_at).days <= 14


# =====================================================================
# CART (logged-in users only — guests use session)
# =====================================================================
class CartItem(db.Model):
    __tablename__ = "cart_items"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    qty = db.Column(db.Integer, default=1, nullable=False)
    added_at = db.Column(db.DateTime, default=utcnow)


# =====================================================================
# WISHLIST
# =====================================================================
class WishlistItem(db.Model):
    __tablename__ = "wishlist_items"
    __table_args__ = (db.UniqueConstraint("user_id", "product_id", name="uq_wish_user_product"),)

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"), nullable=False)
    added_at = db.Column(db.DateTime, default=utcnow)


# =====================================================================
# ORDER
# =====================================================================
ORDER_STATUSES = ["PLACED", "CONFIRMED", "PACKED", "SHIPPED",
                  "OUT_FOR_DELIVERY", "DELIVERED", "CANCELLED"]

STATUS_META = {
    "PLACED":           {"icon": "🧾", "color": "secondary", "text": "Order Placed"},
    "CONFIRMED":        {"icon": "✅", "color": "info",      "text": "Confirmed"},
    "PACKED":           {"icon": "📦", "color": "info",      "text": "Packed"},
    "SHIPPED":          {"icon": "🚚", "color": "primary",   "text": "Shipped"},
    "OUT_FOR_DELIVERY": {"icon": "🛵", "color": "warning",   "text": "Out for Delivery"},
    "DELIVERED":        {"icon": "🎉", "color": "success",   "text": "Delivered"},
    "CANCELLED":        {"icon": "❌", "color": "danger",    "text": "Cancelled"},
}


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # ---- address snapshot (frozen copy — user later edits address, order stays correct) ----
    ship_name = db.Column(db.String(120), nullable=False)
    ship_phone = db.Column(db.String(15), nullable=False)
    ship_line1 = db.Column(db.String(200), nullable=False)
    ship_line2 = db.Column(db.String(200))
    ship_city = db.Column(db.String(80), nullable=False)
    ship_state = db.Column(db.String(80), nullable=False)
    ship_pincode = db.Column(db.String(10), nullable=False)

    subtotal = db.Column(db.Integer, nullable=False, default=0)
    shipping_fee = db.Column(db.Integer, nullable=False, default=0)
    total = db.Column(db.Integer, nullable=False, default=0)
    payment_method = db.Column(db.String(20), default="COD")   # COD (later: RAZORPAY)
    status = db.Column(db.String(25), default="PLACED", nullable=False)
    placed_at = db.Column(db.DateTime, default=utcnow)
    delivered_at = db.Column(db.DateTime)

    items = db.relationship("OrderItem", backref="order", lazy=True,
                            cascade="all, delete-orphan")
    history = db.relationship("OrderStatusHistory", backref="order", lazy=True,
                              cascade="all, delete-orphan",
                              order_by="OrderStatusHistory.created_at")

    @property
    def item_count(self):
        return sum(i.qty for i in self.items)

    @property
    def can_cancel(self):
        return self.status in ("PLACED", "CONFIRMED", "PACKED")

    @property
    def status_meta(self):
        return STATUS_META.get(self.status, {"icon": "•", "color": "secondary", "text": self.status})

    @property
    def ship_address(self):
        parts = [self.ship_line1, self.ship_line2, self.ship_city, self.ship_state, self.ship_pincode]
        return ", ".join(p for p in parts if p)


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("products.id"))   # may be deleted later
    product_name = db.Column(db.String(200), nullable=False)           # snapshot
    product_image = db.Column(db.String(255))                          # snapshot
    emoji = db.Column(db.String(10), default="📦")
    color = db.Column(db.String(20), default="#eef1f5")
    seller = db.Column(db.String(100))
    price = db.Column(db.Integer, nullable=False)                      # snapshot of price
    qty = db.Column(db.Integer, nullable=False)
    line_total = db.Column(db.Integer, nullable=False)


class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False)
    status = db.Column(db.String(25), nullable=False)
    note = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=utcnow)

    @property
    def meta(self):
        return STATUS_META.get(self.status, {"icon": "•", "color": "secondary", "text": self.status})
