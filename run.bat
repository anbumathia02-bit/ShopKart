@echo off
REM ============================================================
REM  ShopKart — WINDOWS one-click runner
REM  Intha file-ah DOUBLE CLICK pannunga. Adhu:
REM    1. Python check pannum
REM    2. venv (virtual environment) create pannum
REM    3. requirements install pannum
REM    4. Site start pannum  ->  http://127.0.0.1:5000
REM ============================================================
title ShopKart Server
cd /d "%~dp0"

echo.
echo ========================================
echo   ShopKart launcher
echo ========================================
echo.

REM --- Python check ---
where python >nul 2>nul
if errorlevel 1 (
  echo [X] Python illa!  https://www.python.org/downloads/ la irundhu
  echo     Python install pannunga.  Install pandrapo
  echo     "Add Python to PATH" checkbox-ah TICK pannunga!
  echo.
  pause
  exit /b 1
)

REM --- venv create (once mattum) ---
if not exist "venv\Scripts\activate.bat" (
  echo [1/3] venv create panren...
  python -m venv venv
  if errorlevel 1 (
    echo [X] venv create aagala. Python install-ah check pannunga.
    pause
    exit /b 1
  )
) else (
  echo [1/3] venv already irukku  [OK]
)

REM --- activate + install ---
call venv\Scripts\activate.bat
echo [2/3] Packages install panren (first time konjam neram aagum)...
python -m pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
if errorlevel 1 (
  echo [X] Package install fail. Internet connection-ah check pannunga.
  pause
  exit /b 1
)

REM --- run ---
echo [3/3] Server start panren...
echo.
echo    Browser-la open pannunga:   http://127.0.0.1:5000
echo.
echo    Admin login:    admin@shopkart.com  /  admin123
echo    Customer:       arun@example.com    /  test123
echo.
echo    Niruttha: intha window-la  Ctrl + C
echo ========================================
echo.

python app.py

echo.
echo Server nindrathu. Vera ethavathu problem-na screenshot edunga.
pause
