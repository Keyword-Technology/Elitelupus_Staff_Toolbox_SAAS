# Elitelupus Staff Toolbox SaaS - Continuation Context

Use this file to continue development in a new agent session.

---

## Project Goal

Convert the existing Python Tkinter desktop application into a full SaaS web application with:
- **Backend**: Django 4.2+ with Django REST Framework
- **Frontend**: Next.js 14 with TypeScript and TailwindCSS
- **Real-time**: WebSockets via Django Channels
- **PWA**: Progressive Web App support
- **Docker**: Containerized deployment
- **Auth**: JWT + Steam OpenID + Discord OAuth2

---

## ✅ COMPLETED (100%)

### Backend (100% Complete)
All Django backend files have been created:

```
backend/
├── config/
│   ├── settings.py      ✅
│   ├── urls.py          ✅
│   ├── asgi.py          ✅
│   └── wsgi.py          ✅
├── apps/
│   ├── accounts/        ✅ (models, views, serializers, urls, permissions, pipeline, backends, admin)
│   ├── staff/           ✅ (models, services, views, serializers, urls, admin)
│   ├── counters/        ✅ (models, views, serializers, urls, consumers, routing, admin)
│   ├── servers/         ✅ (models, services, views, serializers, urls, consumers, routing, admin)
│   ├── templates_manager/ ✅ (models, views, serializers, urls, admin)
│   └── rules/           ✅ (models, views, serializers, urls, admin)
├── requirements.txt     ✅
├── Dockerfile           ✅
├── .env.example         ✅
└── manage.py            ✅
```

### Frontend (100% Complete)
All Next.js frontend files have been created:

```
frontend/
├── package.json              ✅
├── tsconfig.json             ✅
├── next.config.js            ✅ (with standalone output for Docker)
├── tailwind.config.js        ✅
├── postcss.config.js         ✅
├── Dockerfile                ✅
├── src/
│   ├── app/
│   │   ├── globals.css       ✅
│   │   ├── layout.tsx        ✅
│   │   ├── page.tsx          ✅
│   │   ├── login/page.tsx    ✅
│   │   ├── register/page.tsx ✅
│   │   ├── auth/callback/page.tsx ✅
│   │   └── dashboard/
│   │       ├── layout.tsx    ✅
│   │       ├── page.tsx      ✅
│   │       ├── counters/page.tsx    ✅
│   │       ├── servers/page.tsx     ✅
│   │       ├── templates/page.tsx   ✅
│   │       ├── rules/page.tsx       ✅
│   │       ├── staff/page.tsx       ✅
│   │       ├── leaderboard/page.tsx ✅
│   │       └── settings/page.tsx    ✅
│   ├── components/
│   │   ├── providers.tsx     ✅
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx   ✅
│   │   │   └── Header.tsx    ✅
│   │   ├── counters/
│   │   │   └── CounterCard.tsx ✅
│   │   └── servers/
│   │       └── ServerStatusCard.tsx ✅
│   ├── contexts/
│   │   ├── AuthContext.tsx   ✅
│   │   └── WebSocketContext.tsx ✅
│   └── lib/
│       └── api.ts            ✅
└── public/
    ├── manifest.json         ✅
    └── icons/
        └── icon.svg          ✅
```

### Docker Configuration (100% Complete)
```
docker-compose.yml            ✅ (PostgreSQL, Redis, Backend, Frontend, Nginx, Celery)
nginx/nginx.conf              ✅ (Reverse proxy with SSL support)
.env.example                  ✅ (Environment variables template)
```

### Documentation
- `.github/copilot-instructions.md` ✅

---

## 🚀 HOW TO RUN

### Development Mode
```bash
# Start with Docker Compose
docker-compose up --build

# Access:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - Admin: http://localhost:8000/admin/
```

### Production Mode
```bash
# Start with production profile (includes Nginx, Celery)
docker-compose --profile production up -d
```

### Manual Development (without Docker)
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

---

## 🧹 CLEANUP: Old Python Files to Delete

After verifying the SaaS application works, delete these legacy files:
- `main.py`
- `Sit_Counter.py`
- `Server_Status.py`
- `Staff_Distribution.py`
- `Template_Maker.py`
- `Elitelupus_ban_search.py`
- `Bard.py`
- `bard_utils.py`
- `steamid_finder_io.py`
- `Useful_Links.py`
- `OCR_SteamID/` folder (if exists)
- `resources/` folder (except what's needed)

---

## Key Technical Details

### Role Hierarchy (Priority - lower = more authority)
```
SYSADMIN: 0, Manager: 10, Staff Manager: 20, Assistant Staff Manager: 30,
Meta Manager: 40, Event Manager: 50, Senior Admin: 60, Admin: 70,
Senior Moderator: 80, Moderator: 90, Senior Operator: 100, Operator: 110, T-Staff: 120
```

### Game Servers to Monitor
- Server 1: `194.69.160.33:27083`
- Server 2: `193.243.190.12:27046`

### Google Sheets Staff Roster
- Sheet ID: `1SSn3GXggr84dOYfQZzeHiRI0B1vaDkGynUyYHWfXIBo`

### WebSocket Endpoints
- Counters: `ws://host/ws/counters/`
- Servers: `ws://host/ws/servers/`

---

## Quick Reference - File Locations

| Component | Path |
|-----------|------|
| Django Settings | `backend/config/settings.py` |
| Django URLs | `backend/config/urls.py` |
| User Model | `backend/apps/accounts/models.py` |
| Counter WebSocket | `backend/apps/counters/consumers.py` |
| API Client | `frontend/src/lib/api.ts` |
| Auth Context | `frontend/src/contexts/AuthContext.tsx` |
| WebSocket Context | `frontend/src/contexts/WebSocketContext.tsx` |
| Tailwind Config | `frontend/tailwind.config.js` |
| Docker Compose | `docker-compose.yml` |
| Nginx Config | `nginx/nginx.conf` |
| Instructions | `.github/copilot-instructions.md` |
