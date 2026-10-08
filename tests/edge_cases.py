"""
edge_cases.py — Hostile-input & security test suite
===================================================
Goal: NOTHING makes the app return a 500 (crash).

  • bad URLs, bad IDs, negative/huge quantities, junk query params
  • SQL-injection & XSS attempts
  • IDOR checks (one customer touching another's order/address)
  • invalid file uploads, oversized requests
  • admin-only routes as normal user

Run (server must be running):   python tests/edge_cases.py
"""
import io
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import http.cookiejar

BASE = os.environ.get("BASE_URL", "http://127.0.0.1:5000")

passed, failed, crashes = 0, [], []


class Client:
    def __init__(self):
        self.cj = http.cookiejar.CookieJar()
        self.op = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(self.cj), NoRedirect())

    def get(self, path):
        try:
            r = self.op.open(BASE + path, timeout=30)
            return r.status, r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "ignore")

    def post(self, path, data=None, raw_body=None, content_type=None):
        if raw_body is not None:
            req = urllib.request.Request(BASE + path, data=raw_body)
            if content_type:
                req.add_header("Content-Type", content_type)
        else:
            req = urllib.request.Request(BASE + path,
                                         data=urllib.parse.urlencode(data or {}).encode())
        try:
            r = self.op.open(req, timeout=30)
            return r.status, r.headers.get("Location"), r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            return e.code, e.headers.get("Location"), e.read().decode("utf-8", "ignore")

    def csrf(self, path):
        _, html = self.get(path)
        m = re.search(r'name="csrf_token" value="([^"]+)"', html)
        if not m:
            m = re.search(r'name="csrf-token" content="([^"]+)"', html)
        return m.group(1) if m else None

    def login(self, email, password):
        t = self.csrf("/login")
        return self.post("/login", {"csrf_token": t, "email": email, "password": password})


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def check(label, code, expect=None, body=""):
    """expect: int, tuple of ints, or callable(code)->bool"""
    global passed
    if code == 500:
        crashes.append(f"{label} → 500 (CRASH)")
        print(f"  💥 {label} → 500 CRASH")
        return
    good = True
    if expect is not None:
        good = (code in expect) if isinstance(expect, (tuple, list, set)) else (code == expect)
    if good:
        passed += 1
        print(f"  ✅ {label}  ({code})")
    else:
        failed.append(f"{label} → {code}, expected {expect}")
        print(f"  ❌ {label} → {code} (expected {expect})")


print("=" * 60)
print("EDGE-CASE / SECURITY TESTS")
print("=" * 60)

# ══════════════════ 1. BAD URLS & IDS ══════════════════
print("\n🔗 Bad URLs and IDs")
g = Client()
check("GET /product/999999 (missing product)", *g.get("/product/999999")[:1], expect=(302, 404))
check("GET /product/abc (non-numeric id)", *g.get("/product/abc")[:1], expect=404)
check("GET /product/-1", *g.get("/product/-1")[:1], expect=404)
check("GET /product/0", *g.get("/product/0")[:1], expect=(302, 404))
check("GET /orders/SK-9999-999999 (unknown order)", *g.get("/orders/SK-9999-999999")[:1], expect=(302, 404))
check("GET /track?order=GARBAGE", *g.get("/track?order=GARBAGE")[:1], expect=200)
check("GET /cart/update/1 with GET method", *g.get("/cart/update/1")[:1], expect=405)
check("GET /nonexistent", *g.get("/nonexistent")[:1], expect=404)

# ══════════════════ 2. JUNK QUERY PARAMS ══════════════════
print("\n🧪 Junk query parameters")
for q, label in [
    ("/products?min=abc&max=xyz", "non-numeric price filter"),
    ("/products?page=99999", "page way out of range"),
    ("/products?page=-5", "negative page"),
    ("/products?page=abc", "non-numeric page"),
    ("/products?rating=notanumber", "non-numeric rating"),
    ("/products?sort=DROP_TABLE", "invalid sort key"),
    ("/products?cat=<script>", "script tag as category"),
    ("/products?q=" + "A" * 300, "300-char search string (app-level cap)"),
    ("/products?min=-99999999&max=99999999", "extreme price range"),
    ("/track?order=" + "9" * 500, "500-digit order number"),
    ("/products?q=" + "A" * 5000, "5000-char URL (web-server rejects safely)"),
]:
    code, _ = g.get(q)
    # a 5000-char URL is refused by gunicorn's request-line limit (400) —
    # that is a safe platform-level rejection, never a crash.
    check(label, code, expect=(200, 400, 414))

# ══════════════════ 3. INJECTION ══════════════════
print("\n💉 SQL injection & XSS")
for payload, label in [
    ("' OR 1=1--", "SQLi classic"),
    ("'; DROP TABLE users;--", "SQLi drop table"),
    ("1' UNION SELECT * FROM users--", "SQLi union"),
    ('<script>alert("xss")</script>', "XSS script tag"),
    ('"><img src=x onerror=alert(1)>', "XSS img onerror"),
]:
    code, html = g.get("/products?q=" + urllib.parse.quote(payload))
    check(f"search: {label}", code, expect=200)
    if code == 200 and "<script>alert" in html:
        crashes.append(f"XSS not escaped for {label}")
        print(f"     💥 XSS payload rendered UNESCAPED!")

# DB still alive after injection attempts?
code, html = g.get("/products")
check("catalog still works after injection attempts", code, expect=200)

# ══════════════════ 4. CART INPUT ABUSE ══════════════════
print("\n🛒 Cart input abuse")
c = Client()
t = c.csrf("/product/1")
check("qty = 999999 (over stock)", *c.post("/cart/add/1", {"csrf_token": t, "qty": "999999"})[:1],
      expect=(302, 200))
t = c.csrf("/product/1")
check("qty = -5 (negative)", *c.post("/cart/add/1", {"csrf_token": t, "qty": "-5"})[:1], expect=(302, 200))
t = c.csrf("/product/1")
check("qty = abc (non-numeric)", *c.post("/cart/add/1", {"csrf_token": t, "qty": "abc"})[:1], expect=(302, 200))
t = c.csrf("/product/1")
check("product 99999 (missing)", *c.post("/cart/add/99999", {"csrf_token": t, "qty": "1"})[:1],
      expect=(302, 404))
code, html = c.get("/cart/")
check("cart page survives all of the above", code, expect=200)

# ══════════════════ 5. AUTH EDGE CASES ══════════════════
print("\n🔐 Auth edge cases")
a = Client()
check("login: wrong password", *a.login("arun@example.com", "WRONG")[:1], expect=(200, 302))
check("login: unknown email", *a.login("nobody@nowhere.com", "whatever")[:1], expect=(200, 302))
check("login: empty values", *a.login("", "")[:1], expect=(200, 302))

b = Client()
t = b.csrf("/signup")
check("signup: duplicate email", *b.post("/signup", {"csrf_token": t, "name": "Dupe",
      "email": "arun@example.com", "password": "secret1", "confirm": "secret1"})[:1], expect=(200, 302))
t = b.csrf("/signup")
check("signup: password mismatch", *b.post("/signup", {"csrf_token": t, "name": "X",
      "email": "new1@example.com", "password": "secret1", "confirm": "secret2"})[:1], expect=(200, 302))
t = b.csrf("/signup")
check("signup: 6-char weak password ok / rejected cleanly",
      *b.post("/signup", {"csrf_token": t, "name": "X2", "email": "new2@example.com",
                          "password": "abc", "confirm": "abc"})[:1], expect=(200, 302))

# ══════════════════ 6. IDOR (other user's data) ══════════════════
print("\n🕵️  IDOR — accessing someone else's data")
arun = Client()
arun.login("arun@example.com", "test123")
_, html = arun.get("/orders")
nums = re.findall(r"/orders/(SK-\d{4}-\d{6})", html)
divya_order = None
d = Client()
d.login("divya@example.com", "test123")
_, html_d = d.get("/orders")
d_nums = set(re.findall(r"/orders/(SK-\d{4}-\d{6})", html_d))
for n in nums:
    if n not in d_nums:
        divya_order = n
        break
if divya_order:
    code, _ = d.get(f"/orders/{divya_order}")     # divya opening arun's order
    check("customer cannot open another's order (404)", code, expect=404)
else:
    print("  ⏭️  (no other-user order available to test)")

# arun posting divya's address id at checkout
addr_code, loc, _ = arun.post("/checkout", {"csrf_token": arun.csrf("/checkout"),
                                            "address_id": "99999", "payment_method": "COD"})
check("checkout with someone else's / bogus address_id", addr_code, expect=(302, 400))

# ══════════════════ 7. ADMIN GUARDS ══════════════════
print("\n🛡️  Admin route guards (as normal customer)")
cust = Client()
cust.login("karthik@example.com", "test123")
for path in ["/admin/", "/admin/products", "/admin/products/new", "/admin/categories",
             "/admin/orders", "/admin/customers", "/admin/customers/1",
             "/admin/orders/1", "/admin/products/1/edit"]:
    code, _ = cust.get(path)
    check(f"blocked: {path}", code, expect=403)

t = cust.csrf("/account")
code, _, _ = cust.post("/admin/products/1/stock", {"csrf_token": t, "stock": "0"})
check("blocked: POST stock update as customer", code, expect=(403, 400))

# ══════════════════ 8. ADMIN BAD INPUTS ══════════════════
print("\n⚙️  Admin panel with bad input")
adm = Client()
adm.login("admin@shopkart.com", "admin123")
t = adm.csrf("/admin/products/new")
check("create product: empty name", *adm.post("/admin/products/new",
      {"csrf_token": t, "name": "", "price": "0", "stock": "0"})[:1], expect=(200, 302))
t = adm.csrf("/admin/products/new")
check("create product: MRP < price", *adm.post("/admin/products/new",
      {"csrf_token": t, "name": "Bad Product", "price": "500", "mrp": "100",
       "stock": "1"})[:1], expect=(200, 302))
t = adm.csrf("/admin/products/new")
check("create product: non-numeric price", *adm.post("/admin/products/new",
      {"csrf_token": t, "name": "Bad2", "price": "abc", "stock": "1"})[:1], expect=(200, 302))
check("edit missing product → 404", *adm.get("/admin/products/999999/edit")[:1], expect=404)
check("order detail missing → 404", *adm.get("/admin/orders/999999")[:1], expect=404)
check("customer detail missing → 404", *adm.get("/admin/customers/999999")[:1], expect=404)
t = adm.csrf("/admin/orders/1")
check("order status: invalid value", *adm.post("/admin/orders/1/status",
      {"csrf_token": t, "status": "HACKED"})[:1], expect=(302, 400))
t = adm.csrf("/admin/categories")
check("category: empty name", *adm.post("/admin/categories", {"csrf_token": t, "name": ""})[:1],
      expect=(200, 302))

# bad file upload (disallowed extension)
boundary = "----ShopKartTest"
bad_file = (
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"csrf_token\"\r\n\r\n"
    f"{adm.csrf('/admin/products/new')}\r\n"
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"name\"\r\n\r\nMalware Upload Test\r\n"
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"price\"\r\n\r\n100\r\n"
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"stock\"\r\n\r\n1\r\n"
    f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"evil.exe\"\r\n"
    f"Content-Type: application/octet-stream\r\n\r\nMZ\x90\x00fake exe\r\n"
    f"--{boundary}--\r\n"
).encode()
code, _, _ = adm.post("/admin/products/new", raw_body=bad_file,
                      content_type=f"multipart/form-data; boundary={boundary}")
check(".exe upload rejected without crashing", code, expect=(200, 302, 400))

# ══════════════════ 9. OVERSIZED REQUEST ══════════════════
print("\n📦 Oversized upload (>5 MB limit)")
import http.client

# Werkzeug rejects a request whose Content-Length exceeds MAX_CONTENT_LENGTH
# BEFORE reading the body — so we announce a 6 MB body and read the answer.
cookie_header = "; ".join(f"{c.name}={c.value}" for c in adm.cj)
conn = http.client.HTTPConnection("127.0.0.1", int(BASE.rsplit(":", 1)[-1]), timeout=20)
try:
    conn.putrequest("POST", "/admin/products/new")
    conn.putheader("Content-Type", "multipart/form-data; boundary=----BigTest")
    conn.putheader("Content-Length", str(6 * 1024 * 1024))
    conn.putheader("Cookie", cookie_header)
    conn.endheaders()
    resp = conn.getresponse()
    body = resp.read().decode("utf-8", "ignore")
    check("6MB upload rejected with clean 413 page", resp.status, expect=(413, 400, 302))
    if resp.status == 413:
        ok_page = ("File too large" in body) or ("413" in body)
        print(f"     ↳ custom 413 page rendered: {ok_page}")
finally:
    conn.close()

# server must still be perfectly alive after that
code, _ = g.get("/healthz")
check("server alive after oversized request", code, expect=200)

# ══════════════════ 10. ORDER FLOW EDGE CASES ══════════════════
print("\n📋 Order flow edge cases")
e = Client()
e.login("divya@example.com", "test123")
_, html = e.get("/orders")
nums_e = re.findall(r"/orders/(SK-\d{4}-\d{6})", html)
delivered = None
for n in nums_e:
    _, h = e.get(f"/orders/{n}")
    if "Delivered" in h and "Cancel Order" not in h:
        delivered = n
        break
if delivered:
    t = e.csrf(f"/orders/{delivered}")
    code, loc, _ = e.post(f"/orders/{delivered}/cancel", {"csrf_token": t})
    check("cancel an already-delivered order (must be refused, no crash)",
          code, expect=(302, 400))
else:
    print("  ⏭️  (no delivered order in this account)")

empty = Client()
empty.login("karthik@example.com", "test123")
t = empty.csrf("/checkout")
code, loc, body = empty.post("/checkout", {"csrf_token": t, "address_id": "1",
                                           "payment_method": "COD"})
check("checkout with empty cart → back to products", code, expect=(302, 200))

# ══════════════════ 11. UNICODE / TAMIL ══════════════════
print("\n🔤 Unicode / Tamil input")
code, _ = g.get("/products?q=" + urllib.parse.quote("சட்டை"))
check("Tamil search term", code, expect=200)
code, _ = g.get("/products?q=" + urllib.parse.quote("🔥🎧 emoji search"))
check("emoji search term", code, expect=200)

# ══════════════════ RESULT ══════════════════
print("\n" + "=" * 60)
print(f"  PASSED: {passed}   FAILED: {len(failed)}   CRASHES(500): {len(crashes)}")
if failed:
    print("\n  Failed expectations:")
    for f in failed:
        print("   -", f)
if crashes:
    print("\n  💥 CRASHES FOUND:")
    for c_ in crashes:
        print("   -", c_)
print("=" * 60)

sys.exit(1 if (failed or crashes) else 0)
