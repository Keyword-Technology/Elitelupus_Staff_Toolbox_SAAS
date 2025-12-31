# Elitelupus Staff Toolbox - GitHub Copilot Instructions

## Project Overview

This is an enterprise-grade full-stack SaaS web application designed for managing staff operations for Elitelupus gaming servers. It replaces the original Python Tkinter desktop application with a modern, scalable, cloud-native architecture featuring real-time synchronization, comprehensive monitoring, and role-based access control.

### Primary Use Cases

1. **Staff Activity Tracking**: Real-time sit and ticket counters with leaderboards
2. **Server Monitoring**: Live game server status via Source Query (A2S protocol)
3. **Staff Management**: Google Sheets-integrated roster with role hierarchy
4. **Template System**: Refund templates with Steam profile lookups
5. **Rules Reference**: Searchable server rules database
6. **System Configuration**: Runtime configuration without redeployment

### Tech Stack

#### Backend
- **Framework**: Django 4.2+ with Django REST Framework
- **Real-time**: Django Channels 4.0+ (WebSockets via Socket.io)
- **ASGI Server**: Daphne 4.0+
- **Authentication**: JWT (SimpleJWT), Steam OpenID, Discord OAuth2
- **Task Queue**: Celery 5.3+ with Celery Beat
- **API Documentation**: drf-spectacular 0.27+

#### Frontend
- **Framework**: Next.js 14 with App Router
- **Language**: TypeScript 5.3+
- **Styling**: TailwindCSS 3.4+
- **State Management**: Zustand 4.4+ (client), React Query 5.17+ (server)
- **WebSocket**: Socket.io-client 4.6+
- **Forms**: React Hook Form 7.49+ with Zod 3.22+ validation
- **UI Components**: Headless UI 1.7+, Heroicons 2.1+

#### Infrastructure
- **Database**: PostgreSQL 15+
- **Cache/Broker**: Redis 7+
- **Reverse Proxy**: Nginx (production)
- **Containerization**: Docker & Docker Compose
- **PWA**: next-pwa 5.6+

#### External Integrations
- **Game Servers**: Source Query (python-a2s) - Garry's Mod servers
- **Steam API**: Profile lookups and OpenID authentication
- **Discord API**: OAuth2 authentication
- **Google Sheets API**: Staff roster synchronization (Sheet ID: 1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo)

## Critical Development Rules

### Backend: ALWAYS Activate Virtual Environment

**CRITICAL**: Before running ANY Django management command or Python script in the backend, you MUST activate the virtual environment first.

**Windows (PowerShell)**:
```powershell
Set-Location 'c:\Users\hessc\OneDrive\Documents\GitHub\Elitelupus_Staff_Toolbox_SAAS\backend'
.\venv\Scripts\Activate.ps1
python manage.py <command>
```

**Unix/Linux/Mac**:
```bash
cd backend
source venv/bin/activate
python manage.py <command>
```

**Commands that REQUIRE venv activation**:
- `python manage.py makemigrations`
- `python manage.py migrate`
- `python manage.py createsuperuser`
- `python manage.py shell`
- `python manage.py runserver`
- `celery -A config worker`
- `celery -A config beat`
- ANY Python script execution in backend/

**How to activate venv in terminal commands**:
```powershell
# Always use this pattern on Windows:
Set-Location 'c:\Users\hessc\OneDrive\Documents\GitHub\Elitelupus_Staff_Toolbox_SAAS\backend'; .\venv\Scripts\Activate.ps1; python manage.py makemigrations
```

### Frontend: Pre-Completion Error Check

**CRITICAL**: Before completing any task that involves frontend changes, you MUST check for TypeScript/build errors.

**Error Check Command (Windows)**:
```powershell
Set-Location 'c:\Users\hessc\OneDrive\Documents\GitHub\Elitelupus_Staff_Toolbox_SAAS\frontend'; npx tsc --noEmit --incremental false
```

**Error Check Command (Unix/Linux/Mac)**:
```bash
cd frontend && npx tsc --noEmit --incremental false
```

**Workflow**:
1. Make frontend changes
2. Run TypeScript check: `npx tsc --noEmit --incremental false`
3. If errors found: Fix them immediately
4. Re-run check until clean
5. Only then complete the task

**Why this check**:
- Fast (no build, just type checking)
- Doesn't affect dev server
- Catches compilation errors before deployment
- Prevents broken production builds

**Do NOT use**:
- `npm run build` (too slow)
- `npm run dev` (interferes with dev server)
- Just use: `npx tsc --noEmit --incremental false`

## Project Structure

```
Elitelupus_Staff_Toolbox_SAAS/
├── backend/                          # Django Backend
│   ├── config/                       # Project Configuration
│   │   ├── settings.py               # Django settings (database, cache, channels, etc.)
│   │   ├── urls.py                   # Root URL patterns
│   │   ├── asgi.py                   # ASGI config for WebSocket support
│   │   ├── wsgi.py                   # WSGI config for HTTP
│   │   └── celery.py                 # Celery task queue configuration
│   ├── apps/                         # Django Applications
│   │   ├── accounts/                 # User Authentication & Management
│   │   │   ├── models.py             # Custom User model with staff roles
│   │   │   ├── serializers.py        # User, registration, profile serializers
│   │   │   ├── views.py              # Auth views (JWT, OAuth callbacks)
│   │   │   └── urls.py               # Auth endpoints
│   │   ├── counters/                 # Sit/Ticket Counter System
│   │   │   ├── models.py             # Counter, CounterHistory models
│   │   │   ├── consumers.py          # WebSocket consumers for real-time updates
│   │   │   ├── views.py              # Counter API (stats, leaderboard)
│   │   │   ├── tasks.py              # Celery tasks (daily reset, aggregation)
│   │   │   └── routing.py            # WebSocket URL routing
│   │   ├── servers/                  # Game Server Monitoring
│   │   │   ├── models.py             # GameServer model (IP, port, config)
│   │   │   ├── services.py           # A2S query logic (python-a2s)
│   │   │   ├── consumers.py          # WebSocket for live server updates
│   │   │   ├── views.py              # Server status API
│   │   │   └── tasks.py              # Periodic server status checks
│   │   ├── staff/                    # Staff Roster Management
│   │   │   ├── models.py             # StaffMember model with role hierarchy
│   │   │   ├── services.py           # Google Sheets integration (gspread)
│   │   │   ├── views.py              # Roster CRUD API
│   │   │   └── tasks.py              # Automated roster sync tasks
│   │   ├── templates_manager/        # Refund Template System
│   │   │   ├── models.py             # RefundTemplate model
│   │   │   ├── views.py              # Template CRUD + Steam lookup
│   │   │   └── services.py           # Steam Web API integration
│   │   ├── rules/                    # Server Rules Reference
│   │   │   ├── models.py             # RuleCategory, Rule models
│   │   │   ├── views.py              # Rules API with search
│   │   │   └── parsers.py            # Markdown parsing with syntax highlighting
│   │   └── system_settings/          # Runtime Configuration
│   │       ├── models.py             # SystemSetting model (key-value store)
│   │       ├── views.py              # Settings API (admin only)
│   │       ├── serializers.py        # Settings serializers with masking
│   │       └── middleware.py         # Dynamic config loading
│   ├── requirements.txt              # Python dependencies
│   ├── Dockerfile                    # Backend container definition
│   └── manage.py                     # Django management CLI
│
├── frontend/                         # Next.js Frontend
│   ├── src/
│   │   ├── app/                      # App Router (Next.js 14)
│   │   │   ├── (auth)/               # Auth route group
│   │   │   │   ├── login/            # Login page with OAuth buttons
│   │   │   │   └── register/         # User registration
│   │   │   ├── dashboard/            # Main dashboard (counters, stats)
│   │   │   ├── counters/             # Counter management page
│   │   │   ├── servers/              # Server monitoring page
│   │   │   ├── staff/                # Staff roster page
│   │   │   ├── templates/            # Template manager page
│   │   │   ├── rules/                # Rules reference page
│   │   │   ├── settings/             # User/system settings
│   │   │   ├── layout.tsx            # Root layout with navigation
│   │   │   ├── page.tsx              # Home/landing page
│   │   │   └── loading.tsx           # Loading UI
│   │   ├── components/               # React Components
│   │   │   ├── auth/                 # LoginForm, RegisterForm, OAuth buttons
│   │   │   ├── counters/             # CounterWidget, CounterStats, Leaderboard
│   │   │   ├── layout/               # Navbar, Sidebar, Footer
│   │   │   ├── servers/              # ServerCard, ServerList, StatusBadge
│   │   │   ├── ui/                   # Reusable UI (Button, Modal, Card, etc.)
│   │   │   └── common/               # Shared components (Loading, Error, etc.)
│   │   ├── contexts/                 # React Contexts
│   │   │   ├── AuthContext.tsx       # Authentication state, user info, logout
│   │   │   ├── WebSocketContext.tsx  # WebSocket connection management
│   │   │   └── ThemeContext.tsx      # Theme/appearance settings
│   │   ├── lib/                      # Utility Functions
│   │   │   ├── api.ts                # Axios API client with interceptors
│   │   │   ├── websocket.ts          # Socket.io client wrapper
│   │   │   ├── auth.ts               # Auth helpers (token storage, refresh)
│   │   │   ├── utils.ts              # General utilities (cn, formatDate, etc.)
│   │   │   └── constants.ts          # App constants (roles, colors, URLs)
│   │   └── styles/                   # Global Styles
│   │       └── globals.css           # Global CSS with Tailwind directives
│   ├── public/                       # Static Assets
│   │   ├── icons/                    # PWA icons (multiple sizes)
│   │   ├── manifest.json             # PWA manifest
│   │   └── sw.js                     # Service worker
│   ├── package.json                  # Node.js dependencies
│   ├── tsconfig.json                 # TypeScript configuration
│   ├── tailwind.config.js            # Tailwind customization
│   ├── next.config.js                # Next.js config (PWA, rewrites)
│   └── Dockerfile                    # Frontend container definition
│
├── nginx/                            # Nginx Reverse Proxy
│   ├── nginx.conf                    # Production configuration
│   ├── nginx.dev.conf                # Development configuration
│   ├── ssl/                          # SSL certificate directory
│   └── Dockerfile                    # Nginx container
│
├── scripts/                          # Utility Scripts
│   ├── dev-start.sh                  # Development startup script (Unix)
│   └── dev-start.bat                 # Development startup script (Windows)
│
├── docker-compose.yml                # Docker orchestration (7 services)
├── .env.example                      # Environment variable template
├── .gitignore                        # Git ignore patterns
├── LICENSE                           # MIT License
└── README.md                         # Comprehensive documentation
```

## Key Features

### 1. User Authentication
- **Local Authentication**: Username/password with JWT tokens
- **Steam OpenID**: Integration for Steam account linking
- **Discord OAuth2**: Discord account authentication
- **JWT Tokens**: Secure API authentication with access/refresh tokens
- **Role-based Access Control**: 13-tier staff hierarchy with granular permissions
- **Session Management**: Token refresh, logout, and expiration handling

### 2. Staff Role Hierarchy
Roles are ordered by priority (lower = higher authority):

| Role | Priority | Color | Hex Code |
|------|----------|-------|----------|
| SYSADMIN | 0 | Red | #FF0000 |
| Manager | 10 | Dark Red | #990000 |
| Staff Manager | 20 | Orange Red | #F04000 |
| Assistant Staff Manager | 30 | Purple | #8900F0 |
| Meta Manager | 40 | Purple | #8900F0 |
| Event Manager | 50 | Purple | #8900F0 |
| Senior Admin | 60 | Pink Purple | #d207d3 |
| Admin | 70 | Hot Pink | #FA1E8A |
| Senior Moderator | 80 | Green | #15c000 |
| Moderator | 90 | Blue | #4a86e8 |
| Senior Operator | 100 | Dark Green | #38761d |
| Operator | 110 | Light Green | #93c47d |
| T-Staff | 120 | Pale Green | #b6d7a8 |

**Permission Levels**:
- Counter Access: All roles
- Template Access: Moderator+ (priority ≤ 90)
- Server Monitoring: All roles (view), Admin+ (refresh)
- Rules Management: Staff Manager+ (priority ≤ 20)
- Staff Roster: Staff Manager+ (edit)
- System Settings: Manager+ (priority ≤ 10)

### 3. Sit/Ticket Counters
- **Real-time Synchronization**: WebSocket-based updates across all connected clients
- **Operations**: Increment, decrement, reset with configurable amounts
- **Statistics**: Daily, weekly, monthly aggregations with timezone support
- **Leaderboards**: Top performers by period (daily/weekly/monthly)
- **History Tracking**: Detailed counter change logs with timestamps
- **Automatic Resets**: Configurable daily/weekly reset schedules via Celery Beat

### 4. Server Status Monitoring
- **Live Queries**: Source Query (A2S protocol) for Garry's Mod servers
- **Tracked Data**: Player count, max players, current map, server name
- **Staff Detection**: Identifies online staff members by Steam ID
- **Auto-refresh**: 60-second interval updates via Celery tasks
- **WebSocket Broadcast**: Real-time status updates to all connected clients
- **Multi-server**: Supports multiple game servers simultaneously

**Monitored Servers**:
- Server 1: `194.69.160.33:27083`
- Server 2: `193.243.190.12:27046`

### 5. Staff Roster
- **Google Sheets Integration**: Two-way sync with Google Sheets API
- **Sheet ID**: `1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo`
- **Auto-sync**: Scheduled synchronization via Celery Beat
- **Multi-timezone**: LOA and activity tracking with timezone conversions
- **Role Management**: Assign/update staff roles with validation
- **Activity Tracking**: Monitor staff activity, sits, tickets, and performance

### 6. Templates
- **Refund Templates**: Pre-built templates for ticket responses
- **Steam Lookup**: Integrated Steam Web API for profile information
- **Template Fields**: Dynamic field replacement (player name, Steam ID, etc.)
- **Quick Copy**: One-click copy-to-clipboard functionality
- **Template Management**: Create, edit, delete, and organize templates

### 7. Rules Reference System
- **Rule Categories**: General server rules, job-specific rules
- **Search Functionality**: Full-text search across all rules
- **Markdown Support**: Rich formatting with syntax highlighting
- **Job Filtering**: Filter rules by specific jobs (Police, Medic, etc.)
- **Categorization**: Organized by rule type and severity

### 8. System Settings
- **Runtime Configuration**: Modify settings without redeployment
- **Setting Types**: String, integer, boolean, JSON
- **Categories**: General, API Keys, Database, Cache, External Services
- **Sensitive Values**: Automatic masking for passwords/API keys
- **Audit Trail**: Track who changed what and when
- **Active/Inactive**: Enable/disable settings dynamically

## Development Commands

### Backend

```bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Environment setup
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput

# Run development server (HTTP only - no WebSockets)
python manage.py runserver

# Run with Daphne (for WebSockets support) - RECOMMENDED
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Start Celery worker (background tasks) - separate terminal
celery -A config worker -P solo -l info

# Start Celery beat (scheduled tasks) - separate terminal
celery -A config beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Create new Django app
python manage.py startapp app_name apps/app_name

# Make migrations
python manage.py makemigrations
python manage.py makemigrations app_name

# Show migrations
python manage.py showmigrations

# Run tests
python manage.py test
python manage.py test apps.counters  # Test specific app

# Django shell
python manage.py shell

# Database shell
python manage.py dbshell
```

### Frontend

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Environment setup
cp .env.example .env.local
# Edit .env.local with API URLs

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run linting
npm run lint

# Run tests
npm test

# Type checking
npx tsc --noEmit

# Clear cache
rm -rf .next node_modules
npm install
```

### Docker

```bash
# Build all images
docker-compose build

# Build specific service
docker-compose build backend
docker-compose build frontend

# Start all services
docker-compose up

# Start in detached mode
docker-compose up -d

# Start specific services
docker-compose up -d db redis
docker-compose up backend

# View logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Execute commands in containers
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser
docker-compose exec db psql -U elitelupus elitelupus

# Stop services
docker-compose stop

# Stop and remove containers
docker-compose down

# Reset database (removes volumes)
docker-compose down -v

# View service status
docker-compose ps

# Restart specific service
docker-compose restart backend
docker-compose restart celery
```

### VS Code Tasks

Available tasks (Ctrl+Shift+P → Tasks: Run Task):

- **Start Docker Services**: Starts PostgreSQL and Redis only
- **Stop Docker Services**: Stops database services
- **Django: Migrate**: Runs database migrations
- **Django: Make Migrations**: Creates new migration files
- **Django: Create Superuser**: Interactive superuser creation
- **Frontend: Install Dependencies**: Runs `npm install`
- **Backend: Install Dependencies**: Runs `pip install -r requirements.txt`
- **Docker: Build All**: Builds all Docker images
- **Docker: Up All Services**: Starts full stack
- **Docker: Down All Services**: Stops and removes all containers

## Environment Variables

### Backend (.env)

```env
# Django Configuration
DEBUG=True
SECRET_KEY=your-super-secret-key-change-this
ALLOWED_HOSTS=localhost,127.0.0.1,backend

# Database
POSTGRES_DB=elitelupus
POSTGRES_USER=elitelupus
POSTGRES_PASSWORD=changeme
POSTGRES_HOST=db  # 'localhost' for manual setup
POSTGRES_PORT=5432

# Redis
REDIS_HOST=redis  # 'localhost' for manual setup
REDIS_PORT=6379

# Steam API (Required)
# Get from: https://steamcommunity.com/dev/apikey
STEAM_API_KEY=your-steam-api-key

# Discord OAuth (Required)
# From: https://discord.com/developers/applications
DISCORD_CLIENT_ID=your-discord-client-id
DISCORD_CLIENT_SECRET=your-discord-client-secret

# Frontend URL
FRONTEND_URL=http://localhost:3000

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000

# Google Sheets (Optional)
GOOGLE_SHEETS_CREDENTIALS=/path/to/credentials.json
STAFF_ROSTER_SHEET_ID=1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo
```

### Frontend (.env.local)

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000

# Production example:
# NEXT_PUBLIC_API_URL=https://api.yourdomain.com
# NEXT_PUBLIC_WS_URL=wss://api.yourdomain.com
```

## API Endpoints

### Authentication
- `POST /api/auth/register/` - Register new user
- `POST /api/auth/login/` - Login (returns JWT)
- `POST /api/auth/token/refresh/` - Refresh JWT
- `GET /api/auth/me/` - Get current user
- `GET /api/auth/steam/login/` - Steam OAuth redirect
- `GET /api/auth/discord/login/` - Discord OAuth redirect
- `GET /api/auth/steam/callback/` - Steam OAuth callback
- `GET /api/auth/discord/callback/` - Discord OAuth callback

### Counters
- `GET /api/counters/` - Get user's counters
- `POST /api/counters/update/{type}/` - Update counter (type: sit|ticket)
- `GET /api/counters/stats/` - Get statistics (query: ?period=daily|weekly|monthly)
- `GET /api/counters/leaderboard/` - Get leaderboard (query: ?period=weekly&limit=10)
- `GET /api/counters/history/` - Get counter change history

### Servers
- `GET /api/servers/` - List all servers
- `GET /api/servers/status/` - Get live status for all servers
- `GET /api/servers/{id}/` - Get specific server details
- `POST /api/servers/refresh/` - Force refresh server status

### Staff
- `GET /api/staff/roster/` - Get staff roster
- `POST /api/staff/sync/` - Trigger Google Sheets sync
- `GET /api/staff/{id}/` - Get staff member details
- `PATCH /api/staff/{id}/` - Update staff member

### Templates
- `GET /api/templates/refunds/` - List refund templates
- `POST /api/templates/refunds/` - Create new template
- `GET /api/templates/refunds/{id}/` - Get specific template
- `PUT /api/templates/refunds/{id}/` - Update template
- `DELETE /api/templates/refunds/{id}/` - Delete template
- `POST /api/templates/steam-lookup/` - Steam profile lookup

### Rules
- `GET /api/rules/categories/` - Get all rule categories
- `GET /api/rules/general/` - Get general server rules
- `GET /api/rules/job-actions/` - Get job-specific rules
- `GET /api/rules/search/` - Search rules (query: ?q=keyword&category=general)

### System Settings
- `GET /api/system-settings/` - List all settings (admin only)
- `GET /api/system-settings/{key}/` - Get specific setting
- `PATCH /api/system-settings/{key}/` - Update setting (admin only)

## WebSocket Channels

### Counter Updates
- Endpoint: `ws://host/ws/counters/`
- Messages:
  - Send: `{"type": "counter_update", "counter_type": "sit|ticket", "action": "increment|decrement", "amount": 1}`
  - Receive: `{"type": "counter_update", "counter_type": "sit|ticket", "count": 123, "user_id": 1, "username": "John", "timestamp": "2024-01-01T12:00:00Z"}`

### Server Status
- Endpoint: `ws://host/ws/servers/`
- Messages:
  - Receive: `{"type": "server_update", "server_id": 1, "status": {"name": "...", "map": "...", "player_count": 64, "max_players": 128, "staff_online": ["Admin1"], "online": true}}`

### Connection
```javascript
import io from 'socket.io-client';

const socket = io('ws://localhost:8000', {
  auth: { token: 'your_jwt_token' },
  transports: ['websocket']
});

// Counter updates
socket.emit('counter_update', {
  type: 'counter_update',
  counter_type: 'sit',
  action: 'increment',
  amount: 1
});

socket.on('counter_update', (data) => {
  console.log('Counter updated:', data);
});

// Server status updates
socket.on('server_update', (data) => {
  console.log('Server status:', data);
});
```

## Code Style Guidelines

### Python (Backend)
- Follow PEP 8 style guide
- Use type hints where appropriate
- Docstrings for all public methods
- Django model fields should have `verbose_name`
- Use Black for formatting: `black backend/`
- Max line length: 100 characters
- Prefer class-based views for complex logic
- Use DRF serializers for all API responses
- Keep business logic in models or services, not views

### TypeScript (Frontend)
- Use strict TypeScript (`"strict": true` in tsconfig.json)
- Prefer functional components with hooks over class components
- Use TailwindCSS for styling (avoid custom CSS when possible)
- Keep components small and focused (single responsibility)
- Use React Query for server state, Zustand for client state
- Destructure props for readability
- Use meaningful variable and function names
- Extract complex logic into custom hooks
- Use Zod for form validation schemas

### General
- Keep commits atomic and well-described
- Write meaningful variable and function names (avoid abbreviations)
- Comment complex logic, not obvious code
- Handle errors gracefully with user-friendly messages
- Log errors with context for debugging
- Never commit sensitive information (.env files, API keys)
- Write tests for critical functionality
- Use async/await over .then() for promises
- Validate all user inputs

### File Organization
- Group related files together
- Keep file names descriptive and consistent
- Use index files for cleaner imports
- Separate concerns (models, views, serializers, services)

### Django Best Practices
```python
# Good: Descriptive model with validation
class Counter(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='counters',
        verbose_name='User'
    )
    sit_count = models.IntegerField(default=0, verbose_name='Sit Count')
    
    def increment_sit(self, amount=1):
        """Increment sit counter by specified amount."""
        self.sit_count += amount
        self.save()
        CounterHistory.objects.create(
            counter=self,
            counter_type='sit',
            action='increment',
            amount=amount
        )
```

### React/Next.js Best Practices
```typescript
// Good: Typed functional component with hooks
interface CounterWidgetProps {
  userId: number;
  counterType: 'sit' | 'ticket';
}

export function CounterWidget({ userId, counterType }: CounterWidgetProps) {
  const { data, isLoading, error } = useQuery({
    queryKey: ['counter', userId, counterType],
    queryFn: () => fetchCounter(userId, counterType),
  });
  
  if (isLoading) return <LoadingSpinner />;
  if (error) return <ErrorMessage error={error} />;
  
  return (
    <div className="rounded-lg bg-white p-4 shadow">
      <h3 className="text-lg font-semibold">{counterType}</h3>
      <p className="text-3xl font-bold">{data?.count}</p>
    </div>
  );
}
```

## Game Server Configuration

The application monitors these Garry's Mod servers using Source Query (A2S protocol):

| Server | IP | Port | Description |
|--------|-----|------|-------------|
| Server 1 | 194.69.160.33 | 27083 | Primary Elitelupus server |
| Server 2 | 193.243.190.12 | 27046 | Secondary Elitelupus server |

### Adding New Servers

To add a new game server:

1. **Via Django Admin**:
   ```
   http://localhost:8000/admin/servers/gameserver/add/
   ```

2. **Via Django Shell**:
   ```python
   from apps.servers.models import GameServer
   
   GameServer.objects.create(
       name='Server 3',
       ip_address='192.168.1.100',
       port=27015,
       is_active=True
   )
   ```

3. **Server Model Fields**:
   - `name`: Display name for the server
   - `ip_address`: Server IP address
   - `port`: Query port (usually game port + 1)
   - `is_active`: Whether to monitor this server
   - `last_queried`: Timestamp of last successful query
   - `last_status`: Cached JSON status data

## Troubleshooting

### WebSocket Connection Issues
- Ensure Redis is running: `docker-compose ps redis`
- Check ASGI server is started (Daphne/Uvicorn, NOT runserver)
- Verify WebSocket URL in frontend config: `NEXT_PUBLIC_WS_URL`
- Check browser console for WebSocket errors
- Verify JWT token is being sent in WebSocket auth

### Database Connection Issues
- Verify PostgreSQL is running: `docker-compose ps db`
- Check DATABASE_URL format in settings
- Run migrations: `python manage.py migrate`
- Test connection: `docker-compose exec db psql -U elitelupus -d elitelupus`

### OAuth Issues
**Steam OpenID**:
- Verify STEAM_API_KEY is set
- Check callback URL matches: `http://localhost:8000/api/auth/steam/callback/`
- Ensure FRONTEND_URL is correct for redirect

**Discord OAuth**:
- Verify DISCORD_CLIENT_ID and DISCORD_CLIENT_SECRET
- Add redirect URI in Discord Developer Portal: `http://localhost:8000/api/auth/discord/callback/`
- Check OAuth2 scopes include: `identify`, `email`

### Counter Not Syncing
- Check WebSocket connection status in browser console
- Verify user is authenticated (JWT token valid)
- Ensure Celery worker is running for background tasks
- Check Redis is accessible

### Frontend Build Errors
- Clear cache: `rm -rf frontend/.next frontend/node_modules && npm install`
- Check TypeScript errors: `npm run lint && npx tsc --noEmit`
- Verify environment variables are set in `.env.local`
- Ensure Node.js version is 18+

### Celery Task Issues
- Check Celery worker logs: `docker-compose logs celery`
- Verify Redis connection: `celery -A config inspect ping`
- Check task registration: `celery -A config inspect registered`
- Restart worker: `docker-compose restart celery`

### Port Already in Use (Windows)
```powershell
# Find process using port
netstat -ano | findstr :8000

# Kill process
taskkill /PID <PID> /F

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Host:Container
```

### Google Sheets Sync Failing
- Verify credentials file exists and is accessible
- Check service account has access to the Google Sheet
- Verify STAFF_ROSTER_SHEET_ID is correct
- Test API access in Django shell:
  ```python
  from apps.staff.services import sync_staff_roster
  sync_staff_roster()
  ```

### Common Error Messages

| Error | Solution |
|-------|----------|
| `OperationalError: FATAL: password authentication failed` | Check `.env` database credentials |
| `ConnectionRefusedError` | Start the service with `docker-compose up` |
| `CORS policy: No 'Access-Control-Allow-Origin'` | Add frontend URL to `CORS_ALLOWED_ORIGINS` |
| `401 Unauthorized` | Refresh JWT token or login again |
| `WebSocket connection failed` | Check `NEXT_PUBLIC_WS_URL` and ensure Daphne is running |

## Deployment Checklist

### Production Configuration
- [ ] Set `DEBUG=False` in production
- [ ] Generate new `SECRET_KEY` (use Django's `get_random_secret_key()`)
- [ ] Configure proper `ALLOWED_HOSTS`
- [ ] Set up SSL/TLS certificates (Let's Encrypt recommended)
- [ ] Configure proper CORS settings (`CORS_ALLOWED_ORIGINS`)
- [ ] Set up database backups (automated daily)
- [ ] Configure logging (file-based or external service)
- [ ] Set up monitoring/alerting (Sentry, New Relic, etc.)
- [ ] Test WebSocket connections in production
- [ ] Verify OAuth callback URLs match production domain
- [ ] Set secure environment variables (API keys, secrets)
- [ ] Configure Nginx for static file serving
- [ ] Enable Gunicorn/Daphne process management (systemd/supervisord)
- [ ] Set up Celery worker and beat as services
- [ ] Configure Redis persistence (AOF or RDB)
- [ ] Test backup restore procedures
- [ ] Set up firewall rules (UFW, iptables)
- [ ] Enable rate limiting on API endpoints
- [ ] Configure CDN for static assets (optional)
- [ ] Set up health check endpoints

### Docker Production
```bash
# Build with production settings
docker-compose build

# Start all services
docker-compose up -d

# Services included:
# - PostgreSQL (port 5433)
# - Redis (port 6379)
# - Django Backend (port 8001)
# - Next.js Frontend (port 3000)
# - Nginx Reverse Proxy (port 280)
# - Celery Worker
# - Celery Beat

# View logs
docker-compose logs -f

# Monitor containers
docker-compose ps
docker stats
```

### SSL Configuration
Place SSL certificates in `nginx/ssl/`:
- `fullchain.pem` - Full certificate chain
- `privkey.pem` - Private key

Update `nginx/nginx.conf` with SSL configuration

### Database Backups
```bash
# Backup
docker-compose exec db pg_dump -U elitelupus elitelupus > backup_$(date +%Y%m%d).sql

# Restore
docker-compose exec -T db psql -U elitelupus elitelupus < backup_20240101.sql

# Automated (add to cron)
0 2 * * * cd /path/to/project && docker-compose exec db pg_dump -U elitelupus elitelupus | gzip > /backups/db_$(date +\%Y\%m\%d).sql.gz
```

### Performance Monitoring
- Monitor memory usage: `docker stats`
- Check disk space: `df -h`
- Review logs: `docker-compose logs -f`
- Database queries: Enable Django Debug Toolbar (dev only)
- API response times: Use DRF profiling middleware
