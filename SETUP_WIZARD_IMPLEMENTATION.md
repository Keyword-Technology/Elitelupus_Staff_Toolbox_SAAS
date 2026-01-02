# First-Time Setup Wizard Implementation

## Overview

Implemented a comprehensive first-time setup wizard that guides new users through essential account configuration when they sign in for the first time. The wizard collects timezone preferences, optional email, password setup (for OAuth users), and configures smart features like auto sit detection and recording.

## Changes Made

### Backend Changes

#### 1. User Model (`backend/apps/accounts/models.py`)
Added setup wizard tracking fields:
- `setup_completed` (BooleanField): Tracks whether user completed initial setup
- `setup_completed_at` (DateTimeField): Timestamp of setup completion

#### 2. Serializers (`backend/apps/accounts/serializers.py`)
- **Updated `UserSerializer`**: Added `setup_completed` and `setup_completed_at` fields
- **New `SetupWizardSerializer`**: Handles setup wizard form validation and user updates
  - Validates timezone selection
  - Optional email and password fields
  - Auto sit detection preference
  - Auto recording preference
  - Automatically creates/updates `UserSitPreferences` based on wizard choices

#### 3. Views (`backend/apps/accounts/views.py`)
Added `SetupWizardView` with two endpoints:
- **POST `/auth/setup-wizard/`**: Completes setup wizard
  - Validates input data
  - Updates user profile
  - Creates sit preferences
  - Marks setup as completed
- **GET `/auth/setup-wizard/`**: Returns setup status and system settings
  - Current setup status
  - Available system features (sit recording, etc.)

#### 4. URLs (`backend/apps/accounts/urls.py`)
Added route: `re_path(r'^setup-wizard/?$', SetupWizardView.as_view())`

#### 5. Database Migration
Created migration: `0004_user_setup_completed_user_setup_completed_at.py`

### Frontend Changes

#### 1. Setup Wizard Component (`frontend/src/components/auth/SetupWizard.tsx`)
Comprehensive 4-step wizard with detailed explanations:

**Step 1: Timezone Selection**
- Dropdown with all available timezones
- Auto-detects user's browser timezone
- Explanation: Used for sit timestamps, activity logs, scheduling

**Step 2: Email (Optional)**
- Optional email input field
- Explanation: Account recovery, notifications, privacy assurance
- Can be skipped and added later

**Step 3: Password (Optional for OAuth)**
- Password input with show/hide toggle
- Required for non-OAuth users
- Optional for Steam/Discord OAuth users
- Explanation: Enables traditional login alongside OAuth

**Step 4: Smart Features**
- **Auto Sit Detection (OCR)**: Checkbox with detailed explanation
  - How it works: Browser-based OCR scanning
  - What it detects: Sit claim/close events
  - Privacy: All processing in browser
  
- **Auto Screen Recording**: Checkbox with detailed explanation (if system setting enabled)
  - How it works: Auto-start/stop recording during sits
  - Browser requirements: Screen Capture API support
  - Privacy: No data sent until explicit save

Features:
- Progress indicator with step icons
- Previous/Next navigation
- Form validation
- Loading states
- Informational tooltips with context
- Responsive design

#### 2. Setup Page (`frontend/src/app/setup/page.tsx`)
Route protection and setup wizard rendering:
- Redirects unauthenticated users to login
- Redirects users with completed setup to dashboard
- Shows loading state during authentication check

#### 3. Auth Context Updates (`frontend/src/contexts/AuthContext.tsx`)
- Added `setup_completed` and `setup_completed_at` to User interface
- Updated `login()` function to check setup status and redirect to `/setup` if needed

#### 4. OAuth Callback Updates (`frontend/src/app/auth/callback/page.tsx`)
- Checks setup completion status after OAuth authentication
- Redirects to `/setup` for first-time users
- Redirects to `/dashboard` for returning users

#### 5. Dashboard Layout Protection (`frontend/src/app/dashboard/layout.tsx`)
- Added middleware check for setup completion
- Redirects to `/setup` if user hasn't completed setup
- Prevents access to dashboard before setup

## User Flow

### First-Time Login (OAuth - Steam/Discord)
```
1. User clicks "Login with Steam/Discord"
2. OAuth flow completes → JWT tokens issued
3. Frontend checks setup_completed status
4. If false → Redirect to /setup
5. User completes 4-step wizard:
   - Select timezone
   - Add email (optional)
   - Set password (optional - enables username/password login)
   - Configure auto-detection and recording
6. Submit → setup_completed = true
7. Redirect to /dashboard
```

### First-Time Login (Traditional)
```
1. User enters username/password
2. Login successful → JWT tokens issued
3. Frontend checks setup_completed status
4. If false → Redirect to /setup
5. User completes 4-step wizard:
   - Select timezone
   - Add email (optional)
   - Change password (optional)
   - Configure auto-detection and recording
6. Submit → setup_completed = true
7. Redirect to /dashboard
```

### Returning User
```
1. User logs in (OAuth or traditional)
2. Frontend checks setup_completed status
3. If true → Direct to /dashboard
4. No wizard shown
```

## Setup Wizard Features

### Timezone Configuration
- **Purpose**: Ensures all timestamps are displayed in user's local timezone
- **Default**: Auto-detects from browser (`Intl.DateTimeFormat().resolvedOptions().timeZone`)
- **Options**: All common timezones via pytz
- **Usage**: Sit timestamps, activity logs, staff roster times, scheduling

### Email Address (Optional)
- **Purpose**: Account recovery, important notifications, future features
- **Privacy**: Explicitly stated that email is never shared with third parties
- **Can Skip**: Users can add email later in settings
- **Validation**: Standard email format validation

### Password Setup
- **For OAuth Users**: Optional - enables traditional login alongside OAuth
- **For Traditional Users**: Can update existing password
- **Requirements**: Minimum 8 characters
- **Security**: Bcrypt hashing via Django's `set_password()`
- **Show/Hide Toggle**: User-friendly password visibility control

### Auto Sit Detection (OCR)
- **Default**: Enabled
- **Explanation Provided**:
  - Uses browser-based OCR (Tesseract.js)
  - Scans specific screen regions for sit events
  - Detects "[Elite Reports] You claimed..." patterns
  - Entirely browser-based processing
  - No data sent to server during detection
- **Integration**: Configures `UserSitPreferences.ocr_enabled`

### Auto Screen Recording
- **Default**: Enabled (if system setting allows)
- **Conditional**: Only shown if `sit_recording_enabled` system setting is true
- **Explanation Provided**:
  - Auto-starts recording when sit claimed
  - Auto-stops when sit closed
  - Uses Screen Capture API (modern browsers)
  - Requires HTTPS for secure context
  - Recordings only uploaded when user saves sit
- **Integration**: Configures `UserSitPreferences.recording_enabled`, `auto_start_recording`, `auto_stop_recording`

## API Endpoints

### POST `/api/auth/setup-wizard/`
**Authentication**: Required (JWT)

**Request Body**:
```json
{
  "timezone": "America/New_York",
  "email": "user@example.com",           // Optional
  "password": "new_password123",         // Optional
  "auto_sit_detection_enabled": true,
  "auto_recording_enabled": true
}
```

**Response** (200 OK):
```json
{
  "message": "Setup completed successfully.",
  "user": {
    "id": 1,
    "username": "player123",
    "email": "user@example.com",
    "timezone": "America/New_York",
    "setup_completed": true,
    "setup_completed_at": "2026-01-02T10:30:00Z",
    ...
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "error": "Setup already completed."
}
```

### GET `/api/auth/setup-wizard/`
**Authentication**: Required (JWT)

**Response**:
```json
{
  "setup_completed": false,
  "system_settings": {
    "sit_recording_available": true
  }
}
```

## Database Schema

### User Model Additions
```python
setup_completed = models.BooleanField(
    default=False,
    help_text='Whether the user has completed the initial setup wizard'
)

setup_completed_at = models.DateTimeField(
    null=True,
    blank=True,
    help_text='Timestamp when setup wizard was completed'
)
```

### Migration
```bash
# Generated migration file
apps/accounts/migrations/0004_user_setup_completed_user_setup_completed_at.py

# Apply migration
python manage.py migrate accounts
```

## Security Considerations

1. **Authentication Required**: Setup wizard endpoint requires valid JWT token
2. **One-Time Setup**: Once completed, setup cannot be re-run (prevents accidental resets)
3. **Optional Fields**: Email and password are optional to respect user privacy
4. **Password Hashing**: Uses Django's built-in `set_password()` for secure bcrypt hashing
5. **Input Validation**: Timezone validated against pytz.common_timezones list
6. **CSRF Protection**: All POST requests include CSRF token validation

## Privacy & Data Handling

### What Data is Collected
- **Timezone**: Required for proper timestamp display
- **Email**: Optional, user can skip or add later
- **Password**: Optional for OAuth users
- **Feature Preferences**: OCR and recording toggles

### What Data is NOT Collected
- No tracking of screen content
- No recording data sent during detection phase
- OCR processing happens entirely in browser
- No analytics or third-party data sharing

### User Control
- All preferences can be changed later in Settings
- Email can be removed at any time
- Recording can be disabled per-sit or globally
- OCR can be toggled on/off anytime

## Testing Checklist

### Backend Testing
- [ ] Setup wizard endpoint requires authentication
- [ ] Timezone validation works correctly
- [ ] Email validation accepts valid formats
- [ ] Password validation enforces 8+ character minimum
- [ ] UserSitPreferences created/updated correctly
- [ ] setup_completed flag set to true after submission
- [ ] setup_completed_at timestamp recorded
- [ ] Cannot re-run setup after completion

### Frontend Testing
- [ ] Wizard shows for users with setup_completed=false
- [ ] Wizard redirects after completion
- [ ] All 4 steps display correctly
- [ ] Progress indicator updates properly
- [ ] Previous/Next navigation works
- [ ] Form validation shows errors
- [ ] Auto sit detection checkbox toggles
- [ ] Auto recording checkbox toggles (if available)
- [ ] System settings fetched correctly
- [ ] Timezone dropdown populated
- [ ] OAuth users see optional password message
- [ ] Traditional users see required password message
- [ ] Submit button shows loading state
- [ ] Success redirects to /dashboard

### Integration Testing
- [ ] OAuth login → setup wizard → dashboard flow
- [ ] Traditional login → setup wizard → dashboard flow
- [ ] Setup completed users bypass wizard
- [ ] Dashboard redirects to setup if incomplete
- [ ] Auth callback checks setup status
- [ ] Token refresh maintains setup state

## Future Enhancements

1. **Welcome Tour**: Interactive dashboard tour after setup completion
2. **Profile Picture**: Allow users to upload avatar during setup
3. **Notification Preferences**: Email notification frequency settings
4. **Display Preferences**: Theme selection, language, date format
5. **Staff Onboarding**: Additional steps for staff members (discord link, server list, etc.)
6. **Setup Progress Persistence**: Save partial progress if user exits wizard
7. **Setup Reminders**: Prompt to complete setup after X days if skipped
8. **Feature Previews**: Video/GIF demos of OCR and recording features

## Related Files

### Backend
- `backend/apps/accounts/models.py` - User model with setup fields
- `backend/apps/accounts/serializers.py` - SetupWizardSerializer
- `backend/apps/accounts/views.py` - SetupWizardView
- `backend/apps/accounts/urls.py` - Setup wizard route
- `backend/apps/accounts/migrations/0004_*.py` - Database migration

### Frontend
- `frontend/src/components/auth/SetupWizard.tsx` - Main wizard component
- `frontend/src/app/setup/page.tsx` - Setup page route
- `frontend/src/contexts/AuthContext.tsx` - Auth state management
- `frontend/src/app/auth/callback/page.tsx` - OAuth callback handling
- `frontend/src/app/dashboard/layout.tsx` - Dashboard route protection

## Notes for Developers

### Adding New Setup Steps
To add a new step to the wizard:

1. Add step to `STEPS` array in `SetupWizard.tsx`:
```typescript
{ id: 5, name: 'New Step', icon: IconComponent }
```

2. Add form field to `SetupWizardData` interface:
```typescript
interface SetupWizardData {
  // ...existing fields
  new_field: string;
}
```

3. Add case to `renderStepContent()` switch statement:
```typescript
case 5:
  return (
    <div>
      {/* Step 5 content */}
    </div>
  );
```

4. Update backend `SetupWizardSerializer` to handle new field

### Modifying System Setting Checks
System settings are fetched from `/auth/setup-wizard/` GET endpoint.
To add new system setting checks:

1. Update `SetupWizardView.get()` in backend:
```python
new_setting = SystemSetting.objects.filter(
    key='new_setting_key',
    is_active=True
).first()
```

2. Add to response:
```python
'system_settings': {
    'new_setting_available': new_setting.value.lower() == 'true'
}
```

3. Use in frontend:
```typescript
{systemSettings?.new_setting_available && (
  // Conditional UI
)}
```

## Dependencies

### New Dependencies
None - Uses existing packages:
- Backend: Django, DRF, pytz (already installed)
- Frontend: React, Next.js, Heroicons, react-hot-toast (already installed)

### System Requirements
- Django 4.2+
- PostgreSQL 15+ (for datetime fields)
- Next.js 14+
- Modern browser with ES6 support

## Migration Instructions

### Development Environment
```bash
# Backend
cd backend
source venv/bin/activate  # or .\venv\Scripts\Activate.ps1 on Windows
python manage.py migrate accounts

# Frontend
cd frontend
npm install  # No new dependencies, but verify packages
npx tsc --noEmit  # Check for TypeScript errors

# Test the setup wizard
npm run dev
# Navigate to /setup after logging in with a new test user
```

### Production Deployment
```bash
# 1. Backup database
pg_dump elitelupus > backup_before_setup_wizard.sql

# 2. Apply migrations
docker-compose exec backend python manage.py migrate accounts

# 3. Verify migration
docker-compose exec backend python manage.py showmigrations accounts

# 4. Rebuild frontend
docker-compose exec frontend npm run build

# 5. Restart services
docker-compose restart backend frontend

# 6. Verify setup wizard
# Test with new user account - should redirect to /setup
```

## Rollback Procedure

If issues arise, rollback migration:
```bash
# Backend rollback
python manage.py migrate accounts 0003

# Remove migration file
rm apps/accounts/migrations/0004_user_setup_completed_user_setup_completed_at.py

# Revert code changes
git revert <commit_hash>
```

## Support & Troubleshooting

### Common Issues

**Issue**: Users stuck in setup loop
- **Cause**: setup_completed not saving
- **Fix**: Check database connection, verify serializer logic

**Issue**: Timezone dropdown empty
- **Cause**: Timezones API not loading
- **Fix**: Check `/auth/timezones/` endpoint, verify pytz installation

**Issue**: Recording option not showing
- **Cause**: System setting not enabled
- **Fix**: Enable `sit_recording_enabled` in Django admin

**Issue**: OAuth users redirected to login after setup
- **Cause**: Token refresh issue
- **Fix**: Check JWT token validity, verify refresh flow

### Debug Mode
Enable debug mode in `SetupWizard.tsx`:
```typescript
const DEBUG = true;  // Add at top of component
{DEBUG && <pre>{JSON.stringify(formData, null, 2)}</pre>}
```

## Conclusion

The first-time setup wizard provides a smooth onboarding experience for new users, ensuring essential configuration is completed before accessing the dashboard. The implementation follows Django and Next.js best practices, maintains security standards, and provides clear user guidance throughout the process.
