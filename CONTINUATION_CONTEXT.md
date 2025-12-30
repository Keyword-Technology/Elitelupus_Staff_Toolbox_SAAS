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

## ✅ COMPLETED

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

### Frontend (Partial - ~50% Complete)
Core infrastructure is done:

```
frontend/
├── package.json              ✅
├── tsconfig.json             ✅
├── next.config.js            ✅
├── tailwind.config.js        ✅
├── postcss.config.js         ✅
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
│   │       └── page.tsx      ✅
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
```

### Documentation
- `.github/copilot-instructions.md` ✅

---

## ❌ NOT COMPLETED

### Frontend Pages Needed
```
frontend/src/app/dashboard/
├── counters/page.tsx      ❌  (Dedicated counter page with full stats)
├── servers/page.tsx       ❌  (Server status page)
├── templates/page.tsx     ❌  (Template maker with Steam lookup)
├── rules/page.tsx         ❌  (Server rules display)
├── staff/page.tsx         ❌  (Staff roster from Google Sheets)
├── leaderboard/page.tsx   ❌  (Counter leaderboard)
└── settings/page.tsx      ❌  (User settings, link accounts)
```

### Frontend Components Needed
```
frontend/src/components/
├── templates/
│   └── TemplateForm.tsx   ❌
├── rules/
│   └── RulesDisplay.tsx   ❌
├── staff/
│   └── StaffRosterTable.tsx ❌
└── leaderboard/
    └── LeaderboardTable.tsx ❌
```

### Docker Configuration
```
docker-compose.yml         ❌  (orchestration for backend, frontend, postgres, redis)
frontend/Dockerfile        ❌
```

### PWA Assets
```
frontend/public/
├── manifest.json          ❌
├── icons/
│   ├── icon-192x192.png   ❌
│   └── icon-512x512.png   ❌
└── sw.js                  ❌  (service worker - handled by next-pwa)
```

### Delete Old Python Files
After completion, delete these legacy files:
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
- `OCR_SteamID/` folder
- `resources/` folder (except what's needed)

---

## Key Technical Details

### Role Hierarchy (Priority - lower = more authority)
```
SYSADMIN: 0, Community Manager: 10, Head Admin: 20, Super Admin: 30,
Senior Admin: 40, Admin: 50, Senior Moderator: 60, Moderator: 70,
Trial Moderator: 80, Senior Staff: 90, Staff: 100, T-Mod: 110, T-Staff: 120
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

## Prompt to Continue

Copy and paste this to continue in a new session:

```
Continue building the Elitelupus Staff Toolbox SaaS application. 

Read the CONTINUATION_CONTEXT.md file for full context on what's completed and what remains.

Priority tasks:
1. Create remaining frontend pages (counters, servers, templates, rules, staff, leaderboard, settings)
2. Create docker-compose.yml for deployment
3. Add PWA manifest and icons
4. Delete old Python files when complete

The backend is 100% complete. Focus on completing the frontend pages and Docker setup.
```

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
| Instructions | `.github/copilot-instructions.md` |
