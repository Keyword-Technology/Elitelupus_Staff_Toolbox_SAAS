# Account Linking System - Steam & Discord

## Overview

The system now automatically links Steam and Discord accounts based on the staff roster. When a user signs in with Discord after previously signing in with Steam (or vice versa), the system will:

1. Check the staff roster for matching Steam ID and Discord ID
2. If a match is found, link the accounts into a single user account
3. Prevent duplicate accounts for the same staff member

## How It Works

### Staff Roster Matching

The staff roster (`StaffRoster` model) contains both Steam IDs and Discord IDs for each staff member:

```python
class StaffRoster(models.Model):
    name = models.CharField(max_length=100)
    steam_id = models.CharField(max_length=50, blank=True, null=True)
    discord_id = models.CharField(max_length=50, blank=True, null=True)
    # ... other fields
```

### Authentication Pipeline

The `create_or_link_user` pipeline function (in `apps/accounts/pipeline.py`) has been enhanced to:

#### For Steam Login:
1. Check if user exists with this Steam ID → use existing account
2. **NEW:** Check staff roster for matching Steam ID → find associated Discord ID
3. **NEW:** If Discord user exists → link Steam account to that user
4. Check email match → link if found
5. Create new account if no match

#### For Discord Login:
1. Check if user exists with this Discord ID → use existing account
2. **NEW:** Check staff roster for matching Discord ID → find associated Steam ID
3. **NEW:** If Steam user exists → link Discord account to that user
4. Check email match → link if found
5. Create new account if no match

### Example Scenarios

#### Scenario 1: Steam First, Then Discord

1. **User signs in with Steam:**
   - Creates account: `username="steam_76561198123456789"`
   - Sets: `steam_id="STEAM_0:1:12345"`, `steam_id_64="76561198123456789"`

2. **Same user later signs in with Discord:**
   - Staff roster shows: `steam_id="STEAM_0:1:12345"`, `discord_id="987654321"`
   - System finds existing Steam user with matching Steam ID
   - Links Discord info to existing account:
     - Sets: `discord_id="987654321"`, `discord_username="JohnDoe"`
   - User continues using the same account ✓

#### Scenario 2: Discord First, Then Steam

1. **User signs in with Discord:**
   - Creates account: `username="discord_987654321"`
   - Sets: `discord_id="987654321"`, `discord_username="JohnDoe"`

2. **Same user later signs in with Steam:**
   - Staff roster shows: `discord_id="987654321"`, `steam_id="STEAM_0:1:12345"`
   - System finds existing Discord user with matching Discord ID
   - Links Steam info to existing account:
     - Sets: `steam_id="STEAM_0:1:12345"`, `steam_id_64="76561198123456789"`
   - User continues using the same account ✓

## Retroactive Account Linking

For existing users who already have separate Steam and Discord accounts, use the management command:

### Test First (Dry Run)

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py link_accounts --dry-run
```

This will show you what would be linked without making any changes.

### Apply the Linking

```powershell
cd backend
.\venv\Scripts\Activate.ps1
python manage.py link_accounts
```

### What the Command Does

The `link_accounts` command:

1. **Finds roster entries** with both Steam and Discord IDs
2. **Looks for user accounts** with matching Steam or Discord IDs
3. **Merges accounts** in the following ways:

   **Case 1: Both Steam and Discord users exist (separate accounts)**
   - Links Discord info to Steam account
   - Deactivates the Discord-only account
   - Preserves all data in the Steam account

   **Case 2: Only Steam user exists**
   - Adds Discord ID to Steam account
   - Discord details will be filled in on next Discord login

   **Case 3: Only Discord user exists**
   - Adds Steam ID to Discord account
   - Steam details will be filled in on next Steam login

   **Case 4: Already linked**
   - Skips (no action needed)

### Command Output Example

```
Starting account linking process...
Found 25 roster entries with both Steam and Discord IDs

Found separate accounts for John Doe:
  Steam account: steam_76561198123456789 (ID: 15)
  Discord account: discord_987654321 (ID: 42)
  ✓ Linked Discord to Steam account and deactivated Discord-only account

Adding Discord info to steam_76561198111111111 from roster
  ✓ Added Discord ID to Steam account

============================================================
COMPLETE: Linked 18 accounts
Skipped: 7 (already linked or no users yet)
============================================================
```

## Data Flow Diagram

```
Staff Roster (Google Sheets)
    ↓ [Sync]
StaffRoster Model
    ├─ steam_id: "STEAM_0:1:12345"
    └─ discord_id: "987654321"
         ↓ [OAuth Login]
    Authentication Pipeline
         ↓ [Check Roster]
    User Account (Linked)
    ├─ steam_id: "STEAM_0:1:12345"
    ├─ steam_id_64: "76561198123456789"
    ├─ discord_id: "987654321"
    └─ discord_username: "JohnDoe"
```

## Database Schema

### User Model Fields

```python
class User(AbstractUser):
    # Steam Integration
    steam_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    steam_id_64 = models.CharField(max_length=50, blank=True, null=True)
    steam_profile_url = models.URLField(blank=True, null=True)
    steam_avatar = models.URLField(blank=True, null=True)
    
    # Discord Integration
    discord_id = models.CharField(max_length=50, blank=True, null=True, unique=True)
    discord_username = models.CharField(max_length=100, blank=True, null=True)
    discord_discriminator = models.CharField(max_length=10, blank=True, null=True)
    discord_avatar = models.URLField(blank=True, null=True)
```

Both `steam_id` and `discord_id` can exist on the same user account!

## Testing the Integration

### Test Plan

1. **Create test roster entry** in Google Sheets with both Steam and Discord IDs
2. **Sync the roster:**
   ```powershell
   cd backend
   .\venv\Scripts\Activate.ps1
   python manage.py sync_staff
   ```

3. **Test Steam login:**
   - Go to login page
   - Click "Sign in with Steam"
   - Verify account created

4. **Test Discord linking:**
   - Logout
   - Click "Sign in with Discord" 
   - Should link to the same account (check username stays the same)

5. **Verify in database:**
   ```powershell
   python manage.py shell
   ```
   ```python
   from apps.accounts.models import User
   
   user = User.objects.get(username='steam_76561198123456789')
   print(f"Steam ID: {user.steam_id}")
   print(f"Discord ID: {user.discord_id}")  # Should be populated!
   ```

### Expected Results

- ✅ Only ONE user account exists
- ✅ Account has both `steam_id` and `discord_id` populated
- ✅ User can login with either Steam or Discord and access the same account
- ✅ Display name and avatar can come from either platform
- ✅ No duplicate counters, notes, or other user-related data

## Logging

The system logs account linking operations:

```python
logger.info(f"Linked Discord account to existing Steam user {existing_user.username} via staff roster")
logger.info(f"Linked Steam account to existing Discord user {existing_user.username} via staff roster")
```

Check Django logs for these messages to confirm linking is working.

## Benefits

1. **Single Sign-On**: Users can login with either Steam or Discord
2. **No Duplicates**: Staff members won't have multiple accounts
3. **Data Integrity**: Counters, notes, and activity tracked in one place
4. **Seamless Experience**: Users don't need to know which account they used before
5. **Automatic**: Happens transparently during login, no user action needed

## Requirements

- Staff roster must have both Steam ID and Discord ID for the staff member
- Staff roster must be synced before first login
- User must be in active staff roster to login

## Limitations

- Only links accounts that are in the staff roster
- Requires staff roster to have both identifiers populated
- If roster data is incorrect, linking won't work correctly

## Troubleshooting

### User has two separate accounts

**Problem:** User logged in with Steam before roster sync, then with Discord after.

**Solution:**
```powershell
python manage.py link_accounts
```

### Linking not working

**Check:**
1. Is staff roster synced? `python manage.py sync_staff`
2. Does roster have both Steam and Discord IDs?
3. Are the IDs correct in the roster?
4. Check Django logs for linking messages

### Account linked to wrong user

**Problem:** Incorrect Steam/Discord ID in roster

**Solution:**
1. Fix the roster data in Google Sheets
2. Re-sync: `python manage.py sync_staff`
3. Manually update user in Django admin if needed

## Code References

- **Pipeline:** `backend/apps/accounts/pipeline.py` → `create_or_link_user()`
- **Management Command:** `backend/apps/accounts/management/commands/link_accounts.py`
- **User Model:** `backend/apps/accounts/models.py` → `User`
- **Staff Roster:** `backend/apps/staff/models.py` → `StaffRoster`

## Summary

The account linking system ensures that staff members have a single, unified account regardless of which authentication method they use. This is achieved by cross-referencing the staff roster during the OAuth login process and linking accounts when a match is found.
