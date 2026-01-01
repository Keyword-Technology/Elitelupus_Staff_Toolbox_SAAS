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

### How It Works

1. **Continuous Monitoring**: Staff starts "monitoring mode" which captures the game screen
2. **Frame Analysis**: Every 1-2 seconds, capture a frame and analyze specific regions
3. **OCR Detection**: Use Tesseract.js to read text from sit notification areas
4. **Auto-Trigger**: When sit claim detected → start recording + show sit panel
5. **Auto-End**: When sit close detected → stop recording + show completion modal

### Screen Regions for OCR

```
┌─────────────────────────────────────────────────────────────────┐
│                     GAME SCREEN                                 │
│  ┌─────────────────────────────────────────┐                   │
│  │  OCR REGION 1 (Top notifications)       │  ← Chat/ULX msgs  │
│  └─────────────────────────────────────────┘                   │
│                    [Game World]                                 │
│  ┌──────────────────┐                                          │
│  │ OCR REGION 2     │  ← Admin menu area                       │
│  └──────────────────┘                                          │
│                                           ┌──────────────────┐ │
│                                           │ OCR REGION 3     │ │
│                                           │ (Chat box)       │ │
│                                           └──────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Detection Patterns

#### Sit Claimed Patterns
```typescript
const SIT_CLAIMED_PATTERNS = [
    /brought\s+(.+?)\s+to/i,           // ULX: "brought PlayerName to them"
    /teleported\s+(.+?)\s+to\s+you/i,  // ULX variant
    /claimed\s+(.+?)(?:'s)?\s+sit/i,   // SAM style
    /handling\s+(.+?)(?:'s)?\s+request/i,
    /sit\s+accepted/i,
    /now\s+handling/i,
];
```

#### Sit Closed Patterns
```typescript
const SIT_CLOSED_PATTERNS = [
    /returned\s+(.+?)\s+to/i,   // ULX: "returned PlayerName to..."
    /sent\s+(.+?)\s+back/i,
    /sit\s+closed/i,
    /sit\s+finished/i,
    /sit\s+completed/i,
];
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

const DEFAULT_OCR_REGIONS: OCRRegion[] = [
    { id: '1', name: 'Top Notifications', x: 0.0, y: 0.0, width: 0.5, height: 0.15, enabled: true },
    { id: '2', name: 'Chat Area', x: 0.0, y: 0.7, width: 0.4, height: 0.3, enabled: true },
];

export function useScreenOCR(videoStream: MediaStream | null, options: {
    onSitClaimed: (playerName?: string) => void;
    onSitClosed: (playerName?: string) => void;
    scanInterval?: number;
}) {
    const [isMonitoring, setIsMonitoring] = useState(false);
    const [ocrRegions, setOcrRegions] = useState(DEFAULT_OCR_REGIONS);
    const workerRef = useRef<Worker | null>(null);
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const videoRef = useRef<HTMLVideoElement>(null);
    
    // Initialize Tesseract worker
    useEffect(() => {
        const init = async () => {
            const worker = await createWorker('eng');
            workerRef.current = worker;
        };
        init();
        return () => { workerRef.current?.terminate(); };
    }, []);
    
    // Capture frame and run OCR on each region
    const captureAndAnalyze = useCallback(async () => {
        if (!videoStream || !workerRef.current) return;
        
        for (const region of ocrRegions.filter(r => r.enabled)) {
            // Draw region to canvas, preprocess, run OCR
            // Check against SIT_CLAIMED_PATTERNS and SIT_CLOSED_PATTERNS
            // Call options.onSitClaimed() or options.onSitClosed() on match
        }
    }, [videoStream, ocrRegions, options]);
    
    const startMonitoring = () => {
        setIsMonitoring(true);
        // Start interval for captureAndAnalyze
    };
    
    const stopMonitoring = () => {
        setIsMonitoring(false);
        // Clear interval
    };
    
    return { isMonitoring, startMonitoring, stopMonitoring, ocrRegions, setOcrRegions };
}
```

### User Flow with Auto-Detection

1. **Start Monitoring**: Staff clicks "Share Game Screen" → browser prompts window selection
2. **Waiting State**: System scans OCR regions every 1.5 seconds for sit patterns
3. **Sit Detected**: Shows confirmation popup "Sit detected! Start recording?" (auto-confirms in 3s)
4. **Recording Active**: Staff handles sit, system watches for close patterns
5. **Close Detected**: Stops recording, shows completion modal

### Configuration Options

| Setting | Description | Default |
|---------|-------------|---------|
| OCR Regions | Draggable/resizable scan areas | Top + Chat |
| Scan Interval | Time between OCR scans | 1500ms |
| Debounce Time | Cooldown between detections | 5000ms |
| Auto-confirm Delay | Seconds before auto-starting | 3s |
| Contrast Boost | Image preprocessing strength | 1.5x |

### Custom Patterns

Staff can add custom detection patterns for their specific admin addon via settings.

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
