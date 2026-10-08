@echo off
setlocal enabledelayedexpansion

title Auto-Triage AI System Launcher

echo ========================================================
echo          AUTO-TRIAGE AI SYSTEM - FULL STARTUP
echo ========================================================
echo.

set "ROOT_DIR=%~dp0"
set "BACKEND_DIR=%ROOT_DIR%backend"
set "FRONTEND_DIR=%ROOT_DIR%frontend"

:: ------------------------------------------------------------------
:: 1. Launch FastAPI Backend
:: ------------------------------------------------------------------
echo [1/2] Launching Backend (FastAPI)...

if not exist "%BACKEND_DIR%" (
    echo [ERROR] Backend folder not found at: %BACKEND_DIR%
    pause
    exit /b 1
)

start "Auto-Triage Backend (FastAPI - Port 8000)" cmd /k "cd /d "%BACKEND_DIR%" && echo Starting FastAPI Backend on http://localhost:8000 ... && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"

:: ------------------------------------------------------------------
:: 2. Launch Vite React Frontend
:: ------------------------------------------------------------------
echo [2/2] Launching Frontend (Vite / React)...

if not exist "%FRONTEND_DIR%" (
    echo [ERROR] Frontend folder not found at: %FRONTEND_DIR%
    pause
    exit /b 1
)

start "Auto-Triage Frontend (React - Port 5173)" cmd /k "cd /d "%FRONTEND_DIR%" && echo Starting Vite Frontend on http://localhost:5173 ... && npm run dev"

:: ------------------------------------------------------------------
:: Summary & URLs
:: ------------------------------------------------------------------
echo.
echo ========================================================
echo  All services have been launched in dedicated windows!
echo ========================================================
echo.
echo   * Backend API:       http://localhost:8000
echo   * Interactive Docs:  http://localhost:8000/docs
echo   * Frontend Web App:  http://localhost:5173
echo.
echo  Keep the opened command windows running while working.
echo ========================================================
echo.
