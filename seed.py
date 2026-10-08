"""
seed.py — Demo data so the site looks alive on first run.
Creates: admin, 3 customers, 6 categories, 16 products, 4 demo orders.
Run:  python -c "from app import app; from seed import seed_all; seed_all(app)"
"""
from datetime import datetime, timedelta
from extensions import db
from models import (User, Address, Category, Product, Order, OrderItem,
                    OrderStatusHistory, utcnow)
from utils import slugify


CATEGORIES = [
    ("Fashion", "👗"), ("Electronics", "📱"), ("Home & Furniture", "🛋️"),
    ("Kitchen", "🍳"), ("Beauty", "💄"), ("Sports", "🏏"),
]

# name, category, price, mrp, stock, emoji, color, rating, reviews, seller
PRODUCTS = [
    ("Men's Cotton Casual Shirt (Slim Fit)", "Fashion", 499, 1299, 45, "👔", "#e8f0fe", 4.3, 12480, "StyleHub"),
    ("Women's Anarkali Kurta Set — Rayon", "Fashion", 749, 1999, 30, "👗", "#fde8f1", 4.5, 9820, "TrendyThreads"),
    ("Ethnic Jhumka Earrings — Gold Plated", "Fashion", 249, 799, 120, "💍", "#fdf7e0", 4.2, 18600, "TrendyThreads"),
    ("Cotton Kurta for Men — Festive", "Fashion", 899, 2199, 25, "🥻", "#eefaf3", 4.1, 4300, "StyleHub"),

    ("Wireless Bluetooth Earbuds 40hr Playback", "Electronics", 899, 2999, 60, "🎧", "#f3e8fd", 4.1, 38210, "TechZone"),
    ("Smart Watch AMOLED Display & SpO2", "Electronics", 1799, 4999, 38, "⌚", "#fff4e0", 3.9, 24110, "TechZone"),
    ("Smartphone 5G — 8GB RAM, 128GB", "Electronics", 13999, 17999, 15, "📱", "#e9ecfd", 4.4, 41200, "MobileMart"),
    ("Bluetooth Speaker 20W — Waterproof", "Electronics", 1299, 3499, 4, "🔊", "#e8f7fd", 4.0, 8700, "TechZone"),

    ("3-Seater Fabric Sofa — Premium Grey", "Home & Furniture", 15999, 29999, 8, "🛋️", "#eef1f5", 4.2, 3210, "FurniCraft"),
    ("Cotton Bedsheet Set — King Size", "Home & Furniture", 699, 1899, 55, "🛏️", "#f5eefb", 4.4, 11200, "HomeEssentials"),
    ("LED Study Table Lamp — Dimmable", "Home & Furniture", 549, 1299, 70, "💡", "#fdf9e8", 4.3, 5400, "HomeEssentials"),

    ("Stainless Steel Pressure Cooker 5L", "Kitchen", 1249, 2499, 40, "🍲", "#e8fdf1", 4.4, 15340, "HomeEssentials"),
    ("Non-Stick Cookware Set (3 Pieces)", "Kitchen", 899, 2199, 32, "🍳", "#f0fde8", 4.3, 6720, "HomeEssentials"),
    ("Masala Dabba / Spice Box — Steel", "Kitchen", 349, 899, 90, "🧂", "#fef3e8", 4.5, 9100, "HomeEssentials"),

    ("Vitamin C Face Serum — 30ml", "Beauty", 399, 899, 80, "🧴", "#fdf3e8", 4.6, 52100, "GlowUp"),
    ("Matte Liquid Lipstick — Long Stay", "Beauty", 299, 699, 65, "💄", "#fde8ee", 4.2, 22300, "GlowUp"),

    ("Running Shoes — Lightweight", "Sports", 1099, 2999, 28, "👟", "#e8f7fd", 4.0, 8900, "SportyFit"),
    ("Yoga Mat 6mm — Anti-Slip with Strap", "Sports", 549, 1299, 50, "🧘", "#f1e8fd", 4.5, 7410, "SportyFit"),
    ("Cricket Bat — Kashmir Willow", "Sports", 1499, 3499, 12, "🏏", "#fdf0e8", 4.1, 3300, "SportyFit"),
]

DEMO_CUSTOMERS = [
    ("Arun Kumar", "arun@example.com", "9876543210", "Home", "Arun Kumar", "9876543210",
     "12, Anna Nagar 2nd Street", "Near Tower Park", "Chennai", "Tamil Nadu", "600040"),
    ("Divya Raman", "divya@example.com", "9876500001", "Work", "Divya Raman", "9876500001",
     "45, T Nagar Main Road", "Flat 3B", "Chennai", "Tamil Nadu", "600017"),
    ("Karthik S", "karthik@example.com", "9876500002", "Home", "Karthik S", "9876500002",
     "78, Gandhi Street", "", "Coimbatore", "Tamil Nadu", "641001"),
]


def seed_all(app):
    with app.app_context():
        admin = User(name="Admin", email="admin@shopkart.com",
                     phone="9000000000", is_admin=True)
        admin.set_password("admin123")
        db.session.add(admin)

        # ---------------- categories ----------------
        cat_map = {}
        for name, icon in CATEGORIES:
            c = Category(name=name, slug=slugify(name), icon=icon)
            db.session.add(c)
            cat_map[name] = c
        db.session.flush()

        # ---------------- products ----------------
        for (name, cat, price, mrp, stock, emoji, color, rating, reviews, seller) in PRODUCTS:
            db.session.add(Product(
                name=name, slug=slugify(name), price=price, mrp=mrp, stock=stock,
                category_id=cat_map[cat].id, emoji=emoji, color=color,
                rating=rating, review_count=reviews, seller=seller,
                description=(f"{name}. Quality checked and fulfilled by {seller}. "
                             f"7-day easy returns. Free delivery on orders above ₹499."),
            ))
        db.session.flush()

        # ---------------- customers + addresses ----------------
        customers = []
        for (nm, em, ph, label, fan, fph, l1, l2, city, state, pin) in DEMO_CUSTOMERS:
            u = User(name=nm, email=em, phone=ph)
            u.set_password("test123")
            db.session.add(u)
            db.session.flush()
            db.session.add(Address(user_id=u.id, label=label, full_name=fan, phone=fph,
                                   line1=l1, line2=l2, city=city, state=state,
                                   pincode=pin, is_default=True))
            customers.append(u)
        db.session.flush()

        # ---------------- demo orders ----------------
        demo_orders = [
            # (customer_index, days_ago, status, [(product_slug_part, qty)])
            (0, 9, "DELIVERED", [("wireless-bluetooth-earbuds", 1), ("non-stick-cookware", 1)]),
            (1, 6, "SHIPPED",   [("anarkali-kurta", 2)]),
            (2, 3, "CONFIRMED", [("running-shoes", 1), ("yoga-mat", 1)]),
            (0, 1, "PLACED",    [("vitamin-c-face-serum", 2)]),
            (1, 0, "PACKED",    [("smart-watch", 1)]),
        ]

        for (ci, days, status, lines) in demo_orders:
            u = customers[ci]
            addr = u.addresses[0]
            placed = utcnow() - timedelta(days=days)

            order = Order(
                order_number="TEMP", user_id=u.id,
                ship_name=addr.full_name, ship_phone=addr.phone,
                ship_line1=addr.line1, ship_line2=addr.line2,
                ship_city=addr.city, ship_state=addr.state, ship_pincode=addr.pincode,
                payment_method="COD", status=status, placed_at=placed,
                delivered_at=placed + timedelta(days=2) if status == "DELIVERED" else None,
            )
            db.session.add(order)
            db.session.flush()
            order.order_number = f"SK-{placed.year}-{order.id:06d}"

            subtotal = 0
            for (part, qty) in lines:
                p = Product.query.filter(Product.slug.like(f"%{part}%")).first()
                if not p:
                    continue
                subtotal += p.price * qty
                db.session.add(OrderItem(order_id=order.id, product_id=p.id,
                                         product_name=p.name, product_image=p.image,
                                         emoji=p.emoji, color=p.color, seller=p.seller,
                                         price=p.price, qty=qty, line_total=p.price * qty))

            shipping = 0 if subtotal >= 499 else 49
            order.subtotal, order.shipping_fee = subtotal, shipping
            order.total = subtotal + shipping

            # status timeline
            flow = ["PLACED", "CONFIRMED", "PACKED", "SHIPPED", "OUT_FOR_DELIVERY", "DELIVERED"]
            upto = flow.index(status) if status in flow else 0
            for i in range(upto + 1):
                db.session.add(OrderStatusHistory(
                    order_id=order.id, status=flow[i], note="Demo data",
                    created_at=placed + timedelta(hours=6 * i)))

        db.session.commit()
        print(f"   → admin@shopkart.com / admin123")
        print(f"   → arun@example.com / test123  (customer)")
        print(f"   → {len(PRODUCTS)} products, {len(CATEGORIES)} categories, "
              f"{len(customers)} customers, {len(demo_orders)} orders")
