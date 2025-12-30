@echo off
REM Development startup script for Elitelupus Staff Toolbox (Windows)

echo 🚀 Starting Elitelupus Staff Toolbox Development Environment...
echo.

REM Check if Docker is running
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not running. Please start Docker Desktop first.
    exit /b 1
)

REM Start the development environment
echo 📦 Starting Docker containers (PostgreSQL and Redis)...
docker-compose up -d db redis

REM Wait for database to be ready
echo ⏳ Waiting for database to be ready...
timeout /t 5 /nobreak >nul

REM Check if backend dependencies are installed
if not exist "backend\venv" (
    echo 📚 Creating Python virtual environment...
    cd backend
    python -m venv venv
    call venv\Scripts\activate
    pip install -r requirements.txt
    cd ..
) else (
    echo ✅ Backend dependencies already installed
)

REM Check if frontend dependencies are installed
if not exist "frontend\node_modules" (
    echo 📚 Installing frontend dependencies...
    cd frontend
    npm install
    cd ..
) else (
    echo ✅ Frontend dependencies already installed
)

echo.
echo ✅ Development environment ready!
echo.
echo To start the services, run these commands in separate terminals:
echo.
echo 1. Backend (Django):
echo    cd backend
echo    venv\Scripts\activate
echo    python manage.py migrate
echo    daphne -b 0.0.0.0 -p 8000 config.asgi:application
echo.
echo 2. Frontend (Next.js):
echo    cd frontend
echo    npm run dev
echo.
echo 3. Celery Worker (optional):
echo    cd backend
echo    venv\Scripts\activate
echo    celery -A config worker -l INFO
echo.
echo The app will be available at:
echo    - Frontend: http://localhost:3000
echo    - Backend API: http://localhost:8000
echo.
