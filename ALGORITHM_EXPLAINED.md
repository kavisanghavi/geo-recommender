# GeoSocial Recommendation Algorithm - Explained Simply

## 🎯 Overview

GeoSocial uses a **multi-factor ranking algorithm** to recommend local business videos to users based on their interests, friend activity, location, and content freshness. Think of it as "TikTok meets Yelp meets your friend group's recommendations."

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
| Per friend | +2 | Friend is interested in this venue |
| Cap | +10 max | Prevents over-weighting |

**Example:**
- "3 friends love this place" = +6 points
  - Meaning: 3 friends watched different videos from Blue Note SoHo
  - Shows venue popularity in your social circle

#### C) Mutual Friends (2nd Degree)
Friends-of-friends who engaged:

| Metric | Points | What It Means |
|--------|--------|---------------|
| Per mutual | +2 | Weak signal but indicates broader interest |

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

### 🚀 Medium Priority

#### 6. Mood-Based Recommendations
**Enhancement:**
- User selects mood: "Adventurous", "Romantic", "Casual hangout"
- Adjust weights dynamically:
  - Adventurous: Lower taste match, higher trending
  - Romantic: Higher proximity, specific venue types
  - Casual: Higher social proof from close friends

**Implementation:**
- Add `mood_profiles` config
- Dynamic weight adjustment per request

#### 7. Dietary Restrictions & Preferences
**Enhancement:**
- User profile: vegetarian, vegan, gluten-free, halal, kosher
- Automatically filter/boost relevant venues
- "Vegetarian-friendly" badge

**Implementation:**
- Add `dietary_tags` to venues
- Filter in candidate generation
- Boost taste match for compatible venues

#### 8. Budget-Aware Filtering
**Enhancement:**
- User sets budget: $, $$, $$$, $$$$
- Filter venues by price tier
- "Great deals" boost for discounts/happy hours

**Implementation:**
- Already have `price_tier` metadata
- Add budget filter in Step 2
- Track "special_offers" in video metadata

#### 9. Friend Group Clustering
**Enhancement:**
- Identify friend groups: "Work friends", "College buddies", "Family"
- Weight social proof higher from certain groups
- "Your work friends love this place"

**Implementation:**
- Community detection in Neo4j (Louvain algorithm)
- Add `group_id` to FRIENDS_WITH relationship
- Weight social proof by group relevance

#### 10. Collaborative Filtering
**Enhancement:**
- "Users similar to you loved this place"
- Find taste-twins in the network
- Expand recommendations beyond direct friends

**Implementation:**
- User-user similarity matrix (cosine similarity)
- k-NN to find similar users
- New contributor type: "Similar users"

---

### 💡 Experimental Ideas

#### 11. Repeat Visit Patterns
**Enhancement:**
- Track if user returns to same venue multiple times
- Boost similar venues: "Since you love Blue Note, try Village Vanguard"
- "You've been here 3 times - you love this place!"

**Implementation:**
- Count visit frequency per venue
- Content-based filtering for similar venues
- Add "Favorites" badge

#### 12. Social Influence Scoring
**Enhancement:**
- Some friends are "tastemakers" - their recommendations carry more weight
- Track recommendation success rate
- "Nina's recommendations are 85% match for you"

**Implementation:**
- Calculate per-friend match rate
- Weight social proof by friend's influence score
- Show "Top recommender" badges

#### 13. Occasion-Based Recommendations
**Enhancement:**
- User specifies: "Date night", "Business lunch", "Birthday party"
- Filter by occasion appropriateness
- "Great for dates" badges

**Implementation:**
- Add `occasions` tags to venues
- Filter/boost based on user's selected occasion
- ML model to predict occasion suitability

#### 14. Serendipity Injection
**Enhancement:**
- 10% of feed = random discoveries
- "Try something completely different"
- Helps users escape filter bubbles

**Implementation:**
- Replace 2-3 videos with random samples
- Mark as "Discovery picks"
- Track engagement to improve over time

#### 15. Chain/Franchise Deduplication
**Enhancement:**
- User saw Starbucks in Manhattan, don't show another Starbucks
- Prioritize local/independent businesses
- "You've seen this chain recently"

**Implementation:**
- Add `chain_id` to venue metadata
- Deduplicate across chain locations
- Boost local/independent in ranking

---

## 🔧 Data Tracking for Future Features

### Currently Tracked
✅ Video views (with watch time)
✅ Saves, shares, skips
✅ User interests
✅ Friend relationships
✅ Video metadata (title, description, categories)
✅ Venue location
✅ Timestamps

### Should Start Tracking

#### User Behavior
- [ ] Time of engagement (hour of day, day of week)
- [ ] Device type (mobile, desktop)
- [ ] Session length
- [ ] Bounce rate (quick exits)
- [ ] Scroll depth (how far in feed)
- [ ] Negative feedback ("Not interested" clicks)
- [ ] Search queries
- [ ] Filter usage

#### Venue Data
- [ ] Operating hours
- [ ] Current wait time / crowdedness
- [ ] Price range (specific $$ amounts, not just tier)
- [ ] Dietary options (vegan, GF, etc.)
- [ ] Ambiance (quiet, lively, romantic)
- [ ] Parking availability
- [ ] Reservation requirements
- [ ] Special events calendar
- [ ] Weather suitability (indoor/outdoor)

#### Social Graph
- [ ] Friend interaction frequency (who do you engage with most?)
- [ ] Friend group clusters
- [ ] Recommendation success rate per friend
- [ ] Mutual venue visits (co-location data)

#### Video Performance
- [ ] Engagement velocity (views per hour)
- [ ] Completion rate (% who watched to end)
- [ ] Peak viewing times
- [ ] Geographic concentration (where is video popular?)

#### Business Outcomes
- [ ] Click-to-visit conversion
- [ ] Booking completions
- [ ] Revenue per recommendation
- [ ] Return visits after recommendation

---

## 🧪 A/B Testing Opportunities

### Weight Tuning
Test different weight combinations:
- Current: 30/40/20/10
- Social-heavy: 20/50/20/10
- Discovery-focused: 40/30/15/15

### Deduplication Strategies
- Max 1 video per venue (current)
- Max 2 videos per venue
- No deduplication (let high-scoring venues dominate)

### Friend Injection Volume
- Current: Top 50 friend videos
- Test: Top 20 (more selective)
- Test: Top 100 (more inclusive)

### Watch Time Threshold
- Current: ≥10s counts as engagement
- Test: ≥15s (higher quality bar)
- Test: ≥5s (more inclusive)

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
- TikTok-style swipeable feed
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
- `seeder_video.py` - Data model & test data

---

**Last Updated:** November 2025
**Version:** 1.0
**Authors:** GeoSocial Team
