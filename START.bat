@echo off
chcp 65001 >nul
title ShopKart Store - Auto Start
cd /d "%~dp0"

echo ============================================================
echo    ShopKart Store  -  ONE CLICK START
echo    (idhu dhaan live preview-la irukkira same project)
echo ============================================================
echo.

REM ---------- 1. project check ----------
if not exist "app.py" (
    echo  [X] app.py kaanala!
    echo      Intha START.bat file-ah project ROOT folder-la vachu
    echo      double-click pannunga ^(app.py + templates + static irukkura folder^).
    echo.
    pause
    exit /b 1
)

REM ---------- 2. python check ----------
set "PY=python"
where python >nul 2>nul
if errorlevel 1 set "PY=py"
%PY% --version >nul 2>nul
if errorlevel 1 (
    echo  [X] Python install aagala / PATH-la illa!
    echo      https://www.python.org/downloads/  - install pannunga
    echo      Install screen-la "Add Python to PATH" TICK panna marakkaadheenga!
    echo.
    pause
    exit /b 1
)
echo  [1/4] Python ready:
%PY% --version
echo.

REM ---------- 3. reminder ----------
echo  [i] Munnadi oru server window run aagirundha, andha window-la Ctrl+C
echo      adichu nirtunga. Illa-na "port 5000 busy" error varum.
echo.

REM ---------- 4. packages ----------
echo  [2/4] Packages install aaguthu... ^(first time mattum 1-2 nimisham^)
%PY% -m pip install -r requirements.txt --disable-pip-version-check --quiet
echo      Done.
echo.

REM ---------- 5. browser + server ----------
echo  [3/4] Browser 5 second-la thaanae open aagum: http://127.0.0.1:5000
start "" cmd /c "ping -n 6 127.0.0.1 >nul & start http://127.0.0.1:5000"
echo  [4/4] Server start aaguthu... INTHA WINDOW-AH MOODAADHEENGA!
echo        ^(Site-ah nirutha: intha window-la Ctrl + C^)
echo.
%PY% app.py

echo.
echo  ------------------------------------------------------------
echo   Server nindru poachu. Thirumba start panna:
echo   intha START.bat file-ah marupadiyum double-click pannunga.
echo  ------------------------------------------------------------
pause
