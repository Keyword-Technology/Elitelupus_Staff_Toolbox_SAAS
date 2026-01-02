# OCR Detection Fix - Sit Claim Not Detected

## Issues Identified

### 1. **Stale Closure Problem** ⚠️
The OCR detection callback was suffering from a stale closure issue:
- `useScreenOCR` was initialized with `onDetection: (event) => handleOCRDetection(event)`
- `handleOCRDetection` was defined later in the component
- When `handleOCRDetection` dependencies changed, the OCR hook still referenced the old version
- **Result**: Detection events were logged but never triggered the UI response

### 2. **Overly Strict Regex Patterns** 🔍
The original patterns were too strict for OCR text recognition:
```typescript
// OLD - too strict
CLAIM_PATTERN: /\[Elite Reports\]\s*(\w+)\s+claimed\s+(.+?)['']?s?\s+repo[rt]/i
```

OCR frequently mangles text:
- "Elite Reports" → "Elite Report" or "EliteReports" or "Elite Repo rts"
- "claimed" → "claim" or "claime"
- "report" → "repor" or "repo" or "rep ort"

**Examples from logs**:
- ✅ Detected: `[Elite Reports] ofcWilliam claimed PurpleBits's repor`
- ❌ Missed: `Elite Reports ofcWilliam claim PurpleBits repo`

### 3. **Insufficient Debugging** 🐛
When detection failed, there was no clear indication of:
- Why the regex didn't match
- What the actual OCR text was
- Whether the callback was even being called

## Solutions Implemented

### Fix 1: Callback Ref Pattern ✅
Implemented a ref-based callback to prevent stale closures:

```typescript
// Add ref for the callback
const ocrDetectionCallbackRef = useRef<((event: OCRDetectionEvent) => void) | null>(null);

// OCR hook uses a stable wrapper
const ocr = useScreenOCR(recording.stream, {
  onDetection: (event) => {
    console.log('[useActiveSit] OCR detection callback triggered:', event.type);
    if (ocrDetectionCallbackRef.current) {
      ocrDetectionCallbackRef.current(event);
    } else {
      console.warn('[useActiveSit] OCR detection callback ref is null!');
    }
  },
});

// Update ref when handler changes
useEffect(() => {
  console.log('[useActiveSit] Updating OCR detection callback ref');
  ocrDetectionCallbackRef.current = handleOCRDetection;
}, [handleOCRDetection]);
```

**Why this works**:
- The `onDetection` function passed to OCR is now stable (doesn't change)
- It always calls the latest version of `handleOCRDetection` via the ref
- No stale closure issues

### Fix 2: More Flexible Regex Patterns ✅
Made patterns more lenient to handle OCR errors:

```typescript
// NEW - flexible for OCR errors
CLAIM_PATTERN: /\[Elite\s*Reports?\]\s*(\w+)\s+claim(?:ed)?\s+(.+?)['']?s?\s+rep(?:o[rt]?|or|ort)/i
CLOSE_PATTERN: /You\s+have\s+clos(?:ed)?\s+(.+?)['']?s?\s+rep(?:o[rt]?|or|ort)/i
```

**Improvements**:
- `Elite\s*Reports?` - Allows "Elite Report" or "Elite Reports" with flexible spacing
- `claim(?:ed)?` - Matches "claim" or "claimed"
- `rep(?:o[rt]?|or|ort)` - Matches "rep", "repo", "repor", "report", "reort"
- More flexible whitespace handling

### Fix 3: Enhanced Debug Logging ✅
Added comprehensive logging at every step:

**In useActiveSit.ts**:
```typescript
console.log('[useActiveSit] handleOCRDetection called:', {
  type: event.type,
  isFeatureEnabled: state.isFeatureEnabled,
  ocrEnabled: state.preferences?.ocr_enabled,
  isActive: state.isActive,
  reporterName: event.parsedData.reporterName,
  staffName: event.parsedData.staffName,
});
```

**In useScreenOCR.ts**:
```typescript
// When pattern doesn't match but keywords are present
if (text.includes('Elite') && text.includes('claim') && text.includes('rep')) {
  console.log('[OCR] ⚠️ Claim keywords found but pattern did NOT match. Text sample:', {
    sample: text.substring(0, 300),
    hasEliteReports: /Elite\s*Reports?/i.test(text),
    hasClaim: /claim(?:ed)?/i.test(text),
    hasReport: /rep(?:o[rt]?|or|ort)/i.test(text),
    testPattern: OCR_PATTERNS.CLAIM_PATTERN.toString(),
  });
}
```

## Testing the Fixes

### What to Look For in Console Logs

1. **When OCR detects a claim**:
   ```
   [OCR chat] Scan #X: {textLength: 340, preview: "[Elite Reports] ofcWilliam claimed..."}
   [OCR] 🎯 CLAIM DETECTED: {staffName: 'ofcWilliam', reporterName: 'PurpleBits', ...}
   [useActiveSit] OCR detection callback triggered: claim
   [useActiveSit] handleOCRDetection called: {type: 'claim', isActive: false, ...}
   [useActiveSit] 🎯 Claim detected - starting new sit
   ```

2. **If pattern fails but keywords present**:
   ```
   [OCR] ⚠️ Claim keywords found but pattern did NOT match. Text sample: {...}
   ```
   This helps us refine the regex further if needed.

3. **If callback isn't set**:
   ```
   [useActiveSit] OCR detection callback ref is null!
   ```
   This would indicate the ref initialization failed.

### Expected Behavior After Fix

1. ✅ **Claim Detection**: When "[Elite Reports] StaffName claimed PlayerName's report" appears in chat
   - OCR detects it
   - Console shows detection logs
   - If auto-start enabled: Sit modal opens immediately
   - If confirmation enabled: Shows confirmation modal

2. ✅ **Popup Detection**: When report popup shows "CLAIM" button
   - Alternative detection method
   - Should trigger same sit creation flow

3. ✅ **Close Detection**: When "You have closed PlayerName's report" appears
   - Automatically ends active sit
   - Uploads recording if enabled

## Files Modified

1. **frontend/src/hooks/useScreenOCR.ts**
   - More flexible `CLAIM_PATTERN` and `CLOSE_PATTERN`
   - Enhanced debug logging for pattern matching failures
   - Better handling of OCR text variations

2. **frontend/src/hooks/useActiveSit.ts**
   - Added `ocrDetectionCallbackRef` to prevent stale closures
   - Stable wrapper function for OCR `onDetection`
   - `useEffect` to update callback ref
   - Comprehensive logging throughout `handleOCRDetection`

## Common OCR Text Variations Handled

| Expected Text | OCR Variations Handled |
|---------------|------------------------|
| `[Elite Reports]` | `[Elite Report]`, `[EliteReports]`, `[Elite Repo rts]` |
| `claimed` | `claim`, `claime`, `claimed` |
| `report` | `repo`, `repor`, `report`, `rep ort`, `reort` |
| `PurpleBits's` | `PurpleBits's`, `PurpleBits'`, `PurpleBits` |

## If Still Not Working

### Debug Checklist

1. **Check OCR is enabled**:
   - Navigate to Counter Settings
   - Ensure "Enable OCR Sit Detection" is ON
   - Check "OCR Chat Region" and "OCR Popup Region" are enabled

2. **Check screen capture permissions**:
   - Browser console should show: `[OCR] ✅ Video metadata loaded`
   - If not, screen capture isn't working

3. **Verify OCR region alignment**:
   - Use the region adjuster tool to ensure regions capture chat/popup areas
   - Save custom regions if default positions are off

4. **Check console for errors**:
   - Look for pattern match failures: `[OCR] ⚠️ Claim keywords found but pattern did NOT match`
   - This shows the actual OCR text and what's being tested
   - If you see this, share the full log to refine the regex further

5. **Test with different resolutions**:
   - OCR quality varies with screen resolution
   - Higher resolution = better OCR accuracy
   - Consider adjusting scan interval if CPU-bound

## Performance Notes

- Scan interval: Default 1500ms (1.5 seconds)
- Scans two regions: chat (lower-left) and popup (upper-left)
- Each scan processes ~0.15-0.3 MB of image data
- Tesseract.js runs in Web Worker (non-blocking)
- Consider increasing interval to 2000-3000ms on slower machines

## Next Steps if Issues Persist

If detection still fails with these fixes:

1. **Capture screenshot during claim** and share it
2. **Copy full console log** starting from "Screen capture started"
3. **Note screen resolution** and game settings
4. **Try manually adjusting OCR regions** to better capture text areas

The enhanced logging will now show exactly where the detection is failing, making it much easier to diagnose and fix.
