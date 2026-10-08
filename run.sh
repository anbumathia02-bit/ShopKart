#!/usr/bin/env bash
# ============================================================
#  ShopKart — Mac / Linux one-click runner
#  Run panna:   bash run.sh      (illa  ./run.sh)
#
#  Idhu automatic-ah:
#    1. Python check pannum
#    2. venv create pannum
#    3. requirements install pannum
#    4. Site start pannum  ->  http://127.0.0.1:5000
# ============================================================
set -e
cd "$(dirname "$0")"

echo
echo "========================================"
echo "  ShopKart launcher"
echo "========================================"
echo

# --- Python check ---
if ! command -v python3 >/dev/null 2>&1; then
  echo "[X] python3 illa! Install pannunga:  https://www.python.org/downloads/"
  exit 1
fi

# --- venv create (once mattum) ---
if [ ! -f "venv/bin/activate" ]; then
  echo "[1/3] venv create panren..."
  python3 -m venv venv
else
  echo "[1/3] venv already irukku  [OK]"
fi

# --- activate + install ---
# shellcheck disable=SC1091
source venv/bin/activate
echo "[2/3] Packages install panren (first time konjam neram aagum)..."
python3 -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt

# --- run ---
echo "[3/3] Server start panren..."
echo
echo "   Browser-la open pannunga:   http://127.0.0.1:5000"
echo
echo "   Admin login:    admin@shopkart.com  /  admin123"
echo "   Customer:       arun@example.com    /  test123"
echo
echo "   Niruttha:  Ctrl + C"
echo "========================================"
echo

python3 app.py
