"""
add_product_images.py — product photos + demo-data cleanup helper 🖼️🧹
======================================================================
Enna pannum? RENDU velai:

  1) 🖼️ PHOTOS LINK
     static/uploads/products/ folder-la irukkura .jpg files-ah paakkum.
     File peru == product "slug" (example: men-s-cotton-casual-shirt-slim-fit.jpg)
     Adha DB-la `image` column-la update pannum → photos cards-la varum!

  2) 🧹 JUNK CLEANUP
     Test scripts (smoke_test / edge_cases) create panna test products-ah
     ("QA Neckband...", "Malware Upload Test") site-la irundhu remove pannum.
     Order-la use aagirundha delete pannaadhu — "hide" mattum pannum (safe).

Eppo run pannanum? — ORU VAATI mattum:
        python "add_product_images.py"

  (Project root-la irundhu — app.py irukkura folder-la dhaan)

Note:
  • Idempotent — ethana vaati run pannaalum problem illa ✅
  • Re-seed pannaalum (python seed.py) photos automatically link aagum ✅
  • File illaadha product-ku emoji placeholder-dhaan kaattum (app crash aagaadhu) ✅
"""
from pathlib import Path

from app import app
from extensions import db
from models import Product, OrderItem

FOLDER = Path(__file__).resolve().parent / "static" / "uploads" / "products"


def clean_junk():
    """Test-script artifacts-ah remove pannum (order-la irundha hide mattum)."""
    junk = Product.query.filter(
        db.or_(Product.name.like("QA %"), Product.name.like("%Malware Upload Test%"))
    ).all()
    removed = hidden = 0
    for p in junk:
        if OrderItem.query.filter_by(product_id=p.id).count() == 0:
            db.session.delete(p)
            removed += 1
        else:
            p.is_active = False       # order history-la irukku — delete aagaadhu!
            hidden += 1
    db.session.commit()
    return removed, hidden


def link_photos():
    """Folder-la irukkura photos-ah products-oda link pannum."""
    photos = {p.stem: p.name for p in FOLDER.glob("*.jpg")}
    linked = already = 0
    for prod in Product.query.all():
        fname = photos.get(prod.slug)
        if not fname:
            continue
        if prod.image == fname:
            already += 1
        else:
            prod.image = fname
            linked += 1
    db.session.commit()
    return linked, already, len(photos)


def main():
    print()
    print("=" * 56)
    print("  🖼️  ShopKart — photos link + junk cleanup")
    print("=" * 56)

    with app.app_context():
        # ---- 1) junk cleanup ----
        removed, hidden = clean_junk()
        if removed or hidden:
            print(f"  🧹 Junk cleanup : {removed} test-product(s) delete, {hidden} hide panniten")
        else:
            print("  🧹 Junk cleanup : clean-ah irukku ✅ (test products illa)")

        # ---- 2) photo linking ----
        if not any(FOLDER.glob("*.jpg")):
            print("  ❌ static/uploads/products/ la .jpg files illa!")
            print("     First new zip-la irundhu photos-ah antha folder-la copy pannunga.")
            return

        linked, already, n_files = link_photos()
        total = Product.query.count()
        with_photo = Product.query.filter(Product.image.isnot(None)).count()

        print(f"  🖼️  Photos link  : {linked} newly linked, {already} already irundhuchu")
        print(f"     Folder-la      : {n_files} jpg files")
        print(f"     Database-la    : {with_photo}/{total} products-ku photo ✅")

    print()
    print("  ▶️  Ippo site-ah open pannunga:  http://127.0.0.1:5000")
    print("=" * 56)
    print()


if __name__ == "__main__":
    main()
