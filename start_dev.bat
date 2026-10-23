@echo off
echo ===================================================
echo Starting AI Startup Co-Founder Team (Backend + Frontend)
echo ===================================================

echo Starting FastAPI Backend on http://localhost:8000...
start "AI Co-Founder Backend" cmd /k "uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting Vite React Frontend on http://localhost:5173...
start "AI Co-Founder Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo Both services launched in separate windows!
echo - Frontend UI: http://localhost:5173
echo - Backend API: http://localhost:8000/docs
echo.
pause
