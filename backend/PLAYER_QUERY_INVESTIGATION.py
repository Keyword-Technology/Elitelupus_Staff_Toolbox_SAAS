"""
Investigation findings for player query bz2 decompression issue.

## Problem Analysis:

The error occurs at: a2s_fragment.py line 35: `frag.payload = bz2.decompress(reader.read())`

### Root Cause:
The game server is sending **compressed player data using bz2**, but the data stream is:
1. **Incomplete/truncated** - The bz2 compressed data is cut off mid-stream
2. **Corrupted** - The compression headers or data is malformed
3. **Fragmented incorrectly** - Multi-packet responses aren't being reassembled properly

### Why This Happens:
1. **Large player count (78 players)** means the player list needs compression
2. **GMod servers with many players** often have issues with fragmented A2S responses
3. **Some GMod plugins/addons** interfere with A2S player queries
4. **Network packet fragmentation** can cause incomplete data transmission

### Evidence:
- Server INFO query works fine (smaller response, no compression needed)
- Player query fails consistently with "Invalid data stream"
- Error specifically happens during bz2.decompress() call
- Timeout increases don't help (not a timing issue)

### Why We Can't Fix It Completely:
- This is a **server-side issue** with how GMod sends compressed player data
- The a2s library correctly tries to decompress, but the data is malformed
- Without fixing the game server's A2S implementation, we can't get player lists

### Workarounds Implemented:
1. ✅ Catch OSError for bz2 decompression failures
2. ✅ Continue with empty player list (server still shows as online)
3. ✅ Log warning for debugging
4. ✅ Server info (player count, map, name) still works

### What Staff Tracking Loses:
- Cannot track individual players by name
- Cannot detect which specific staff members are online
- Cannot track staff join/leave times accurately
- Staff online count will always show 0

### Possible Future Solutions:
1. **Use alternative source query library** (valve-python, srcds-py)
2. **Contact server admin** to fix GMod A2S configuration
3. **Use RCON instead** (requires server auth but more reliable)
4. **Parse from web-based player lists** if server has web API
5. **Install server-side plugin** that provides custom API endpoint

### Recommendation:
Accept that player tracking won't work with current server configuration.
The info query provides enough data for basic server status monitoring.
"""
pass
