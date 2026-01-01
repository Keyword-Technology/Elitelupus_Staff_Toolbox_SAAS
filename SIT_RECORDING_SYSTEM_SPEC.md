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

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | - | Initial specification |
