# Staff Time Tracking Feature

## Overview

The staff time tracking feature automatically monitors when staff members join and leave game servers, providing comprehensive analytics on their server activity, session patterns, and performance metrics.

## Features

### 1. Automatic Session Tracking
- **Real-time Monitoring**: Tracks when staff members join or leave servers through the existing A2S query system
- **Session Management**: Automatically opens sessions when staff join and closes them when they leave
- **Duration Calculation**: Calculates exact time spent on each server for each session

### 2. Staff Details Page
A comprehensive details page for each staff member accessible from the staff roster.

**Access**: Available to Assistant Staff Manager and higher roles

**URL Pattern**: `/dashboard/staff/[id]`

#### Statistics Displayed:
- **Total Server Time**: Cumulative time across all servers
- **Total Sessions**: Number of server sessions
- **Sits/Tickets**: Integration with counter system
- **Average Session Time**: Mean duration of sessions
- **Last Server Join**: Most recent server activity
- **Time per Server**: Breakdown by individual server with visual progress bars
- **Session History**: Table of recent sessions with join/leave times

### 3. Data Aggregation
Celery tasks run periodically to aggregate session data into:
- **Daily**: Previous day statistics
- **Weekly**: Current week statistics (Monday-Sunday)
- **Monthly**: Current month statistics

## Backend Implementation

### Models

#### ServerSession
Tracks individual server sessions:
```python
- staff: Foreign key to StaffRoster
- server: Foreign key to GameServer
- join_time: When staff joined
- leave_time: When staff left (null if active)
- duration: Session length in seconds
- steam_id: For correlation
- player_name: Staff member name
```

#### ServerSessionAggregate
Pre-computed statistics for performance:
```python
- staff: Foreign key to StaffRoster
- server: Foreign key to GameServer (null = all servers)
- period_type: 'daily', 'weekly', 'monthly', 'all_time'
- period_start/end: Date range
- total_time: Sum of session durations
- session_count: Number of sessions
- avg_session_time: Average duration
- longest_session: Maximum duration
```

### API Endpoints

#### Get Staff Details
```
GET /api/staff/roster/{id}/details/
Permission: IsAuthenticated, IsStaffManager (role_priority ≤ 20)
```
Returns comprehensive staff information including:
- Basic profile info
- Time tracking statistics
- Server breakdown
- Counter stats (sits/tickets)
- Recent sessions

#### Get Session History
```
GET /api/staff/roster/{id}/sessions/?server={server_id}&start_date={date}&end_date={date}&active_only={true|false}
Permission: IsAuthenticated, IsStaffManager
```
Returns paginated list of server sessions with filtering options.

#### Get Aggregated Stats
```
GET /api/staff/roster/{id}/stats/?period={daily|weekly|monthly}&server={server_id}
Permission: IsAuthenticated, IsStaffManager
```
Returns aggregated statistics for specified period and optional server.

### Session Tracking Logic

Located in `backend/apps/servers/services.py`:

1. **Server Query**: A2S queries run every 60 seconds
2. **Player Comparison**: Compares current online staff with previous query
3. **Join Detection**: New staff detected → create `ServerSession`
4. **Leave Detection**: Missing staff detected → close active `ServerSession` with leave_time
5. **Duration Calculation**: `duration = leave_time - join_time` in seconds

### Celery Tasks

#### aggregate_server_sessions
**Schedule**: Daily at 2:00 AM (recommended)

Aggregates previous day's sessions into:
- Daily aggregates for yesterday
- Weekly aggregates for current week
- Monthly aggregates for current month

Run manually:
```bash
python manage.py shell
>>> from apps.staff.tasks import aggregate_server_sessions
>>> aggregate_server_sessions.delay()
```

## Frontend Implementation

### Staff Details Page

**Location**: `frontend/src/app/dashboard/staff/[id]/page.tsx`

#### Components:
1. **Header**: Back button, staff name, role badge, status badge
2. **Summary Stats**: 4 cards showing total time, sessions, sits, tickets
3. **Session Habits**: Average session time, last join, timezone
4. **Account Info**: Steam ID, Discord tag
5. **Time per Server**: Visual breakdown with progress bars
6. **Recent Sessions**: Filterable table (All/Active)

#### Features:
- Permission-based access (403 redirect if unauthorized)
- Loading states
- Error handling
- Responsive design
- Real-time formatting of durations

### Navigation
From staff roster page, click "Details" button in Actions column to view full staff details.

## Permission System

### Required Permissions
- **View Staff Details**: `IsStaffManager` (Assistant Staff Manager and higher)
  - Priority ≤ 20
  - Roles: SYSADMIN, Manager, Staff Manager, Assistant Staff Manager

### Implementation
```python
from apps.accounts.permissions import IsStaffManager

class StaffDetailsView(generics.RetrieveAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStaffManager]
```

## Usage Examples

### Viewing Staff Details
1. Navigate to Staff Roster (`/dashboard/staff`)
2. Find staff member in table
3. Click "Details" button in Actions column
4. View comprehensive time tracking and statistics

### Filtering Sessions
On staff details page:
- Click "All" to see all sessions
- Click "Active" to see only ongoing sessions

### Understanding Metrics
- **Total Server Time**: Sum of all completed sessions
- **Average Session Time**: Total time ÷ number of sessions
- **Time per Server**: Shows distribution across servers
- **Progress Bars**: Width represents percentage of total time

## Database Migrations

Apply migrations to enable time tracking:
```bash
cd backend
python manage.py migrate staff
```

Migration file: `backend/apps/staff/migrations/0005_serversessionaggregate_serversession.py`

## Monitoring and Maintenance

### Check Active Sessions
```python
from apps.staff.models import ServerSession
active = ServerSession.objects.filter(leave_time__isnull=True)
print(f"Active sessions: {active.count()}")
```

### Check Aggregates
```python
from apps.staff.models import ServerSessionAggregate
from datetime import date

today_aggregates = ServerSessionAggregate.objects.filter(
    period_type='daily',
    period_start=date.today()
)
print(f"Today's aggregates: {today_aggregates.count()}")
```

### Manual Session Close
If a session gets stuck open (server crash, etc.):
```python
from apps.staff.models import ServerSession
from django.utils import timezone

session = ServerSession.objects.get(id=SESSION_ID)
session.leave_time = timezone.now()
session.calculate_duration()
session.save()
```

## Performance Considerations

1. **Aggregates**: Pre-computed for fast queries
2. **Indexes**: Added on frequently queried fields (staff, server, join_time)
3. **Pagination**: Session history supports pagination
4. **Caching**: Consider Redis caching for frequently accessed staff details

## Troubleshooting

### Sessions Not Being Created
- Check server query service is running
- Verify staff roster has correct Steam IDs
- Check logs: `docker-compose logs celery`

### Duration Not Calculated
- Ensure leave_time is set
- Check `calculate_duration()` method
- Verify timezone settings

### Permission Denied
- Verify user role priority ≤ 20
- Check authentication token
- Review permission classes

### Aggregates Not Updating
- Check Celery beat is running
- Verify task schedule in Django admin
- Run task manually to test

## Future Enhancements

Potential improvements:
- Charts and graphs for time trends
- Export functionality (CSV/PDF reports)
- Alerts for unusual activity patterns
- Comparison between staff members
- Peak activity time analysis
- Session quality metrics
- Mobile app support
