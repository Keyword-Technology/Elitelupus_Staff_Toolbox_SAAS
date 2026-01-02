# Sit Recording System Specification

## Overview

This document outlines an alternative sit tracking system that integrates screen recording with the web application to provide comprehensive sit documentation, accountability, and future reference capabilities for staff and management.

## Problem Statement

The current sit counter system tracks quantity but lacks:
- **Context**: No record of what actually happened during a sit
- **Accountability**: No evidence for disputed situations
- **Training**: No way to review sits for coaching purposes
- **Audit Trail**: Management cannot verify sit quality or outcomes

## Proposed Solution

A comprehensive sit tracking system that records the entire sit session, captures metadata, and stores everything for future reference.

---

## User Flow

### 1. Accept Sit In-Game
- Staff member receives a sit request in Garry's Mod
- Staff accepts the sit via in-game admin menu (ULX/SAM)
- Staff teleports to the sit location

### 2. Start Sit on Web Application
- Staff opens the Elitelupus Staff Toolbox web app
- Navigates to **Sits** → **Active Sit** (or quick-access button on dashboard)
- Clicks **"Start Sit"** button
- System prompts for game window selection (if multiple monitors/windows)
- Screen recording begins on the selected game window
- Timer starts tracking sit duration
- Real-time sit panel opens with note-taking tools

### 3. Handle Sit (Active Recording)
During the sit, staff has access to:
- **Notes Panel**: Real-time note-taking with timestamps
- **Steam ID Input**: Fields for Reporter and Reportee Steam IDs
  - Auto-lookup: Fetches player name and profile from Steam API
  - Quick-paste from in-game console
- **Quick Actions**: Common note shortcuts (e.g., "RDM", "NLR", "Prop Abuse")
- **Timer Display**: Shows current sit duration
- **Recording Indicator**: Visual confirmation recording is active

### 4. Close Sit In-Game
- Staff resolves the situation in-game
- Returns players if needed
- Closes the sit via in-game admin menu

### 5. End Sit on Web Application
- Staff clicks **"End Sit"** button
- Screen recording stops
- Timer stops

### 6. Post-Sit Report Modal
Staff is prompted with a completion form:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| Outcome | Dropdown | Yes | What action was taken |
| Rule Violated | Multi-select | Conditional | Which rules were broken (if applicable) |
| Punishment Given | Dropdown | Conditional | Type of punishment (if any) |
| Punishment Duration | Input | Conditional | Length of punishment (if applicable) |
| Additional Notes | Textarea | No | Final summary notes |
| Reporter Steam ID | Pre-filled | Yes | Auto-populated from sit panel |
| Reportee Steam ID | Pre-filled | Yes | Auto-populated from sit panel |

**Outcome Options:**
- No Action Taken (False Report)
- Verbal Warning
- Formal Warning
- Kick
- Ban (requires duration)
- Escalated to Higher Staff
- Other (requires notes)

### 7. Save & Upload
- Recording is processed and compressed
- All data is saved to the database
- Sit is counted towards the staff member's sit count
- Recording is uploaded to storage
- Confirmation shown to staff member

### 8. Future Reference
Both staff and management can:
- View sit history with recordings
- Search by player Steam ID, date, outcome, or staff member
- Download recordings for evidence
- Generate reports for staff reviews

---

## Technical Architecture

### Frontend Components

```
src/
├── app/
│   └── sits/
│       ├── page.tsx              # Sit list/history
│       ├── active/
│       │   └── page.tsx          # Active sit interface
│       └── [id]/
│           └── page.tsx          # Sit detail/playback
├── components/
│   └── sits/
│       ├── ActiveSitPanel.tsx    # Main sit recording interface
│       ├── SitTimer.tsx          # Duration timer component
│       ├── SitNotesPanel.tsx     # Real-time notes with timestamps
│       ├── SteamIdInput.tsx      # Steam ID entry with lookup
│       ├── QuickActionsBar.tsx   # Common action shortcuts
│       ├── RecordingIndicator.tsx # Recording status display
│       ├── PostSitModal.tsx      # Completion form modal
│       ├── SitHistoryList.tsx    # Paginated sit history
│       ├── SitCard.tsx           # Individual sit summary
│       └── SitPlayback.tsx       # Video playback component
└── hooks/
    ├── useScreenRecording.ts     # Screen capture API hook
    ├── useActiveSit.ts           # Active sit state management
    └── useSitHistory.ts          # Sit history queries
```

### Backend Components

```
backend/apps/
└── sits/
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── models.py                 # Sit, SitNote, SitRecording models
    ├── serializers.py            # API serializers
    ├── views.py                  # API endpoints
    ├── urls.py                   # URL routing
    ├── consumers.py              # WebSocket for real-time updates
    ├── routing.py                # WebSocket routing
    ├── tasks.py                  # Celery tasks (video processing)
    └── migrations/
```

### Database Models

#### Sit Model
```python
class Sit(models.Model):
    # Relationships
    staff_member = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sits')
    
    # Steam IDs
    reporter_steam_id = models.CharField(max_length=20, blank=True)
    reporter_name = models.CharField(max_length=100, blank=True)
    reportee_steam_id = models.CharField(max_length=20, blank=True)
    reportee_name = models.CharField(max_length=100, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField()
    ended_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.IntegerField(default=0)
    
    # Outcome
    outcome = models.CharField(max_length=50, choices=OUTCOME_CHOICES)
    punishment_type = models.CharField(max_length=50, blank=True)
    punishment_duration = models.CharField(max_length=50, blank=True)
    rules_violated = models.JSONField(default=list)  # List of rule IDs
    
    # Notes
    summary_notes = models.TextField(blank=True)
    
    # Recording
    has_recording = models.BooleanField(default=False)
    recording_url = models.URLField(blank=True)
    recording_size_bytes = models.BigIntegerField(default=0)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['staff_member', 'started_at']),
            models.Index(fields=['reporter_steam_id']),
            models.Index(fields=['reportee_steam_id']),
        ]


class SitNote(models.Model):
    """Real-time notes taken during a sit"""
    sit = models.ForeignKey(Sit, on_delete=models.CASCADE, related_name='notes')
    content = models.TextField()
    timestamp_seconds = models.IntegerField()  # Seconds into the sit
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp_seconds']
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/sits/start/` | Start a new sit session |
| `PATCH` | `/api/sits/{id}/end/` | End sit and submit outcome |
| `GET` | `/api/sits/` | List sit history (paginated) |
| `GET` | `/api/sits/{id}/` | Get sit details |
| `GET` | `/api/sits/active/` | Get current active sit (if any) |
| `POST` | `/api/sits/{id}/notes/` | Add timestamped note |
| `GET` | `/api/sits/{id}/notes/` | Get all notes for a sit |
| `POST` | `/api/sits/{id}/upload-recording/` | Upload recording file |
| `GET` | `/api/sits/{id}/recording/` | Get recording URL (signed) |
| `GET` | `/api/sits/stats/` | Get sit statistics |
| `GET` | `/api/sits/search/` | Search sits by various criteria |

### WebSocket Events

#### Client → Server
| Event | Payload | Description |
|-------|---------|-------------|
| `sit.start` | `{}` | Notify server sit started |
| `sit.note` | `{ content, timestamp_seconds }` | Add real-time note |
| `sit.update_steam_ids` | `{ reporter_steam_id, reportee_steam_id }` | Update Steam IDs |
| `sit.end` | `{ outcome, ... }` | End sit with outcome data |

#### Server → Client
| Event | Payload | Description |
|-------|---------|-------------|
| `sit.started` | `{ sit_id, started_at }` | Confirmation sit started |
| `sit.note_added` | `{ note_id, content, timestamp }` | Note saved confirmation |
| `sit.ended` | `{ sit_id, duration }` | Sit ended confirmation |
| `sit.steam_lookup` | `{ type, steam_id, name, avatar }` | Steam lookup result |

---

## Screen Recording Implementation

### Browser API: Screen Capture API

The system will use the **Screen Capture API** (`getDisplayMedia`) available in modern browsers.

```typescript
// hooks/useScreenRecording.ts

interface UseScreenRecordingReturn {
  isRecording: boolean;
  startRecording: () => Promise<void>;
  stopRecording: () => Promise<Blob>;
  recordingDuration: number;
  error: string | null;
}

const useScreenRecording = (): UseScreenRecordingReturn => {
  // Request screen capture permission
  const stream = await navigator.mediaDevices.getDisplayMedia({
    video: {
      displaySurface: 'window',  // Prefer window selection
      frameRate: 30,
      width: { ideal: 1920 },
      height: { ideal: 1080 },
    },
    audio: false,  // Game audio optional
  });
  
  // Use MediaRecorder API for recording
  const mediaRecorder = new MediaRecorder(stream, {
    mimeType: 'video/webm;codecs=vp9',
    videoBitsPerSecond: 2500000,  // 2.5 Mbps
  });
  
  // ... implementation
};
```

### Recording Flow

1. **Permission Request**: Browser prompts user to select screen/window
2. **Window Selection**: User selects Garry's Mod game window
3. **Recording Start**: MediaRecorder begins capturing
4. **Chunk Collection**: Video chunks stored in memory (or streamed)
5. **Recording Stop**: Final blob created
6. **Compression**: Client-side compression (if needed)
7. **Upload**: Chunked upload to server
8. **Processing**: Server-side processing (format conversion, thumbnail)

### Video Storage Options

| Option | Pros | Cons |
|--------|------|------|
| **Local Storage** | Free, fast | Limited capacity, no redundancy |
| **AWS S3** | Scalable, reliable | Cost, complexity |
| **Cloudflare R2** | S3-compatible, free egress | Newer service |
| **Backblaze B2** | Cheap, simple | Less features |
| **Self-hosted MinIO** | Free, S3-compatible | Maintenance overhead |

**Recommended**: Start with local storage, migrate to S3/R2 when needed.

### Video Retention Policy

| User Role | Retention Period | Max Storage |
|-----------|------------------|-------------|
| T-Staff | 7 days | 5 GB |
| Operator | 14 days | 10 GB |
| Moderator | 30 days | 25 GB |
| Admin+ | 90 days | 50 GB |
| Flagged Sits | 1 year | Unlimited |

Recordings can be:
- **Flagged**: Marked for extended retention (disputes, training)
- **Archived**: Moved to cold storage after retention period
- **Deleted**: Permanently removed after archive period

---

## UI/UX Design

### Active Sit Panel Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  🔴 Recording                                    ⏱️ 03:45        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │   Reporter           │  │          Notes                   │ │
│  │   ┌────────────────┐ │  │  ┌──────────────────────────────┐│ │
│  │   │ STEAM_0:1:123  │ │  │  │ [00:15] Player claims RDM   ││ │
│  │   └────────────────┘ │  │  │ [01:30] Checking logs...    ││ │
│  │   👤 PlayerName      │  │  │ [02:45] Found evidence      ││ │
│  │   ⏳ 500 hrs | VAC ✓ │  │  └──────────────────────────────┘│ │
│  │                      │  │                                   │ │
│  │   Reportee           │  │  ┌──────────────────────────────┐│ │
│  │   ┌────────────────┐ │  │  │ Add note...                  ││ │
│  │   │ STEAM_0:0:456  │ │  │  └──────────────────────────────┘│ │
│  │   └────────────────┘ │  │                                   │ │
│  │   👤 OtherPlayer     │  └──────────────────────────────────┘ │
│  │   ⏳ 50 hrs | VAC ✗  │                                        │
│  └──────────────────────┘                                        │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ Quick Actions:  [RDM] [NLR] [Prop Abuse] [FailRP] [More...] ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│           ┌──────────────────────────────────┐                  │
│           │         🛑 End Sit               │                  │
│           └──────────────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────┘
```

### Post-Sit Modal

```
┌─────────────────────────────────────────────────────────────────┐
│                      Sit Complete                               │
│                      Duration: 03:45                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  What was the outcome of this sit?                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ▼ Select outcome...                                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Rules Violated (if any):                                       │
│  ☐ RDM        ☐ NLR         ☐ Prop Abuse                       │
│  ☐ FailRP    ☐ Meta Gaming  ☐ Harassment                       │
│  ☐ Other: [________________]                                    │
│                                                                  │
│  Punishment Given:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ ▼ None                                                   │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  Additional Notes:                                              │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                                                          │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ☑ Save recording for future reference                         │
│                                                                  │
│           ┌──────────────┐    ┌──────────────┐                 │
│           │    Cancel    │    │  Save Sit    │                 │
│           └──────────────┘    └──────────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

### Sit History View

```
┌─────────────────────────────────────────────────────────────────┐
│  📋 Sit History                           🔍 [Search...]  [Filter ▼]│
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ #1247  │  Today 2:30 PM  │  Duration: 4:12  │  🎬 📝        ││
│  │ Reporter: PlayerA (STEAM_0:1:123)                           ││
│  │ Reportee: PlayerB (STEAM_0:0:456)                           ││
│  │ Outcome: ⚠️ Warning Given  │  Rule: RDM                      ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ #1246  │  Today 1:15 PM  │  Duration: 2:30  │  🎬           ││
│  │ Reporter: SomeUser (STEAM_0:1:789)                          ││
│  │ Reportee: AnotherUser (STEAM_0:0:012)                       ││
│  │ Outcome: ✅ No Action (False Report)                         ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                  │
│  [Load More...]                                                  │
└─────────────────────────────────────────────────────────────────┘

Legend: 🎬 = Has Recording  📝 = Has Notes  ⭐ = Flagged
```

---

## Permission Requirements

### Browser Permissions
- **Screen Capture**: `getDisplayMedia` permission (user must grant)
- **Storage**: IndexedDB for temporary chunk storage (automatic)

### Staff Role Permissions

| Permission | T-Staff | Op | Mod | Admin | Manager |
|------------|---------|-----|-----|-------|---------|
| Start/End Own Sits | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Own Sit History | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Own Recordings | ✅ | ✅ | ✅ | ✅ | ✅ |
| View All Sit History | ❌ | ❌ | ❌ | ✅ | ✅ |
| View All Recordings | ❌ | ❌ | ❌ | ✅ | ✅ |
| Flag Sits | ❌ | ❌ | ✅ | ✅ | ✅ |
| Delete Recordings | ❌ | ❌ | ❌ | ❌ | ✅ |
| Export Sit Data | ❌ | ❌ | ❌ | ✅ | ✅ |

---

## Integration Points

### Existing Systems

1. **Counter System**: Completed sits automatically increment sit counter
2. **Staff Roster**: Link sits to staff member records
3. **Rules Reference**: Link violated rules to rule database
4. **Steam Lookup**: Use existing Steam API integration

### Future Integrations

1. **Discord Bot**: Send sit summary to staff logs channel
2. **Auto-Detection**: Game server plugin to auto-start sits (optional)
3. **Analytics Dashboard**: Sit trends, rule violations over time
4. **Performance Reviews**: Sit metrics for staff evaluations

---

## Security Considerations

### Recording Privacy
- Recordings are private to the staff member and management
- Signed URLs with expiration for playback
- No public access to any recording
- Audit log for who viewed which recordings

### Data Protection
- Steam IDs stored securely (not in URLs)
- HTTPS required for all uploads
- Recordings encrypted at rest (if using cloud storage)
- Automatic deletion per retention policy

### Abuse Prevention
- Rate limiting on sit creation (max 50/day per staff)
- Max recording duration (30 minutes auto-stop)
- File size limits (500MB per recording)
- Storage quota per user role

---

## Performance Considerations

### Client-Side
- WebM format for efficient browser encoding
- Chunked recording to prevent memory issues
- Background upload during post-sit modal
- Progressive video loading for playback

### Server-Side
- Async upload processing with Celery
- Video transcoding queue (if needed)
- CDN for video delivery (optional)
- Database indexing for search queries

### Storage Estimates

| Assumption | Value |
|------------|-------|
| Average sit duration | 5 minutes |
| Video bitrate | 2.5 Mbps |
| Average file size | ~94 MB |
| Sits per day (server-wide) | 100 |
| Daily storage | ~9.4 GB |
| Monthly storage (before retention) | ~280 GB |

---

## Implementation Phases

### Phase 1: Core Functionality (MVP)
- [ ] Sit model and API endpoints
- [ ] Basic active sit panel (no recording)
- [ ] Steam ID input with lookup
- [ ] Note-taking functionality
- [ ] Post-sit outcome modal
- [ ] Integration with sit counter

### Phase 2: Screen Recording
- [ ] Screen Capture API integration
- [ ] MediaRecorder implementation
- [ ] Local file upload
- [ ] Basic playback in sit detail view
- [ ] Recording indicator UI

### Phase 3: Enhanced Features
- [ ] Timestamped notes with video sync
- [ ] Quick action shortcuts
- [ ] Advanced search and filtering
- [ ] Sit history export
- [ ] Management overview dashboard

### Phase 4: Polish & Optimization
- [ ] Cloud storage migration
- [ ] Video compression optimization
- [ ] Retention policy automation
- [ ] Discord integration
- [ ] Mobile-responsive design

---

## Automatic Sit Detection (Browser-Based OCR)

Since we're already capturing the game screen for recording, we can analyze frames from that video stream to automatically detect when sits are claimed and closed using browser-based OCR (Tesseract.js).

### Visual Reference - Elitelupus Report System

Based on actual in-game screenshots, the report system has these distinct visual states:

#### State Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│  STATE: 0 SITS (No Active Reports)                                  │
│                                                                     │
│  • No report popup visible in top-left                              │
│  • Only HUD elements (Staff on Duty badge, props counter)           │
│  • Chat area may show admin activity                                │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ New report filed
┌─────────────────────────────────────────────────────────────────────┐
│  STATE: 1+ SITS UNCLAIMED                                           │
│  ┌─────────────────────────────┐                                    │
│  │ [PlayerName]'s Report    ✕  │                                    │
│  │ Report Type: RDM            │                                    │
│  │ Reported Player: [Name]     │                                    │
│  │ Reason: [description...]    │                                    │
│  │ ┌───────┐  ┌───────┐        │                                    │
│  │ │ Claim │  │ Close │        │  ← UNCLAIMED buttons              │
│  │ └───────┘  └───────┘        │                                    │
│  └─────────────────────────────┘                                    │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ Staff clicks "Claim"
┌─────────────────────────────────────────────────────────────────────┐
│  STATE: 1+ SITS CLAIMED                                             │
│  ┌─────────────────────────────┐                                    │
│  │ [PlayerName]'s Report    ✕  │                                    │
│  │ Report Type: RDM            │                                    │
│  │ Reported Player: [Name]     │                                    │
│  │ Reason: [description...]    │                                    │
│  │ ┌───────┐ ┌───────┐ ┌─────┐ │                                    │
│  │ │ Go To │ │ Bring │ │Close│ │  ← CLAIMED buttons                │
│  │ └───────┘ └───────┘ └─────┘ │                                    │
│  └─────────────────────────────┘                                    │
│                                                                     │
│  CHAT: "[Elite Reports] ofcWilliam claimed Melky's report"           │
└─────────────────────────────────────────────────────────────────────┘
                              ↓ Staff clicks "Close" (after handling)
┌─────────────────────────────────────────────────────────────────────┐
│  STATE: SIT CLOSED                                                  │
│                                                                     │
│  • Report popup disappears                                          │
│  • Chat may show: "[Elite Reports] ofcWilliam closed [X]'s report"   │
│  • Returns to 0 sits or remaining unclaimed sits                    │
└─────────────────────────────────────────────────────────────────────┘
```

#### Multiple Sits (Stacked Popups)

```
┌─────────────────────────────┐
│ нє6є soendergaard's Report  │ ← Report 1 (unclaimed: Claim/Close)
│ Report Type: RDM            │
│ [Claim] [Close]             │
├─────────────────────────────┤
│ AC1D EMINEM's Report        │ ← Report 2 (claimed: GoTo/Bring/Close)
│ Report Type: Other          │
│ [Go To] [Bring] [Close]     │
├─────────────────────────────┤
│ jozo59739's Report          │ ← Report 3 (unclaimed: Claim/Close)
│ Report Type: Other          │
│ [Claim] [Close]             │
└─────────────────────────────┘
```

### OCR Screen Regions (Actual Layout)

Based on the screenshots, here are the exact regions to monitor:

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ┌─────────────────────────┐                                              │
│ │ OCR REGION 1            │                          [Player names bar]  │
│ │ REPORT POPUPS           │                                              │
│ │ x: 0%, y: 0%            │                                              │
│ │ w: 20%, h: 50%          │                                              │
│ │                         │                                              │
│ │ Detect:                 │                                              │
│ │ - "'s Report" title     │                                              │
│ │ - Button text changes   │                                              │
│ │ - "Claim" vs "Go To"    │                                              │
│ └─────────────────────────┘                                              │
│                                                                          │
│                              [GAME WORLD]                                │
│                                                                          │
│ ┌─────────────────────────────────┐                       ┌────────────┐ │
│ │ OCR REGION 2                    │                       │ FPS/ping   │ │
│ │ CHAT AREA                       │                       │ stats      │ │
│ │ x: 0%, y: 60%                   │                       │ (ignore)   │ │
│ │ w: 25%, h: 25%                  │                       └────────────┘ │
│ │                                 │                                      │
│ │ Detect:                         │                                      │
│ │ - "claimed [X]'s report"        │                                      │
│ │ - "closed [X]'s report"         │                                      │
│ │ - "[Elite Admin Stats]" prefix       │                                      │
│ └─────────────────────────────────┘                                      │
│ ┌───────────────────────────────────┐                                    │
│ │ HUD REGION (Reference only)       │                                    │
│ │ Staff on Duty badge               │                                    │
│ └───────────────────────────────────┘                                    │
└──────────────────────────────────────────────────────────────────────────┘
```

### Detection Strategy

#### Primary Detection: Chat Messages (Most Reliable)

```typescript
// Monitor CHAT AREA for claim/close messages
const CHAT_SIT_CLAIMED = [
    /claimed\s+(.+?)(?:'s)?\s+report/i,      // "[Elite Reports] ofcWilliam claimed Melky's report"
    /(\w+)\s+claimed\s+(.+?)(?:'s)?\s+report/i,
];

const CHAT_SIT_CLOSED = [
    /closed\s+(.+?)(?:'s)?\s+report/i,       // "[Elite Reports] ofcWilliam closed Melky's report"
    /(\w+)\s+closed\s+(.+?)(?:'s)?\s+report/i,
    /returned\s+(.+?)\s+to/i,                // "returned PlayerName to their position"
];
```

#### Secondary Detection: Button State Changes (Backup)

```typescript
// Monitor REPORT POPUP AREA for button text
const POPUP_UNCLAIMED_INDICATORS = [
    /Claim/i,           // "Claim" button visible = unclaimed sit exists
];

const POPUP_CLAIMED_INDICATORS = [
    /Go\s*To/i,         // "Go To" button = sit is claimed (by you or other staff)
    /Bring/i,           // "Bring" button = sit is claimed
];

// Detect report presence
const REPORT_TITLE_PATTERN = /(.+?)(?:'s)?\s+Report/i;  // "Melky's Report"
```

#### Detection Logic

```typescript
interface SitDetectionState {
    hasActiveReport: boolean;       // Is there a popup visible?
    isReportClaimed: boolean;       // Does popup show Go To/Bring (vs Claim)?
    reporterName: string | null;    // Extracted from "[X]'s Report"
    reportedPlayer: string | null;  // From "Reported Player:" line
    reportType: string | null;      // RDM, NLR, Other, etc.
    staffRating: number | null;     // 1-5 stars (derived from credits)
}

function analyzeFrame(ocrResults: { region: string; text: string }[]): SitDetectionState {
    const popupText = ocrResults.find(r => r.region === 'REPORT_POPUP')?.text || '';
    const chatText = ocrResults.find(r => r.region === 'CHAT_AREA')?.text || '';
    
    // Check if report popup exists
    const reportMatch = popupText.match(/(.+?)(?:'s)?\s+Report/i);
    const hasActiveReport = !!reportMatch;
    
    // Check button state to determine if claimed
    const hasClaimButton = /\bClaim\b/i.test(popupText);
    const hasGoToButton = /Go\s*To/i.test(popupText) || /\bBring\b/i.test(popupText);
    
    // Check chat for claim/close events (EXACT Elitelupus format)
    const claimMatch = chatText.match(/\[Elite\s*Reports\]\s*(\w+)\s+claimed\s+(.+?)(?:'s)?\s+report/i);
    const closeMatch = chatText.match(/\[Elite\s*Reports\]\s*You\s+have\s+closed\s+(.+?)(?:'s)?\s+report/i);
    
    // Check for rating/credits message (optional - only appears if user rated)
    const creditsMatch = chatText.match(/\[Elite\s*Admin\s*Stats\]\s*Your\s+performance\s+has\s+earned\s+you\s+(\d+)\s+credits/i);
    const staffRating = creditsMatch ? creditsToStars(parseInt(creditsMatch[1])) : null;
    
    return {
        hasActiveReport,
        isReportClaimed: hasGoToButton && !hasClaimButton,
        reporterName: reportMatch?.[1] || claimMatch?.[2] || null,
        reportedPlayer: popupText.match(/Reported Player:\s*(.+)/i)?.[1] || null,
        reportType: popupText.match(/Report Type:\s*(.+)/i)?.[1] || null,
        staffRating,
    };
}

// Convert credits to star rating
function creditsToStars(credits: number): number {
    const creditMap: Record<number, number> = {
        0: 1,  // 1 star = 0 credits
        2: 2,  // 2 stars = 2 credits
        4: 3,  // 3 stars = 4 credits
        6: 4,  // 4 stars = 6 credits
        8: 5,  // 5 stars = 8 credits
    };
    return creditMap[credits] ?? Math.ceil(credits / 2) + 1;
}
```

### Chat Message Formats (Elitelupus Exact)

These are the exact chat message formats used by the Elite Reports system:

#### Sit Claimed
```
[Elite Reports] ofcWilliam claimed Melky's report.
```

#### Sit Closed
```
[Elite Reports] You have closed Melky's report.
```

#### Staff Rating (Optional - only appears if player rated the sit)
```
[Elite Admin Stats] Your performance has earned you 8 credits.
```

**Credits to Star Rating Conversion:**
| Stars | Credits | Interpretation |
|-------|---------|----------------|
| ⭐ | 0 | Poor |
| ⭐⭐ | 2 | Below Average |
| ⭐⭐⭐ | 4 | Average |
| ⭐⭐⭐⭐ | 6 | Good |
| ⭐⭐⭐⭐⭐ | 8 | Excellent |

**Note**: If no rating message appears within ~5 seconds of closing, the user did not rate the sit.

### Detection Patterns (Elitelupus Exact)

#### Sit Claimed Patterns
```typescript
const SIT_CLAIMED_PATTERNS = [
    // PRIMARY: Exact Elitelupus format
    /\[Elite\s*Reports\]\s*(\w+)\s+claimed\s+(.+?)(?:'s)?\s+report\.?/i,
    // Example: "[Elite Reports] ofcWilliam claimed Melky's report."
    // Captures: [1] = "ofcWilliam" (staff), [2] = "Melky" (reporter)
    
    // SECONDARY: Popup button state change
    /Go\s*To.*Bring.*Close/i,  // Button sequence indicates claimed
];
```

#### Sit Closed Patterns
```typescript
const SIT_CLOSED_PATTERNS = [
    // PRIMARY: Exact Elitelupus format (first-person)
    /\[Elite\s*Reports\]\s*You\s+have\s+closed\s+(.+?)(?:'s)?\s+report\.?/i,
    // Example: "[Elite Reports] You have closed Melky's report."
    // Captures: [1] = "Melky" (reporter)
    
    // SECONDARY: Popup disappearance
    // Detected by: previously had report popup → now no popup text
];
```

#### Staff Rating Detection
```typescript
const STAFF_RATING_PATTERN = 
    /\[Elite\s*Admin\s*Stats\]\s*Your\s+performance\s+has\s+earned\s+you\s+(\d+)\s+credits\.?/i;
// Example: "[Elite Admin Stats] Your performance has earned you 8 credits."
// Captures: [1] = "8" (credits → 5 stars)

// Use within ~5 seconds after sit close to associate rating with the sit
```

#### Report Info Extraction Patterns
```typescript
const REPORT_INFO_PATTERNS = {
    reporterName: /^(.+?)(?:'s)?\s+Report$/im,           // "Melky's Report"
    reportType: /Report\s*Type:\s*(.+?)$/im,             // "Report Type: RDM"
    reportedPlayer: /Reported\s*Player:\s*(.+?)$/im,     // "Reported Player: Courtney Davies"
    reason: /Reason:\s*(.+?)(?=\n|$)/im,                 // "Reason: just randomly killed me..."
};
```

### Implementation: useScreenOCR Hook

```typescript
// hooks/useScreenOCR.ts
import { createWorker, Worker } from 'tesseract.js';
import { useState, useRef, useEffect, useCallback } from 'react';

interface OCRRegion {
    id: string;
    name: string;
    x: number;      // Percentage from left (0-1)
    y: number;      // Percentage from top (0-1)
    width: number;  // Percentage of screen width
    height: number; // Percentage of screen height
    enabled: boolean;
}

interface ReportInfo {
    reporterName: string | null;
    reportedPlayer: string | null;
    reportType: string | null;
    reason: string | null;
}

interface DetectionState {
    hasActiveReport: boolean;
    isReportClaimed: boolean;
    reportInfo: ReportInfo;
    lastClaimEvent: string | null;
    lastCloseEvent: string | null;
}

// ELITELUPUS-SPECIFIC OCR REGIONS (based on actual screenshots)
const ELITELUPUS_OCR_REGIONS: OCRRegion[] = [
    { 
        id: 'report_popup', 
        name: 'Report Popups (Top-Left)', 
        x: 0.0,      // Left edge
        y: 0.0,      // Top edge
        width: 0.20, // ~20% of screen width
        height: 0.50, // ~50% of screen height (stacked popups)
        enabled: true 
    },
    { 
        id: 'chat_area', 
        name: 'Chat Area (Bottom-Left)', 
        x: 0.0,      // Left edge
        y: 0.60,     // 60% down from top
        width: 0.25, // ~25% of screen width
        height: 0.25, // ~25% of screen height
        enabled: true 
    },
];

// ELITELUPUS-SPECIFIC DETECTION PATTERNS (Exact formats)
const PATTERNS = {
    // Chat messages (PRIMARY - most reliable)
    // "[Elite Reports] ofcWilliam claimed Melky's report."
    chatClaimed: /\[Elite\s*Reports\]\s*(\w+)\s+claimed\s+(.+?)(?:'s)?\s+report\.?/i,
    // "[Elite Reports] You have closed Melky's report."
    chatClosed: /\[Elite\s*Reports\]\s*You\s+have\s+closed\s+(.+?)(?:'s)?\s+report\.?/i,
    // "[Elite Admin Stats] Your performance has earned you 8 credits."
    staffRating: /\[Elite\s*Admin\s*Stats\]\s*Your\s+performance\s+has\s+earned\s+you\s+(\d+)\s+credits\.?/i,
    
    // Popup button detection (SECONDARY)
    claimButton: /\bClaim\b/,
    goToButton: /Go\s*To/i,
    bringButton: /\bBring\b/i,
    closeButton: /\bClose\b/i,
    
    // Report info extraction
    reportTitle: /^(.+?)(?:'s)?\s+Report$/im,
    reportType: /Report\s*Type:\s*(.+?)$/im,
    reportedPlayer: /Reported\s*Player:\s*(.+?)$/im,
    reason: /Reason:\s*(.+?)(?=\n|$)/ims,
};

// Convert credits to star rating (Elitelupus specific)
const CREDITS_TO_STARS: Record<number, number> = {
    0: 1,  // 1 star = 0 credits
    2: 2,  // 2 stars = 2 credits
    4: 3,  // 3 stars = 4 credits
    6: 4,  // 4 stars = 6 credits
    8: 5,  // 5 stars = 8 credits
};

function creditsToStars(credits: number): number {
    return CREDITS_TO_STARS[credits] ?? Math.ceil(credits / 2) + 1;
}

export function useScreenOCR(videoStream: MediaStream | null, options: {
    onSitClaimed: (reportInfo: ReportInfo) => void;
    onSitClosed: (reporterName?: string, staffRating?: number) => void;
    onReportDetected: (reportInfo: ReportInfo) => void;
    onStaffRating?: (stars: number, credits: number) => void;
    scanInterval?: number;
}) {
    const [isMonitoring, setIsMonitoring] = useState(false);
    const [ocrRegions, setOcrRegions] = useState(ELITELUPUS_OCR_REGIONS);
    const [lastState, setLastState] = useState<DetectionState | null>(null);
    const [debugText, setDebugText] = useState<string>('');
    const [pendingRating, setPendingRating] = useState<{ stars: number; credits: number } | null>(null);
    
    const workerRef = useRef<Worker | null>(null);
    const canvasRef = useRef<HTMLCanvasElement | null>(null);
    const videoRef = useRef<HTMLVideoElement | null>(null);
    const intervalRef = useRef<NodeJS.Timeout | null>(null);
    const lastClaimTimeRef = useRef<number>(0);
    const lastCloseTimeRef = useRef<number>(0);
    const ratingWindowRef = useRef<NodeJS.Timeout | null>(null);
    
    const DEBOUNCE_MS = 5000; // Prevent duplicate detections
    const RATING_WINDOW_MS = 5000; // Time to wait for rating after close
    
    // Initialize Tesseract worker
    useEffect(() => {
        const initWorker = async () => {
            const worker = await createWorker('eng');
            // Optimize for screen text (monospace fonts, high contrast)
            await worker.setParameters({
                tessedit_char_whitelist: 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 :\'[]()!?,.-_',
            });
            workerRef.current = worker;
        };
        initWorker();
        
        // Create canvas for frame extraction
        canvasRef.current = document.createElement('canvas');
        
        return () => { 
            workerRef.current?.terminate();
            if (intervalRef.current) clearInterval(intervalRef.current);
        };
    }, []);
    
    // Setup video element when stream changes
    useEffect(() => {
        if (!videoStream) return;
        
        const video = document.createElement('video');
        video.srcObject = videoStream;
        video.play();
        videoRef.current = video;
        
        return () => {
            video.pause();
            video.srcObject = null;
        };
    }, [videoStream]);
    
    // Extract region from video frame
    const extractRegion = useCallback((region: OCRRegion): ImageData | null => {
        if (!videoRef.current || !canvasRef.current) return null;
        
        const video = videoRef.current;
        const canvas = canvasRef.current;
        const ctx = canvas.getContext('2d');
        if (!ctx) return null;
        
        // Calculate pixel coordinates
        const x = Math.floor(video.videoWidth * region.x);
        const y = Math.floor(video.videoHeight * region.y);
        const w = Math.floor(video.videoWidth * region.width);
        const h = Math.floor(video.videoHeight * region.height);
        
        canvas.width = w;
        canvas.height = h;
        
        // Draw region to canvas
        ctx.drawImage(video, x, y, w, h, 0, 0, w, h);
        
        // Preprocess for better OCR (increase contrast)
        const imageData = ctx.getImageData(0, 0, w, h);
        preprocessImage(imageData);
        ctx.putImageData(imageData, 0, 0);
        
        return imageData;
    }, []);
    
    // Preprocess image for better OCR accuracy
    const preprocessImage = (imageData: ImageData) => {
        const data = imageData.data;
        for (let i = 0; i < data.length; i += 4) {
            // Convert to grayscale
            const gray = 0.299 * data[i] + 0.587 * data[i + 1] + 0.114 * data[i + 2];
            // Increase contrast
            const contrast = gray < 128 ? 0 : 255;
            data[i] = data[i + 1] = data[i + 2] = contrast;
        }
    };
    
    // Analyze OCR results (Elitelupus-specific patterns)
    const analyzeResults = useCallback((results: { regionId: string; text: string }[]) => {
        const popupText = results.find(r => r.regionId === 'report_popup')?.text || '';
        const chatText = results.find(r => r.regionId === 'chat_area')?.text || '';
        
        // Extract report info from popup
        const reporterMatch = popupText.match(PATTERNS.reportTitle);
        const reportTypeMatch = popupText.match(PATTERNS.reportType);
        const reportedMatch = popupText.match(PATTERNS.reportedPlayer);
        const reasonMatch = popupText.match(PATTERNS.reason);
        
        // Check button state
        const hasClaimButton = PATTERNS.claimButton.test(popupText);
        const hasGoToButton = PATTERNS.goToButton.test(popupText) || PATTERNS.bringButton.test(popupText);
        
        // Check chat for events (EXACT Elitelupus format)
        // "[Elite Reports] ofcWilliam claimed Melky's report."
        const claimMatch = chatText.match(PATTERNS.chatClaimed);
        // "[Elite Reports] You have closed Melky's report."
        const closeMatch = chatText.match(PATTERNS.chatClosed);
        // "[Elite Admin Stats] Your performance has earned you 8 credits."
        const ratingMatch = chatText.match(PATTERNS.staffRating);
        
        // Parse staff rating if present
        let staffRating: { stars: number; credits: number } | null = null;
        if (ratingMatch) {
            const credits = parseInt(ratingMatch[1]);
            staffRating = { credits, stars: creditsToStars(credits) };
        }
        
        return {
            hasActiveReport: !!reporterMatch || hasClaimButton || hasGoToButton,
            isReportClaimed: hasGoToButton && !hasClaimButton,
            reportInfo: {
                reporterName: reporterMatch?.[1]?.trim() || claimMatch?.[2]?.trim() || null,
                reportedPlayer: reportedMatch?.[1]?.trim() || null,
                reportType: reportTypeMatch?.[1]?.trim() || null,
                reason: reasonMatch?.[1]?.trim() || null,
            },
            claimEvent: claimMatch ? {
                staffName: claimMatch[1],      // "ofcWilliam"
                reporterName: claimMatch[2],   // "Melky"
            } : null,
            closeEvent: closeMatch ? {
                reporterName: closeMatch[1],   // "Melky"
            } : null,
            staffRating,
        };
    }, []);
    
    // Main scan loop
    const captureAndAnalyze = useCallback(async () => {
        if (!videoStream || !workerRef.current || !videoRef.current?.videoWidth) return;
        
        const results: { regionId: string; text: string }[] = [];
        
        for (const region of ocrRegions.filter(r => r.enabled)) {
            const imageData = extractRegion(region);
            if (!imageData) continue;
            
            const { data: { text } } = await workerRef.current.recognize(canvasRef.current!);
            results.push({ regionId: region.id, text });
        }
        
        const state = analyzeResults(results);
        setDebugText(JSON.stringify(state, null, 2));
        
        const now = Date.now();
        
        // Detect claim event: "[Elite Reports] ofcWilliam claimed Melky's report."
        if (state.claimEvent || (state.isReportClaimed && lastState && !lastState.isReportClaimed)) {
            if (now - lastClaimTimeRef.current > DEBOUNCE_MS) {
                lastClaimTimeRef.current = now;
                options.onSitClaimed(state.reportInfo);
            }
        }
        
        // Detect close event: "[Elite Reports] You have closed Melky's report."
        if (state.closeEvent || (lastState?.hasActiveReport && !state.hasActiveReport)) {
            if (now - lastCloseTimeRef.current > DEBOUNCE_MS) {
                lastCloseTimeRef.current = now;
                
                // Start watching for rating message (5 second window)
                if (ratingWindowRef.current) clearTimeout(ratingWindowRef.current);
                ratingWindowRef.current = setTimeout(() => {
                    // No rating received within 5 seconds = user didn't rate
                    if (pendingRating === null) {
                        options.onSitClosed(state.closeEvent?.reporterName, undefined);
                    }
                    setPendingRating(null);
                }, RATING_WINDOW_MS);
                
                // Store reporter name for rating association
                setPendingRating(null); // Clear any previous pending
            }
        }
        
        // Detect rating: "[Elite Admin Stats] Your performance has earned you X credits."
        if (state.staffRating && now - lastCloseTimeRef.current < RATING_WINDOW_MS) {
            setPendingRating(state.staffRating);
            options.onStaffRating?.(state.staffRating.stars, state.staffRating.credits);
            
            // Now call onSitClosed with the rating
            options.onSitClosed(lastState?.closeEvent?.reporterName, state.staffRating.stars);
            
            // Clear the rating window timer
            if (ratingWindowRef.current) {
                clearTimeout(ratingWindowRef.current);
                ratingWindowRef.current = null;
            }
        }
        
        // Notify about new unclaimed report (for pre-claim awareness)
        if (state.hasActiveReport && !state.isReportClaimed && (!lastState || !lastState.hasActiveReport)) {
            options.onReportDetected(state.reportInfo);
        }
        
        setLastState(state);
    }, [videoStream, ocrRegions, lastState, extractRegion, analyzeResults, options, pendingRating]);
    
    const startMonitoring = useCallback(() => {
        if (!videoStream || isMonitoring) return;
        
        setIsMonitoring(true);
        intervalRef.current = setInterval(captureAndAnalyze, options.scanInterval || 1500);
    }, [videoStream, isMonitoring, captureAndAnalyze, options.scanInterval]);
    
    const stopMonitoring = useCallback(() => {
        setIsMonitoring(false);
        if (intervalRef.current) {
            clearInterval(intervalRef.current);
            intervalRef.current = null;
        }
        if (ratingWindowRef.current) {
            clearTimeout(ratingWindowRef.current);
            ratingWindowRef.current = null;
        }
    }, []);
    
    return { 
        isMonitoring, 
        startMonitoring, 
        stopMonitoring, 
        ocrRegions, 
        setOcrRegions,
        lastDetectionState: lastState,
        debugText, // For development/testing
    };
}
```

### User Flow with Auto-Detection (Elitelupus)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. STAFF OPENS TOOLBOX                                                  │
│    └─→ Clicks "Share Game Screen" button                                │
│    └─→ Browser prompts: "Share your screen" → Select Garry's Mod window │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. MONITORING MODE (Idle)                                               │
│    ┌──────────────────────────────┐                                     │
│    │  🔴 Monitoring Active        │                                     │
│    │  Status: Waiting for sits... │  ← OCR scanning every 1.5s         │
│    │  [Stop Monitoring]           │                                     │
│    └──────────────────────────────┘                                     │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        ↓ OCR detects "[X]'s Report" popup
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. REPORT DETECTED (Pre-Claim Awareness)                                │
│    ┌──────────────────────────────────┐                                 │
│    │  📋 New Report Detected          │                                 │
│    │  Reporter: Melky                 │  ← Extracted from popup         │
│    │  Type: RDM                       │                                 │
│    │  Reported: Courtney Davies       │                                 │
│    │  ─────────────────────────       │                                 │
│    │  Waiting for you to claim...     │                                 │
│    └──────────────────────────────────┘                                 │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        ↓ OCR: "[Elite Reports] ofcWilliam claimed Melky's report."
                                          OR button changes to "Go To | Bring | Close"
┌─────────────────────────────────────────────────────────────────────────┐
│ 4. SIT CLAIMED → AUTO-START RECORDING                                   │
│    ┌──────────────────────────────────────────┐                         │
│    │  🔴 RECORDING                  00:00:15  │                         │
│    │  ──────────────────────────────────────  │                         │
│    │  Reporter: Melky                         │  ← Auto-populated       │
│    │  Reported: Courtney Davies               │                         │
│    │  Type: RDM                               │                         │
│    │  ──────────────────────────────────────  │                         │
│    │  Steam IDs: [Add...]                     │                         │
│    │  Notes: [________________]               │                         │
│    │                                          │                         │
│    │  [End Sit Manually]                      │  ← Manual fallback      │
│    └──────────────────────────────────────────┘                         │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        ↓ OCR: "[Elite Reports] You have closed Melky's report."
                                          OR popup disappears
┌─────────────────────────────────────────────────────────────────────────┐
│ 5. SIT CLOSED → WAIT FOR RATING (5 second window)                       │
│    ┌──────────────────────────────────────────┐                         │
│    │  ⏳ Sit Closed - Waiting for rating...   │                         │
│    │  Duration: 3:45                          │                         │
│    │  Reporter: Melky                         │                         │
│    └──────────────────────────────────────────┘                         │
└───────────────────────────────────────┬─────────────────────────────────┘
        ↓ (Optional) OCR: "[Elite Admin Stats] Your performance has earned you 8 credits."
        ↓ OR 5 seconds pass with no rating message
┌─────────────────────────────────────────────────────────────────────────┐
│ 6. OUTCOME MODAL (with or without rating)                               │
│    ┌──────────────────────────────────────────┐                         │
│    │  ✅ Sit Completed                         │                         │
│    │  Duration: 3:45                          │                         │
│    │  ──────────────────────────────────────  │                         │
│    │  Player Rating: ⭐⭐⭐⭐⭐ (8 credits)      │  ← Auto-filled if      │
│    │               OR "No rating received"    │    rating detected      │
│    │  ──────────────────────────────────────  │                         │
│    │  What was the outcome?                   │                         │
│    │  ┌─────────┐ ┌─────────┐ ┌─────────┐    │                         │
│    │  │ Warning │ │ Kicked  │ │ Banned  │    │                         │
│    │  └─────────┘ └─────────┘ └─────────┘    │                         │
│    │  ┌─────────┐ ┌─────────┐                │                         │
│    │  │No Action│ │  Other  │                │                         │
│    │  └─────────┘ └─────────┘                │                         │
│    │                                          │                         │
│    │  [Save & Close]                          │                         │
│    └──────────────────────────────────────────┘                         │
└───────────────────────────────────────┬─────────────────────────────────┘
                                        ↓
┌─────────────────────────────────────────────────────────────────────────┐
│ 7. RETURN TO MONITORING (Loop)                                          │
│    └─→ Continue scanning for next report                                │
│    └─→ Counter incremented (+1 sit)                                     │
│    └─→ Recording saved to history                                       │
│    └─→ Rating saved (if received)                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

### Detection Events Summary

| Event | Chat Message Format | Action |
|-------|---------------------|--------|
| **New Report** | N/A (popup detection) | Show "Report Detected" notification |
| **Sit Claimed** | `[Elite Reports] ofcWilliam claimed Melky's report.` | Start recording, show sit panel |
| **Sit Closed** | `[Elite Reports] You have closed Melky's report.` | Stop recording, wait for rating |
| **Staff Rating** | `[Elite Admin Stats] Your performance has earned you 8 credits.` | Auto-fill rating in modal (⭐⭐⭐⭐⭐) |

### Staff Rating (Credits to Stars)

| Chat Message | Credits | Stars | Display |
|--------------|---------|-------|---------|
| `...earned you 0 credits.` | 0 | 1 | ⭐ |
| `...earned you 2 credits.` | 2 | 2 | ⭐⭐ |
| `...earned you 4 credits.` | 4 | 3 | ⭐⭐⭐ |
| `...earned you 6 credits.` | 6 | 4 | ⭐⭐⭐⭐ |
| `...earned you 8 credits.` | 8 | 5 | ⭐⭐⭐⭐⭐ |
| *(no message within 5s)* | - | - | "No rating" |

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| OCR Regions | Draggable/resizable scan areas | Top + Chat |
| Scan Interval | Time between OCR scans | 1500ms |
| Debounce Time | Cooldown between detections | 5000ms |
| Auto-confirm Delay | Seconds before auto-starting | 3s |
| Contrast Boost | Image preprocessing strength | 1.5x |

### Performance Optimizations

| Optimization | Impact |
|--------------|--------|
| Selective regions (not full screen) | ~80% less CPU |
| Web Worker for Tesseract | No UI blocking |
| B/W preprocessing | Better OCR accuracy |
| Configurable scan interval | CPU vs responsiveness trade-off |

### Limitations & Fallback

- OCR may miss text → Manual buttons always available
- False positives → Confirmation popup with dismiss option
- Different fonts/themes → Custom patterns + contrast settings

```tsx
// Manual fallback always visible
<div className="flex gap-2 mt-4 border-t pt-4">
    <Button onClick={manualStartSit} disabled={isRecording}>
        Start Sit Manually
    </Button>
    <Button onClick={manualEndSit} disabled={!isRecording}>
        End Sit Manually
    </Button>
</div>
```

### Browser Requirements

| Browser | Support |
|---------|---------|
| Chrome 72+ | ✅ Full |
| Firefox 66+ | ✅ Full |
| Edge 79+ | ✅ Full |
| Safari 13+ | ⚠️ Limited |

**Note**: HTTPS required (screen capture needs secure context)

---

## Open Questions

1. **Audio Recording**: Should we capture game/voice audio? (Privacy implications)
2. **Multi-Monitor Support**: How to handle staff with multiple monitors?
3. **Interrupted Sits**: What happens if browser crashes during recording?
4. **Offline Support**: Should notes work offline and sync later?
5. **Video Quality Settings**: Should staff choose quality vs. file size?
6. **Batch Operations**: Should management be able to bulk review/delete sits?

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Recording success rate | > 95% |
| Average upload time | < 30 seconds |
| Storage per staff/month | < 10 GB |
| Sit completion rate | > 90% |
| Staff adoption (using recordings) | > 80% |

---

## Appendix

### A. Outcome Codes

| Code | Label | Requires Punishment |
|------|-------|---------------------|
| `no_action` | No Action Taken | No |
| `false_report` | False Report | No |
| `verbal_warning` | Verbal Warning | No |
| `formal_warning` | Formal Warning | No |
| `kick` | Kick | No |
| `ban` | Ban | Yes (duration) |
| `escalated` | Escalated to Higher Staff | No |
| `other` | Other | No |

### B. Rule Categories

Link to existing rules reference system for rule selection in outcome modal.

### C. Browser Compatibility

| Browser | Screen Capture | MediaRecorder | Status |
|---------|----------------|---------------|--------|
| Chrome 72+ | ✅ | ✅ | Fully Supported |
| Firefox 66+ | ✅ | ✅ | Fully Supported |
| Edge 79+ | ✅ | ✅ | Fully Supported |
| Safari 13+ | ⚠️ | ⚠️ | Limited Support |
| Opera 60+ | ✅ | ✅ | Fully Supported |

**Recommendation**: Chrome or Firefox for best experience.

---

## Server-Side OCR Option (Performance Enhancement)

### Overview

The browser-based OCR (Tesseract.js) approach works but can cause significant CPU load on the end user's machine, especially during gameplay. This section outlines an alternative **server-side OCR** approach that offloads processing to the backend.

### Comparison: Client-Side vs Server-Side OCR

| Aspect | Client-Side (Tesseract.js) | Server-Side (pytesseract) |
|--------|---------------------------|---------------------------|
| **CPU Impact on User** | High (30-50% CPU during scans) | Minimal (only capture + encode) |
| **Network Usage** | None | ~50-200 KB per frame (JPEG) |
| **Latency** | Instant (local processing) | 100-500ms (network + processing) |
| **Privacy** | Screen never leaves device | Screen frames sent to server |
| **Server Cost** | None | CPU/memory on backend |
| **Scalability** | Each client independent | Server load increases with users |
| **Offline Support** | Works offline | Requires connection |

### Recommendation

Implement **both modes** with user preference:
- **Client-Side (Default)**: For users with capable machines who prioritize privacy
- **Server-Side**: For users experiencing performance issues, or on lower-end hardware

### Server-Side Architecture (Microservice)

The OCR processor is a **separate, scalable microservice** independent from the main Django backend. This allows:
- Horizontal scaling (run multiple OCR workers)
- Independent deployment and updates
- Resource isolation (OCR doesn't impact main app)
- Technology flexibility (can swap to different OCR engines)

```
┌─────────────────────────────────────────────────────────────────────────┐
│ FRONTEND (Browser)                                                      │
│                                                                         │
│  ┌─────────────────────┐    ┌──────────────────────────────────────┐   │
│  │ Screen Capture      │ -> │ Extract Regions + JPEG Encode        │   │
│  │ (getDisplayMedia)   │    │ (Canvas -> toBlob, quality: 0.7)     │   │
│  └─────────────────────┘    └──────────────────────────────────────┘   │
│                                           │                             │
│                                           ▼                             │
│                              ┌────────────────────────┐                │
│                              │ WebSocket: Binary Frame │                │
│                              │ + JSON metadata         │                │
│                              └────────────────────────┘                │
│                                           │                             │
└───────────────────────────────────────────│─────────────────────────────┘
                                            │
                                            ▼
┌───────────────────────────────────────────────────────────────────────────┐
│ BACKEND (Django Channels - Router Service)                               │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐ │
│  │ OCRConsumer (WebSocket)                                              │ │
│  │                                                                       │ │
│  │  1. Receive binary frame data + metadata                             │ │
│  │  2. Authenticate user (JWT validation)                               │ │
│  │  3. Publish to Redis queue: "ocr:jobs:{user_id}"                     │ │
│  │  4. Wait for result on: "ocr:results:{job_id}"                       │ │
│  │  5. Send detection results back via WebSocket                        │ │
│  │                                                                       │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
└─────────────────────────────┬─────────────────────────────────────────────┘
                              │
                              ▼ Redis Pub/Sub
┌───────────────────────────────────────────────────────────────────────────┐
│ REDIS (Message Broker)                                                    │
│                                                                           │
│  ┌───────────────────────┐    ┌─────────────────────────────────────┐   │
│  │ Queue: ocr:jobs       │    │ Queue: ocr:results                  │   │
│  │ - Frame data (binary) │    │ - Detection events                  │   │
│  │ - Region definitions  │    │ - OCR text results                  │   │
│  │ - User ID             │    │ - Processing metadata               │   │
│  │ - Job ID              │    │ - Timestamps                        │   │
│  └───────────────────────┘    └─────────────────────────────────────┘   │
│                                                                           │
└─────────────────────────────┬─────────────────────────────────────────────┘
                              │
                              ▼ Multiple workers pull jobs
┌───────────────────────────────────────────────────────────────────────────┐
│ OCR SERVICE (Scalable Python Microservice)                                │
│                                                                           │
│  ┌──────────────────────┐  ┌──────────────────────┐  ┌────────────────┐ │
│  │ OCR Worker 1         │  │ OCR Worker 2         │  │ OCR Worker N   │ │
│  │                      │  │                      │  │                │ │
│  │ 1. Poll Redis queue  │  │ 1. Poll Redis queue  │  │ (Scale to N)   │ │
│  │ 2. Decode JPEG       │  │ 2. Decode JPEG       │  │                │ │
│  │ 3. Preprocess image  │  │ 3. Preprocess image  │  │                │ │
│  │ 4. Run pytesseract   │  │ 4. Run pytesseract   │  │                │ │
│  │ 5. Pattern matching  │  │ 5. Pattern matching  │  │                │ │
│  │ 6. Publish results   │  │ 6. Publish results   │  │                │ │
│  │                      │  │                      │  │                │ │
│  │ Status: Processing   │  │ Status: Idle         │  │ Status: Ready  │ │
│  └──────────────────────┘  └──────────────────────┘  └────────────────┘ │
│                                                                           │
│  Shared: Tesseract engine, OpenCV, pattern library                       │
│  Load Balancing: Round-robin via Redis queue consumption                 │
│  Health Checks: Heartbeat to Redis every 30s                             │
│                                                                           │
└───────────────────────────────────────────────────────────────────────────┘
```

**Key Components:**

1. **Backend Router**: Django Channels WebSocket that handles client connections and routes jobs
2. **Redis**: Message broker for job distribution and result delivery
3. **OCR Workers**: Independent Python processes that consume jobs and process frames
4. **Load Balancer**: Redis queue ensures fair distribution across workers

**Scaling Strategy:**
```bash
# Run 1 worker (low load)
docker-compose up -d ocr_service

# Scale to 3 workers (medium load)
docker-compose up -d --scale ocr_service=3

# Scale to 10 workers (high load)
docker-compose up -d --scale ocr_service=10
```

### Backend Implementation

#### 1. Backend Router (Django - WebSocket Handler)

The main backend only handles WebSocket connections and job routing - no OCR processing.

```python
# backend/requirements.txt (add these)
redis>=5.0.0
hiredis>=2.2.0  # Faster Redis parsing
```

```python
# backend/apps/counters/consumers/ocr_consumer.py
import json
import uuid
import asyncio
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

class OCRConsumer(AsyncWebsocketConsumer):
    """WebSocket router for OCR jobs - no processing done here."""
    
  ocr_service/ocr_engine.py
import pytesseract
import cv2
import numpy as np
from PIL import Image
import io
import re
from dataclasses import dataclass
from typing import List
import time

# Optimized tesseract config for game text
TESSERACT_CONFIG = (
    '--oem 3 '  # LSTM + legacy engine
    '--psm 6 '  # Assume uniform block of text
    '-c tessedit_char_whitelist="ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789[]:\\'\\' .-_"'
)

# Elitelupus-specific patterns
OCR_PATTERNS = {
    'claim': re.compile(r'\[Elite Reports\]\s*(\w+)\s+claimed\s+(.+?)[\'']s\s+report', re.IGNORECASE),
    'close': re.compile(r'\[Elite Reports\]\s*You have closed\s+(.+?)[\'']s\s+report', re.IGNORECASE),
    'claim_button': re.compile(r'CLAIM\s*REPORT', re.IGNORECASE),
    'close_button': re.compile(r'CLOSE\s*REPORT', re.IGNORECASE),
}

@dataclass
class OCRResult:
    text: str
    region: str
    processing_time_ms: float

@dataclass
class DetectionEvent:
    event_type: str
    region: str
    raw_text: str
    parsed_data: dict

class OCREngine:
    """OCR processing engine for game text detection."""
    
    def __init__(self):
        # Verify tesseract is available
        try:
            pytesseract.get_tesseract_version()
            print(f"✅ Tesseract {pytesseract.get_tesseract_version()} initialized")
        except Exception as e:
            raise RuntimeError(f"Tesseract OCR engine not available: {e}")
    
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply slight blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        # Adaptive thresholding
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def process_frame(self, jpeg_data: bytes, regions: List[dict]) -> List[OCRResult]:
        """Process frame and extract text from specified regions."""
        # Decode JPEG
        image = Image.open(io.BytesIO(jpeg_data))
        img_array = np.array(image)
        
        results = []
        img_height, img_width = img_array.shape[:2]
        
        for region in regions:
            start_time = time.time()
            
            # Calculate pixel coordinates
            x = int(region['x'] * img_width)
            y = int(region['y'] * img_height)
            w = int(region['width'] * img_width)
            h = int(region['height'] * img_height)
            
            # Extract and process region
            region_img = img_array[y:y+h, x:x+w]
            processed = self.preprocess_image(region_img)
            
            # OCR
            text = pytesseract.image_to_string(processed, config=TESSERACT_CONFIG)
            processing_time = (time.time() - start_time) * 1000
            
            results.append(OCRResult(
                text=text.strip(),
                region=region['name'],
                processing_time_ms=processing_time
            ))
        
        return results
    
    def detect_events(self, ocr_results: List[OCRResult]) -> List[DetectionEvent]:
        """Parse OCR results for sit detection events."""
        events = []
        
        for result in ocr_results:
            text = result.text
            
            for event_type, pattern in OCR_PATTERNS.items():
                match = pattern.search(text)
                if match:
                    parsed_data = {}
                    if event_type == 'claim':
                        parsed_data = {
                            'staff_name': match.group(1),
                            'reporter_name': match.group(2)
                        }
                    elif event_type == 'close':
                        parsed_data = {
                            'reporter_name': match.group(1)
                        }
                    
                    events.append(DetectionEvent(
                        event_type=event_type,
                        region=result.region,
                        raw_text=text,
                        parsed_data=parsed_data
                    ))
        
        return events
```

**Worker Process:**
```python
# ocr_service/worker.py
import redis
import json
import logging
import time
from ocr_engine import OCREngine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OCRWorker:
    """Scalable OCR worker that processes jobs from Redis queue."""
    
    def __init__(self, redis_url='redis://redis:6379', worker_id=None):
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.worker_id = worker_id or f"worker-{int(time.time())}"
        self.ocr_engine = OCREngine()
        self.jobs_processed = 0
        
        logger.info(f"🚀 OCR Worker {self.worker_id} started")
    
    def run(self):
        """Main worker loop - poll Redis for jobs."""
        logger.info(f"👷 Worker {self.worker_id} ready - waiting for jobs...")
        
        while True:
            try:
                # Blocking pop from Redis queue (30s timeout)
                job_data = self.redis_client.blpop('ocr:jobs', timeout=30)
                
                if job_data is None:
                    # No job within timeout - send heartbeat
                    self._heartbeat()
                    continue
                
                # Parse job
                _, job_json = job_data
                job = json.loads(job_json)
                
                # Process job
                self._process_job(job)
                
            except KeyboardInterrupt:
                logger.info(f"Worker {self.worker_id} shutting down...")
                break
            except Exception as e:
                logger.exception(f"Worker error: {e}")
                time.sleep(1)
    
    def _process_job(self, job: dict):
        """Process a single OCR job."""
        job_id = job['job_id']
        user_id = job['user_id']
        
        start_time = time.time()
        logger.info(f"📋 Processing job {job_id} (user {user_id})")
        
        try:
            # Fetch frame data from Redis
            frame_data = self.redis_client.get(f"ocr:frame:{job_id}")
            
            if not frame_data:
                logger.warning(f"Frame {job_id} not found (expired?)")
                self._publish_error(job_id, "Frame data not found")
                return
            
            # Default regions (can be customized per job)
            regions = [
                {'name': 'chat', 'x': 0, 'y': 0.7, 'width': 0.35, 'height': 0.25},
                {'name': 'popup', 'x': 0, 'y': 0.1, 'width': 0.3, 'height': 0.4},
            ]
            
            # Run OCR
            ocr_results = self.ocr_engine.process_frame(frame_data, regions)
            events = self.ocr_engine.detect_events(ocr_results)
            
            # Prepare result
            result = {
                'type': 'ocr_result',
                'job_id': job_id,
                'results': [
                    {
                        'region': r.region,
                        'text': r.text,
                        'processing_time_ms': r.processing_time_ms
                    }
                    for r in ocr_results
                ],
                'events': [
                    {
                        'event_type': e.event_type,
                        'region': e.region,
                        'parsed_data': e.parsed_data
                    }
                    for e in events
                ],
                'worker_id': self.worker_id,
                'total_time_ms': (time.time() - start_time) * 1000
            }
            
            # Publish result to Redis (10s expiry)
            self.redis_client.setex(
                f"ocr:result:{job_id}",
                10,
                json.dumps(result)
            )
            
            self.jobs_processed += 1
            logger.info(
                f"✅ Job {job_id} complete in {result['total_time_ms']:.1f}ms "
                f"(total: {self.jobs_processed})"
            )
            
        except Exception as e:
            logger.exception(f"Error processing job {job_id}: {e}")
            self._publish_error(job_id, str(e))
    
    def _publish_error(self, job_id: str, error: str):
        """Publish error result."""
        result = {
            'type': 'error',
            'job_id': job_id,
            'message': error,
            'worker_id': self.worker_id
        }
        self.redis_client.setex(
            f"ocr:result:{job_id}",
            10,
            json.dumps(result)
        )
    
    def _heartbeat(self):
        """Send heartbeat to Redis."""
        self.redis_client.setex(
            f"ocr:worker:{self.worker_id}",
            60,
            json.dumps({
                'worker_id': self.worker_id,
                'jobs_processed': self.jobs_processed,
                'timestamp': time.time()
            })
        )

if __name__ == '__main__':
    import os
    worker = OCRWorker(
        redis_url=os.getenv('REDIS_URL', 'redis://redis:6379'),
        worker_id=os.getenv('WORKER_ID', None)
    )
    worker.run()
    def preprocess_image(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # Increase contrast using CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        # Apply slight blur to reduce noise
        blurred = cv2.GaussianBlur(enhanced, (1, 1), 0)
        
        # Adaptive thresholding for text extraction
        binary = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )
        
        return binary
    
    def process_frame(self, jpeg_data: bytes, regions: List[dict]) -> List[OCRResult]:
        """Process a single frame from the client.
        
        Args:
            jpeg_data: Raw JPEG bytes from client
            regions: List of region definitions [{name, x, y, width, height}]
                    Coordinates are percentages (0-1)
        
        Returns:
            List of OCR results for each region
        """
        import time
        
        # Decode JPEG
        image = Image.open(io.BytesIO(jpeg_data))
        img_array = np.array(image)
        
        results = []
        img_height, img_width = img_array.shape[:2]
        
        for region in regions:
            start_time = time.time()
            
            # Calculate pixel coordinates from percentages
            x = int(region['x'] * img_width)
            y = int(region['y'] * img_height)
            w = int(region['width'] * img_width)
            h = int(region['height'] * img_height)
            
            # Extract region
            region_img = img_array[y:y+h, x:x+w]
            
            # Preprocess
            processed = self.preprocess_image(region_img)
            
            # OCR
            text = pytesseract.image_to_string(processed, config=TESSERACT_CONFIG)
            
            processing_time = (time.time() - start_time) * 1000
            
            results.append(OCRResult(
                text=text.strip(),
                region=region['name'],
                processing_time_ms=processing_time
            ))
            
            logger.debug(f"OCR [{region['name']}]: {len(text)} chars in {processing_time:.1f}ms")
        
        return results
    
    def detect_events(self, ocr_results: List[OCRResult]) -> List[DetectionEvent]:
        """Parse OCR results for sit detection events."""
        events = []
        
        for result in ocr_results:
            text = result.text
            
            # Check each pattern
            for event_type, pattern in OCR_PATTERNS.items():
                match = pattern.search(text)
                if match:
                    parsed_data = {}
                    if event_type == 'claim':
                        parsed_data = {
                            'staff_name': match.group(1),
                            'reporter_name': match.group(2)
                        }
                    elif event_type == 'close':
                        parsed_data = {
                            'reporter_name': match.group(1)
                        }
                    
                    events.append(DetectionEvent(
                        event_type=event_type,
                        region=result.region,
                        raw_text=text,
                        parsed_data=parsed_data
                    ))
                    
                    logger.info(f"Detected {event_type} event: {parsed_data}")
        
        return events

# Singleton instance
_ocr_service: Optional[OCRService] = None

def get_ocr_service() -> OCRService:
    global _ocr_service
    if _ocr_service is None:
        _ocr_service = OCRService()
    return _ocr_service
```

#### 3. WebSocket Consumer

```python
# backend/apps/counters/consumers/ocr_consumer.py
import json
import logging
from channels.generic.websocket import AsyncWebsocketConsumer
from asgiref.sync import sync_to_async
from ..services.ocr_service import get_ocr_service

logger = logging.getLogger(__name__)

# Default regions matching frontend
DEFAULT_REGIONS = [
    {'name': 'chat', 'x': 0, 'y': 0.7, 'width': 0.35, 'height': 0.25},
    {'name': 'popup', 'x': 0, 'y': 0.1, 'width': 0.3, 'height': 0.4},
]

class OCRConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for server-side OCR processing."""
    
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return
        
        self.ocr_service = get_ocr_service()
        self.regions = DEFAULT_REGIONS.copy()
        
        await self.accept()
        logger.info(f"OCR WebSocket connected for user {self.user.id}")
    
    async def disconnect(self, close_code):
        logger.info(f"OCR WebSocket disconnected: {close_code}")
    
    async def receive(self, text_data=None, bytes_data=None):
        """Handle incoming frames.
        
        Text messages: JSON configuration updates
        Binary messages: JPEG frame data
        """
        if text_data:
            # Configuration message
            data = json.loads(text_data)
            if data.get('type') == 'config':
                if 'regions' in data:
                    self.regions = data['regions']
                await self.send(text_data=json.dumps({
                    'type': 'config_ack',
                    'regions': self.regions
                }))
        
        elif bytes_data:
            # Frame data - process OCR
            try:
                results = await sync_to_async(self.ocr_service.process_frame)(
                    bytes_data, self.regions
                )
                
                events = await sync_to_async(self.ocr_service.detect_events)(results)
                
                # Send results back
                await self.send(text_data=json.dumps({
                    'type': 'ocr_result',
                    'results': [
                        {
                            'region': r.region,
                            'text': r.text,
                            'processing_time_ms': r.processing_time_ms
                        }
                        for r in results
                    ],
                    'events': [
                        {
                            'event_type': e.event_type,
                            'region': e.region,
                            'parsed_data': e.parsed_data
                        }
                        for e in events
                    ]
                }))
                
            except Exception as e:
                logger.exception(f"OCR processing error: {e}")
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': str(e)
                }))
```

#### 4. URL Routing

```python
# backend/apps/counters/routing.py (add to existing)
from django.urls import path
from .consumers.ocr_consumer import OCRConsumer

websocket_urlpatterns = [
    # ... existing patterns
    path('ws/ocr/', OCRConsumer.as_asgi()),
]
```

### Frontend Implementation (Server-Side Mode)

#### 1. OCR Mode Hook

```typescript
// frontend/src/hooks/useServerSideOCR.ts
'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';

interface OCREvent {
  event_type: 'claim' | 'close' | 'claim_button' | 'close_button';
  region: string;
  parsed_data: Record<string, string>;
}

interface ServerOCROptions {
  scanIntervalMs?: number;
  imageQuality?: number;  // 0-1 for JPEG quality
  regions?: Array<{ name: string; x: number; y: number; width: number; height: number }>;
  onDetection?: (event: OCREvent) => void;
  onError?: (error: string) => void;
}

const DEFAULT_REGIONS = [
  { name: 'chat', x: 0, y: 0.7, width: 0.35, height: 0.25 },
  { name: 'popup', x: 0, y: 0.1, width: 0.3, height: 0.4 },
];

export function useServerSideOCR(
  stream: MediaStream | null,
  options: ServerOCROptions = {}
) {
  const {
    scanIntervalMs = 1500,
    imageQuality = 0.7,
    regions = DEFAULT_REGIONS,
    onDetection,
    onError,
  } = options;
  
  const { token } = useAuth();
  const wsRef = useRef<WebSocket | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  
  const [isConnected, setIsConnected] = useState(false);
  const [isScanning, setIsScanning] = useState(false);
  const [lastResult, setLastResult] = useState<string>('');
  const [processingTimeMs, setProcessingTimeMs] = useState(0);
  const [scanCount, setScanCount] = useState(0);
  
  // Initialize canvas and video elements
  useEffect(() => {
    if (typeof document !== 'undefined') {
      canvasRef.current = document.createElement('canvas');
      videoRef.current = document.createElement('video');
      videoRef.current.autoplay = true;
      videoRef.current.muted = true;
    }
  }, []);
  
  // Connect stream to video
  useEffect(() => {
    if (videoRef.current && stream) {
      videoRef.current.srcObject = stream;
      videoRef.current.play();
    }
  }, [stream]);
  
  // Connect WebSocket
  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL}/ws/ocr/?token=${token}`;
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      setIsConnected(true);
      // Send region config
      ws.send(JSON.stringify({ type: 'config', regions }));
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      
      if (data.type === 'ocr_result') {
        // Update state with results
        const totalTime = data.results.reduce(
          (sum: number, r: any) => sum + r.processing_time_ms, 0
        );
        setProcessingTimeMs(totalTime);
        
        const combinedText = data.results.map((r: any) => r.text).join(' ');
        setLastResult(combinedText);
        setScanCount(prev => prev + 1);
        
        // Emit detection events
        for (const event of data.events) {
          onDetection?.(event);
        }
      } else if (data.type === 'error') {
        onError?.(data.message);
      }
    };
    
    ws.onclose = () => setIsConnected(false);
    ws.onerror = () => onError?.('WebSocket connection error');
    
    wsRef.current = ws;
  }, [token, regions, onDetection, onError]);
  
  // Capture and send frame
  const captureAndSendFrame = useCallback(() => {
    if (!canvasRef.current || !videoRef.current || !wsRef.current) return;
    if (wsRef.current.readyState !== WebSocket.OPEN) return;
    
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    if (video.videoWidth === 0 || video.videoHeight === 0) return;
    
    // Set canvas to full video size
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    
    // Draw frame
    ctx.drawImage(video, 0, 0);
    
    // Convert to JPEG blob and send
    canvas.toBlob((blob) => {
      if (blob && wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(blob);
      }
    }, 'image/jpeg', imageQuality);
   yaml
# docker-compose.yml - Add OCR microservice
version: '3.8'

services:
  # ... existing services (db, redis, backend, frontend)
  
  ocr_service:
    build: ./ocr_service
    container_name: elitelupus_ocr_worker
    restart: unless-stopped
    depends_on:
      - redis
    environment:
      - REDIS_URL=redis://redis:6379
      - WORKER_ID=${HOSTNAME:-worker-1}
      - LOG_LEVEL=INFO
    networks:
      - app-network
    deploy:
      resources:
        limits:
          cpus: '1.0'      # Limit CPU per worker
          memory: 512M     # Limit RAM per worker
        reservations:
          cpus: '0.5'
          memory: 256M
    healthcheck:
      test: ["CMD", "python", "-c", "import redis; r=redis.from_url('redis://redis:6379'); r.ping()"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

networks:
  app-network:
    driver: bridge
```

**Scaling Commands:**

```bash
# Start with 1 worker (default)
docker-compose up -d ocr_service

# Scale to 3 workers for medium load
docker-compose up -d --scale ocr_service=3

# Scale to 5 workers for high load
docker-compose up -d --scale ocr_service=5

# Scale down to 2 workers
docker-compose up -d --scale ocr_service=2

# View worker status
docker-compose ps ocr_service

# View logs from all workers
docker-compose logs -f ocr_service

# View logs from specific worker
docker logs elitelupus_ocr_worker_1
```

**Production Deployment (Kubernetes):**

```yaml
# k8s/ocr-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ocr-service
spec:
  replicas: 3  # Default 3 workers
  selector:
    matchLabels:
      app: ocr-service
  template:
    metadata:
      labels:
        app: ocr-service
    spec:
      containers:
      - name: ocr-worker
        image: elitelupus/ocr-service:latest
        env:
        - name: REDIS_URL
          value: "redis://redis-service:6379"
        resources:
     Resource Planning (Per OCR Worker)

| Workers | Concurrent Users | Total RAM | Total CPU | Avg Latency |
|---------|------------------|-----------|-----------|-------------|
| 1 | 1-3 | 256 MB | 0.5 core | < 200ms |
| 2 | 4-8 | 512 MB | 1 core | < 250ms |
| 3 | 9-15 | 768 MB | 1.5 cores | < 300ms |
| 5 | 16-30 | 1.25 GB | 2.5 cores | < 350ms |
| 10 | 31-60 | 2.5 GB | 5 cores | < 400ms |
| 20+ | 60+ | Scale horizontally | Scale horizontally | < 500ms |

**Key Metrics:**
- **Each worker**: ~256MB RAM, 0.5 CPU core
- **Processing capacity**: ~2-3 users per worker
- **Frame processing time**: 150-300ms per frame
- **Queue throughput**: ~1000 jobs/minute per worker
            command:
            - python
     Horizontal Scaling**: Add more OCR workers during peak hours
   ```bash
   docker-compose up -d --scale ocr_service=10
   ```

2. **Frame Difference Detection**: Only send frames when screen changes
   ```typescript
   // Client-side optimization
   if (frameHashChanged(currentFrame, lastFrame)) {
     sendToOCR(currentFrame);
   }
   ```

3. **Resolution Reduction**: Scale down before sending (50% sufficient)
   ```typescript
   canvas.width = video.videoWidth * 0.5;
   canvas.height = video.videoHeight * 0.5;
   ```

4. **Adaptive Scan Intervals**: Slow down when idle
   ```typescript
   const interval = hasActiveReport ? 1000 : 3000;  // Fast when active
   ```

5. **Worker Auto-scaling**: Use Kubernetes HPA for automatic scaling
   - Scale up when CPU > 70%
   - Scale down when CPU < 30%
   - Min 2 workers, max 20 workers

6. **Redis Optimization**: Use connection pooling and pipelining
   ```python
   # Use connection pool
   pool = redis.ConnectionPool(host='redis', port=6379, db=0)
   redis_client = redis.Redis(connection_pool=pool)
   ```

7. **Monitoring & Alerts**: Track worker health and queue depth
   ```python
   # Monitor queue depth
   queue_depth = redis_client.llen('ocr:jobs')
   if queue_depth > 100:
       alert("OCR queue backlog - scale up workers")
   ```
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ocr-service-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ocr-service
  minReplicas: 2
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70);
    
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, []);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopScanning();
    };
  }, [stopScanning]);
  
  return {
    isConnected,
    isScanning,
    lastResult,
    processingTimeMs,
    scanCount,
    startScanning,
    stopScanning,
  };
}
```

#### 2. User Preference for OCR Mode

Add to user preferences model:

```python
# Add to UserSitPreferences model
ocr_mode = models.CharField(
    max_length=20,
    choices=[('client', 'Client-Side'), ('server', 'Server-Side')],
    default='client',
    help_text='Where to process OCR: locally or on server'
)
```

```typescript
// Add to preferences UI
<div className="flex items-center justify-between">
  <div>
    <h4 className="text-sm font-medium text-gray-900 dark:text-white">
      OCR Processing Mo
   - WebSocket validates JWT token before accepting connection
   - Each job includes user_id for audit trail
   
2. **Rate Limiting**: 
   - Max 2 frames/second per user (enforced at WebSocket layer)
   - Redis rate limiter: `INCR ocr:rate:{user_id}` with 1s expiry
   
3. **Frame Validation**: 
   - Verify JPEG format and magic bytes
   - Max size 500KB per frame
   - Reject malformed data
   
4. **Privacy & Data Retention**:
   - Frames stored in Redis with 10s TTL (auto-deletion)
   - Workers process in-memory only - no disk writes
   - Results stored with 10s TTL
   - No logging of frame content
   
5. **Network Security**:
   - WSS (WebSocket Secure) in production
   - OCR workers isolated in private network
   - Redis requires AUTH password
   
6. **Worker Isolation**:
   - Each worker runs in separate container
   - No shared file system
   - Resource limits prevent DoS
   
7. **Audit Trail**:
   ```python
   # Log all OCR jobs
   logger.info(f"OCR job {job_id} by user {user_id} - {len(frame)} bytes")
   ```
    </p>
  </div>
  <select
    value={preferences.ocr_mode}
    onChange={(e) => handleChange('ocr_mode', e.target.value)}
  # Monitoring & Observability

#### Metrics to Track

1. **Worker Metrics**:
   - Active workers: `redis.keys("ocr:worker:*")`
   - Jobs processed per worker
   - Average processing time
   - Error rate

2. **Queue Metrics**:
   - Queue depth: `redis.llen("ocr:jobs")`
   - Jobs waiting > 5s
   - Jobs timing out

3. **Performance Metrics**:
   - P50, P95, P99 latency
   - Frame processing time
   - Network transfer time

4. **Health Dashboard**:
   ```python
   # backend/apps/counters/views.py - Admin endpoint
   @api_view(['GET'])
   @permission_classes([IsAdminUser])
   def ocr_health(request):
       redis_client = redis.from_url('redis://redis:6379')
       
       # Count active workers
       worker_keys = redis_client.keys('ocr:worker:*')
       workers = [
           json.loads(redis_client.get(key))
           for key in worker_keys
       ]
       
       # Queue depth
       queue_depth = redis_client.llen('ocr:jobs')
       
       return Response({
           'status': 'healthy' if len(workers) > 0 else 'degraded',
           'active_workers': len(workers),
           'workers': workers,
           'queue_depth': queue_depth,
           'timestamp': time.time()
       })
   ```

#### Logging

```python
# Structured logging in workers
import structlog

logger = structlog.get_logger()

logger.info(
    "ocr.job.complete",
    job_id=job_id,
    user_id=user_id,
    processing_time_ms=processing_time,
    worker_id=worker_id,
    events_detected=len(events)
)
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | - | Initial specification |
| 1.1 | 2026-01-02 | - | Added server-side OCR option for performance |
| 1.2 | 2026-01-02 | - | Refactored OCR to separate scalable microservi
```

### Performance Considerations

#### Server-Side Resource Usage

| Concurrent Users | RAM (est.) | CPU Cores | Processing Time |
|------------------|------------|-----------|-----------------|
| 1-5 | 512 MB | 1 | < 200ms/frame |
| 5-20 | 1 GB | 2 | < 300ms/frame |
| 20-50 | 2 GB | 4 | < 400ms/frame |
| 50+ | Consider Celery queue | Scale horizontally |

#### Bandwidth Estimation

- Frame size (JPEG, quality 0.7): ~50-150 KB
- Scan interval: 1.5 seconds
- Per user: ~200-600 KB/min = ~12-36 MB/hour
- Response data: ~1-2 KB/scan (negligible)

#### Optimization Strategies

1. **Only send changed regions**: Detect frame differences client-side
2. **Reduce resolution**: Scale down before sending (50% sufficient for OCR)
3. **Adaptive intervals**: Increase interval when no events detected
4. **Connection pooling**: Reuse Tesseract worker instances
5. **Celery for scale**: Offload to background workers during high load

### Security Considerations

1. **Authentication**: WebSocket must validate JWT token
2. **Rate limiting**: Max 2 frames/second per user
3. **Frame validation**: Verify JPEG format, max size 500KB
4. **Privacy**: Frames processed in-memory, never stored
5. **Encryption**: WSS (WebSocket Secure) in production

### Docker Configuration

```dockerfile
# Add to backend Dockerfile
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    && rm -rf /var/lib/apt/lists/*
```

```yaml
# docker-compose.yml - Add OCR worker (optional, for scale)
ocr_worker:
  build: ./backend
  command: celery -A config worker -Q ocr -c 2
  depends_on:
    - redis
    - db
  environment:
    - CELERY_QUEUES=ocr
```

---

## System Administration - OCR Monitoring Dashboard

### Overview

SYSADMIN role gets access to a dedicated monitoring dashboard for the OCR microservice infrastructure. This provides real-time visibility into worker health, queue performance, and system capacity.

### Access Control

| Role | Access |
|------|--------|
| SYSADMIN | Full access (view, control, restart) |
| Manager | View only |
| All others | No access |

### Page Location

```
/dashboard/admin/ocr-monitor
```

### Backend API Endpoints

#### 1. OCR Health & Worker Status

```python
# backend/apps/counters/views.py

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import redis
import json
from datetime import datetime, timedelta

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ocr_health(request):
    """Get OCR service health and worker status."""
    # Only SYSADMIN can access
    if request.user.role != 'SYSADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    redis_client = redis.from_url('redis://redis:6379', decode_responses=True)
    
    try:
        # Get all active workers
        worker_keys = redis_client.keys('ocr:worker:*')
        workers = []
        for key in worker_keys:
            worker_data = json.loads(redis_client.get(key))
            workers.append({
                'worker_id': worker_data['worker_id'],
                'jobs_processed': worker_data['jobs_processed'],
                'last_heartbeat': datetime.fromtimestamp(worker_data['timestamp']).isoformat(),
                'uptime_seconds': time.time() - worker_data.get('started_at', worker_data['timestamp']),
                'status': 'healthy' if time.time() - worker_data['timestamp'] < 60 else 'stale'
            })
        
        # Get queue metrics
        queue_depth = redis_client.llen('ocr:jobs')
        
        # Get recent job statistics (last 5 minutes)
        job_stats_key = 'ocr:stats:recent'
        recent_jobs = redis_client.lrange(job_stats_key, 0, -1)
        recent_jobs_data = [json.loads(job) for job in recent_jobs]
        
        # Calculate metrics
        total_jobs = sum(w['jobs_processed'] for w in workers)
        avg_processing_time = (
            sum(job['processing_time_ms'] for job in recent_jobs_data) / len(recent_jobs_data)
            if recent_jobs_data else 0
        )
        
        return Response({
            'status': 'healthy' if len(workers) > 0 and queue_depth < 100 else 'degraded',
            'workers': {
                'active_count': len(workers),
                'workers': workers,
                'total_jobs_processed': total_jobs
            },
            'queue': {
                'depth': queue_depth,
                'status': 'normal' if queue_depth < 50 else 'high' if queue_depth < 100 else 'critical'
            },
            'performance': {
                'avg_processing_time_ms': round(avg_processing_time, 2),
                'jobs_last_5min': len(recent_jobs_data),
                'throughput_per_min': len(recent_jobs_data) / 5 * 60
            },
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return Response({
            'status': 'error',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ocr_queue_jobs(request):
    """Get list of jobs currently in queue."""
    if request.user.role != 'SYSADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    redis_client = redis.from_url('redis://redis:6379', decode_responses=True)
    
    # Get jobs from queue (first 100)
    queue_jobs = redis_client.lrange('ocr:jobs', 0, 99)
    
    jobs = []
    for job_json in queue_jobs:
        job = json.loads(job_json)
        jobs.append({
            'job_id': job['job_id'],
            'user_id': job['user_id'],
            'frame_size': job['frame_size'],
            'queued_at': datetime.fromtimestamp(job['timestamp']).isoformat(),
            'wait_time_seconds': time.time() - job['timestamp']
        })
    
    return Response({
        'queue_depth': len(jobs),
        'jobs': jobs,
        'showing': f"1-{len(jobs)} of {redis_client.llen('ocr:jobs')}"
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def ocr_flush_queue(request):
    """Emergency: Flush the OCR job queue."""
    if request.user.role != 'SYSADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    redis_client = redis.from_url('redis://redis:6379', decode_responses=True)
    
    queue_depth = redis_client.llen('ocr:jobs')
    redis_client.delete('ocr:jobs')
    
    return Response({
        'message': f'Flushed {queue_depth} jobs from queue',
        'jobs_removed': queue_depth
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def ocr_worker_history(request, worker_id):
    """Get detailed history for a specific worker."""
    if request.user.role != 'SYSADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    redis_client = redis.from_url('redis://redis:6379', decode_responses=True)
    
    # Get worker info
    worker_key = f'ocr:worker:{worker_id}'
    worker_data = redis_client.get(worker_key)
    
    if not worker_data:
        return Response({'error': 'Worker not found'}, status=status.HTTP_404_NOT_FOUND)
    
    worker = json.loads(worker_data)
    
    # Get job history for this worker
    history_key = f'ocr:worker:{worker_id}:history'
    history = redis_client.lrange(history_key, 0, 99)
    job_history = [json.loads(job) for job in history]
    
    return Response({
        'worker_id': worker_id,
        'current_status': worker,
        'job_history': job_history,
        'total_jobs': worker['jobs_processed']
    })
```

#### 2. URL Configuration

```python
# backend/apps/counters/urls.py (add these)

urlpatterns = [
    # ... existing patterns
    
    # OCR Monitoring (SYSADMIN only)
    path('ocr/health/', views.ocr_health, name='ocr_health'),
    path('ocr/queue/', views.ocr_queue_jobs, name='ocr_queue_jobs'),
    path('ocr/queue/flush/', views.ocr_flush_queue, name='ocr_flush_queue'),
    path('ocr/worker/<str:worker_id>/', views.ocr_worker_history, name='ocr_worker_history'),
]
```

### Frontend Implementation

Full implementation provided in spec with:
- Real-time dashboard with auto-refresh
- Worker status table
- Queue inspection table  
- Emergency queue flush
- Formatted metrics and timestamps

### UI Mockup

```
┌─────────────────────────────────────────────────────────────────────────┐
│  OCR Service Monitor                         Auto-refresh ☑  [HEALTHY]  │
│  Real-time monitoring of OCR workers and queue status                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────────┐│
│  │Active Workers│  │ Queue Depth  │  │  Avg Time    │  │ Throughput ││
│  │      3       │  │      12      │  │    245ms     │  │  180/min   ││
│  │52 jobs total │  │Status: normal│  │  Per frame   │  │            ││
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────────┘│
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Active Workers (3)                                              │  │
│  ├──────────────┬────────┬───────────┬─────────┬──────────────────┤  │
│  │ Worker ID    │ Status │ Jobs Done │ Uptime  │ Last Heartbeat   │  │
│  ├──────────────┼────────┼───────────┼─────────┼──────────────────┤  │
│  │ worker-1     │[healthy]│    24     │ 2h 15m  │ 3s ago          │  │
│  │ worker-2     │[healthy]│    19     │ 2h 10m  │ 2s ago          │  │
│  │ worker-3     │[healthy]│     9     │ 45m     │ 5s ago          │  │
│  └──────────────┴────────┴───────────┴─────────┴──────────────────┘  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐  │
│  │ Queued Jobs (12)                             [Flush Queue]      │  │
│  ├──────────────┬────────┬────────────┬──────────┬─────────────────┤  │
│  │ Job ID       │User ID │ Frame Size │Wait Time │ Queued At       │  │
│  ├──────────────┼────────┼────────────┼──────────┼─────────────────┤  │
│  │ a3f4b2c1...  │   42   │  125.3 KB  │  2.1s    │ 5s ago         │  │
│  │ d7e8f3a2...  │   18   │  98.7 KB   │  1.8s    │ 7s ago         │  │
│  │ ...          │   ...  │  ...       │  ...     │ ...            │  │
│  └──────────────┴────────┴────────────┴──────────┴─────────────────┘  │
│                                                                         │
│                    Last updated: 2s ago                                 │
└─────────────────────────────────────────────────────────────────────────┘
```

### Features

1. **Real-time Monitoring**:
   - Worker count and health status
   - Queue depth with status indicators (normal/high/critical)
   - Average processing time
   - Throughput (jobs per minute)

2. **Worker Details**:
   - Worker ID
   - Health status (healthy/stale)
   - Total jobs processed
   - Uptime
   - Last heartbeat timestamp

3. **Queue Inspection**:
   - View queued jobs (first 100)
   - Job ID, user ID, frame size
   - Wait time in queue
   - Timestamp when queued

4. **Emergency Actions**:
   - Flush entire queue (with confirmation)
   - Future: Restart worker, scale workers

5. **Auto-refresh**:
   - Toggle 5-second auto-refresh
   - Manual refresh option

6. **Status Indicators**:
   - Color-coded health status (green/yellow/red)
   - Queue status indicators
   - Worker heartbeat freshness

---

## System Administration - Live Screen Monitoring

### Overview

SYSADMIN role gets access to a live monitoring page showing real-time screen feeds from all staff members who have OCR detection actively running. This enables supervisors to verify staff are in valid sits, monitor compliance, and assist with technical issues.

### Access Control

| Role | Access |
|------|--------|
| SYSADMIN | Full access (view all screens) |
| Manager | No access |
| All others | No access |

### Privacy & Consent

- **Explicit Opt-in**: Users must enable OCR monitoring to be visible
- **Active Indicator**: Clear visual indicator when screen is being shared
- **User Control**: Users can stop sharing at any time
- **Transparency**: Users are informed that SYSADMIN can view their screen during sits

### Page Location

```
/dashboard/admin/live-monitors
```

### Features

#### 1. Grid View - All Active Screens

Display all staff members currently running OCR detection in a responsive grid layout:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Live Staff Monitoring                              [◉ Auto-Refresh] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │  🟢 [LIVE]   │  │  🟢 [LIVE]   │  │  🔴 [LIVE]   │              │
│  │              │  │              │  │              │              │
│  │   [Video]    │  │   [Video]    │  │   [Video]    │              │
│  │   Preview    │  │   Preview    │  │   Preview    │              │
│  │              │  │              │  │              │              │
│  ├──────────────┤  ├──────────────┤  ├──────────────┤              │
│  │ Admin1       │  │ Moderator2   │  │ Operator3    │              │
│  │ ✅ In Sit    │  │ ✅ In Sit    │  │ ❌ No Sit    │              │
│  │ 2m 34s       │  │ 15m 02s      │  │ Idle         │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                       │
│  ┌──────────────┐  ┌──────────────┐                                 │
│  │  🟢 [LIVE]   │  │  🟢 [LIVE]   │                                 │
│  │              │  │              │                                 │
│  │   [Video]    │  │   [Video]    │                                 │
│  │   Preview    │  │   Preview    │                                 │
│  │              │  │              │                                 │
│  ├──────────────┤  ├──────────────┤                                 │
│  │ SrMod4       │  │ Admin5       │                                 │
│  │ ✅ In Sit    │  │ ✅ In Sit    │                                 │
│  │ 45s          │  │ 8m 12s       │                                 │
│  └──────────────┘  └──────────────┘                                 │
│                                                                       │
│                       Monitoring 5 staff members                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Card Information**:
- **Live Indicator**: Green/Red dot showing stream status
- **Video Preview**: Live video feed at ~320x180px (scaled down)
- **Username**: Staff member name with role badge
- **Sit Status**: ✅ In Sit / ❌ No Sit
- **Timer**: Current sit duration or "Idle"
- **Click Action**: Opens full-size popup modal

#### 2. Full-Size Modal (Click to Expand)

When clicking on a card, open a modal dialog with larger video feed:

```
┌─────────────────────────────────────────────────────────────────────┐
│  [×] Admin1 - Live Screen Monitor                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│                                                                       │
│                         [Large Video Feed]                            │
│                           1280x720px                                  │
│                                                                       │
│                                                                       │
├─────────────────────────────────────────────────────────────────────┤
│  👤 Admin1 (Admin)                    🟢 Connected                   │
│  📊 Sit Status: ✅ In Sit             ⏱️ Duration: 2m 45s            │
│  🖥️ Resolution: 1920x1080            📡 FPS: ~1 frame/sec            │
│  🎯 Last Detection: 2s ago            📊 Total Sits Today: 12        │
│                                                                       │
│  Recent Detections:                                                   │
│  • 2s ago  - "Sitting with John Doe"                                 │
│  • 34s ago - "Sitting with Jane Smith"                               │
│  • 1m ago  - "No active sit detected"                                │
└─────────────────────────────────────────────────────────────────────┘
```

**Modal Features**:
- **Larger Video**: Display at 1280x720px or largest available
- **Real-time Stats**: Connection status, FPS, resolution
- **Sit Information**: Current sit duration, recent detections
- **Detection History**: Last 5-10 OCR detection results
- **Daily Summary**: Total sits counted today

### Architecture

#### Backend - WebSocket Feed Broadcaster

```python
# backend/apps/counters/consumers.py

import json
import base64
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache

class ScreenMonitorConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for broadcasting staff screen feeds to SYSADMIN.
    
    Two connection types:
    1. Staff (broadcaster): Sends video frames for monitoring
    2. Admin (viewer): Receives all staff video frames
    """
    
    async def connect(self):
        self.user = self.scope['user']
        
        if not self.user.is_authenticated:
            await self.close()
            return
        
        # Get connection type from query params
        self.connection_type = self.scope['url_route']['kwargs'].get('type', 'viewer')
        
        if self.connection_type == 'viewer':
            # Admin viewing screens
            if self.user.role != 'SYSADMIN':
                await self.close()
                return
            
            # Join monitoring room to receive all broadcasts
            await self.channel_layer.group_add('screen_monitors', self.channel_name)
            
        elif self.connection_type == 'broadcaster':
            # Staff sharing their screen
            self.broadcaster_id = f"broadcaster_{self.user.id}"
            
            # Add to active broadcasters
            await self.channel_layer.group_add('screen_broadcasters', self.channel_name)
            
            # Notify monitors that new broadcaster is online
            await self.channel_layer.group_send(
                'screen_monitors',
                {
                    'type': 'broadcaster_online',
                    'user_id': self.user.id,
                    'username': self.user.username,
                    'role': self.user.role,
                }
            )
            
            # Track active broadcaster in cache
            cache.set(f'broadcaster:{self.user.id}', {
                'username': self.user.username,
                'role': self.user.role,
                'connected_at': datetime.now().isoformat(),
            }, timeout=None)  # Persist until disconnect
        
        await self.accept()
    
    async def disconnect(self, close_code):
        if self.connection_type == 'viewer':
            await self.channel_layer.group_discard('screen_monitors', self.channel_name)
        elif self.connection_type == 'broadcaster':
            await self.channel_layer.group_discard('screen_broadcasters', self.channel_name)
            
            # Notify monitors that broadcaster is offline
            await self.channel_layer.group_send(
                'screen_monitors',
                {
                    'type': 'broadcaster_offline',
                    'user_id': self.user.id,
                }
            )
            
            # Remove from cache
            cache.delete(f'broadcaster:{self.user.id}')
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        
        if self.connection_type == 'broadcaster':
            # Staff sending video frame
            if data['type'] == 'video_frame':
                # Broadcast frame to all monitors
                await self.channel_layer.group_send(
                    'screen_monitors',
                    {
                        'type': 'video_frame',
                        'user_id': self.user.id,
                        'username': self.user.username,
                        'role': self.user.role,
                        'frame_data': data['frame'],  # Base64 encoded JPEG
                        'sit_status': data.get('sit_status', {}),
                        'timestamp': data['timestamp'],
                    }
                )
            
            elif data['type'] == 'sit_status_update':
                # Staff's sit status changed
                await self.channel_layer.group_send(
                    'screen_monitors',
                    {
                        'type': 'sit_status_update',
                        'user_id': self.user.id,
                        'sit_status': data['sit_status'],
                    }
                )
    
    # Handlers for messages from channel layer
    async def video_frame(self, event):
        """Send video frame to admin viewer."""
        await self.send(text_data=json.dumps({
            'type': 'video_frame',
            'user_id': event['user_id'],
            'username': event['username'],
            'role': event['role'],
            'frame': event['frame_data'],
            'sit_status': event['sit_status'],
            'timestamp': event['timestamp'],
        }))
    
    async def broadcaster_online(self, event):
        """Notify admin that staff started sharing."""
        await self.send(text_data=json.dumps({
            'type': 'broadcaster_online',
            'user_id': event['user_id'],
            'username': event['username'],
            'role': event['role'],
        }))
    
    async def broadcaster_offline(self, event):
        """Notify admin that staff stopped sharing."""
        await self.send(text_data=json.dumps({
            'type': 'broadcaster_offline',
            'user_id': event['user_id'],
        }))
    
    async def sit_status_update(self, event):
        """Notify admin of sit status change."""
        await self.send(text_data=json.dumps({
            'type': 'sit_status_update',
            'user_id': event['user_id'],
            'sit_status': event['sit_status'],
        }))
```

#### Backend - REST API for Active Broadcasters

```python
# backend/apps/counters/views.py

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_active_broadcasters(request):
    """Get list of all staff currently broadcasting their screens."""
    # Only SYSADMIN can access
    if request.user.role != 'SYSADMIN':
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    # Get all active broadcasters from cache
    pattern = 'broadcaster:*'
    keys = cache.keys(pattern)
    
    broadcasters = []
    for key in keys:
        data = cache.get(key)
        if data:
            user_id = int(key.split(':')[1])
            broadcasters.append({
                'user_id': user_id,
                'username': data['username'],
                'role': data['role'],
                'connected_at': data['connected_at'],
            })
    
    return Response({
        'count': len(broadcasters),
        'broadcasters': broadcasters,
    })
```

#### Backend - WebSocket Routing

```python
# backend/apps/counters/routing.py

from django.urls import path
from . import consumers

websocket_urlpatterns = [
    path('ws/counters/', consumers.CounterConsumer.as_asgi()),
    path('ws/screen-monitor/<str:type>/', consumers.ScreenMonitorConsumer.as_asgi()),
]
```

#### Frontend - Staff Broadcaster Hook

```typescript
// frontend/src/hooks/useScreenBroadcast.ts

import { useEffect, useRef } from 'react';
import io from 'socket.io-client';

interface SitStatus {
  inSit: boolean;
  sitDuration?: number;
  detectedText?: string;
}

export function useScreenBroadcast(
  mediaStream: MediaStream | null,
  sitStatus: SitStatus,
  enabled: boolean = true
) {
  const socketRef = useRef<any>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled || !mediaStream) return;

    // Connect to WebSocket as broadcaster
    const token = localStorage.getItem('access_token');
    socketRef.current = io(`${process.env.NEXT_PUBLIC_WS_URL}/ws/screen-monitor/broadcaster/`, {
      auth: { token },
      transports: ['websocket'],
    });

    socketRef.current.on('connect', () => {
      console.log('[Broadcast] Connected to monitoring server');
    });

    // Setup video element for frame capture
    const video = document.createElement('video');
    video.srcObject = mediaStream;
    video.play();
    videoRef.current = video;

    // Setup canvas for frame extraction
    const canvas = document.createElement('canvas');
    canvasRef.current = canvas;

    video.onloadedmetadata = () => {
      canvas.width = 320;  // Send small preview frames
      canvas.height = 180;
      
      // Start sending frames at 1 FPS
      intervalRef.current = setInterval(() => {
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        // Draw current video frame to canvas
        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Convert to JPEG base64 (compressed)
        canvas.toBlob((blob) => {
          if (!blob) return;

          const reader = new FileReader();
          reader.onloadend = () => {
            const base64 = reader.result as string;
            
            // Send frame to server
            socketRef.current?.emit('video_frame', {
              type: 'video_frame',
              frame: base64.split(',')[1],  // Remove data:image/jpeg;base64, prefix
              sit_status: sitStatus,
              timestamp: Date.now(),
            });
          };
          reader.readAsDataURL(blob);
        }, 'image/jpeg', 0.6);  // 60% JPEG quality
      }, 1000);  // 1 frame per second
    };

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
      socketRef.current?.disconnect();
      videoRef.current?.pause();
    };
  }, [mediaStream, enabled]);

  // Update sit status when it changes
  useEffect(() => {
    if (socketRef.current?.connected) {
      socketRef.current.emit('sit_status_update', {
        type: 'sit_status_update',
        sit_status: sitStatus,
      });
    }
  }, [sitStatus]);
}
```

#### Frontend - Admin Monitoring Page

```typescript
// frontend/src/app/dashboard/admin/live-monitors/page.tsx

'use client';

import { useEffect, useState, useRef } from 'react';
import io from 'socket.io-client';
import { XMarkIcon } from '@heroicons/react/24/outline';

interface Broadcaster {
  user_id: number;
  username: string;
  role: string;
  connected_at: string;
  lastFrame?: string;  // Base64 JPEG
  sitStatus?: {
    inSit: boolean;
    sitDuration?: number;
    detectedText?: string;
  };
  lastUpdate?: number;
}

export default function LiveMonitorsPage() {
  const [broadcasters, setBroadcasters] = useState<Map<number, Broadcaster>>(new Map());
  const [selectedBroadcaster, setSelectedBroadcaster] = useState<Broadcaster | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const socketRef = useRef<any>(null);

  useEffect(() => {
    // Fetch initial list of broadcasters
    fetch('/api/counters/active-broadcasters/', {
      headers: {
        Authorization: `Bearer ${localStorage.getItem('access_token')}`,
      },
    })
      .then(res => res.json())
      .then(data => {
        const map = new Map<number, Broadcaster>();
        data.broadcasters.forEach((b: Broadcaster) => {
          map.set(b.user_id, b);
        });
        setBroadcasters(map);
      });

    // Connect to WebSocket as viewer
    const token = localStorage.getItem('access_token');
    socketRef.current = io(`${process.env.NEXT_PUBLIC_WS_URL}/ws/screen-monitor/viewer/`, {
      auth: { token },
      transports: ['websocket'],
    });

    socketRef.current.on('connect', () => {
      console.log('[Monitor] Connected to monitoring server');
    });

    socketRef.current.on('broadcaster_online', (data: any) => {
      console.log('[Monitor] Broadcaster online:', data.username);
      setBroadcasters(prev => {
        const map = new Map(prev);
        map.set(data.user_id, {
          user_id: data.user_id,
          username: data.username,
          role: data.role,
          connected_at: new Date().toISOString(),
        });
        return map;
      });
    });

    socketRef.current.on('broadcaster_offline', (data: any) => {
      console.log('[Monitor] Broadcaster offline:', data.user_id);
      setBroadcasters(prev => {
        const map = new Map(prev);
        map.delete(data.user_id);
        return map;
      });
      
      // Close modal if viewing this broadcaster
      if (selectedBroadcaster?.user_id === data.user_id) {
        setSelectedBroadcaster(null);
      }
    });

    socketRef.current.on('video_frame', (data: any) => {
      setBroadcasters(prev => {
        const map = new Map(prev);
        const broadcaster = map.get(data.user_id);
        if (broadcaster) {
          map.set(data.user_id, {
            ...broadcaster,
            lastFrame: data.frame,
            sitStatus: data.sit_status,
            lastUpdate: data.timestamp,
          });
        }
        return map;
      });
    });

    socketRef.current.on('sit_status_update', (data: any) => {
      setBroadcasters(prev => {
        const map = new Map(prev);
        const broadcaster = map.get(data.user_id);
        if (broadcaster) {
          map.set(data.user_id, {
            ...broadcaster,
            sitStatus: data.sit_status,
          });
        }
        return map;
      });
    });

    return () => {
      socketRef.current?.disconnect();
    };
  }, []);

  const formatDuration = (ms?: number) => {
    if (!ms) return 'Idle';
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}m ${secs}s`;
  };

  const broadcastersArray = Array.from(broadcasters.values());

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="mx-auto max-w-7xl">
        {/* Header */}
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Live Staff Monitoring</h1>
            <p className="mt-1 text-sm text-gray-500">
              Monitoring {broadcastersArray.length} staff member{broadcastersArray.length !== 1 ? 's' : ''}
            </p>
          </div>
          
          <div className="flex items-center gap-3">
            <label className="flex items-center gap-2">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
                className="h-4 w-4 rounded border-gray-300 text-blue-600"
              />
              <span className="text-sm text-gray-700">Auto-refresh</span>
            </label>
          </div>
        </div>

        {/* Grid of broadcaster cards */}
        {broadcastersArray.length === 0 ? (
          <div className="rounded-lg bg-white p-12 text-center shadow">
            <p className="text-gray-500">No staff members are currently sharing their screens</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {broadcastersArray.map(broadcaster => (
              <div
                key={broadcaster.user_id}
                onClick={() => setSelectedBroadcaster(broadcaster)}
                className="group cursor-pointer overflow-hidden rounded-lg bg-white shadow transition hover:shadow-lg"
              >
                {/* Live indicator */}
                <div className="flex items-center gap-2 bg-gray-100 px-3 py-2">
                  <div className={`h-2 w-2 rounded-full ${broadcaster.lastFrame ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span className="text-xs font-medium text-gray-700">LIVE</span>
                </div>

                {/* Video preview */}
                <div className="relative aspect-video bg-gray-900">
                  {broadcaster.lastFrame ? (
                    <img
                      src={`data:image/jpeg;base64,${broadcaster.lastFrame}`}
                      alt={`${broadcaster.username}'s screen`}
                      className="h-full w-full object-contain"
                    />
                  ) : (
                    <div className="flex h-full items-center justify-center text-gray-400">
                      No frame received
                    </div>
                  )}
                  
                  {/* Overlay on hover */}
                  <div className="absolute inset-0 flex items-center justify-center bg-black/50 opacity-0 transition group-hover:opacity-100">
                    <span className="text-sm font-medium text-white">Click to expand</span>
                  </div>
                </div>

                {/* Info */}
                <div className="p-3">
                  <p className="font-medium text-gray-900">{broadcaster.username}</p>
                  <div className="mt-1 flex items-center gap-2">
                    <span className={`text-lg ${broadcaster.sitStatus?.inSit ? 'text-green-600' : 'text-gray-400'}`}>
                      {broadcaster.sitStatus?.inSit ? '✅' : '❌'}
                    </span>
                    <span className="text-sm text-gray-600">
                      {broadcaster.sitStatus?.inSit ? 'In Sit' : 'No Sit'}
                    </span>
                  </div>
                  <p className="mt-1 text-xs text-gray-500">
                    {formatDuration(broadcaster.sitStatus?.sitDuration)}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Full-size modal */}
        {selectedBroadcaster && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4">
            <div className="w-full max-w-5xl overflow-hidden rounded-lg bg-white shadow-2xl">
              {/* Header */}
              <div className="flex items-center justify-between border-b bg-gray-50 px-6 py-4">
                <div>
                  <h2 className="text-xl font-bold text-gray-900">
                    {selectedBroadcaster.username} - Live Screen Monitor
                  </h2>
                  <p className="text-sm text-gray-500">{selectedBroadcaster.role}</p>
                </div>
                <button
                  onClick={() => setSelectedBroadcaster(null)}
                  className="rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600"
                >
                  <XMarkIcon className="h-6 w-6" />
                </button>
              </div>

              {/* Large video feed */}
              <div className="relative aspect-video bg-gray-900">
                {selectedBroadcaster.lastFrame ? (
                  <img
                    src={`data:image/jpeg;base64,${selectedBroadcaster.lastFrame}`}
                    alt={`${selectedBroadcaster.username}'s screen`}
                    className="h-full w-full object-contain"
                  />
                ) : (
                  <div className="flex h-full items-center justify-center text-gray-400">
                    Waiting for frames...
                  </div>
                )}
              </div>

              {/* Stats */}
              <div className="grid grid-cols-2 gap-4 border-t bg-gray-50 p-6 lg:grid-cols-4">
                <div>
                  <p className="text-xs font-medium text-gray-500">Status</p>
                  <p className="mt-1 flex items-center gap-2">
                    <span className="text-lg">
                      {selectedBroadcaster.sitStatus?.inSit ? '✅' : '❌'}
                    </span>
                    <span className="font-semibold text-gray-900">
                      {selectedBroadcaster.sitStatus?.inSit ? 'In Sit' : 'No Sit'}
                    </span>
                  </p>
                </div>
                
                <div>
                  <p className="text-xs font-medium text-gray-500">Duration</p>
                  <p className="mt-1 font-semibold text-gray-900">
                    {formatDuration(selectedBroadcaster.sitStatus?.sitDuration)}
                  </p>
                </div>
                
                <div>
                  <p className="text-xs font-medium text-gray-500">Connection</p>
                  <p className="mt-1 flex items-center gap-2">
                    <span className="h-2 w-2 rounded-full bg-green-500" />
                    <span className="font-semibold text-gray-900">Connected</span>
                  </p>
                </div>
                
                <div>
                  <p className="text-xs font-medium text-gray-500">Last Update</p>
                  <p className="mt-1 font-semibold text-gray-900">
                    {selectedBroadcaster.lastUpdate
                      ? `${Math.floor((Date.now() - selectedBroadcaster.lastUpdate) / 1000)}s ago`
                      : 'N/A'}
                  </p>
                </div>
              </div>

              {/* Detection history */}
              {selectedBroadcaster.sitStatus?.detectedText && (
                <div className="border-t p-6">
                  <h3 className="text-sm font-medium text-gray-700">Last Detection</h3>
                  <p className="mt-2 rounded bg-gray-100 p-3 font-mono text-sm text-gray-800">
                    {selectedBroadcaster.sitStatus.detectedText}
                  </p>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
```

#### Frontend - Integration with OCR Hook

```typescript
// frontend/src/hooks/useScreenOCR.ts (MODIFIED)

// Add broadcasting support
import { useScreenBroadcast } from './useScreenBroadcast';

export function useScreenOCR() {
  // ... existing OCR code ...

  // Add broadcast hook (SYSADMIN will see these streams)
  const [broadcastEnabled, setBroadcastEnabled] = useState(true);
  
  useScreenBroadcast(
    mediaStream,
    {
      inSit: sitStatus.inSit,
      sitDuration: sitStatus.duration,
      detectedText: lastDetectedText,
    },
    broadcastEnabled && isScanning
  );

  return {
    // ... existing returns ...
    broadcastEnabled,
    setBroadcastEnabled,
  };
}
```

### Security & Performance Considerations

#### 1. **Privacy Protection**
- Frames are sent at low quality (60% JPEG, 320x180px) to reduce bandwidth
- Only 1 FPS to minimize data transfer
- Users must explicitly start OCR monitoring (implicit consent)
- Clear visual indicator shows when broadcasting

#### 2. **Network Efficiency**
- Small frame size (~5-15 KB per frame)
- Low frame rate (1 FPS = ~60 KB/minute per user)
- 10 concurrent broadcasters = ~600 KB/minute = ~10 KB/sec
- WebSocket compression reduces bandwidth further

#### 3. **Access Control**
- Only SYSADMIN can view screens (enforced at WebSocket level)
- JWT authentication required for both broadcaster and viewer connections
- Django Channels permission checks on connect

#### 4. **Scalability**
- Redis Channel Layer handles message distribution
- No frames stored on server (real-time only)
- Minimal CPU impact (no server-side processing of frames)
- Horizontal scaling possible with Redis cluster

#### 5. **User Control**
- Users can disable broadcasting via settings toggle
- Stopping OCR monitoring automatically stops broadcast
- No background broadcasting - only when actively in sit mode

### Backend - URL Configuration

```python
# backend/config/urls.py

urlpatterns = [
    # ... existing patterns ...
    path('api/counters/active-broadcasters/', views.get_active_broadcasters),
]
```

### UI Navigation

Add link to admin navigation:

```typescript
// frontend/src/components/layout/AdminNav.tsx

{user.role === 'SYSADMIN' && (
  <>
    <NavLink href="/dashboard/admin/ocr-monitor">OCR Monitoring</NavLink>
    <NavLink href="/dashboard/admin/live-monitors">Live Screens</NavLink>
  </>
)}
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | - | Initial specification |
| 1.1 | 2026-01-02 | - | Added server-side OCR option for performance |
| 1.2 | 2026-01-02 | - | Refactored OCR to separate scalable microservice |
| 1.3 | 2026-01-02 | - | Added SYSADMIN OCR monitoring dashboard |
| 1.4 | 2026-01-02 | - | Added SYSADMIN live screen monitoring feature |
