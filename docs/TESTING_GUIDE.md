# 🧪 Testing Guide: Geo-Recommender Algorithm

This guide will help you test and validate the watch time algorithm and social proof features.

---

## 🚀 Quick Start

### Prerequisites
1. Backend running: `docker-compose up`
2. Frontend running: `npm start` (in frontend directory)
3. Data seeded: `docker-compose exec api python seeder_enhanced.py --all`

### Open the App
- Navigate to: `http://localhost:3000`
- You should see 200 seeded users with engagement data

---

## 📋 Test Scenarios

### Test 1: Watch Time Affects Friend Recommendations

**Goal**: Prove that watching a venue for 10+ seconds makes it appear in friend's feeds with social proof.

#### Steps:

1. **Select User A (Your Main Test User)**
   - Go to Feed page
   - Select "Angela Meyer" (user_195) from dropdown
   - Note: Angela has 10 friends

2. **Find a Venue to Test**
   - Look at the feed in Grid View
   - Pick a venue with LOW social proof (e.g., 0-2 friends)
   - Note the venue name (e.g., "Paula Cooper SoHo")

3. **Switch to User B (A Friend of Angela)**
   - Go to Profiles page
   - Check Angela's friends list (Jesus Nelson, Lisa Guzman, etc.)
   - Switch to Feed → Select one of Angela's friends (e.g., "Jesus Nelson")

4. **Clear User B's Activity (Fresh Start)**
   - Go to Profiles → Select Jesus Nelson
   - Click "🗑️ Clear Activity" button
   - Confirm the action
   - ✅ Jesus now has NO engagement history

5. **Jesus Watches the Venue for 15 Seconds**
   - Go to Feed → Select Jesus Nelson
   - Click "Immersive View"
   - Swipe until you find "Paula Cooper SoHo"
   - **WAIT 15 SECONDS** (watch the timer in the background)
   - You should see engagement being logged every 5 seconds
   - Swipe to next venue

6. **Verify Jesus's Activity Was Logged**
   - Go to Profiles → Select Jesus Nelson
   - Click "🔄 Refresh" button
   - Check "Recent Activity" section
   - ✅ You should see "Paula Cooper SoHo" with "Viewed, 15s watched"

7. **Check Angela's Feed (Should Show Social Proof)**
   - Go to Feed → Select Angela Meyer
   - Refresh the page (Cmd+R / Ctrl+R)
   - Find "Paula Cooper SoHo" in the feed
   - **Expected Results:**
     - Social Proof score should be HIGHER than before
     - Algorithm breakdown should show: "Jesus Nelson 👀 watched ≥10s +5"
     - Venue ranking may have changed (moved up in feed)

8. **Compare: Short Watch (Under 10s) Doesn't Count**
   - Still as Jesus Nelson
   - Go to Profiles → Click "🗑️ Clear Activity" again
   - Go to Immersive View
   - Find a DIFFERENT venue
   - **Watch for only 5 seconds** then swipe away quickly
   - Go back to Angela's feed
   - ✅ This venue should NOT show Jesus in social proof (filtered out by 10s threshold)

---

### Test 2: Different Actions Have Different Weights

**Goal**: Demonstrate that Shared (+15), Saved (+8), and Watched 10s+ (+5) have different impacts.

#### Steps:

1. **Setup: Clear User B's Activity**
   - Profiles → Select Jesus Nelson → Clear Activity

2. **Test Venue 1: Jesus SHARES**
   - Switch to Jesus in Immersive View
   - Find "Blue Note Greenpoint"
   - Watch for 5 seconds
   - Click "Share" button (green button)
   - ✅ Alert: "Shared with friends!"

3. **Test Venue 2: Jesus SAVES**
   - Swipe to next venue (e.g., "Dominique Ansel")
   - Watch for 5 seconds
   - Click "Save" button (blue button)
   - ✅ Alert: "Saved!"

4. **Test Venue 3: Jesus WATCHES 15s**
   - Swipe to next venue (e.g., "Pace Gallery")
   - **Wait 15 seconds** (don't click anything)
   - Then swipe away

5. **Check Angela's Feed - Compare Point Values**
   - Go to Feed → Select Angela Meyer
   - Refresh page
   - Find all three venues
   - **Expected Algorithm Breakdown:**
     - Blue Note: "Jesus Nelson 📤 shared +15" (highest boost)
     - Dominique Ansel: "Jesus Nelson 💾 saved +8" (medium boost)
     - Pace Gallery: "Jesus Nelson 👀 watched ≥10s +5" (lowest boost)
   - ✅ Venues should be ranked in this order (shared > saved > watched)

---

### Test 3: Multiple Friends Compound Social Proof

**Goal**: Show that multiple friends engaging with the same venue creates strong social proof.

#### Steps:

1. **Pick a Target Venue**
   - Select Angela Meyer's feed
   - Choose a venue (e.g., "Roberta's Williamsburg")

2. **Have 3 Different Friends Engage**
   - **Friend 1 (Jesus)**: Share the venue
   - **Friend 2 (Lisa)**: Save the venue
   - **Friend 3 (Peter)**: Watch for 20 seconds

3. **Check Angela's Feed**
   - Refresh Angela's feed
   - Find "Roberta's Williamsburg"
   - **Expected Social Proof:**
     - "Jesus Nelson 📤 shared +15"
     - "Lisa Guzman 💾 saved +8"
     - "Peter Smith 👀 watched ≥10s +5"
     - **Total Social Score: +28 points** (normalized to ~56%)
   - ✅ Venue should rank VERY HIGH in feed

---

### Test 4: Watch Time Threshold (10 Second Filter)

**Goal**: Prove that only views ≥10 seconds count.

#### Steps:

1. **Setup: Fresh Slate**
   - Clear Jesus Nelson's activity
   - Pick a test venue (e.g., "Clinton St. Baking")

2. **Watch for Exactly 5 Seconds**
   - Switch to Jesus in Immersive View
   - Find "Clinton St. Baking"
   - Start watching
   - **After 5 seconds exactly**, swipe away
   - Go to Profiles → Refresh
   - ✅ Should show "Clinton St. Baking, Viewed, 5s watched"

3. **Check Angela's Feed**
   - Switch to Angela
   - Refresh feed
   - Find "Clinton St. Baking"
   - **Expected Result:**
     - Social proof should NOT include Jesus
     - Algorithm breakdown should NOT show "Jesus Nelson watched"
     - ✅ 5 seconds is below the 10s threshold

4. **Now Watch for 12 Seconds**
   - Clear Jesus's activity again
   - Go to Immersive View
   - Find same venue "Clinton St. Baking"
   - **Watch for 12+ seconds**
   - Swipe away

5. **Check Angela's Feed Again**
   - Refresh Angela's feed
   - Find "Clinton St. Baking"
   - **Expected Result:**
     - ✅ NOW shows "Jesus Nelson 👀 watched ≥10s +5"
     - Social score increased
     - Ranking may have improved

---

### Test 5: Mutual Friends Boost

**Goal**: Understand how mutual friends (friends-of-friends) affect recommendations.

#### Steps:

1. **Check Angela's Friend Network**
   - Profiles → Select Angela
   - Note her direct friends (10 people)

2. **Find Angela's Mutual Friends**
   - Select one of Angela's friends (e.g., Jesus)
   - Check Jesus's friend list
   - Find people who are Jesus's friends but NOT Angela's direct friends
   - These are "mutual friends" (2nd degree connections)

3. **Have a Mutual Friend Engage**
   - Switch to a mutual friend
   - Have them save a venue
   - Clear their activity first for clean test

4. **Check Angela's Feed**
   - Look for that venue in Angela's feed
   - **Expected Social Proof:**
     - Should show "X mutual friends interested +2" (per mutual)
     - Lower boost than direct friends (+2 vs +5/+8/+15)
     - ✅ Demonstrates that network effects extend beyond direct friends

---

## 🔍 Verification Checklist

### Algorithm Transparency

For EVERY venue in the feed, verify you can see:

- [ ] **Final Match Score** (big percentage number)
- [ ] **Formula**: `0.3×Taste + 0.4×Social + 0.2×Proximity + 0.1×Trending`
- [ ] **Watch Time Filter Notice**: "⏱️ Only friends who watched ≥10s count"
- [ ] **Taste Match Score** with % and progress bar
- [ ] **Friend Activity Score** with % and progress bar
- [ ] **Friend-by-Friend Breakdown**: Names, actions (📤/💾/👀), and point values
- [ ] **Proximity Score** with distance in km
- [ ] **Trending Score** with recent engagement count

### Profile Page

For each user profile, verify:

- [ ] **Friends Section**: Shows all friends with interests
- [ ] **My Places Section**: Shows saved venues with gradient headers
- [ ] **Recent Activity Section**: Shows all engagement with watch times
- [ ] **Refresh Button**: Works to reload latest data
- [ ] **Clear Activity Button**: Works to reset engagement history

---

## 🎯 Expected Outcomes

### Social Proof Point System
```
Action          | Points | Shows in Feed
----------------|--------|---------------------------
Shared          | +15    | "👥 Name 📤 shared"
Saved           | +8     | "👥 Name 💾 saved"
Watched 10s+    | +5     | "👥 Name 👀 watched ≥10s"
Watched <10s    | 0      | NOT shown (filtered out)
Mutual Friend   | +2     | "X mutual friends interested"
```

### Score Normalization
- Raw points are normalized to 0-100%
- Max expected social score: ~50 raw points = 100%
- Example: 15 points (1 share) = 30% social score

### Final Ranking Formula
```
Final Score = (0.3 × Taste Match %) +
              (0.4 × Social Proof %) +
              (0.2 × Proximity %) +
              (0.1 × Trending %)
```

**Weights Explained:**
- **Social (40%)**: Highest weight - friends' opinions matter most
- **Taste (30%)**: Your personal interests
- **Proximity (20%)**: How close the venue is
- **Trending (10%)**: Recent popularity

---

## 🐛 Common Issues & Debugging

### Issue: "No venues found" in Immersive View

**Solution:**
```bash
# Re-seed the database
docker-compose exec api python seeder_enhanced.py --all
```

### Issue: Friend activity not showing up

**Checklist:**
1. Did you refresh the page after the friend engaged?
2. Did the friend watch for ≥10 seconds? (Check their Recent Activity)
3. Are they actually friends? (Check Friends list on Profiles page)
4. Is the venue within the 2km radius? (Check proximity score)

### Issue: Watch time seems wrong

**Debug:**
```bash
# Check raw engagement data
curl http://localhost:8000/user/user_195 | jq '.watch_history'

# Clear specific user's activity
curl -X POST http://localhost:8000/debug/clear-activity \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_195"}'
```

### Issue: Profile not updating after save

**Solution:**
- Click the "🔄 Refresh" button on Profiles page
- Or navigate away and back to the Profiles page

---

## 📊 API Testing Commands

### Check User's Current Activity
```bash
curl http://localhost:8000/user/user_195 | jq '.watch_history | length'
```

### Manually Log Engagement (for testing)
```bash
# Log a 15-second view
curl -X POST http://localhost:8000/engage \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_195",
    "venue_id": "venue_1",
    "watch_time_seconds": 15,
    "action": "view"
  }'

# Log a save
curl -X POST http://localhost:8000/engage \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_195",
    "venue_id": "venue_1",
    "watch_time_seconds": 5,
    "action": "save"
  }'

# Log a share
curl -X POST http://localhost:8000/engage \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_195",
    "venue_id": "venue_1",
    "watch_time_seconds": 3,
    "action": "share"
  }'
```

### Get Feed for a User
```bash
curl "http://localhost:8000/feed?user_id=user_195&lat=40.7128&lon=-74.0060&radius_km=2.0&limit=10" \
  | jq '.feed[0] | {name, final_score, explanation}'
```

### Check Neo4j Data
```bash
# Count all engagement relationships
docker-compose exec neo4j cypher-shell -u neo4j -p password \
  "MATCH ()-[r:ENGAGED_WITH]->() RETURN count(r)"

# Find all friends of a user
docker-compose exec neo4j cypher-shell -u neo4j -p password \
  "MATCH (u:User {id: 'user_195'})-[:FRIENDS_WITH]-(f) RETURN f.name"
```

### Clear All Activity for a User
```bash
curl -X POST http://localhost:8000/debug/clear-activity \
  -H "Content-Type: application/json" \
  -d '{"user_id": "user_195"}'
```

---

## 🎬 Demo Script (5 Minutes)

Perfect for showing stakeholders:

### Setup (30 seconds)
1. Open app, show Feed page with Angela Meyer
2. Point out algorithm transparency on any venue card

### Demo 1: Watch Time Filter (2 minutes)
1. Switch to Jesus Nelson (Angela's friend)
2. Clear Jesus's activity
3. Show Immersive view, find a venue
4. "I'm going to watch this for only 5 seconds" → swipe away
5. Switch to Angela's feed
6. "Notice: Jesus's 5-second view doesn't appear in social proof"
7. Back to Jesus, watch same venue for 15 seconds
8. Switch to Angela's feed, refresh
9. **"Now it appears! 👀 watched ≥10s +5 points"**

### Demo 2: Action Weight Differences (2 minutes)
1. As Jesus: Share a venue → Show "+15 points"
2. As Jesus: Save a venue → Show "+8 points"
3. As Jesus: Watch a venue 15s → Show "+5 points"
4. Switch to Angela's feed
5. **"Different actions have different weights based on intent strength"**

### Wrap Up (30 seconds)
1. Show formula: "40% social proof is our highest weight"
2. Show full transparency: "Every number is explained"
3. **"Users can understand and trust the algorithm"**

---

## ✅ Test Coverage Summary

After completing all tests, you will have validated:

- ✅ Watch time threshold (10 seconds) is enforced
- ✅ Different actions have different point values (15/8/5)
- ✅ Multiple friends compound social proof
- ✅ Mutual friends (2nd degree) provide smaller boosts
- ✅ Algorithm is fully transparent and explainable
- ✅ Real-time engagement tracking works correctly
- ✅ Profile updates show latest activity
- ✅ Clear activity button works for fresh testing
- ✅ Final score formula is visible and accurate
- ✅ Watch time logs to correct venue (not next one)

---

## 📝 Notes

- **Feed is calculated on-demand**: Every time you load/refresh the feed page
- **No caching**: Changes appear immediately after refresh
- **Testing is non-destructive**: Use "Clear Activity" to reset anytime
- **200 seeded users**: Pre-loaded with realistic engagement patterns
- **150 NYC venues**: Across 10 neighborhoods (Williamsburg, SoHo, etc.)

For questions or issues, check `WATCH_TIME_GUIDE.md` for detailed algorithm documentation.
