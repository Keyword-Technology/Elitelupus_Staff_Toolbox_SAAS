#!/bin/bash
# Development startup script for Elitelupus Staff Toolbox

echo "🚀 Starting Elitelupus Staff Toolbox Development Environment..."
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop first."
    exit 1
fi

# Start the development environment
echo "📦 Starting Docker containers..."
docker-compose up -d db redis

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 5

# Check if backend dependencies are installed
if [ ! -d "backend/venv" ]; then
    echo "📚 Creating Python virtual environment..."
    cd backend
    python -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    cd ..
else
    echo "✅ Backend dependencies already installed"
fi

# Check if frontend dependencies are installed
if [ ! -d "frontend/node_modules" ]; then
    echo "📚 Installing frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "✅ Frontend dependencies already installed"
fi

echo ""
echo "✅ Development environment ready!"
echo ""
echo "To start the services, run these commands in separate terminals:"
echo ""
echo "1. Backend (Django):"
echo "   cd backend"
echo "   source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "   python manage.py migrate"
echo "   daphne -b 0.0.0.0 -p 8000 config.asgi:application"
echo ""
echo "2. Frontend (Next.js):"
echo "   cd frontend"
echo "   npm run dev"
echo ""
echo "3. Celery Worker (optional):"
echo "   cd backend"
echo "   source venv/bin/activate"
echo "   celery -A config worker -l INFO"
echo ""
echo "The app will be available at:"
echo "   - Frontend: http://localhost:3000"
echo "   - Backend API: http://localhost:8000"
echo ""
