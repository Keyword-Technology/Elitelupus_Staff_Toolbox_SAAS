# Elitelupus Staff Toolbox SaaS

A modern, enterprise-grade full-stack web application for managing staff operations for Elitelupus gaming servers. This SaaS solution replaces the original Python Tkinter desktop application with a scalable, cloud-native architecture featuring real-time synchronization, comprehensive monitoring, and role-based access control.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![Django](https://img.shields.io/badge/django-4.2+-green.svg)
![Next.js](https://img.shields.io/badge/next.js-14-black.svg)
![Docker](https://img.shields.io/badge/docker-compose-2496ED.svg)

## ✨ Key Features

### 🎮 Real-time Server Monitoring
- Live player counts via Source Query (A2S protocol)
- Active map and server name tracking
- Staff online detection and tracking
- Auto-refresh every 60 seconds
- Multi-server support (Server 1: 194.69.160.33:27083, Server 2: 193.243.190.12:27046)

### 📊 Sit & Ticket Counters
- Real-time synchronized counters across all connected clients
- WebSocket-based instant updates (no polling)
- Daily, weekly, and monthly statistics with timezone support
- Historical data tracking and analytics
- Leaderboard with competitive rankings
- Automatic reset schedules

### 📋 Template Manager
- Pre-built refund ticket templates
- Steam profile lookup integration (Steam Web API)
- Template versioning and management
- Quick copy-to-clipboard functionality

### 📜 Rules Reference System
- Comprehensive general server rules
- Job-specific rules and guidelines
- Searchable rule database
- Markdown formatting with syntax highlighting
- Categories and tags for easy navigation

### 👥 Staff Roster Management
- Google Sheets integration (Auto-sync)
- Sheet ID: `1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo`
- Multi-timezone support for LOA tracking
- Role-based hierarchy system (12 staff levels)
- Activity and performance tracking

### 🔐 Advanced Authentication
- Local username/password authentication
- Steam OpenID integration
- Discord OAuth2 integration
- JWT token-based API authentication
- Role-based access control (RBAC)
- Session management and security

### ⚙️ System Settings
- Runtime configuration management
- Dynamic settings without redeployment
- Sensitive value masking
- Category organization (General, API Keys, External Services, etc.)
- Audit trail for configuration changes

### 📱 Progressive Web App (PWA)
- Install as mobile or desktop application
- Offline capability support
- Push notifications ready
- Native app-like experience

## 🛠 Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Next.js** | 14.0.4 | React framework with App Router |
| **TypeScript** | 5.3+ | Type-safe JavaScript |
| **TailwindCSS** | 3.4+ | Utility-first CSS framework |
| **React Query** | 5.17+ | Server state management |
| **Zustand** | 4.4+ | Client state management |
| **Socket.io** | 4.6+ | WebSocket client |
| **Headless UI** | 1.7+ | Accessible UI components |
| **React Hook Form** | 7.49+ | Form validation |
| **Zod** | 3.22+ | Schema validation |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| **Django** | 4.2+ | Web framework |
| **DRF** | 3.14+ | REST API framework |
| **Django Channels** | 4.0+ | WebSocket support |
| **Daphne** | 4.0+ | ASGI server |
| **SimpleJWT** | 5.3+ | JWT authentication |
| **Celery** | 5.3+ | Task queue |
| **Celery Beat** | 2.5+ | Periodic tasks |

### Infrastructure
| Technology | Version | Purpose |
|------------|---------|---------|
| **PostgreSQL** | 15+ | Primary database |
| **Redis** | 7+ | Cache & message broker |
| **Docker** | Latest | Containerization |
| **Docker Compose** | Latest | Multi-container orchestration |
| **Nginx** | Latest | Reverse proxy |

### External Integrations
| Service | Purpose |
|---------|---------|
| **Steam Web API** | Profile lookups & OpenID auth |
| **Discord OAuth2** | Discord authentication |
| **Google Sheets API** | Staff roster sync |
| **Source Query (A2S)** | Game server monitoring |

## 🚀 Quick Start

### Prerequisites

- Docker & Docker Compose (recommended) OR:
  - Python 3.11+
  - Node.js 18+
  - PostgreSQL 15+
  - Redis 7+

### Option 1: Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/connorhess/Elitelupus_Staff_Toolbox.git
cd Elitelupus_Staff_Toolbox_SAAS

# Create environment file
cp .env.example .env

# Edit .env with your configuration
# Required: STEAM_API_KEY, DISCORD_CLIENT_ID, DISCORD_CLIENT_SECRET
# Optional: GOOGLE_SHEETS_CREDENTIALS (for roster sync)

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Run migrations (first time only)
docker-compose exec backend python manage.py migrate

# Create superuser (first time only)
docker-compose exec backend python manage.py createsuperuser

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8001
# Admin Panel: http://localhost:8001/admin/
# Nginx Proxy: http://localhost:280
```

### Option 2: Manual Development Setup

#### 1. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
# Edit .env with your database and API credentials

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Start development server (with WebSocket support)
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# In separate terminal: Start Celery worker
celery -A config worker -P solo -l info

# In separate terminal: Start Celery beat
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

#### 2. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Create environment file
cp .env.example .env.local

# Edit .env.local
# NEXT_PUBLIC_API_URL=http://localhost:8000
# NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

#### 3. Required Services

Ensure PostgreSQL and Redis are running:

```bash
# PostgreSQL (default port 5432)
# Redis (default port 6379)

# Or use Docker for just the databases
docker-compose up -d db redis
```

## 🔧 Environment Variables

### Backend Environment (.env)

```env
# Django Configuration
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this-in-production
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database Configuration
POSTGRES_DB=elitelupus
POSTGRES_USER=elitelupus
POSTGRES_PASSWORD=changeme
POSTGRES_HOST=db  # Use 'localhost' for manual setup
POSTGRES_PORT=5432

# Redis Configuration
REDIS_HOST=redis  # Use 'localhost' for manual setup
REDIS_PORT=6379

# Steam API (Required)
# Get your key from: https://steamcommunity.com/dev/apikey
STEAM_API_KEY=your-steam-api-key-here

# Discord OAuth (Required for Discord login)
# Create app at: https://discord.com/developers/applications
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret

# Frontend URL (for OAuth callbacks)
FRONTEND_URL=http://localhost:3000

# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Google Sheets Integration (Optional)
# For staff roster sync - requires service account credentials
GOOGLE_SHEETS_CREDENTIALS=/path/to/credentials.json
STAFF_ROSTER_SHEET_ID=1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo
```

### Frontend Environment (.env.local)

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# For production, use your domain:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
# NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
```

### Docker Compose Environment (.env)

Create a `.env` file in the root directory with all the above variables. Docker Compose will use these automatically.

### Getting API Keys

#### Steam API Key
1. Visit https://steamcommunity.com/dev/apikey
2. Sign in with your Steam account
3. Enter a domain name (can be localhost for dev)
4. Copy the generated key

#### Discord OAuth
1. Go to https://discord.com/developers/applications
2. Click "New Application"
3. Go to OAuth2 settings
4. Add redirect URI: `http://localhost:8000/api/auth/discord/callback/`
5. Copy Client ID and Client Secret

#### Google Sheets (Optional)
1. Create a project in Google Cloud Console
2. Enable Google Sheets API
3. Create a Service Account
4. Download credentials JSON file
5. Share your Google Sheet with the service account email

## 👥 Staff Role Hierarchy

The application uses a priority-based role system where lower numbers indicate higher authority. Each role has specific permissions and capabilities.

| Priority | Role | Color | Permissions |
|----------|------|-------|-------------|
| 0 | **SYSADMIN** | `#FF0000` | Full system access, all features |
| 10 | **Manager** | `#990000` | Staff management, all moderation |
| 20 | **Staff Manager** | `#F04000` | Staff oversight, advanced moderation |
| 30 | **Assistant Staff Manager** | `#8900F0` | Staff assistance, moderation |
| 40 | **Meta Manager** | `#8900F0` | Meta event management |
| 50 | **Event Manager** | `#8900F0` | Event coordination |
| 60 | **Senior Admin** | `#d207d3` | Advanced administration |
| 70 | **Admin** | `#FA1E8A` | Standard administration |
| 80 | **Senior Moderator** | `#15c000` | Advanced moderation |
| 90 | **Moderator** | `#4a86e8` | Standard moderation |
| 100 | **Senior Operator** | `#38761d` | Advanced support |
| 110 | **Operator** | `#93c47d` | Standard support |
| 120 | **T-Staff** | `#b6d7a8` | Trial staff (limited access) |

### Role Capabilities

- **Counter Access**: All roles can track sits and tickets
- **Template Access**: Moderator+ can access refund templates
- **Server Monitoring**: All roles can view server status
- **Rules Management**: Staff Manager+ can edit rules
- **Staff Roster**: Staff Manager+ can modify roster
- **System Settings**: Manager+ can change system settings

## 📡 API Documentation

### Authentication Endpoints

#### JWT Authentication
```http
POST /api/auth/token/
Content-Type: application/json

{
  "username": "your_username",
  "password": "your_password"
}

Response: {
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

#### Token Refresh
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "jwt_refresh_token"
}

Response: {
  "access": "new_jwt_access_token"
}
```

#### Register New User
```http
POST /api/auth/register/
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "password": "secure_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

#### OAuth Authentication
```http
GET /api/auth/steam/login/      # Redirects to Steam OpenID
GET /api/auth/discord/login/    # Redirects to Discord OAuth

# Callbacks (configured in OAuth apps)
GET /api/auth/steam/callback/
GET /api/auth/discord/callback/
```

#### Get Current User Profile
```http
GET /api/auth/profile/
Authorization: Bearer {jwt_access_token}

Response: {
  "id": 1,
  "username": "user",
  "email": "user@example.com",
  "staff_role": "Moderator",
  "discord_id": "123456789",
  "steam_id": "76561198000000000"
}
```

### Counter Endpoints

```http
# Get user's counters
GET /api/counters/
Authorization: Bearer {token}

# Update counter (increment/decrement)
POST /api/counters/update/{type}/
Authorization: Bearer {token}
Body: {
  "action": "increment",  # or "decrement"
  "amount": 1
}

# Get statistics (daily, weekly, monthly)
GET /api/counters/stats/
Authorization: Bearer {token}
Query: ?period=daily&start_date=2024-01-01&end_date=2024-01-31

# Get leaderboard
GET /api/counters/leaderboard/
Authorization: Bearer {token}
Query: ?period=weekly&type=sit&limit=10
```

### Server Endpoints

```http
# List all configured servers
GET /api/servers/

# Get live server status
GET /api/servers/status/

# Get specific server
GET /api/servers/{id}/

# Force refresh server status
POST /api/servers/refresh/
Authorization: Bearer {token}
```

### Staff Roster Endpoints

```http
# Get full staff roster
GET /api/staff/roster/
Authorization: Bearer {token}

# Trigger Google Sheets sync
POST /api/staff/sync/
Authorization: Bearer {token}

# Get staff member details
GET /api/staff/{id}/
Authorization: Bearer {token}

# Update staff member
PATCH /api/staff/{id}/
Authorization: Bearer {token}
Body: {
  "role": "Admin",
  "is_active": true
}
```

### Template Endpoints

```http
# List refund templates
GET /api/templates/refunds/
Authorization: Bearer {token}

# Create template
POST /api/templates/refunds/
Authorization: Bearer {token}
Body: {
  "name": "Standard Refund",
  "content": "Template content here"
}

# Steam profile lookup
POST /api/templates/steam-lookup/
Authorization: Bearer {token}
Body: {
  "steam_id": "76561198000000000"
}

Response: {
  "personaname": "PlayerName",
  "profileurl": "https://steamcommunity.com/...",
  "avatar": "https://...",
  "timecreated": 1234567890
}
```

### Rules Endpoints

```http
# Get all rule categories
GET /api/rules/categories/

# Get general server rules
GET /api/rules/general/

# Get job-specific rules
GET /api/rules/job-actions/
Query: ?job=Police

# Search rules
GET /api/rules/search/
Query: ?q=nlr&category=general
```

### System Settings Endpoints

```http
# List all settings (admin only)
GET /api/system-settings/
Authorization: Bearer {token}

# Get specific setting
GET /api/system-settings/{key}/
Authorization: Bearer {token}

# Update setting (admin only)
PATCH /api/system-settings/{key}/
Authorization: Bearer {token}
Body: {
  "value": "new_value"
}
```

## 🔌 WebSocket Endpoints

The application uses Socket.io for real-time communication. All WebSocket connections require authentication.

### Connection

```javascript
import io from 'socket.io-client';

const socket = io('ws://localhost:8000', {
  auth: {
    token: 'your_jwt_token'
  },
  transports: ['websocket']
});
```

### Counter Updates Channel

**Namespace**: `/ws/counters/`

**Client → Server Messages**:
```javascript
// Increment counter
socket.emit('counter_update', {
  type: 'counter_update',
  counter_type: 'sit',  // or 'ticket'
  action: 'increment',
  amount: 1
});

// Decrement counter
socket.emit('counter_update', {
  type: 'counter_update',
  counter_type: 'sit',
  action: 'decrement',
  amount: 1
});
```

**Server → Client Messages**:
```javascript
// Receive counter updates
socket.on('counter_update', (data) => {
  console.log(data);
  // {
  //   type: 'counter_update',
  //   counter_type: 'sit',
  //   count: 123,
  //   user_id: 1,
  //   username: 'John',
  //   timestamp: '2024-01-01T12:00:00Z'
  // }
});
```

### Server Status Channel

**Namespace**: `/ws/servers/`

**Server → Client Messages**:
```javascript
// Receive server status updates (every 60 seconds)
socket.on('server_update', (data) => {
  console.log(data);
  // {
  //   type: 'server_update',
  //   server_id: 1,
  //   status: {
  //     name: 'Elitelupus Server 1',
  //     map: 'rp_downtown_v4c_v2',
  //     player_count: 64,
  //     max_players: 128,
  //     staff_online: ['Admin1', 'Moderator2'],
  //     online: true
  //   }
  // }
});
```

### Error Handling

```javascript
socket.on('error', (error) => {
  console.error('WebSocket error:', error);
});

socket.on('connect_error', (error) => {
  console.error('Connection error:', error);
});
```

## 🚢 Production Deployment

### Docker Compose Production

```bash
# Build all images
docker-compose build

# Start all services in production mode
docker-compose up -d

# Services included:
# - PostgreSQL (port 5433)
# - Redis (port 6379)
# - Django Backend (port 8001)
# - Next.js Frontend (port 3000)
# - Nginx Reverse Proxy (port 280)
# - Celery Worker
# - Celery Beat (scheduled tasks)

# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend
docker-compose logs -f celery

# Check service health
docker-compose ps
```

### Manual Production Deployment

#### Backend (Django)

```bash
# Set production environment variables
export DEBUG=False
export SECRET_KEY='your-production-secret-key'
export ALLOWED_HOSTS='yourdomain.com,www.yourdomain.com'

# Install production dependencies
pip install -r requirements.txt gunicorn

# Collect static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Start with Gunicorn + Daphne
# HTTP/REST API
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4

# WebSocket support (separate process)
daphne -b 0.0.0.0 -p 8001 config.asgi:application

# Or use Daphne for both (simpler)
daphne -b 0.0.0.0 -p 8000 config.asgi:application --workers 4
```

#### Frontend (Next.js)

```bash
# Build production bundle
npm run build

# Start production server
npm start

# Or use PM2 for process management
npm install -g pm2
pm2 start npm --name "elitelupus-frontend" -- start
pm2 save
pm2 startup
```

#### Background Workers

```bash
# Start Celery worker
celery -A config worker -l INFO --concurrency=4

# Start Celery beat (scheduled tasks)
celery -A config beat -l INFO --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Use supervisord or systemd to manage these processes
```

### SSL/TLS Configuration

#### Nginx SSL Setup

1. Obtain SSL certificates (Let's Encrypt, etc.)
2. Place certificates in `nginx/ssl/`:
   - `fullchain.pem` - Certificate chain
   - `privkey.pem` - Private key

3. Update `nginx/nginx.conf`:
```nginx
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/fullchain.pem;
    ssl_certificate_key /etc/nginx/ssl/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Backend API
    location /api/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /ws/ {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### Environment-Specific Configuration

Create separate `.env` files:
- `.env.development`
- `.env.staging`
- `.env.production`

```bash
# Load specific environment
docker-compose --env-file .env.production up -d
```

### Health Checks

The Docker Compose configuration includes health checks for:
- PostgreSQL: `pg_isready`
- Redis: `redis-cli ping`

Monitor these with:
```bash
docker-compose ps
```

### Backup Strategy

#### Database Backups

```bash
# Backup PostgreSQL
docker-compose exec db pg_dump -U elitelupus elitelupus > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T db psql -U elitelupus elitelupus < backup_20240101.sql

# Automated daily backups (cron)
0 2 * * * cd /path/to/project && docker-compose exec db pg_dump -U elitelupus elitelupus | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

#### Volume Backups

```bash
# Backup all volumes
docker run --rm -v elitelupus_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```

### Monitoring & Logging

#### View Application Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend

# Follow specific patterns
docker-compose logs -f | grep ERROR
```

#### Django Logging

Configure in `backend/config/settings.py`:
```python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/django/app.log',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
        },
    },
}
```

## 📁 Project Structure

```
Elitelupus_Staff_Toolbox_SAAS/
├── backend/                          # Django Backend
│   ├── config/                       # Project Configuration
│   │   ├── settings.py               # Django settings
│   │   ├── urls.py                   # Root URL configuration
│   │   ├── asgi.py                   # ASGI config (WebSockets)
│   │   ├── wsgi.py                   # WSGI config
│   │   └── celery.py                 # Celery configuration
│   ├── apps/                         # Django Applications
│   │   ├── accounts/                 # User Authentication & Management
│   │   │   ├── models.py             # Custom user model
│   │   │   ├── serializers.py        # DRF serializers
│   │   │   ├── views.py              # Auth views (JWT, OAuth)
│   │   │   └── urls.py               # Auth endpoints
│   │   ├── counters/                 # Sit/Ticket Counters
│   │   │   ├── models.py             # Counter models
│   │   │   ├── consumers.py          # WebSocket consumers
│   │   │   ├── views.py              # Counter API views
│   │   │   └── tasks.py              # Celery tasks (reset, stats)
│   │   ├── servers/                  # Server Monitoring
│   │   │   ├── models.py             # Server configurations
│   │   │   ├── services.py           # A2S query logic
│   │   │   ├── consumers.py          # WebSocket updates
│   │   │   └── tasks.py              # Periodic status checks
│   │   ├── staff/                    # Staff Management
│   │   │   ├── models.py             # Staff roster model
│   │   │   ├── services.py           # Google Sheets integration
│   │   │   ├── views.py              # Roster API
│   │   │   └── tasks.py              # Auto-sync tasks
│   │   ├── templates_manager/        # Refund Templates
│   │   │   ├── models.py             # Template model
│   │   │   ├── views.py              # Template CRUD
│   │   │   └── services.py           # Steam API integration
│   │   ├── rules/                    # Server Rules
│   │   │   ├── models.py             # Rules categories & content
│   │   │   ├── views.py              # Rules API
│   │   │   └── parsers.py            # Markdown parsing
│   │   └── system_settings/          # System Configuration
│   │       ├── models.py             # Settings model
│   │       ├── views.py              # Settings API
│   │       └── middleware.py         # Dynamic config loading
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend container
│   └── manage.py                     # Django CLI
│
├── frontend/                         # Next.js Frontend
│   ├── src/
│   │   ├── app/                      # App Router (Next.js 14)
│   │   │   ├── (auth)/               # Auth pages
│   │   │   │   ├── login/            # Login page
│   │   │   │   └── register/         # Registration
│   │   │   ├── dashboard/            # Main dashboard
│   │   │   ├── counters/             # Counter management
│   │   │   ├── servers/              # Server monitoring
│   │   │   ├── staff/                # Staff roster
│   │   │   ├── templates/            # Template manager
│   │   │   ├── rules/                # Rules reference
│   │   │   ├── settings/             # User settings
│   │   │   ├── layout.tsx            # Root layout
│   │   │   └── page.tsx              # Home page
│   │   ├── components/               # React Components
│   │   │   ├── auth/                 # Auth components
│   │   │   ├── counters/             # Counter widgets
│   │   │   ├── layout/               # Layout components
│   │   │   ├── servers/              # Server cards
│   │   │   ├── ui/                   # Reusable UI components
│   │   │   └── common/               # Shared components
│   │   ├── contexts/                 # React Contexts
│   │   │   ├── AuthContext.tsx       # Authentication state
│   │   │   ├── WebSocketContext.tsx  # WebSocket connection
│   │   │   └── ThemeContext.tsx      # Theme management
│   │   ├── lib/                      # Utilities
│   │   │   ├── api.ts                # API client (axios)
│   │   │   ├── websocket.ts          # WebSocket client
│   │   │   ├── auth.ts               # Auth helpers
│   │   │   └── utils.ts              # General utilities
│   │   └── styles/                   # Global styles
│   ├── public/                       # Static Assets
│   │   ├── icons/                    # PWA icons
│   │   ├── manifest.json             # PWA manifest
│   │   └── sw.js                     # Service worker
│   ├── package.json                  # Node dependencies
│   ├── tsconfig.json                 # TypeScript config
│   ├── tailwind.config.js            # Tailwind config
│   ├── next.config.js                # Next.js config
│   └── Dockerfile                    # Frontend container
│
├── nginx/                            # Nginx Reverse Proxy
│   ├── nginx.conf                    # Production config
│   ├── nginx.dev.conf                # Development config
│   ├── ssl/                          # SSL certificates
│   └── Dockerfile                    # Nginx container
│
├── scripts/                          # Utility Scripts
│   ├── dev-start.sh                  # Dev startup (Linux/Mac)
│   └── dev-start.bat                 # Dev startup (Windows)
│
├── docker-compose.yml                # Docker orchestration
├── .env.example                      # Environment template
├── .gitignore                        # Git ignore rules
├── LICENSE                           # MIT License
└── README.md                         # This file
```

### Key Directories Explained

- **`backend/apps/`**: Each Django app is self-contained with models, views, serializers, and URLs
- **`frontend/src/app/`**: Next.js 14 App Router with file-based routing
- **`frontend/src/components/`**: Organized by feature for maintainability
- **`frontend/src/contexts/`**: Global state management (auth, WebSocket)
- **`nginx/`**: Reverse proxy configuration for production deployment

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





