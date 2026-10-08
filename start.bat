@echo off
setlocal enabledelayedexpansion

:: If user types 'start system' or 'start', launch start_system.bat
if "%1"=="" goto launch_all
if /i "%1"=="system" goto launch_all
if /i "%1"=="backend" goto launch_backend
if /i "%1"=="frontend" goto launch_frontend

echo [USAGE]
echo   start system     - Start both Backend and Frontend
echo   start backend    - Start only FastAPI Backend
echo   start frontend   - Start only Vite Frontend
exit /b 0

:launch_all
call "%~dp0start_system.bat"
exit /b 0

:launch_backend
start "Auto-Triage Backend (FastAPI - Port 8000)" cmd /k "cd /d "%~dp0backend" && if exist venv\Scripts\activate.bat (call venv\Scripts\activate.bat) && python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000"
exit /b 0

:launch_frontend
start "Auto-Triage Frontend (React - Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"
exit /b 0
