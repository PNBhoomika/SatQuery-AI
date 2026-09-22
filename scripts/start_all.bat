@echo off
REM =====================================================================
REM OrbitIntel / SatQuery-AI - Single-Click Startup Script (Windows)
REM SIH 2026 Problem Statement 26227
REM =====================================================================
SETLOCAL ENABLEDELAYEDEXPANSION

SET PROJECT_ROOT=%~dp0..
SET BACKEND_DIR=%PROJECT_ROOT%\backend
SET FRONTEND_DIR=%PROJECT_ROOT%\frontend

echo.
echo ====================================================================
echo  ORBITINTEL / SatQuery-AI  --  SIH 2026 Demo Launcher
echo ====================================================================
echo.

REM ── Step 1: Check Python ──────────────────────────────────────────────
python --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [ERROR] Python not found. Please install Python 3.10+
    pause & exit /b 1
)
echo [OK] Python found.

REM ── Step 2: Check Node ───────────────────────────────────────────────
node --version >nul 2>&1
IF ERRORLEVEL 1 (
    echo [WARN] Node.js not found. Frontend will not start.
    SET NO_FRONTEND=1
) ELSE (
    echo [OK] Node.js found.
    SET NO_FRONTEND=0
)

REM ── Step 3: Install Python dependencies if needed ────────────────────
echo.
echo [INFO] Checking backend Python dependencies...
pip show fastapi >nul 2>&1
IF ERRORLEVEL 1 (
    echo [INFO] Installing backend requirements...
    pip install -r "%BACKEND_DIR%\requirements.txt" --quiet
    IF ERRORLEVEL 1 (
        echo [ERROR] Failed to install Python requirements.
        pause & exit /b 1
    )
)
echo [OK] Backend dependencies ready.

REM ── Step 4: Install npm deps if needed ───────────────────────────────
IF "%NO_FRONTEND%"=="0" (
    IF NOT EXIST "%FRONTEND_DIR%\node_modules" (
        echo [INFO] Installing frontend npm packages...
        cd /d "%FRONTEND_DIR%"
        npm install --silent
        IF ERRORLEVEL 1 (
            echo [ERROR] npm install failed.
            SET NO_FRONTEND=1
        )
    ) ELSE (
        echo [OK] Frontend node_modules already present.
    )
)

REM ── Step 5: Launch Backend ────────────────────────────────────────────
echo.
echo [INFO] Starting FastAPI backend on http://127.0.0.1:8000 ...
cd /d "%BACKEND_DIR%"
start "SatQuery-AI Backend" cmd /k "python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload"
timeout /t 3 >nul

REM ── Step 6: Launch Frontend ───────────────────────────────────────────
IF "%NO_FRONTEND%"=="0" (
    echo [INFO] Starting Vite dev server on http://localhost:5173 ...
    cd /d "%FRONTEND_DIR%"
    start "SatQuery-AI Frontend" cmd /k "npm run dev"
    timeout /t 4 >nul
    echo [OK] Frontend launching...
)

REM ── Step 7: Open browser ─────────────────────────────────────────────
echo.
echo [INFO] Opening browser in 5 seconds...
timeout /t 5 >nul
start http://localhost:5173

echo.
echo ====================================================================
echo  SatQuery-AI is RUNNING
echo    Backend API:   http://127.0.0.1:8000
echo    API Docs:      http://127.0.0.1:8000/docs
echo    Frontend:      http://localhost:5173
echo ====================================================================
echo  Press any key to exit this launcher (services keep running)
echo ====================================================================
pause >nul
