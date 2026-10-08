"""
capture_screenshots.py — Takes real screenshots of the running app.

Usage: python blueprints/capture_screenshots.py
(server must be running on :5000)
"""

import os

from playwright.sync_api import sync_playwright


BASE = os.environ.get("BASE_URL", "http://127.0.0.1:5000")

OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "screenshots"
)

os.makedirs(OUT, exist_ok=True)

CUSTOMER = ("arun@example.com", "test123")
ADMIN = ("admin@shopkart.com", "admin123")


def shot(page, name, full=False, wait=700):
    page.wait_for_timeout(wait)
    page.screenshot(
        path=os.path.join(OUT, name),
        full_page=full
    )
    print("  📸", name)


def login(page, email, password):
    """Login and VERIFY it actually worked."""

    page.goto(f"{BASE}/login")

    page.fill('input[name="email"]', email)
    page.fill('input[name="password"]', password)

    page.locator('main button[type="submit"]').first.click()

    page.wait_for_load_state("networkidle")

    if "/login" in page.url:
        raise RuntimeError(
            f"LOGIN FAILED for {email} — still on {page.url}"
        )

    print(f"  🔓 logged in as {email}")


with sync_playwright() as p:

    browser = p.chromium.launch()

    # ══════════════════ CUSTOMER (desktop) ══════════════════

    ctx = browser.new_context(
        viewport={"width": 1500, "height": 950}
    )

    page = ctx.new_page()

    print("👤 Customer flow…")

    page.goto(BASE)
    shot(page, "01-home.png", full=True, wait=1000)

    page.goto(f"{BASE}/login")
    shot(page, "02-login.png")

    login(page, *CUSTOMER)

    page.goto(f"{BASE}/products")
    shot(page, "03-products.png", wait=900)

    page.goto(f"{BASE}/products?q=shirt&sort=plow")
    shot(page, "04-search.png", wait=900)

    page.goto(f"{BASE}/product/5")
    shot(page, "05-product-detail.png", wait=900)

    # Add to cart (AJAX)

    page.locator(
        'form[data-ajax-cart] button[type="submit"]'
    ).first.click()

    page.wait_for_timeout(900)

    page.goto(f"{BASE}/product/12")

    page.locator(
        'form[data-ajax-cart] button[type="submit"]'
    ).first.click()

    page.wait_for_timeout(700)

    # Wishlist one product

    page.goto(f"{BASE}/product/7")

    page.locator("[data-wish]").first.click()

    page.wait_for_timeout(700)

    page.goto(f"{BASE}/cart/")
    shot(page, "06-cart.png", wait=800)

    page.goto(f"{BASE}/wishlist")
    shot(page, "07-wishlist.png", wait=700)

    page.goto(f"{BASE}/checkout")
    shot(page, "08-checkout.png", wait=800)

    # Place the order (COD)

    page.click(
        'button[type="submit"]:has-text("Place Order")'
    )

    page.wait_for_load_state("networkidle")

    shot(
        page,
        "09-order-success.png",
        full=True,
        wait=900
    )

    order_url = page.url
    order_number = order_url.rstrip("/").split("/")[-1]

    page.goto(f"{BASE}/orders")
    shot(
        page,
        "10-my-orders.png",
        full=True,
        wait=800
    )

    page.goto(f"{BASE}/orders/{order_number}")
    shot(
        page,
        "11-order-detail.png",
        full=True,
        wait=800
    )

    page.goto(f"{BASE}/account")
    shot(
        page,
        "12-my-account.png",
        full=True,
        wait=700
    )

    ctx.close()

    # ══════════════════ GUEST TRACKING ══════════════════

    print("🔎 Guest tracking…")

    gctx = browser.new_context(
        viewport={"width": 1500, "height": 950}
    )

    gp = gctx.new_page()

    gp.goto(f"{BASE}/track?order={order_number}")

    shot(
        gp,
        "13-track-order.png",
        wait=800
    )

    gctx.close()

    # ══════════════════ ADMIN ══════════════════

    print("⚙️ Admin flow…")

    actx = browser.new_context(
        viewport={"width": 1500, "height": 950}
    )

    ap = actx.new_page()

    login(ap, *ADMIN)

    ap.goto(f"{BASE}/admin/")
    shot(
        ap,
        "14-admin-dashboard.png",
        full=True,
        wait=1200
    )

    ap.goto(f"{BASE}/admin/products")
    shot(
        ap,
        "15-admin-products.png",
        full=True,
        wait=800
    )

    ap.goto(f"{BASE}/admin/products/new")
    shot(
        ap,
        "16-admin-add-product.png",
        full=True,
        wait=800
    )

    ap.goto(f"{BASE}/admin/orders")
    shot(
        ap,
        "17-admin-orders.png",
        full=True,
        wait=800
    )

    ap.goto(f"{BASE}/admin/orders/1")
    shot(
        ap,
        "18-admin-order-detail.png",
        full=True,
        wait=800
    )

    ap.goto(f"{BASE}/admin/customers")
    shot(
        ap,
        "19-admin-customers.png",
        full=True,
        wait=800
    )

    ap.goto(f"{BASE}/admin/categories")
    shot(
        ap,
        "20-admin-categories.png",
        wait=700
    )

    actx.close()

    # ══════════════════ MOBILE ══════════════════

    print("📱 Mobile view…")

    mctx = browser.new_context(
        viewport={"width": 390, "height": 844},
        device_scale_factor=2,
        is_mobile=True,
        has_touch=True
    )

    mp = mctx.new_page()

    mp.goto(BASE)
    shot(
        mp,
        "21-mobile-home.png",
        full=True,
        wait=900
    )

    mp.goto(f"{BASE}/products")
    shot(
        mp,
        "22-mobile-products.png",
        full=True,
        wait=900
    )

    mctx.close()

    browser.close()


print(f"\n✅ Screenshots saved to {OUT}")
print(f"   Order placed during demo: {order_number}")