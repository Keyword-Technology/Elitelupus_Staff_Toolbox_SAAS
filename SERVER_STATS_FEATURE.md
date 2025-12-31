# Server Stats Feature - Implementation Summary

## Overview
Added a comprehensive server statistics page that displays staff presence tracking over the last 24 hours and average daily staff distribution to help identify times when servers need more staff coverage.

## Changes Made

### Backend (Django)

#### 1. New API Endpoint
**File**: `backend/apps/servers/views.py`
- Added `ServerStatsView` class that provides:
  - Last 24 hours of staff and player counts
  - Hourly averages over the last 30 days
  - Real-time calculation of staff distribution patterns

**Endpoint**: `GET /api/servers/<server_id>/stats/`

**Response Structure**:
```json
{
  "server": {
    "id": 1,
    "name": "Server 1",
    "server_name": "Elitelupus DarkRP",
    "is_online": true
  },
  "current_staff": 3,
  "last_24h": [
    {
      "timestamp": "2025-12-31T10:00:00Z",
      "staff_count": 2,
      "player_count": 45,
      "is_online": true
    }
  ],
  "hourly_averages": [
    {
      "hour": 0,
      "avg_staff": 1.5,
      "avg_players": 35.2,
      "sample_count": 150
    }
  ],
  "stats_period": {
    "start": "2025-12-30T12:00:00Z",
    "end": "2025-12-31T12:00:00Z",
    "average_period_days": 30
  }
}
```

#### 2. URL Configuration
**File**: `backend/apps/servers/urls.py`
- Added route: `path('<int:pk>/stats/', ServerStatsView.as_view(), name='server_stats')`

### Frontend (Next.js/React)

#### 1. Server Stats Page
**File**: `frontend/src/app/servers/[id]/stats/page.tsx`
- Dynamic route page for displaying detailed server statistics
- Features:
  - **24-Hour Line Chart**: Shows staff count and total players over time
  - **Hourly Averages Bar Chart**: Displays average staff distribution by hour
  - **Staffing Insights**: Automatically identifies the 3 hours with lowest staff coverage
  - Responsive design with dark theme consistency
  - Loading states and error handling

#### 2. Server Status Card Update
**File**: `frontend/src/components/servers/ServerStatusCard.tsx`
- Added "View Server Stats" button with chart icon
- Button navigates to the new stats page
- Maintains existing functionality (player count, staff list, etc.)

#### 3. New Dependencies
**Package**: `recharts` (v3.6.0)
- Professional charting library for React
- Used for line charts (24-hour tracking) and bar charts (hourly averages)
- Includes TypeScript types via `@types/recharts`

## Features

### 1. 24-Hour Staff Tracking
- Real-time visualization of staff presence over the last 24 hours
- Dual-line chart showing both staff count and total player count
- Helps track staff activity patterns throughout the day

### 2. Hourly Average Distribution
- Bar chart showing average staff count for each hour (0-23)
- Based on 30 days of historical data
- Helps identify consistent patterns in staff availability

### 3. Staffing Insights
- Automatically calculates the 3 hours with lowest average staff
- Provides actionable recommendations for scheduling
- Highlights times when the server typically needs more coverage

### 4. Current Status Display
- Shows current staff count
- Server online/offline status badge
- Quick access back to server list

## Usage

1. **Access Stats**: Click the "View Server Stats" button on any server card in the server status page
2. **View Charts**: The stats page displays two main charts:
   - Top: Last 24 hours of staff activity (line chart)
   - Bottom: Average hourly distribution (bar chart)
3. **Insights**: Scroll down to see which hours typically have the lowest staff coverage

## Data Requirements

The feature relies on `ServerStatusLog` model which tracks:
- `staff_count`: Number of staff members online
- `player_count`: Total players online
- `timestamp`: When the data was recorded
- `is_online`: Whether the server was accessible

This data is automatically collected by the existing `refresh_all_servers` Celery task.

## API Authentication

All endpoints require JWT authentication:
```javascript
headers: {
  Authorization: `Bearer ${access_token}`
}
```

## Future Enhancements

Potential improvements:
- Add date range selector for custom time periods
- Export data to CSV/PDF
- Compare multiple servers side-by-side
- Alert notifications when staff count drops below threshold
- Integration with staff scheduling system
- Predictive analytics for future staffing needs

## Technical Notes

- Uses Django's aggregation functions (`Avg`, `Count`) for efficient database queries
- Charts are responsive and work on mobile devices
- All timestamps are timezone-aware using Django's timezone utilities
- Frontend uses Next.js App Router (not Pages Router)
- Charts use custom colors matching the application's dark theme

## Testing

To test the feature:
1. Ensure the backend server is running with migrations applied
2. Ensure Redis and Celery are running (for data collection)
3. Visit `/servers` page in the frontend
4. Click "View Server Stats" on any online server
5. Verify charts display properly with actual data

## Files Modified

**Backend**:
- `backend/apps/servers/views.py` (added `ServerStatsView`)
- `backend/apps/servers/urls.py` (added stats route)

**Frontend**:
- `frontend/src/app/servers/[id]/stats/page.tsx` (new file)
- `frontend/src/components/servers/ServerStatusCard.tsx` (added button)
- `frontend/package.json` (added recharts dependency)

## Dependencies Added

```json
{
  "dependencies": {
    "recharts": "^3.6.0"
  },
  "devDependencies": {
    "@types/recharts": "^1.8.29"
  }
}
```
