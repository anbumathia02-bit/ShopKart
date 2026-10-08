#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
doctor.py - ShopKart Project Doctor
===================================
Error vandha (TemplateNotFound, file kaanala, etc.) intha script-ah
run pannunga. Idhu check pannum:

  1) Neenga RIGHT folder-la irukkingala? (app.py irukkura folder)
  2) Zip extract pannumbodhu files DOUBLE-NESTED aagiirukka?
     Example: Shopkart\shopkart\templates\index.html  <- ithu dhaan #1 problem!
  3) Ethavathu file MISS aagiirukka? (templates/index.html etc.)

RUN PANNA:
    python doctor.py          -> check mattum (report)
    python doctor.py --fix    -> check + AUTO-FIX

--fix enna pannum?
  * Double-nested files-ah oru level mela (correct place-ku) move pannum
  * Missing files-ah unga Desktop / Downloads / project folder-la
    irukkura zip-la irundhu (shopkart-render-ready.zip) restore pannum
  * Product photos-um illaama na, zip-la irundhu restore pannum

Idhu unga database (instance/shopkart.db) ah thodaave thodaadhu. Safe.
"""

from __future__ import annotations

import shutil
import sys
import zipfile
from pathlib import Path

# Windows console-la emoji print crash aagakoodadhu
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ROOT = Path.cwd()
FIX = "--fix" in sys.argv

SKIP_DIRS = {"__pycache__", ".venv", "venv", ".git", ".pytest_cache",
             "node_modules", "instance"}

# ---------------------------------------------------------------
#  Project-la MUST-irukkanum-ngura files list
# ---------------------------------------------------------------
REQUIRED = {
    "Root files": [
        "app.py", "wsgi.py", "config.py", "extensions.py", "models.py",
        "cart_utils.py", "utils.py", "seed.py", "requirements.txt",
    ],
    "blueprints/": [
        "blueprints/__init__.py", "blueprints/main.py", "blueprints/auth.py",
        "blueprints/cart.py", "blueprints/orders.py", "blueprints/admin.py",
    ],
    "templates/": [
        "templates/base.html", "templates/_macros.html", "templates/index.html",
        "templates/index_simple.html", "templates/products.html",
        "templates/product_detail.html", "templates/cart.html",
        "templates/checkout.html", "templates/wishlist.html",
        "templates/orders.html", "templates/order_detail.html",
        "templates/order_success.html", "templates/track.html",
        "templates/admin/base.html", "templates/admin/dashboard.html",
        "templates/admin/products.html", "templates/admin/product_form.html",
        "templates/admin/categories.html", "templates/admin/orders.html",
        "templates/admin/order_detail.html", "templates/admin/customers.html",
        "templates/admin/customer_detail.html",
        "templates/auth/login.html", "templates/auth/signup.html",
        "templates/auth/account.html", "templates/auth/addresses.html",
        "templates/errors/403.html", "templates/errors/404.html",
        "templates/errors/500.html", "templates/errors/generic.html",
    ],
    "static/": [
        "static/css/sk.css", "static/js/sk.js",
        "static/vendor/bootstrap.min.css",
        "static/vendor/bootstrap-icons.css",
        "static/vendor/bootstrap.bundle.min.js",
        "static/vendor/fonts/bootstrap-icons.woff2",
    ],
}

ALL_REQUIRED = [f for group in REQUIRED.values() for f in group]

BAR = "=" * 62


def head(msg):
    print()
    print(BAR)
    print(f"  {msg}")
    print(BAR)


# ---------------------------------------------------------------
#  Helper: nested folder-ah merge pannum
# ---------------------------------------------------------------
def merge_nested(nested: Path) -> int:
    """Move shopkart/shopkart/** files -> shopkart/** (overwrite old)."""
    moved = 0
    for src in sorted(nested.rglob("*")):
        if any(part in SKIP_DIRS for part in src.relative_to(nested).parts):
            continue
        if src.is_dir():
            continue
        rel = src.relative_to(nested)
        dest = ROOT / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        if dest.exists():
            try:
                dest.unlink()
            except OSError:
                continue
        try:
            shutil.move(str(src), str(dest))
            moved += 1
        except OSError:
            pass
    # leftover empty dirs remove (bottom-up)
    for c in sorted([p for p in nested.rglob("*") if p.is_dir()],
                    key=lambda p: len(p.parts), reverse=True):
        try:
            c.rmdir()
        except OSError:
            pass
    try:
        nested.rmdir()
    except OSError:
        pass
    return moved


# ---------------------------------------------------------------
#  Helper: zip kandupidikkiradhu + restore
# ---------------------------------------------------------------
def find_zip():
    bases = [ROOT, ROOT.parent, Path.home() / "Desktop",
             Path.home() / "Downloads", Path.home()]
    seen = set()
    for base in bases:
        try:
            if not base or not base.exists() or base in seen:
                continue
            seen.add(base)
            for z in sorted(base.glob("*.zip")):
                try:
                    with zipfile.ZipFile(z) as zf:
                        names = zf.namelist()
                    if (any(n.endswith("/app.py") for n in names)
                            and any(n.endswith("/templates/base.html") for n in names)):
                        return z
                except Exception:
                    continue
        except Exception:
            continue
    return None


def restore_from_zip(zpath: Path, missing):
    """Zip-la irundhu missing files-ah copy pannum."""
    restored, failed = 0, []
    with zipfile.ZipFile(zpath) as zf:
        names = zf.namelist()
        for rel in missing:
            tail = "/" + rel.replace("\\", "/")
            member = None
            for n in names:
                if n == rel or n.endswith(tail):
                    member = n
                    break
            if not member:
                failed.append(rel)
                continue
            dest = ROOT / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(zf.read(member))
            restored += 1
    return restored, failed


# ===============================================================
#  START
# ===============================================================
head("ShopKart Doctor - Project Health Check")
print(f"  Folder : {ROOT}")
print(f"  Mode   : {'CHECK + FIX' if FIX else 'CHECK only'}   (fix venum-na: python doctor.py --fix)")

problems = 0

# ---------------------------------------------------------------
# 1) Right folder check
# ---------------------------------------------------------------
has_app = (ROOT / "app.py").exists()

if not has_app:
    problems += 1
    print()
    print("  [X] app.py intha folder-la ILLA!")
    # Parent-la irukka?
    parent_app = (ROOT.parent / "app.py").exists()
    sub_roots = []
    try:
        for d in sorted(ROOT.iterdir()):
            if d.is_dir() and (d / "app.py").exists():
                sub_roots.append(d)
    except Exception:
        pass

    if parent_app:
        print()
        print("  >>> Puriyudhu: Neenga project-ku ULLA (nested) folder-la irukkinga.")
        print(f"      Correct root idhu dhaan -> {ROOT.parent}")
        print()
        print("  FIX: intha command run pannunga:")
        print("       cd ..")
        print("       python doctor.py --fix")
    elif sub_roots:
        print()
        print("  >>> Puriyudhu: Neenga project root-ku VELIYE-la irukkinga.")
        for d in sub_roots:
            print(f"      Correct root idhu dhaan -> {d}")
        print()
        print("  FIX: intha command run pannunga:")
        print(f'       cd "{sub_roots[0].name}"')
        print("       python doctor.py --fix")
    else:
        print()
        print("  >>> app.py engayum illa. Full project-ah zip-la irundhu")
        print("      thirumba extract panni copy pannunga.")
    print()
    print(BAR)
    sys.exit(1)

print("  [OK] Right folder - app.py irukku")

# ---------------------------------------------------------------
# 2) Double-nested folder check  (Shopkart\shopkart\...)
# ---------------------------------------------------------------
nested = ROOT / "shopkart"
nested_app = nested / "app.py"

if nested_app.exists():
    problems += 1
    print()
    print("  [X] DOUBLE-NESTED folder kandupidichiten!")
    print(f"      {nested}")
    print("      Zip-ah extract pannumbodhu oru folder JASTI aagirukku.")
    print("      Flask paakkura edam: " + str(ROOT / "templates") + "\\index.html")
    print("      Files irukkura edam:  " + str(nested / "templates") + "\\index.html")
    if FIX:
        n = merge_nested(nested)
        print()
        print(f"  [FIXED] {n} files-ah correct place-ku move panniten!")
        print(f"          '{nested.name}' nested folder-ah remove panniten.")
        # re-check
        if nested_app.exists():
            print("  [!] Nested folder innum irukku - files lock aagirukkum.")
            print("      Server (python app.py) & VS Code close panni, thirumba run pannunga.")
        else:
            problems -= 1
    else:
        print()
        print("  FIX: python doctor.py --fix   <-- ithu run pannunga!")
else:
    print("  [OK] Nested folder illa - structure correct")

# ---------------------------------------------------------------
# 3) Missing files check
# ---------------------------------------------------------------
missing = [f for f in ALL_REQUIRED if not (ROOT / f).exists()]

if missing:
    problems += 1
    print()
    print(f"  [X] {len(missing)} file(s) MISSING:")
    for f in missing[:15]:
        print(f"        - {f}")
    if len(missing) > 15:
        print(f"        ... innum {len(missing) - 15}")

    if FIX:
        z = find_zip()
        if z:
            print()
            print(f"  [FIX] Zip kandupidichiten: {z}")
            restored, failed = restore_from_zip(z, missing)
            print(f"        {restored} file(s) restore panniten!")
            for f in failed[:8]:
                print(f"        [!] {f} - zip-la illa")
            missing = [f for f in missing if not (ROOT / f).exists()]
            if not missing:
                problems -= 1
                print("        [OK] Ippo ellam irukku!")
        else:
            print()
            print("  [!] Zip kaanala (Desktop/Downloads-la illa).")
            print("      Manual: shopkart-render-ready.zip -> extract ->")
            print("      shopkart\\templates\\index.html file-ah unga")
            print("      templates\\ folder-la copy pannunga.")
else:
    print("  [OK] Ella 46 required files-um irukku")

# ---------------------------------------------------------------
# 4) Product photos
# ---------------------------------------------------------------
photo_dir = ROOT / "static" / "uploads" / "products"
photos = sorted(photo_dir.glob("*.jpg")) if photo_dir.exists() else []
if len(photos) >= 15:
    print(f"  [OK] Product photos: {len(photos)} jpg")
elif photos:
    print(f"  [!]  Product photos: {len(photos)} mattum (19 irukkanum)")
    problems += 1
else:
    print("  [!]  Product photos: 0 (photos illa - cards-la emoji kaattum)")
    problems += 1

# Photos missing + FIX -> zip-la irundhu restore
if len(photos) < 15 and FIX:
    z = find_zip()
    if z:
        restored = 0
        with zipfile.ZipFile(z) as zf:
            for n in zf.namelist():
                if "/static/uploads/products/" in n and n.endswith(".jpg"):
                    dest = ROOT / "static" / "uploads" / "products" / n.split("/")[-1]
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    dest.write_bytes(zf.read(n))
                    restored += 1
        if restored:
            print(f"  [FIXED] {restored} product photos-ah zip-la irundhu restore panniten!")
            problems -= 1
    elif photos:
        pass
    else:
        print("       (Zip kaanala - photos venum-na zip-la irundhu manual copy)")

# ---------------------------------------------------------------
# 5) Database
# ---------------------------------------------------------------
db = ROOT / "instance" / "shopkart.db"
if db.exists():
    kb = db.stat().st_size // 1024
    print(f"  [OK] Database: instance/shopkart.db ({kb} KB) - unga data safe!")
else:
    print("  [i]  Database illa - first run-la auto-create aagum (OK)")

# ---------------------------------------------------------------
# FINAL VERDICT
# ---------------------------------------------------------------
head("RESULT")
if problems == 0:
    print("  [PERFECT] Unga project 100% correct-ah irukku!")
    print()
    print("  Site run panna:")
    print("       python app.py")
    print("       Browser: http://127.0.0.1:5000")
    print()
    print("  Error INNUM vandha - server vera folder-la irundhu run")
    print("  pandringala nu paarunga (terminal-la prompt path check).")
else:
    print(f"  {problems} problem(s) irukku (mela paarunga)")
    print()
    print("  --> Intha command run pannunga (auto-fix):")
    print("       python doctor.py --fix")
print(BAR)

