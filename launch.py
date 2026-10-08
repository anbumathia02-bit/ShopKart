  { 
   // ============================================================
  //  ShopKart — VS Code Run/Debug config
  //
  //  F5 NU ADICHAA SITE START AAGUM! 🚀
  //
  //  Eppadi use pannuvadhu:
  //   1. Intha project folder-ah VS Code-la open pannunga
  //   2. Keyboard-la  F5  adikkunga  (illa Run menu → Start Debugging)
  //   3. Terminal-la link varum → Ctrl+Click pannunga (browser open aagum)
  //   4. Niruttha:  Shift + F5
  // ============================================================
  "version": "0.2.0",
  "configurations": [
    {
      // ─────────── MAIN CONFIG — F5 (recommended!) ───────────
      "name": "🚀 ShopKart Server (F5 — ithu dhaan!)",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/app.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "justMyCode": true,
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PORT": "5000"
      }
    },
    {
      // ─────────── No-debug version (simple run) ───────────
      "name": "▶️ ShopKart Server (debug illama, fast)",
      "type": "debugpy",
      "request": "launch",
      "program": "${workspaceFolder}/app.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "noDebug": true,
      "env": {
        "PYTHONUNBUFFERED": "1",
        "PORT": "5000"
      }
    },
    {
      // ─────────── Production style (gunicorn — Render pola) ───────────
      "name": "🏭 ShopKart production-ah (gunicorn)",
      "type": "debugpy",
      "request": "launch",
      "module": "gunicorn",
      "args": ["--preload", "--workers", "1", "--threads", "4", "-b", "0.0.0.0:5000", "wsgi:app"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "noDebug": true,
      "env": { "FLASK_DEBUG": "0" }
    }
  ]
}
