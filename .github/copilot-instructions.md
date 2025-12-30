# Elitelupus Staff Toolbox - Copilot Instructions

## Project Overview

This is a full-stack SaaS web application for managing staff operations for Elitelupus gaming servers. It replaces the original Python Tkinter desktop application with a modern web-based solution.

### Tech Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Frontend**: Next.js 14 with TypeScript and TailwindCSS
- **Database**: PostgreSQL
- **Cache/Message Broker**: Redis
- **Real-time**: Django Channels (WebSockets)
- **Authentication**: JWT (SimpleJWT), Steam OpenID, Discord OAuth2
- **Containerization**: Docker & Docker Compose
- **PWA**: Progressive Web App support via next-pwa

## Project Structure

```
Elitelupus_Staff_Toolbox_SAAS/
├── backend/                    # Django backend
│   ├── config/                 # Django project configuration
│   │   ├── settings.py         # Main settings file
│   │   ├── urls.py             # Root URL configuration
│   │   ├── asgi.py             # ASGI config for WebSockets
│   │   └── wsgi.py             # WSGI config
│   ├── apps/                   # Django applications
│   │   ├── accounts/           # User authentication & management
│   │   ├── staff/              # Staff roster & Google Sheets sync
│   │   ├── counters/           # Sit/Ticket counters with real-time
│   │   ├── servers/            # Game server status monitoring
│   │   ├── templates_manager/  # Refund templates & Steam lookup
│   │   └── rules/              # Server rules management
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend Docker image
│   └── manage.py               # Django management script
├── frontend/                   # Next.js frontend
│   ├── src/
│   │   ├── app/                # Next.js App Router pages
│   │   ├── components/         # React components
│   │   ├── contexts/           # React contexts (Auth, WebSocket)
│   │   └── lib/                # Utilities and API client
│   ├── public/                 # Static assets & PWA manifest
│   ├── package.json            # Node.js dependencies
│   └── Dockerfile              # Frontend Docker image
├── docker-compose.yml          # Docker orchestration
└── .github/
    └── copilot-instructions.md # This file
```

## Key Features

### 1. User Authentication
- Local username/password authentication
- Steam OpenID integration
- Discord OAuth2 integration
- JWT token-based API authentication
- Role-based access control

### 2. Staff Role Hierarchy
Roles are ordered by priority (lower = higher authority):

| Role | Priority | Color |
|------|----------|-------|
| SYSADMIN | 0 | #FF0000 |
| Manager | 10 | #990000 |
| Staff Manager | 20 | #F04000 |
| Assistant Staff Manager | 30 | #8900F0 |
| Meta Manager | 40 | #8900F0 |
| Event Manager | 50 | #8900F0 |
| Senior Admin | 60 | #d207d3 |
| Admin | 70 | #FA1E8A |
| Senior Moderator | 80 | #15c000 |
| Moderator | 90 | #4a86e8 |
| Senior Operator | 100 | #38761d |
| Operator | 110 | #93c47d |
| T-Staff | 120 | #b6d7a8 |

### 3. Sit/Ticket Counters
- Real-time synchronized counters across all devices
- WebSocket-based instant updates
- Daily, weekly, and monthly statistics
- Leaderboard functionality

### 4. Server Status Monitoring
- Live player counts via Source Query (a2s)
- Map information and server name
- Staff online tracking
- Auto-refresh every 60 seconds

### 5. Staff Roster
- Google Sheets integration
- Automatic sync with sheet ID: `1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo`
- Multi-timezone support for LOA/activity tracking

### 6. Templates
- Refund ticket templates
- Steam profile lookup integration
- Customizable template fields

## Development Commands

### Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run with Daphne (for WebSockets)
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

### Docker

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Reset database
docker-compose down -v
```

## Environment Variables

### Backend (.env)

```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgres://user:password@localhost:5432/elitelupus

# Redis
REDIS_URL=redis://localhost:6379/0

# Steam API
STEAM_API_KEY=your-steam-api-key

# Discord OAuth
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret

# Google Sheets
GOOGLE_SHEETS_CREDENTIALS=path/to/credentials.json
STAFF_ROSTER_SHEET_ID=1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo

# Frontend URL (for OAuth callbacks)
FRONTEND_URL=http://localhost:3000
```

### Frontend (.env.local)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (returns JWT)
- `POST /api/auth/token/refresh/` - Refresh JWT
- `GET /api/auth/me/` - Get current user
- `GET /auth/login/steam/` - Steam OAuth redirect
- `GET /auth/login/discord/` - Discord OAuth redirect

### Counters
- `GET /api/counters/` - Get user's counters
- `POST /api/counters/update/` - Update counter
- `GET /api/counters/stats/` - Get statistics
- `GET /api/counters/leaderboard/` - Get leaderboard

### Servers
- `GET /api/servers/` - List all servers
- `GET /api/servers/status/` - Get live status

### Staff
- `GET /api/staff/roster/` - Get staff roster
- `POST /api/staff/sync/` - Trigger Google Sheets sync

### Templates
- `GET /api/templates/` - List templates
- `POST /api/templates/` - Create template
- `GET /api/templates/steam-lookup/` - Steam profile lookup

### Rules
- `GET /api/rules/` - List rules categories
- `GET /api/rules/general/` - Get general rules
- `GET /api/rules/job-actions/` - Get job-specific rules

## WebSocket Channels

### Counter Updates
- Endpoint: `ws://host/ws/counters/`
- Messages:
  - Send: `{"type": "counter_update", "counter_type": "sit|ticket", "action": "increment|decrement", "amount": 1}`
  - Receive: `{"type": "counter_update", "counter_type": "sit|ticket", "count": 123, "user_id": 1}`

### Server Status
- Endpoint: `ws://host/ws/servers/`
- Messages:
  - Receive: `{"type": "server_update", "server_id": 1, "status": {...}}`

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints where appropriate
- Docstrings for all public methods
- Django model fields should have `verbose_name`

### TypeScript (Frontend)
- Use strict TypeScript
- Prefer functional components with hooks
- Use TailwindCSS for styling
- Keep components small and focused

### General
- Keep commits atomic and well-described
- Write meaningful variable and function names
- Comment complex logic
- Handle errors gracefully

## Game Server Configuration

The application monitors these Garry's Mod servers:

| Server | IP | Port |
|--------|-----|------|
| Server 1 | 194.69.160.33 | 27083 |
| Server 2 | 193.243.190.12 | 27046 |

## Troubleshooting

### WebSocket Connection Issues
- Ensure Redis is running
- Check ASGI server is started (Daphne/Uvicorn)
- Verify WebSocket URL in frontend config

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL format
- Run migrations: `python manage.py migrate`

### OAuth Issues
- Verify callback URLs match configuration
- Check API keys/secrets are correct
- Ensure HTTPS in production

### Counter Not Syncing
- Check WebSocket connection status
- Verify user is authenticated
- Check browser console for errors

## Deployment Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Generate new `SECRET_KEY`
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up SSL/TLS certificates
- [ ] Configure proper CORS settings
- [ ] Set up database backups
- [ ] Configure logging
- [ ] Set up monitoring/alerting
- [ ] Test WebSocket connections
- [ ] Verify OAuth callback URLs
