# GeoSocial Recommendation Algorithm - Explained Simply

## 🎯 Overview

GeoSocial uses a **multi-factor ranking algorithm** to recommend local business videos to users based on their interests, friend activity, location, and content freshness. Think of it as "Short Video meets Yelp meets your friend group's recommendations."

## 📊 How Videos Are Ranked

Every video gets a **Final Match Score** (0-100%) calculated from 4 weighted factors:

```
Final Score = (0.3 × Taste Match) + (0.4 × Friend Activity) + (0.2 × Proximity) + (0.1 × Trending)
```

---

## 1️⃣ Taste Match (30% Weight)

### What It Measures
How well the video matches your personal interests and preferences.

### How It Works
- Uses **vector similarity search** (embeddings) to compare:
  - Your saved interests (e.g., "jazz", "wine", "galleries")
  - The video's categories and venue type
  - Your engagement history (venues/videos you've interacted with)

### Example
- **User Profile:** Interested in jazz, wine, galleries
- **Video:** "Live Jazz Night at Blue Note" (categories: music, jazz, bar)
- **Result:** High taste match (~80-90%) because jazz + music align with interests

### Technical Details
- Embeddings stored in Qdrant vector database
- Cosine similarity between user vector and video vector
- Returns top candidates based on taste similarity

---

## 2️⃣ Friend Activity (40% Weight) - **Highest Weight!**

### What It Measures
How your friends have engaged with this video and venue.

### Why It's Weighted Highest
Friend recommendations are the **most trusted signal** in local discovery. If your friend loved a place, you're much more likely to enjoy it too.

### Two Types of Social Proof

#### A) Video-Specific Engagement (Higher Weight)
Friends who interacted with **THIS exact video**:

| Action | Points | Quality Signal |
|--------|--------|----------------|
| **Shared** | +15 | Strongest - friend actively recommends it |
| **Saved** | +8 | Strong - friend wants to return/remember |
| **Watched ≥10s** | +5 | Good - friend found it interesting |

**Example:**
- "Nina Patel shared this video" = +15 points
- "Sarah Chen saved this video" = +8 points

#### B) Venue-Level Context (Lower Weight)
Friends who engaged with **OTHER videos from this venue**:

| Metric | Points | What It Means |
|--------|--------|---------------|
| **Per friend** | +2 | Friend is interested in this venue |
| **Cap** | +10 max | Prevents over-weighting |

**Example:**
- "3 friends love this place" = +6 points
  - Meaning: 3 friends watched different videos from Blue Note SoHo
  - Shows venue popularity in your social circle

#### C) Mutual Friends (2nd Degree)
Friends-of-friends who engaged:

| Metric | Points | What It Means |
|--------|--------|---------------|
| **Per mutual** | +2 | Weak signal but indicates broader interest |

### Watch Time Quality Filter ⏱️
Only **genuine engagement counts** toward social proof:
- ✅ Watch time ≥10 seconds → Counts
- ❌ Watch time <10 seconds → Ignored (quick skip)
- ✅ Saved/Shared → Always counts

This prevents accidental swipes or quick dismissals from inflating scores.

### Real Example Breakdown
```
Video: "Happy Hour Special" at Blue Note SoHo
Social Score: 23 points

Contributors:
- Nina Patel shared this video (+15)
- 3 friends love this place (+6)
- 1 mutual friend interested (+2)

Total: 23 points → Normalized to 46% score (23/50)
```

---

## 3️⃣ Proximity (20% Weight)

### What It Measures
How close the venue is to your current location.

### How It Works
- Uses **haversine distance** (straight-line distance between GPS coordinates)
- Closer = higher score
- Score calculation:
  ```
  proximity_score = max(0, 1.0 - (distance_km / (radius_km × 2)))
  ```

### Example
- **User location:** 40.7128, -74.0060 (NYC Center)
- **Venue location:** 0.5km away
- **Search radius:** 5km
- **Score:** ~90% (very close)

### Special Feature: Friend-Recommended Radius Boost
- Regular videos: Within radius (e.g., 5km)
- Friend-recommended videos: **1.5× larger radius** (e.g., 7.5km)
- Why? You're more willing to travel farther for a friend's recommendation

---

## 4️⃣ Trending (10% Weight)

### What It Measures
How fresh and timely the video content is.

### Freshness Scoring

| Video Age | Score | Why |
|-----------|-------|-----|
| 0-2 days | 100% | Brand new content |
| 3-7 days | 70% | Still very fresh |
| 8-14 days | 50% | Recent but not new |
| 15-30 days | 30% | Older content |
| 30+ days | 10% | Evergreen content |

### Example
- Video posted **yesterday** → 100% trending score
- Video posted **2 weeks ago** → 50% trending score

### Why It Matters
- Keeps feed fresh with new videos
- Surfaces timely content (e.g., "Live Jazz Tonight!")
- Balances evergreen content with new discoveries

---

## 🔄 The Complete Ranking Flow

### Step 1: Candidate Generation
1. **Vector search** finds top ~80 videos (limit × 4) matching user's taste
2. **Friend injection** adds 50 videos friends engaged with (even if taste doesn't match)
3. Result: ~130 candidate videos

### Step 2: Filtering
1. **Seen videos removed** - Don't show videos user already watched
2. **Proximity filter** - Remove videos outside radius (with friend boost)
3. Result: ~60-80 qualified candidates

### Step 3: Scoring
For each candidate:
1. Calculate taste match score (from vector similarity)
2. Query Neo4j for social proof data
3. Calculate proximity score
4. Calculate freshness score
5. Combine: `Final = 0.3×Taste + 0.4×Social + 0.2×Proximity + 0.1×Trending`

### Step 4: Deduplication
- **Problem:** Same venue might have multiple high-scoring videos
- **Solution:** Max 1 video per venue per feed batch
- **Priority:** Choose video with **highest social proof** from that venue
  - Example: If 3 videos from Blue Note qualify, pick the one friends engaged with most

### Step 5: Ranking & Delivery
1. Sort by final score (descending)
2. Take top N (e.g., 20 videos)
3. Return to user

---

## 🎬 Example: Complete Scoring

**Video:** "Live Jazz Tonight at 8pm!" - Blue Note SoHo

### Inputs:
- **User:** Sarah Chen (interests: jazz, wine, galleries)
- **Location:** 0.9km from Blue Note
- **Video age:** 2 days old
- **Friend activity:**
  - Nina Patel shared this video
  - 1 friend loves this venue
  - 1 mutual friend interested

### Calculations:

| Factor | Score | Weight | Contribution |
|--------|-------|--------|--------------|
| Taste Match | 85% | 30% | 0.255 (25.5%) |
| Friend Activity | 48% | 40% | 0.192 (19.2%) |
| Proximity | 95% | 20% | 0.190 (19.0%) |
| Trending | 100% | 10% | 0.100 (10.0%) |

**Final Match Score: 73.7%** ⭐

### Why This Score?
- ✅ Strong taste match (jazz + music)
- ✅ Great social proof (shared by Nina)
- ✅ Very close location (walking distance)
- ✅ Brand new content (posted 2 days ago)

---

## 🎯 Key Algorithm Features

### 1. Friend Injection System
**Problem:** Vector search only finds taste-matching videos. If your friend loved a sushi place but you've never shown interest in sushi, you'd never see it.

**Solution:** Inject videos friends engaged with, even if taste doesn't match. The high social proof weight (40%) ensures they rank well.

### 2. Seen Video Tracking
**Problem:** Users don't want to see the same video twice.

**Solution:** Track every video engagement in Neo4j. Filter out seen videos before ranking.

### 3. Venue Deduplication
**Problem:** Same venue might flood the feed with multiple videos.

**Solution:** Max 1 video per venue per batch. Prioritize video with most friend engagement.

### 4. Watch Time Quality Filter
**Problem:** Accidental clicks or quick swipes shouldn't count as "engagement."

**Solution:** Only count views ≥10 seconds. Saved/shared always count.

---

## 💻 Technical Implementation Details

### Weight Calculation Logic
How engagement weights are assigned in `app/main.py`:

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

### Social Proof Calculation Logic
How social scores are aggregated in `app/graph.py`:

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

**Implications:**
- ✅ Friend watched 15s → **Counts** (+5 pts to that venue for you)
- ❌ Friend watched 5s → **Ignored** (doesn't affect your feed)
- ✅ Friend saved → **Strong signal** (+8 pts)
- ✅ Friend shared → **Strongest signal** (+15 pts)

---

## 📈 Future Enhancements

### 🔥 High Priority

#### 1. Time-of-Day & Day-of-Week Personalization
**Current:** Static recommendations
**Enhancement:**
- Morning → Coffee shops, breakfast spots
- Lunch → Quick casual restaurants
- Evening → Bars, fine dining, live music venues
- Weekend → Brunch spots, galleries, experiences

**Implementation:**
- Add `preferred_times` to user profile
- Add `peak_hours` to venue metadata
- New factor: Time Match (5-10% weight)

#### 2. Real-Time Trending Events
**Current:** Freshness based on video age only
**Enhancement:**
- Track engagement velocity: views/hour, saves/hour
- "10 friends checked this out in the last hour"
- Surface viral content in your network

**Implementation:**
- Redis for real-time counters
- Trending score: `base_freshness + engagement_velocity`

#### 3. Group Recommendations
**Current:** Individual user recommendations
**Enhancement:**
- "Find a place for me and 3 friends"
- Aggregate taste profiles
- Show venues that satisfy everyone's interests

**Implementation:**
- New endpoint: `/feed-group?user_ids=[]`
- Aggregate vectors (average or weighted)
- Show "95% group match" scores

#### 4. Negative Feedback Learning
**Current:** Only track positive engagement
**Enhancement:**
- "Not interested" button
- Track skipped videos (<3s watch time)
- Downrank similar content

**Implementation:**
- Add `DISLIKED` relationship in Neo4j
- Negative embeddings in vector search
- Reduce taste match for similar categories

#### 5. Weather-Aware Recommendations
**Current:** No weather consideration
**Enhancement:**
- Rainy day → Indoor venues, cozy cafes
- Sunny day → Outdoor patios, rooftop bars
- Hot day → Ice cream, parks, water activities

**Implementation:**
- Integrate weather API (OpenWeatherMap)
- Add `venue_attributes` (indoor/outdoor, patio, etc.)
- Boost score by 10-20% for weather-appropriate venues

---

## 📚 Technical Architecture

### Components

**Neo4j Graph Database**
- Users, Videos, Venues
- Relationships: FRIENDS_WITH, WATCHED, POSTED
- Stores: Watch time, engagement type, timestamps

**Qdrant Vector Database**
- User embeddings (512-dim vectors)
- Video embeddings (512-dim vectors)
- Fast similarity search (<100ms)

**FastAPI Backend**
- `/feed-video` - Main recommendation endpoint
- `/engage-video` - Track user engagement
- `/user/{id}` - User profile & history

**React Frontend**
- Immersive swipeable feed
- Grid view with algorithm transparency
- Real-time engagement tracking

---

## 🎓 Key Learnings

### Why This Architecture Works

1. **Hybrid approach:** Vector search (taste) + Graph traversal (social) = Best of both worlds
2. **Explainability:** Every score is transparent - users see WHY they got a recommendation
3. **Friend-first:** 40% weight on social proof reflects real-world behavior
4. **Quality filters:** 10s watch time prevents noise in social proof
5. **Deduplication:** Keeps feed fresh, prevents venue flooding

### Common Pitfalls Avoided

❌ **Pure collaborative filtering** → Cold start problem for new users
✅ **Solution:** Hybrid with content-based (taste match)

❌ **Popularity bias** → Only show viral content
✅ **Solution:** Personalized taste match + friend social proof

❌ **Filter bubble** → Only recommend similar content
✅ **Solution:** Friend injection brings diversity

❌ **Stale content** → Same recommendations every day
✅ **Solution:** Seen video tracking + trending boost

---

## 📞 Questions?

For technical questions or enhancement proposals, see:
- `README.md` - Setup & installation
- `app/main.py` - API endpoints
- `app/graph.py` - Social proof calculations
- `seeder_enhanced.py` - Data model & test data

---

**Last Updated:** November 2025
**Version:** 1.1
**Authors:** GeoSocial Team
