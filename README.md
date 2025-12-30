# Elitelupus Staff Toolbox SaaS

A modern, full-stack web application for managing staff operations for Elitelupus gaming servers. This replaces the original Python Tkinter desktop application with a scalable SaaS solution.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![Django](https://img.shields.io/badge/django-4.2-green.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)

## Features

- 🎮 **Real-time Server Monitoring** - Track player counts, maps, and staff online
- 📊 **Sit & Ticket Counters** - Real-time synchronized counters with WebSocket support
- 🏆 **Leaderboard** - Competitive rankings for staff activity
- 📋 **Template Maker** - Refund templates with Steam profile lookup
- 📜 **Rules Reference** - Searchable general and job-specific rules
- 👥 **Staff Roster** - Synced with Google Sheets
- 🔐 **Multi-Auth** - Local accounts, Steam, and Discord OAuth
- 📱 **PWA Support** - Install as mobile/desktop app

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Frontend** | Next.js 14, TypeScript, TailwindCSS |
| **Backend** | Django 4.2, Django REST Framework |
| **Real-time** | Django Channels, WebSockets |
| **Database** | PostgreSQL |
| **Cache** | Redis |
| **Auth** | JWT, Steam OpenID, Discord OAuth2 |
| **Container** | Docker, Docker Compose |

## Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/connorhess/Elitelupus_Staff_Toolbox.git
cd Elitelupus_Staff_Toolbox

# Copy environment files
cp .env.example .env
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local

# Edit .env with your configuration
# (Steam API key, Discord credentials, etc.)

# Start all services
docker-compose up --build

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Admin Panel: http://localhost:8000/admin/
```

### Manual Development Setup

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server (with WebSocket support)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.example .env.local

# Start development server
npm run dev
```

## Environment Variables

### Backend (.env)

| Variable | Description | Example |
|----------|-------------|---------|
| `DJANGO_SECRET_KEY` | Django secret key | Generate a random key |
| `DEBUG` | Debug mode | `True` for development |
| `POSTGRES_*` | Database credentials | See `.env.example` |
| `REDIS_HOST` | Redis hostname | `redis` or `localhost` |
| `STEAM_API_KEY` | Steam Web API key | Get from Steam |
| `DISCORD_CLIENT_ID` | Discord OAuth app ID | Get from Discord |
| `DISCORD_CLIENT_SECRET` | Discord OAuth secret | Get from Discord |
| `GOOGLE_SHEETS_ID` | Staff roster sheet ID | `1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo` |

### Frontend (.env.local)

| Variable | Description | Example |
|----------|-------------|---------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | `http://localhost:8000` |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL | `ws://localhost:8000` |

## Staff Role Hierarchy

Roles are ordered by priority (lower = higher authority):

| Priority | Role |
|----------|------|
| 0 | SYSADMIN |
| 10 | Manager |
| 20 | Staff Manager |
| 30 | Assistant Staff Manager |
| 40 | Meta Manager |
| 50 | Event Manager |
| 60 | Senior Admin |
| 70 | Admin |
| 80 | Senior Moderator |
| 90 | Moderator |
| 100 | Senior Operator |
| 110 | Operator |
| 120 | T-Staff |

## API Endpoints

### Authentication
- `POST /api/auth/token/` - Login (returns JWT)
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/token/refresh/` - Refresh JWT
- `GET /api/auth/profile/` - Get current user

### Counters
- `GET /api/counters/` - Get counters
- `POST /api/counters/update/{type}/` - Update counter
- `GET /api/counters/stats/` - Get statistics
- `GET /api/counters/leaderboard/` - Get leaderboard

### Servers
- `GET /api/servers/` - List servers
- `GET /api/servers/status/` - Live status
- `POST /api/servers/refresh/` - Force refresh

### Staff
- `GET /api/staff/roster/` - Staff roster
- `POST /api/staff/sync/` - Trigger Google Sheets sync

### Templates
- `GET /api/templates/refunds/` - List templates
- `POST /api/templates/steam-lookup/` - Steam profile lookup

### Rules
- `GET /api/rules/categories/` - Rule categories
- `GET /api/rules/search/` - Search rules

## WebSocket Endpoints

- `ws://host/ws/counters/` - Real-time counter updates
- `ws://host/ws/servers/` - Real-time server status

## Production Deployment

```bash
# Start with production profile
docker-compose --profile production up -d

# This includes:
# - Nginx reverse proxy with SSL
# - Celery workers for background tasks
# - Celery beat for scheduled tasks
```

### SSL Configuration

Place your SSL certificates in `nginx/ssl/`:
- `fullchain.pem` - Full certificate chain
- `privkey.pem` - Private key

## Project Structure

```
Elitelupus_Staff_Toolbox_SAAS/
├── backend/                    # Django backend
│   ├── config/                 # Project configuration
│   ├── apps/                   # Django applications
│   │   ├── accounts/           # Authentication
│   │   ├── counters/           # Sit/Ticket counters
│   │   ├── servers/            # Server monitoring
│   │   ├── staff/              # Staff management
│   │   ├── templates_manager/  # Refund templates
│   │   └── rules/              # Server rules
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/                # App Router pages
│   │   ├── components/         # React components
│   │   ├── contexts/           # Auth & WebSocket
│   │   └── lib/                # API client
│   ├── package.json
│   └── Dockerfile
├── nginx/                      # Nginx configuration
├── docker-compose.yml          # Docker orchestration
└── .env.example                # Environment template
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, contact Connor on Discord or open an issue on GitHub.





