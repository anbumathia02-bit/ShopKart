"""
build_gallery.py — Builds a SELF-CONTAINED HTML demo gallery.
All screenshots are embedded as base64 data-URIs, so the file works offline
(no external images/CSS) and previews perfectly inside sandboxed iframes.

Run:  python demo/build_gallery.py
Out:  demo/gallery.html
"""
import base64
import io
import os
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
SHOTS = os.path.join(HERE, "screenshots")
OUT = os.path.join(HERE, "gallery.html")

MAX_W = 1100          # resize width for embedding
JPEG_Q = 82


def embed(filename):
    """Load screenshot, crop ultra-tall mobile pages, resize, return data-URI."""
    path = os.path.join(SHOTS, filename)
    im = Image.open(path).convert("RGB")

    # very tall pages (mobile full-page) → show top portion only
    if im.height / im.width > 3.2:
        im = im.crop((0, 0, im.width, int(im.width * 3.2)))

    if im.width > MAX_W:
        h = int(im.height * MAX_W / im.width)
        im = im.resize((MAX_W, h), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=JPEG_Q, optimize=True, progressive=True)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return f"data:image/jpeg;base64,{b64}", im.size


# ── (file, section, step-title, tamil narration, callout) ───────────────
STEPS = [
    # ---------------- CUSTOMER ----------------
    ("01-home.png", "customer", "Home Page",
     "Ithu than unga website first-la open aagum page. Hero banner, category tiles, "
     "Today's Deals, Top Rated, New Arrivals ellam automatic-ah database-la irundhu varum. "
     "Header-la search bar + cart icon + login. Category nav bar-la ellam clickable.",
     "Amazon/Meesho style grid layout — mobile-la 2 column, desktop-la 4 column aagum."),

    ("02-login.png", "customer", "Login Page",
     "Email + password login. Keezha demo accounts box irukku — test panna easy. "
     "'Remember me' option + Signup link.",
     "Security: password bcrypt-ah hash aagum, CSRF token ellam form-la irukku."),

    ("03-products.png", "customer", "Product Listing + Filters",
     "Left side-la Filters: Category, Price range (min–max), Rating. Right side-la products. "
     "Sort dropdown: Popularity / Price low-high / Rating / Newest.",
     "12 products per page + pagination. Ella filter-um URL-la save aagum — link share pannalam!"),

    ("04-search.png", "customer", "Search Working",
     "Search box-la 'shirt' nu type pannina — product name, description, seller name "
     "rendu-la search aagum. Result count + sort ellam work aagum.",
     "Try pannunga: 'earbuds', 'kitchen', 'TrendyThreads' (seller name) kooda search aagum!"),

    ("05-product-detail.png", "customer", "Product Detail Page",
     "Left: product image (or emoji fallback), stock status. Right: price, MRP, discount %, "
     "rating, seller name, description. 3 buttons: Add to Cart, Buy Now, Wishlist.",
     "Buy Now = direct-ah checkout-ku poidum. Add to Cart = AJAX (page reload aagaathu)."),

    ("06-cart.png", "customer", "Cart",
     "Namma add pannina products inga varum. Qty +/− buttons, Remove, stock warning. "
     "Right side-la price breakdown: MRP, discount, delivery charge, TOTAL.",
     "₹499-ku mela order pannina FREE delivery. Adhukku kammi na, 'Add ₹X more' nu hint varum."),

    ("07-wishlist.png", "customer", "Wishlist",
     "Heart icon click pannina product inga save aagum. Later-ah cart-ku add pannalam.",
     "Guest-a irundha, heart click pannina login page-ku poidum — login panna automatic-ah save aagum."),

    ("08-checkout.png", "customer", "Checkout",
     "3 steps: (1) Delivery Address select, (2) Payment Method, (3) Items review. "
     "COD selected by default. UPI/Card option grey-ah irukku — Phase 9-la activate aagum.",
     "Address illama na 'Add new address' link varum — checkout-il irundhu address add pannalam."),

    ("09-order-success.png", "customer", "Order Placed! 🎉",
     "Order place pannina udane: Order ID generate aagum (SK-2026-000006), stock automatic-ah "
     "kammi aagum, order tracking timeline start aagum.",
     "Order number format: SK-<year>-<6 digit>. Idhu customer-ku SMS/email-la anuppalam."),

    ("10-my-orders.png", "customer", "My Orders",
     "Customer oda ella order-um inga varum — status badge, total, items thumbnail. "
     "View Details / Track / Cancel buttons.",
     "Cancel pannina, stock automatic-ah thirumbi add aagum (inventory correct-ah irukkum)."),

    ("11-order-detail.png", "customer", "Order Detail + Tracking Timeline",
     "Order Progress tracker: Placed → Confirmed → Packed → Shipped → Out for Delivery → "
     "Delivered. Keezha full timeline with timestamps. Right side-la payment + address.",
     "Idhu than Amazon-la paakura 'Track Package' screen — same concept!"),

    ("12-my-account.png", "customer", "My Account",
     "Profile info, total orders, saved addresses count, member since. Recent orders list. "
     "Sidebar-la Orders, Addresses, Wishlist ellam.",
     "Address management: add / delete / set-default ellam inga irukku."),

    ("13-track-order.png", "customer", "Public Order Tracking 🔎",
     "Login illama kooda order track pannalam — order number type panna podhum. "
     "Idhu guest customers-ku romba useful.",
     "Real-la idhu SMS/WhatsApp-la anuppura tracking link-ah irukkum."),

    # ---------------- ADMIN ----------------
    ("14-admin-dashboard.png", "admin", "Sales Dashboard",
     "4 KPI cards: Total Revenue, Total Orders, Customers, Products. Last 7 days revenue "
     "chart (CSS bars — JS library illa). Orders by status breakdown. Recent orders table. "
     "Top selling products + ⚠️ Low stock alerts.",
     "Indha numbers ellam LIVE-ah database-la irundhu calculate aagum — real business-ku ready."),

    ("15-admin-products.png", "admin", "Product Management",
     "Ella products-um list-ah varum. Search + category filter. Price, MRP, stock inline-ah "
     "edit pannalam. Active/Hidden status. Edit / View / Deactivate buttons.",
     "Stock column-la number type panni ✓ click panna — stock update aagum. 5-ku kammi na "
     "'Low' badge varum."),

    ("16-admin-add-product.png", "admin", "Add / Edit Product + Image Upload",
     "Product name, description, price, MRP, stock, category, seller, rating. "
     "Image upload with LIVE PREVIEW. Image illama na emoji + colour fallback.",
     "Left side image upload → right side-la preview. Idhu admin-friendly design."),

    ("17-admin-orders.png", "admin", "Order Management",
     "Ella orders-um table-la. Status chips-la click panni filter pannalam "
     "(PLACED orders mattum paakkanum na). Order number search kooda irukku.",
     "Order status-ah inga irundhu update pannina, customer-oda tracking page-um udane "
     "update aagum."),

    ("18-admin-order-detail.png", "admin", "Order Detail + Status Update",
     "Order items table, status timeline, customer details, shipping address. "
     "Right side-la 'Update Status' form — status + note add pannalam.",
     "CANCELLED set pannina stock automatic-ah thirumbi add aagum. DELIVERED set pannina "
     "delivered date save aagum."),

    ("19-admin-customers.png", "admin", "Customer Management",
     "Customers list: orders count, total spent, joined date. Click panni full profile "
     "paakkalam — order history + saved addresses.",
     "Idhu CRM-ku base — yaaru top customer nu kandupidikkalam (total spent column)."),

    ("20-admin-categories.png", "admin", "Category Management",
     "Categories list with product count. Add new category (emoji icon kooda). "
     "Products irukkura category-ah delete panna mudiyaadhu — safety feature!",
     "Category icon nav bar-la automatic-ah varum."),

    # ---------------- MOBILE ----------------
    ("21-mobile-home.png", "mobile", "Mobile — Home",
     "Same website mobile-la (390px width). Header hamburger-aagum, products 2 column, "
     "search bar full width. India-la 80% traffic mobile-la irundhu varum!",
     "Bootstrap responsive grid + custom CSS media queries — separate mobile site thevai illa."),

    ("22-mobile-products.png", "mobile", "Mobile — Products",
     "Filters mobile-la side-ku poidum, products 2-column grid. Ellam tap-friendly size.",
     "Ithu than real-world-la customer 80% neram paakura view."),
]

SECTION_META = {
    "customer": ("👤", "Customer Side", "Customer website-la enna panna mudiyum — home-la irundhu order place pannum varai"),
    "admin":    ("⚙️", "Admin Panel", "Neenga (shop owner) enna paakkalaam / control pannalaam"),
    "mobile":   ("📱", "Mobile View", "Mobile-la epdi theriyum — India-ku ithu mukkiyam"),
}

# ── build ────────────────────────────────────────────────────────────────
print("Embedding screenshots…")
data = {}
for fname, *_ in STEPS:
    uri, size = embed(fname)
    data[fname] = uri
    print(f"  {fname:26} {size[0]}x{size[1]}  {len(uri)//1024} KB")

cards_html = []
current_section = None
step_no = 0

for fname, section, title, narration, callout in STEPS:
    if section != current_section:
        if current_section is not None:
            cards_html.append("</div></section>")
        current_section = section
        ico, name, sub = SECTION_META[section]
        cards_html.append(
            f'<section class="sec" id="sec-{section}">'
            f'<div class="sec-head"><span class="sec-ico">{ico}</span>'
            f'<div><h2>{name}</h2><p>{sub}</p></div></div><div class="grid">'
        )
    step_no += 1
    cards_html.append(f"""
    <article class="card">
      <div class="card-head">
        <span class="step">{step_no:02d}</span>
        <h3>{title}</h3>
      </div>
      <div class="shot"><img src="{data[fname]}" alt="{title}" loading="lazy"></div>
      <p class="narr">{narration}</p>
      <div class="callout"><b>💡</b> {callout}</div>
      <div class="file">📁 demo/screenshots/{fname}</div>
    </article>""")

cards_html.append("</div></section>")
body = "\n".join(cards_html)

HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ShopKart — Live Demo Walkthrough</title>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,"Noto Sans Tamil",Arial,sans-serif;
    background:#0f1522; color:#e8ebf3; line-height:1.6;
  }}
  .hero {{
    background:linear-gradient(135deg,#7b2ff7,#f43397 55%,#ff6b6b);
    padding:54px 24px 44px; text-align:center;
  }}
  .hero h1 {{ font-size:2.5rem; font-weight:800; letter-spacing:-.5px; }}
  .hero p {{ opacity:.94; margin-top:10px; font-size:1.05rem; }}
  .hero .pill {{
    display:inline-block; background:rgba(255,255,255,.2); border:1px solid rgba(255,255,255,.35);
    border-radius:999px; padding:6px 16px; font-size:.82rem; font-weight:600; margin-top:18px;
  }}
  .wrap {{ max-width:1180px; margin:0 auto; padding:0 20px; }}

  .quickbar {{
    display:grid; grid-template-columns:repeat(auto-fit,minmax(215px,1fr)); gap:12px;
    margin:-26px 0 34px;
  }}
  .q {{
    background:#1a2334; border:1px solid #2a3550; border-radius:14px; padding:14px 16px;
  }}
  .q .k {{ font-size:.72rem; text-transform:uppercase; letter-spacing:.08em; color:#8b95ad; font-weight:700; }}
  .q .v {{ font-size:.95rem; font-weight:700; margin-top:3px; }}
  .q code {{ background:#0f1522; padding:2px 7px; border-radius:6px; font-size:.85rem; color:#ffb3d9; }}

  .toc {{ display:flex; gap:10px; flex-wrap:wrap; margin-bottom:38px; }}
  .toc a {{
    background:#1a2334; border:1px solid #2a3550; color:#cfd6e6; text-decoration:none;
    padding:9px 18px; border-radius:999px; font-size:.88rem; font-weight:600;
  }}
  .toc a:hover {{ border-color:#f43397; color:#fff; }}

  .sec {{ margin-bottom:64px; scroll-margin-top:20px; }}
  .sec-head {{ display:flex; align-items:center; gap:16px; margin-bottom:24px;
    border-bottom:1px solid #24304a; padding-bottom:16px; }}
  .sec-ico {{ font-size:2rem; }}
  .sec-head h2 {{ font-size:1.5rem; font-weight:800; }}
  .sec-head p {{ color:#8b95ad; font-size:.88rem; }}

  .card {{
    background:#151d2e; border:1px solid #24304a; border-radius:16px;
    margin-bottom:30px; overflow:hidden;
  }}
  .card-head {{ display:flex; align-items:center; gap:13px; padding:18px 22px 12px; }}
  .step {{
    background:#f43397; color:#fff; font-weight:800; font-size:.82rem;
    width:34px; height:34px; border-radius:10px; display:flex; align-items:center;
    justify-content:center; flex:0 0 34px;
  }}
  .card-head h3 {{ font-size:1.12rem; font-weight:700; }}
  .shot {{ background:#0b101a; padding:14px 22px; }}
  .shot img {{ width:100%; display:block; border-radius:10px; border:1px solid #24304a; }}
  .narr {{ padding:16px 22px 6px; color:#c7d0e2; font-size:.94rem; }}
  .callout {{
    margin:8px 22px 16px; background:#1d2a1f; border-left:3px solid #38ef7d;
    border-radius:8px; padding:11px 15px; font-size:.87rem; color:#c9e8d2;
  }}
  .file {{ padding:0 22px 18px; color:#5f6b85; font-size:.76rem; font-family:monospace; }}

  .finish {{
    background:#151d2e; border:1px solid #24304a; border-radius:16px; padding:28px;
    margin-bottom:60px;
  }}
  .finish h2 {{ font-size:1.3rem; margin-bottom:14px; }}
  .finish ol {{ margin-left:20px; color:#c7d0e2; }}
  .finish li {{ margin-bottom:9px; font-size:.93rem; }}
  .finish code {{ background:#0f1522; padding:2px 7px; border-radius:6px; color:#ffb3d9; font-size:.86rem; }}

  footer {{ background:#0b101a; text-align:center; padding:34px 20px; color:#5f6b85; font-size:.85rem; }}
  footer b {{ color:#e8ebf3; }}

  @media (max-width:640px) {{
    .hero h1 {{ font-size:1.7rem; }}
    .card-head h3 {{ font-size:.98rem; }}
    .shot {{ padding:10px; }}
  }}
</style>
</head>
<body>

<div class="hero">
  <h1>🛒 ShopKart — Live Demo</h1>
  <p>Flask + MySQL e-commerce website — real screenshots, step by step</p>
  <div class="pill">✅ 45/45 automated tests passing · COD checkout · Admin panel included</div>
</div>

<div class="wrap">

  <div class="quickbar">
    <div class="q"><div class="k">Run panna</div><div class="v"><code>python app.py</code></div></div>
    <div class="q"><div class="k">Website</div><div class="v">localhost:5000</div></div>
    <div class="q"><div class="k">Admin login</div><div class="v"><code>admin@shopkart.com</code> / admin123</div></div>
    <div class="q"><div class="k">Customer login</div><div class="v"><code>arun@example.com</code> / test123</div></div>
  </div>

  <div class="toc">
    <a href="#sec-customer">👤 Customer Side (13 screens)</a>
    <a href="#sec-admin">⚙️ Admin Panel (7 screens)</a>
    <a href="#sec-mobile">📱 Mobile (2 screens)</a>
  </div>

  {body}

  <div class="finish">
    <h2>🚀 Ippo neenga enna pannanum?</h2>
    <ol>
      <li><b>Try pannunga:</b> <code>cd shopkart &amp;&amp; pip install -r requirements.txt &amp;&amp; python app.py</code> →
          <code>http://localhost:5000</code></li>
      <li><b>Admin-ah login pannunga</b> (<code>admin@shopkart.com</code> / <code>admin123</code>) — product add panni,
          order status update panni paarunga. Live-ah storefront-la update aagum.</li>
      <li><b>Real product images</b> upload pannunga — admin panel-la ready. Demo-la emoji fallback use panniruken.</li>
      <li><b>MySQL-ku switch pannunga</b> (production-ku) — <code>.env</code>-la <code>DATABASE_URL</code> mattum set pannunga. Code change illa.</li>
      <li><b>Next:</b> Phase 9 — Razorpay/UPI payment. Checkout page-la option already placeholder-ah irukku 💳</li>
    </ol>
  </div>

</div>

<footer>
  <b>ShopKart</b> — Flask + SQLAlchemy + Bootstrap 5 · 19 products, 6 categories, 5 demo orders seed panniruken<br>
  Screenshots: Playwright headless Chromium-ல எடுத்தது · {len(STEPS)} screens
</footer>

</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"\n✅ Gallery built → {OUT}")
print(f"   Size: {os.path.getsize(OUT)/1024/1024:.2f} MB (self-contained, offline-ready)")
