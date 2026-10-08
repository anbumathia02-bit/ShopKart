"""
wsgi.py — Production entry point
================================
Local:      gunicorn --preload -b 0.0.0.0:8000 wsgi:app
Render:     start command = gunicorn --preload --workers 1 --threads 4 --timeout 60 -b 0.0.0.0:$PORT wsgi:app

On boot it also makes sure the database tables exist and the demo data is
seeded — so a fresh deploy works immediately with zero manual steps.
"""
import os

from app import create_app, ensure_ready

app = create_app()
ensure_ready(app)          # idempotent: create_all + seed only when empty

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
