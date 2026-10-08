@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

echo.
echo ============================================================
echo   ShopKart - FIX NOW   (single file - one double-click!)
echo   Zip thedum - Extract pannum - Verify pannum - Link pannum
echo ============================================================
echo.

REM ---------- 1) Project folder kandupidikkiradhu ----------
set "PROJ="
if exist "%~dp0app.py" set "PROJ=%~dp0"
if not defined PROJ if exist "C:\Users\UZER\Desktop\Shopkart\app.py" set "PROJ=C:\Users\UZER\Desktop\Shopkart"

if not defined PROJ (
    echo [X] ShopKart project folder kaanala!
    echo     Intha file-ah unga Shopkart folder-la ^(app.py irukkura
    echo     folder-la^) vachu double-click pannunga.
    goto :end
)
if "%PROJ:~-1%"=="\" set "PROJ=%PROJ:~0,-1%"
echo [OK] Project: %PROJ%
echo.

REM ---------- 2) Zip-ah ella edathulayum thedal ----------
set "ZIP="
for %%D in ("%PROJ%" "%USERPROFILE%\Desktop" "%USERPROFILE%\Downloads" "%USERPROFILE%\OneDrive\Desktop" "%USERPROFILE%\OneDrive\Downloads") do (
    if not defined ZIP if exist "%%~D\shopkart-render-ready.zip" set "ZIP=%%~D\shopkart-render-ready.zip"
)
if not defined ZIP (
    for %%D in ("%USERPROFILE%\Desktop" "%USERPROFILE%\Downloads") do (
        if not defined ZIP if exist "%%~D\shopkart-render-ready (1).zip" set "ZIP=%%~D\shopkart-render-ready (1).zip"
    )
)

if not defined ZIP (
    echo [X] shopkart-render-ready.zip kaanala!
    echo.
    echo     PANNA VENDIYADHU:
    echo     1^) Mela chat-la irundhu zip-ah DOWNLOAD pannunga
    echo        ^(Download button click - peru type panna thevai illa^)
    echo     2^) Adhu default-ah Downloads folder-la poidum
    echo     3^) Intha FIX_NOW.bat file-ah thirumba double-click pannunga
    echo.
    echo     Zip enge irukku nu paakka intha command type pannunga:
    echo         dir "%%USERPROFILE%%\Downloads\*.zip"
    goto :end
)

for %%F in ("%ZIP%") do set "ZSIZE=%%~zF"
echo [OK] Zip kandupidichiten: %ZIP%
echo      Size: %ZSIZE% bytes   ^(2,410,000+ irukkanum^)

if %ZSIZE% LSS 2000000 (
    echo.
    echo [X] PROBLEM: Zip size rombo chinna - download incomplete!
    echo     Mela chat-la irundhu THIRUMBA download pannunga, appuram
    echo     intha file-ah double-click pannunga.
    goto :end
)
echo.

REM ---------- 3) Unblock (Windows block remove) ----------
powershell -NoProfile -Command "Unblock-File -LiteralPath '%ZIP%'" >nul 2>&1

REM ---------- 4) Extract (PowerShell native - 100%% reliable) ----------
echo --- Zip-ah extract panren (ella file-um fix aagum)...
powershell -NoProfile -Command "Expand-Archive -LiteralPath '%ZIP%' -DestinationPath '%PROJ%' -Force"
if errorlevel 1 (
    echo [X] Extract fail aachu! Manually try pannunga:
    echo     Zip right-click -^> Extract All -^> %PROJ% -^> Replace files
    goto :end
)
echo [OK] Extract mudinjadhu - ella files-um correct-ah vandhuduchu!
echo.

REM ---------- 5) Python kandupidi + verify + link ----------
set "PY="
if exist "%PROJ%\.venv\Scripts\python.exe" set "PY=%PROJ%\.venv\Scripts\python.exe"
if not defined PY if exist "%PROJ%\venv\Scripts\python.exe" set "PY=%PROJ%\venv\Scripts\python.exe"
if not defined PY (
    where python >nul 2>&1 && set "PY=python"
)

cd /d "%PROJ%"
if defined PY (
    echo --- Static files verify panren (check_static.py)...
    "%PY%" check_static.py
    echo.
    echo --- Photos-ah database-la link panren...
    "%PY%" add_product_images.py
) else (
    echo [i] Python kaanala - appuram manualla run pannunga:
    echo      python check_static.py
    echo      python add_product_images.py
)

echo.
echo ============================================================
echo   ELLAM MUDINJADHU!
echo.
echo   IPPO PANNUNGA:
echo     1. Server odalaina:  python app.py
echo     2. Browser-la:       Ctrl + F5  (hard refresh!)
echo     3. Full design + photos varum!
echo ============================================================

:end
echo.
pause
