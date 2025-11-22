# 🎯 Complete Guide: How Watch Time Affects Recommendations

## 1. How Watch Time is Recorded

Every interaction is logged to Neo4j with:
- `user_id`: Who watched
- `venue_id`: What they watched
- `watch_time`: How long (in seconds)
- `action_type`: viewed/saved/shared/skipped
- `weight`: Calculated importance

### Weight Calculation (app/main.py:330-347)

```python
if watch_time < 3:
    weight = -0.5, action = "skipped"  # Negative signal
elif action == "save":
    weight = 1.5, action = "saved"
elif action == "share":
    weight = 3.0, action = "shared"
elif watch_time >= 30:
    weight = 2.0, action = "viewed"    # Full view
elif watch_time >= 10:
    weight = 1.0, action = "viewed"    # Engaged view
elif watch_time >= 3:
    weight = 0.3, action = "viewed"    # Brief view
```

## 2. How Watch Time Affects Friend Recommendations

### Social Proof Calculation (app/graph.py:83-92)

```python
# When calculating social scores for a venue:
for friend_engagement in friends_who_engaged:
    if action == 'shared':
        boost = +15 points  # Highest signal
    elif action == 'saved':
        boost = +8 points
    elif action == 'viewed' AND watch_time >= 10:  # ⭐ KEY FILTER
        boost = +5 points
        # Views <10s are IGNORED - quality filter!
```

**This means:**
- ✅ Friend watched 15s → **Counts** (+5 pts to that venue for you)
- ❌ Friend watched 5s → **Ignored** (doesn't affect your feed)
- ✅ Friend saved → **Strong signal** (+8 pts)
- ✅ Friend shared → **Strongest signal** (+15 pts)

## 3. When Feed Recalculation Happens

### Real-time Calculation:
- Feed is calculated **on-demand** when you load the page
- Uses **current state** of Neo4j graph
- Queries all your friends' engagement in real-time

### Steps:
1. You open Feed page → API `/feed` endpoint called
2. API queries: "What have my friends engaged with?"
3. Filters: "Only count views ≥10s"
4. Ranks venues by: `0.3×Taste + 0.4×Social + 0.2×Proximity + 0.1×Trending`
5. Returns sorted feed

## 4. Testing Watch Time Impact

### Test Scenario:

```
User A (you) and User B (friend) both exist

Step 1: Clear User B's activity
  - Go to Profiles → Select User B
  - Click "🗑️ Clear Activity"

Step 2: Check User A's feed
  - Note which venues appear
  - Note social proof scores

Step 3: User B watches venue X for 15 seconds
  - Switch to User B in TikTok view
  - Watch venue X for 15+ seconds
  - (Automatically logged)

Step 4: Check User A's feed again (refresh)
  - Venue X should now show:
    - "User B watched this" in algorithm breakdown
    - +5 points added to social score
    - Higher ranking in feed

Step 5: Clear and test short watch
  - Clear User B's activity again
  - Watch venue X for only 5 seconds
  - Check User A's feed
  - Venue X should NOT show User B activity
  - (Filtered out by 10s threshold)
```

## 5. New Features Added

### Refresh Button (Profile Page)
- Click "🔄 Refresh" next to "My Places"
- Reloads entire page to show latest data

### Clear Activity Button (Profile Page)
- Click "🗑️ Clear Activity" next to "Recent Activity"
- Removes ALL engagement for selected user
- Perfect for testing from scratch

## 6. Why Updates Don't Show Immediately

### Current Behavior:
- Data writes to Neo4j instantly ✅
- But frontend doesn't auto-poll for changes ❌

### Solution:
- Navigate away and back OR
- Click refresh button OR
- Reload browser

### For Production:
Would add WebSocket for real-time updates, but for POC manual refresh is fine.

---

## 📊 Quick Test Commands

### Clear specific user's activity
```bash
curl -X POST http://localhost:8000/debug/clear-activity \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_195"}'
```

### Check user's current activity
```bash
curl http://localhost:8000/user/user_195 | jq '.watch_history | length'
```

### Log a test watch (15 seconds)
```bash
curl -X POST http://localhost:8000/engage \
  -H "Content-Type: application/json" \
  -d '{"user_id":"user_195","venue_id":"venue_1","watch_time_seconds":15,"action":"view"}'
```

---

## 🔍 Algorithm Formula

### Final Score Calculation
```
Final Score = (0.3 × Taste Match) +
              (0.4 × Friend Activity) +
              (0.2 × Proximity) +
              (0.1 × Trending)
```

### Friend Activity Scoring
- 📤 Shared: **+15 points** (highest signal)
- 💾 Saved: **+8 points**
- 👀 Watched 10s+: **+5 points** (quality filter - only engaged views)
- 👥 Mutuals: **+2 points** per mutual friend

### Watch Time Filter
- Only views ≥10 seconds count toward recommendations
- Prevents quick skips from influencing the algorithm
- Ensures only engaged viewing affects rankings

---

## ✨ New Testing Features

### Refresh Button (Profile Page)
- Located next to "My Places" heading
- Click "🔄 Refresh" to reload page and see latest saved venues
- Useful after saving venues in other tabs/windows

### Clear Activity Button (Profile Page)
- Located next to "Recent Activity" heading
- Click "🗑️ Clear Activity" to remove ALL engagement for selected user
- Perfect for testing from scratch
- Confirms before clearing to prevent accidents

### Watch Time Display (Both Views)
- **TikTok View**: Split-screen shows algorithm breakdown with watch time filter info
- **Grid View**: Each card shows formula and watch time requirements
- Social Proof sections clearly label: "👀 watched ≥10s" for transparency

---

## 🐛 Bugs Fixed

### Watch Time Logging to Wrong Venue
**Problem**: Watch time was being attributed to the next venue instead of current one
**Cause**: JavaScript closure issue - `watchStartTime` state was stale in the interval callback
**Fix**: Used `useRef` to maintain current timestamp across re-renders (`watchStartTimeRef.current`)
**Result**: Watch time now correctly logs to the venue you're actually watching

### Watch Time Not Visible in UI
**Problem**: Users couldn't see how watch time was used in the algorithm
**Fix**: Added explicit labels and info boxes:
- Final Score card: "⏱️ Watch Time Filter: Only friends who watched ≥10s count"
- Social Proof: Quality filter breakdown with point values
- Friend actions: "👀 watched ≥10s" instead of just "watched"
**Result**: Algorithm is now fully transparent about watch time usage
