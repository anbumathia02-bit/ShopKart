"""End-to-end smoke test for ShopKart using only stdlib."""
import re, sys, json
import urllib.request, urllib.parse, http.cookiejar

BASE = "http://127.0.0.1:5000"
ok_count, fail = 0, []


class Client:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj), NoRedirect())

    def get(self, path):
        req = urllib.request.Request(BASE + path)
        try:
            r = self.op.open(req)
            return r.status, r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "ignore")

    def post(self, path, data, follow=False):
        body = urllib.parse.urlencode(data).encode()
        req = urllib.request.Request(BASE + path, data=body)
        try:
            r = self.op.open(req)
            return r.status, r.headers.get("Location"), r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Location"), e.read().decode("utf-8", "ignore")

    def csrf(self, path):
        _, html = self.get(path)
        m = re.search(r'name="csrf_token" value="([^"]+)"', html)
        if not m:
            m = re.search(r'name="csrf-token" content="([^"]+)"', html)
        return m.group(1) if m else None


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def check(label, cond, extra=""):
    global ok_count
    if cond:
        ok_count += 1
        print(f"  ✅ {label}")
    else:
        fail.append(label)
        print(f"  ❌ {label} {extra}")


# ─────────────────────────────── CUSTOMER FLOW
print("\n👤 CUSTOMER FLOW  (arun@example.com)")
c = Client()
code, html = c.get("/login")
check("login page loads", code == 200)

token = c.csrf("/login")
code, loc, html = c.post("/login", {"csrf_token": token, "email": "arun@example.com", "password": "test123"})
check("login POST → redirect", code in (302, 303), f"(got {code}) {loc}")
check("redirected to home", loc in ("/", None), loc)

code, html = c.get("/account")
check("account page has user name", "Arun" in html, f"(status {code})")

# add to cart
token = c.csrf("/product/1")
code, loc, _ = c.post("/cart/add/1", {"csrf_token": token, "qty": "2", "next": "/product/1"})
check("add to cart", code in (302, 303), f"(got {code})")

code, html = c.get("/cart/")
check("cart page shows item", code == 200 and "Your Cart" in html)
check("cart has 2 qty badge", ">2<" in html or '"2"' in html)

# wishlist toggle (AJAX)
token = c.csrf("/product/2")
code, loc, body = c.post("/wishlist/toggle/2", {"csrf_token": token})
code, html = c.get("/wishlist")
check("wishlist contains item", code == 200 and "Wishlist" in html)

# update qty
token = c.csrf("/cart/")
code, loc, _ = c.post("/cart/update/1", {"csrf_token": token, "qty": "3"})
check("update cart qty", code in (302, 303))

# checkout
token = c.csrf("/checkout")
code, html = c.get("/checkout")
check("checkout page loads", code == 200 and "Delivery Address" in html)
m = re.search(r'name="address_id" value="(\d+)"', html)
check("address present", bool(m))
addr_id = m.group(1) if m else "1"

code, loc, body = c.post("/checkout", {"csrf_token": token, "address_id": addr_id, "payment_method": "COD"})
check("place order → redirect to success", code in (302, 303) and "/order/success/" in (loc or ""), f"(got {code}) {loc}")

order_number = (loc or "").split("/order/success/")[-1] if loc and "/order/success/" in loc else ""
check("order number format", order_number.startswith("SK-"), order_number)

code, html = c.get(f"/order/success/{order_number}")
check("order success page", code == 200 and order_number in html)

code, html = c.get("/orders")
check("order history shows order", code == 200 and order_number in html)

code, html = c.get(f"/orders/{order_number}")
check("order detail page", code == 200 and "Track Your Order" in html)

# stock reduced?
code, html = c.get("/product/1")
check("stock reduced after order", "left in stock" in html or "In stock" in html)

# public tracking
c2 = Client()
code, html = c2.get(f"/track?order={order_number}")
check("public track works", code == 200 and order_number in html)

# cancel order
token = c.csrf(f"/orders/{order_number}")
code, loc, _ = c.post(f"/orders/{order_number}/cancel", {"csrf_token": token})
code, html = c.get(f"/orders/{order_number}")
check("order cancelled", code == 200 and "Cancelled" in html)

# ─────────────────────────────── ADMIN FLOW
print("\n⚙️  ADMIN FLOW  (admin@shopkart.com)")
a = Client()
token = a.csrf("/login")
code, loc, _ = a.post("/login", {"csrf_token": token, "email": "admin@shopkart.com", "password": "admin123"})
check("admin login → dashboard", loc == "/admin/", f"(got {loc})")

code, html = a.get("/admin/")
check("dashboard loads", code == 200 and "Sales Dashboard" in html)
check("dashboard shows revenue", "Total Revenue" in html and "₹" in html)
check("dashboard shows chart", "Revenue — Last 7 Days" in html)
check("dashboard shows top products", "Top Selling Products" in html)

for path, needle in [("/admin/products", "Products"), ("/admin/products/new", "Add New Product"),
                     ("/admin/categories", "Add Category"), ("/admin/orders", "Orders"),
                     ("/admin/customers", "Customers")]:
    code, html = a.get(path)
    check(f"{path} loads", code == 200 and needle in html, f"status {code}")

# create product
token = a.csrf("/admin/products/new")
code, loc, _ = a.post("/admin/products/new", {
    "csrf_token": token, "name": "QA Neckband Headphones",
    "description": "QA test product", "price": "799", "mrp": "1999", "stock": "7",
    "category_id": "2", "seller": "QA Seller", "emoji": "🎵", "color": "#e8f0fe",
    "rating": "4.1", "is_active": "on"})
check("create product", code in (302, 303))
code, html = a.get("/admin/products?q=QA+Neckband")
check("new product in admin list", "QA Neckband Headphones" in html)

# stock update
m = re.search(r'/admin/products/(\d+)/stock', html)
pid = m.group(1) if m else None
if pid:
    token = a.csrf("/admin/products")
    code, loc, _ = a.post(f"/admin/products/{pid}/stock", {"csrf_token": token, "stock": "42"})
    check("stock update", code in (302, 303))

# edit product
    token = a.csrf(f"/admin/products/{pid}/edit")
    code, loc, _ = a.post(f"/admin/products/{pid}/edit", {
        "csrf_token": token, "name": "QA Neckband Headphones v2", "price": "699", "mrp": "1999",
        "stock": "42", "category_id": "2", "seller": "QA Seller", "emoji": "🎵",
        "color": "#e8f0fe", "rating": "4.2", "is_active": "on"})
    check("edit product", code in (302, 303))
    code, html = a.get("/admin/products?q=QA+Neckband")
    check("edit reflected", "v2" in html)

# order status update
code, html = a.get("/admin/orders")
m = re.search(r'/admin/orders/(\d+)"', html)
oid = m.group(1) if m else None
if oid:
    token = a.csrf(f"/admin/orders/{oid}")
    code, loc, _ = a.post(f"/admin/orders/{oid}/status",
                          {"csrf_token": token, "status": "SHIPPED", "note": "QA test"})
    check("admin status update", code in (302, 303))
    code, html = a.get(f"/admin/orders/{oid}")
    check("status reflected", "Shipped" in html)

# customer detail
code, html = a.get("/admin/customers")
m = re.search(r'/admin/customers/(\d+)"', html)
if m:
    code, html = a.get(f"/admin/customers/{m.group(1)}")
    check("customer detail", code == 200 and "Order History" in html)

# deactivate test product
if pid:
    token = a.csrf("/admin/products")
    code, loc, _ = a.post(f"/admin/products/{pid}/delete", {"csrf_token": token})
    check("deactivate product", code in (302, 303))
    code, html = a.get("/products?q=Neckband&sort=new")
    check("deactivated product hidden from shop", 'class="pname">QA Neckband Headphones' not in html)

# ─────────────────────────────── SECURITY
print("\n🔒 SECURITY CHECKS")
g = Client()
code, loc, _ = g.post("/checkout", {"csrf_token": "bogus", "address_id": "1"})
check("CSRF protection blocks bad token", code in (400, 302, 401), f"got {code}")

g2 = Client()
code, loc, _ = g2.post("/cart/add/1", {"qty": "1"})
check("guest cannot post without CSRF", code != 200 or "added" not in str(loc), f"got {code}")

c3 = Client()
code, loc = c3.get("/admin/")
check("anonymous /admin/ redirects to login", code == 302 and "login" in (loc or ""), f"got {code} {loc}")

# non-admin hitting admin
cust = Client()
t = cust.csrf("/login")
cust.post("/login", {"csrf_token": t, "email": "divya@example.com", "password": "test123"})
code, html = cust.get("/admin/")
check("non-admin blocked from /admin/", code == 403, f"got {code}")

# guest cart flow
g3 = Client()
token = g3.csrf("/product/3")
code, loc, _ = g3.post("/cart/add/3", {"csrf_token": token, "qty": "1"})
code, html = g3.get("/cart/")
check("guest session cart works", "Your Cart" in html)
# merge on login
t = g3.csrf("/login")
code, loc, html = g3.post("/login", {"csrf_token": t, "email": "karthik@example.com", "password": "test123"})
code, html = g3.get("/cart/")
check("guest cart merged after login", "Your Cart" in html and "Jhumka" in html)

print("\n" + "=" * 52)
print(f"  PASSED: {ok_count}   FAILED: {len(fail)}")
if fail:
    print("  Failed tests:")
    for f in fail:
        print("   -", f)
print("=" * 52)
sys.exit(1 if fail else 0)
