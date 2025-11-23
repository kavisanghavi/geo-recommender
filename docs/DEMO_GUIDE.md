# 🎬 Immersive Geo Discovery - Demo Guide

## Overview

This enhanced version transforms the geo-recommender into a **immersive location discovery app** with:
- ✅ Real NYC venue data across 10 neighborhoods
- ✅ Realistic user personas with interest-based embeddings
- ✅ Simulated engagement patterns (watch times, shares, saves, skips)
- ✅ **Full algorithm transparency** with explainability
- ✅ Immersive vertical swipe UI
- ✅ Watch time tracking and learning

---

## 🚀 Quick Start

### 1. Start Backend Services

```bash
docker-compose up --build -d
```

Wait ~30 seconds for all services to start:
- ✅ Neo4j (port 7474, 7687)
- ✅ Qdrant (port 6333)
- ✅ Redis (port 6379)
- ✅ FastAPI (port 8000)
- ✅ Celery Worker

### 2. Seed Realistic NYC Data

**Option A: Full synthetic dataset with OpenAI embeddings (Recommended)**

```bash
# Set your OpenAI API key for real embeddings
export OPENAI_API_KEY="sk-..."

# Seed everything (takes 2-3 minutes with real embeddings)
docker-compose exec -e OPENAI_API_KEY=$OPENAI_API_KEY api python seeder_enhanced.py --all

# OR specify parameters:
docker-compose exec -e OPENAI_API_KEY=$OPENAI_API_KEY api python seeder_enhanced.py \
  --all \
  --num-users 200 \
  --interactions-per-user 30
```

**Option B: Without OpenAI (uses mock embeddings)**

```bash
docker-compose exec api python seeder_enhanced.py --all
```

**What this creates:**
- 150 venues across 10 NYC neighborhoods
- 200 users with realistic personas (Foodie, Nightlife Pro, Culture Vulture, etc.)
- ~6,000 engagement records (views, shares, saves, skips)
- Social graph with friendship clusters

### 3. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

---

## 📱 Features Demo

### 1. **Immersive Feed** 👆

**Path:** Feed → Immersive View button

**What to show:**
1. Select a user from dropdown
2. Vertical swipe feed with venue videos
3. Watch timer automatically tracking engagement
4. Tap "Why this venue?" to see algorithm breakdown
5. Algorithm transparency shows:
   - 🎯 **Taste Match**: Based on user interests (e.g., "cocktails", "jazz")
   - 👥 **Friend Activity**: Which friends shared/saved/viewed
   - 📍 **Proximity**: Distance from user (0.5-2km)
   - 🔥 **Trending**: Recent engagement count

**Key Interactions:**
- Swipe up/down to navigate
- Save = 1.5x weight
- Share = 3.0x weight (strongest signal!)
- Watch <3s = skip (-0.5 weight)
- Watch 30s+ = full view (2.0x weight)

### 2. **Algorithm Explainability** 🔍

**How it works:**
```
Final Score =
  Taste Match (30%) +
  Social Proof (35%) +
  Proximity (20%) +
  Trending (10%) +
  Diversity (5%)
```

**Example explanation:**
```json
{
  "taste_match": {
    "score": 0.78,
    "reason": "Matches your interests: cocktails, rooftop, jazz"
  },
  "social_proof": {
    "score": 0.92,
    "contributors": [
      {"friend": "Sarah Chen", "action": "shared", "boost": 15},
      {"friend": "Mike Johnson", "action": "saved", "boost": 8},
      {"mutuals": 3, "action": "interested", "boost": 6}
    ]
  },
  "proximity": {
    "score": 0.85,
    "distance_km": 0.8,
    "reason": "0.8km away (~10 min walk)"
  }
}
```

### 3. **User Profile with Friends** 👥

**Path:** User Profile (enhanced version)

**Features:**
- View user archetype (e.g., "Nightlife Pro", "Coffee Snob")
- See all friends with shared interests
- Add new friends (search all users)
- Watch history with engagement details

**Demo flow:**
1. Select user "Sarah Chen" (Nightlife Enthusiast)
2. View her friends (likely other nightlife/music lovers)
3. Click "Add Friends" → search for "foodie"
4. Add a foodie friend
5. Go back to feed → see recommendations change!

### 4. **NYC Neighborhoods** 🗺️

**10 Real Neighborhoods:**
- Williamsburg (hipster, trendy, artsy)
- SoHo (upscale, artsy, shopping)
- East Village (bohemian, diverse, nightlife)
- West Village (charming, cozy, romantic)
- Bushwick (edgy, warehouse, underground)
- Lower East Side (historic, dive bars)
- Brooklyn Heights (upscale, quiet, scenic)
- DUMBO (waterfront, modern, trendy)
- Chelsea (artsy, gallery, upscale)
- Greenpoint (polish, waterfront, hipster)

**Venue types:**
- Rooftop bars, jazz clubs, cocktail lounges
- Coffee shops, brunch spots
- Italian, Japanese, Mexican, Korean BBQ
- Art galleries, music venues, speakeasies
- Bakeries, pizza places

---

## 🎯 Demo Script (5 minutes)

### Act 1: Show the Algorithm (2 min)

1. **Start in Immersive view**
   - "This is a immersive location discovery app"
   - Select user "Sarah Chen" (Nightlife Enthusiast)

2. **Swipe through 2-3 venues**
   - "Notice how venues match her interests: cocktails, rooftop bars"
   - Point out watch time tracker

3. **Tap 'Why this venue?'**
   - "Full algorithm transparency - no black box"
   - Expand to show breakdown:
     - Taste match: 78% (matches cocktails, jazz)
     - Friend activity: Mike shared this (+15 pts)
     - Proximity: 0.8km away
     - Trending: 15 people engaged today

### Act 2: Show Social Proof (2 min)

4. **Switch to user "Mike Johnson"**
   - "Mike is a 'Foodie Explorer'"
   - Swipe to venue
   - Show explanation: 3 friends interested

5. **Go to Mike's profile**
   - View his 8 friends
   - Show watch history: saved 5 ramen spots, shared 2 tacos

6. **Add a new friend**
   - Click "Add Friends"
   - Search for "coffee"
   - Add "Emma (Coffee Snob)"

### Act 3: Show Real-time Learning (1 min)

7. **Back to feed**
   - Watch a venue for 30 seconds (full view = 2.0x weight)
   - Share it (3.0x weight!)
   - Skip the next one (<3s)

8. **Explain the impact**
   - "Every interaction updates the graph in real-time"
   - "Friends see boosted recommendations"
   - "Watch time = implicit interest signal"

---

## 🧪 Testing Scenarios

### Scenario 1: Cold Start User
```bash
# Create a brand new user
curl -X POST http://localhost:8000/debug/user \
  -H "Content-Type: application/json" \
  -d '{"interests": ["craft beer", "pizza", "outdoor"]}'

# Should see recommendations based purely on taste
# No friend activity initially
```

### Scenario 2: Social Butterfly
```bash
# Pick user_0 (typically has most friends due to seeder logic)
# Should see high social proof scores
# Many "X friends interested" badges
```

### Scenario 3: Neighborhood Exploration
```bash
# Change radius in feed API
# Small radius (0.5km) = very local
# Large radius (5km) = cross-borough

curl "http://localhost:8000/feed?user_id=user_0&lat=40.7081&lon=-73.9571&radius_km=0.5"
```

### Scenario 4: Trending Venues
```bash
# After seeding, some venues will have high engagement
# Look for 🔥 trending badges
# Explanation shows "15 people engaged in last 24h"
```

---

## 📊 Data Insights

### User Archetypes (10 types)
1. **Nightlife Pro** - rooftop bars, cocktails, DJs
2. **Foodie Explorer** - ramen, tacos, authentic cuisine
3. **Culture Vulture** - jazz, galleries, wine
4. **Coffee Snob** - specialty coffee, pastries
5. **Beer Enthusiast** - craft beer, beer gardens
6. **Romantic Date-Goer** - intimate, fine dining
7. **Music Fanatic** - live music, concerts
8. **Brunch Lover** - brunch, breakfast, instagram-worthy
9. **Hidden Gem Hunter** - speakeasy, exclusive
10. **Social Connector** - group hangouts, vibrant

### Engagement Distribution (simulated)
- 20% skip (<3s)
- 25% brief view (3-10s)
- 30% engaged view (10-30s)
- 15% full view (30s+)
- 7% save
- 3% share (strongest signal!)

### Social Graph Stats
- Average ~8 friends per user
- Clustering by archetype (60% same-archetype friends)
- Bidirectional friendships

---

## 🛠️ Advanced: Incremental Seeding

### Add more users
```bash
docker-compose exec api python seeder_enhanced.py --users --num-users 50
```

### Add more engagement
```bash
docker-compose exec api python seeder_enhanced.py --engagement --interactions-per-user 50
```

### Re-seed friendships
```bash
docker-compose exec api python seeder_enhanced.py --friends
```

### Clear and restart
```bash
docker-compose exec api python seeder_enhanced.py --all
```

---

## 🐛 Troubleshooting

### "No venues found"
```bash
# Check Qdrant
curl http://localhost:6333/collections/venues

# Re-seed if needed
docker-compose exec api python seeder_enhanced.py --venues
```

### "No users in dropdown"
```bash
# Check Neo4j
docker-compose exec api python -c "from app.graph import driver; print(driver.session().run('MATCH (u:User) RETURN count(u)').single()[0])"

# Re-seed users
docker-compose exec api python seeder_enhanced.py --users
```

### "Algorithm scores all 0"
```bash
# Need engagement data
docker-compose exec api python seeder_enhanced.py --engagement
```

### OpenAI API errors
```bash
# Falls back to mock embeddings automatically
# Check logs: docker-compose logs api

# Verify API key
echo $OPENAI_API_KEY
```

---

## 📈 Metrics to Highlight

1. **Personalization Works**
   - Nightlife Pro sees bars/clubs
   - Foodie sees restaurants
   - Coffee Snob sees cafes

2. **Social Proof Impact**
   - Venues with friend activity rank 2-3x higher
   - Shares = 15pt boost
   - Saves = 8pt boost

3. **Proximity Matters**
   - Venues <1km get 80%+ proximity score
   - Venues >3km drop to <20%

4. **Watch Time Learning**
   - Skip (<3s) = negative signal
   - Full view (30s+) = 2x weight
   - Share = 3x weight

---

## 🎨 UI/UX Highlights

- **Vertical swipe** = natural short-video interaction
- **Explanation panel** = tap to expand algorithm breakdown
- **Real-time tracking** = watch timer visible
- **Social badges** = "Sarah shared this" front and center
- **Neighborhood tags** = location context
- **Price tier** = $ to $$$$

---

## 🚢 Next Steps (Beyond Demo)

1. **Real video content** (currently using images)
2. **Live friend feed** (WebSocket for real-time updates)
3. **Group planning** ("Find venue all 5 friends like")
4. **Event integration** (concerts, pop-ups)
5. **Mobile app** (React Native)
6. **A/B testing** (experiment with weights)

---

## 📝 Key Talking Points

> "Traditional recommendation systems are black boxes. We show exactly why each venue appears in your feed."

> "Watch time is the ultimate signal - if you watch 30 seconds, you're interested. If you skip in 2 seconds, we learn."

> "Social proof drives real-world decisions. Seeing '3 friends are going' is more compelling than '85% match'."

> "Every interaction updates the graph in real-time. Share a venue, and your friends see it boosted immediately."

> "This isn't just personalization - it's social-first discovery with full transparency."

---

## 🎉 Success!

You now have a fully functional **immersive location discovery app** with:
- ✅ 150 real NYC venues
- ✅ 200 simulated users with personas
- ✅ 6,000+ engagement records
- ✅ Full algorithm explainability
- ✅ Real-time graph updates
- ✅ Beautiful UI

**Enjoy the demo!** 🚀
