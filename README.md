# GeoSocial - Video Discovery for Local Businesses

> **Immersive local discovery powered by AI and social proof**

A video-first recommendation engine that combines **vector similarity search**, **social graph analysis**, and **location-based filtering** to help users discover local businesses through short-form video content shared by their friends.

![Python](https://img.shields.io/badge/python-3.11-blue.svg)
![React](https://img.shields.io/badge/react-18.3-blue.svg)

---

## 🎯 What is GeoSocial?

GeoSocial is a local business discovery platform that works like popular short-video apps, but for finding restaurants, cafes, bars, and entertainment venues near you. Businesses create short videos showcasing their offerings, and you discover them through a personalized feed driven by:

- **Your interests** (taste-based matching using AI embeddings)
- **Your friends' activity** (what they've saved, shared, and watched)
- **Your location** (proximity-based filtering)
- **Content freshness** (recent videos get boosted)

### Key Differentiators:
- **Algorithm Transparency**: See exactly why each video was recommended
- **Social Proof First**: Friend recommendations carry 40% weight (highest factor)
- **Quality Engagement**: Only views ≥10 seconds count toward social proof
- **Real-time Learning**: Every interaction refines your feed instantly

---

## ✨ Features

### 🎬 User Experience
- **Immersive Feed**: Vertical swipe interface with full-screen videos
- **Grid View**: Browse multiple recommendations at once
- **Algorithm Breakdown**: Transparent scoring shows Taste Match, Friend Activity, Proximity, and Trending
- **Save & Share**: Bookmark videos and share with friends
- **Booking Agent** (POC): AI-powered "Want to Go" button that extracts intent and creates booking proposals
- **User Profiles**: View saved places, watch history, friends, and interests

### 👥 Social Features
- **Friend Network**: Connect with friends to see their recommendations
- **Activity Tracking**: See when friends save, share, or watch videos
- **Mutual Friends**: Discover venues popular in your extended network
- **Venue-Level Social Proof**: "3 friends love this place" indicators

### 🏢 Business Features
- **Business Directory**: Browse all registered businesses
- **Video Analytics**: Track views, saves, shares, and quality views per video
- **Engagement Metrics**: See how users interact with content

### 🛠️ Developer Features
- **Create User Flow**: Onboard new users with interests and friend selection
- **Debug Tools**: Reset data, clear activity, inspect algorithm weights
- **Simulation Mode**: Test recommendation engine with various scenarios

---

## 🏗️ Architecture

### Technology Stack

**Backend:**
- **FastAPI** (Python 3.11) - API server with async support
- **Neo4j** (Graph Database) - Social connections, videos, venues, user engagement
- **Qdrant** (Vector Database) - Video/venue embeddings for semantic search
- **Redis** - Task queue for async operations
- **Celery** - Background worker for engagement logging

**Frontend:**
- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **TailwindCSS** - Styling
- **Axios** - HTTP client
- **React Router** - Navigation
- **Lucide React** - Icons

**Infrastructure:**
- **Docker Compose** - Containerized deployment
- **Uvicorn** - ASGI server

### Data Model

**Neo4j Graph:**
```
(User)-[:FRIENDS_WITH]-(User)
(User)-[:WATCHED {action, watch_time, timestamp}]->(Video)
(Venue)-[:POSTED]->(Video)
```

**Qdrant Collections:**
- `videos`: Video embeddings (512-dim vectors)
- `venues`: Venue embeddings (512-dim vectors)

### Recommendation Algorithm

The feed ranking uses a weighted multi-factor score:

```
Final Score = (0.3 × Taste Match) + (0.4 × Friend Activity) + (0.2 × Proximity) + (0.1 × Trending)
```

**1. Taste Match (30%)**: Vector similarity between user interests and video content
**2. Friend Activity (40%)**: Social proof from friend engagement (highest weight!)
**3. Proximity (20%)**: Distance from user's current location
**4. Trending (10%)**: Content freshness and recency

See [ALGORITHM_EXPLAINED.md](docs/ALGORITHM_EXPLAINED.md) for detailed breakdown.

---

## 🚀 Getting Started

### Prerequisites

- **Docker Desktop** (for Mac/Windows) or **Docker + Docker Compose** (for Linux)
- **Node.js 18+** and npm
- **(Optional) OpenAI API Key** - For production-quality embeddings

### 1. Clone the Repository

```bash
git clone <repository-url>
cd geo-recommender
```

### 2. Environment Setup

```bash
# Create environment file (optional - only needed for real embeddings)
cp .env.example .env

# Add your OpenAI API key if you have one
echo "OPENAI_API_KEY=sk-..." >> .env
```

> **Note**: The app works without an OpenAI key using mock embeddings, but real embeddings provide better taste matching.

### 3. Start Backend Services

```bash
# Build and start all services (Neo4j, Qdrant, Redis, API, Worker)
docker-compose up --build -d

# Verify all containers are running
docker ps
```

You should see 5 containers running:
- `geo-recommender-api-1` (FastAPI)
- `geo-recommender-worker-1` (Celery)
- `geo-recommender-neo4j-1` (Neo4j)
- `geo-recommender-qdrant-1` (Qdrant)
- `geo-recommender-redis-1` (Redis)

### 4. Seed Demo Data

Generate realistic NYC businesses, videos, and user interactions:

```bash
# Seed with 150 venues, ~500 videos, 15 users
docker-compose exec api python seeder_video.py
```

This creates:
- **150 NYC venues** across 10 neighborhoods (SoHo, Williamsburg, DUMBO, etc.)
- **3-5 videos per venue** (promotional content, events, specials)
- **15 users** with distinct personas and interests
- **Social graph** with realistic friendships
- **Engagement data** (views, saves, shares)

### 5. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:5173** in your browser!

### 6. Access Services

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Neo4j Browser**: http://localhost:7474 (user: `neo4j`, password: `password`)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

---

## 📖 Usage Guide

### Exploring the Feed

1. **Select a User**: Choose from the dropdown (e.g., "Sarah Chen", "David Park")
2. **View Mode**: Toggle between Immersive (vertical) and Grid view
3. **Swipe/Scroll**: Navigate through recommended videos
4. **Interact**: Save, Share, or Watch videos
5. **Algorithm Breakdown**: Expand to see why each video was recommended

### User Profiles

1. Navigate to **Profiles** in the sidebar
2. Select a user from the dropdown
3. View:
   - **Friends**: Social connections
   - **Interests**: User preferences
   - **My Places**: Saved venues
   - **Recent Activity**: Watch history with save/share actions

### Business Directory

1. Navigate to **Businesses** in the sidebar
2. Browse all registered venues
3. Click a business to see:
   - All videos posted by that venue
   - Engagement stats (views, saves, shares, quality views)
   - Venue details (category, neighborhood, price tier)

### Creating Test Users

1. Navigate to **Create User**
2. **Step 1 - Identity**: Enter name (optional) and select interests
3. **Step 2 - Circle**: Add friends from existing users
4. **Step 3 - Taste**: Interact with videos to build taste profile
5. View the new user's personalized feed!

---

## 🧪 Development

### Project Structure

```
geo-recommender/
├── app/                    # Backend application
│   ├── main.py            # FastAPI routes and endpoints
│   ├── graph.py           # Neo4j operations and social proof
│   ├── vector.py          # Qdrant operations and embeddings
│   ├── worker.py          # Celery tasks for async operations
│   └── agent.py           # LangGraph booking agent (experimental)
├── frontend/              # React frontend
│   ├── src/
│   │   ├── pages/         # Feed, Profiles, Businesses, CreateUser
│   │   ├── components/    # ShortVideoFeed, MapView, etc.
│   │   ├── Layout.jsx     # Navigation sidebar
│   │   └── App.jsx        # Routes and app shell
│   └── vite.config.js
├── docs/                  # Documentation
│   ├── ALGORITHM_EXPLAINED.md
│   ├── ARCHITECTURE.md
│   ├── BOOKING_AGENT.md   # Booking agent POC documentation
│   ├── DEMO_GUIDE.md
│   ├── TESTING_GUIDE.md
│   └── GOALS.md
├── seeder_video.py        # Current seeder (video-centric)
├── docker-compose.yml     # Service orchestration
├── Dockerfile             # Backend container
├── requirements.txt       # Python dependencies
└── README.md              # This file
```

### Key API Endpoints

**Video Feed:**
- `GET /feed-video?user_id={id}&lat={lat}&lon={lon}&radius_km={r}&limit={n}` - Personalized video feed
- `POST /engage-video` - Log video engagement (view, save, share, skip)

**Booking Agent (Experimental):**
- `POST /agent/book` - Initiate AI-powered booking workflow
- `POST /agent/confirm-booking` - Confirm booking and store in Neo4j

**Users:**
- `GET /user/{user_id}` - User profile with watch history
- `POST /debug/user` - Create new user
- `POST /social/connect` - Add friendship

**Businesses:**
- `GET /businesses` - All venues with videos and engagement stats
- `GET /venues-with-videos?limit={n}` - Venues with sample videos (for onboarding)

**Debug:**
- `POST /debug/reset` - Clear all data
- `POST /debug/clear-activity` - Clear user activity

See full API documentation at http://localhost:8000/docs

### Running Tests

```bash
# Backend tests (if implemented)
docker-compose exec api pytest

# Frontend tests
cd frontend
npm test
```

### Viewing Logs

```bash
# API logs
docker-compose logs -f api

# Worker logs (async tasks)
docker-compose logs -f worker

# All services
docker-compose logs -f
```

### Database Queries

**Neo4j Cypher Examples:**

```cypher
// View all users and their friends
MATCH (u:User)-[:FRIENDS_WITH]-(f:User)
RETURN u.name, collect(f.name) as friends

// Videos with most saves
MATCH (u:User)-[r:WATCHED]->(v:Video)
WHERE r.action = 'saved'
RETURN v.title, v.venue_name, count(u) as saves
ORDER BY saves DESC
LIMIT 10

// User's watch history
MATCH (u:User {id: 'user_8f016497'})-[r:WATCHED]->(v:Video)
RETURN v.title, r.action, r.watch_time, r.timestamp
ORDER BY r.timestamp DESC
```

**Qdrant API Examples:**

```bash
# Search for videos similar to a query
curl http://localhost:6333/collections/videos/points/search \
  -H "Content-Type: application/json" \
  -d '{
    "vector": [0.1, 0.2, ...],  # 512-dim vector
    "limit": 10
  }'
```

---

## 🤖 AI & Coding Agents Used

This project was developed with assistance from **Claude Code** (Anthropic's AI coding agent):

### Development Tasks:
- **Architecture Design**: Multi-database hybrid system design
- **Algorithm Implementation**: Social proof calculations, vector search integration
- **Frontend Development**: React components, immersive feed, responsive design
- **Bug Fixing**: Save/share persistence, duplicate venue cleanup, UI state management
- **Documentation**: Comprehensive algorithm explanations, setup guides, architecture docs
- **Data Seeding**: Realistic NYC venues, user personas, social graph generation

### Third-Party Resources:
- **Faker** - Generating realistic user names and data
- **OpenAI Embeddings API** - Semantic vector generation (optional)
- **Lucide Icons** - UI iconography
- **TailwindCSS** - Utility-first styling

---

## 📐 Design Decisions

### Why Video-Centric?
Originally venue-focused, pivoted to videos because:
- **Engagement**: Short-form video is proven to drive discovery (Short Video, Reels)
- **Content Variety**: One venue can have multiple videos (events, specials, tours)
- **Social Proof**: More granular tracking (which specific video did friends like?)
- **Algorithm Flexibility**: Easier to rank diverse content than static venues

### Why 40% Weight on Social Proof?
Friend recommendations are the **most trusted signal** in local discovery. Data shows users are 3x more likely to visit a place recommended by a friend vs. algorithm alone.

### Why Neo4j + Qdrant?
- **Neo4j**: Natural fit for social graphs, relationships, and traversals
- **Qdrant**: Fast vector similarity search for taste matching
- **Hybrid**: Combines semantic understanding (AI) with social context (graph)

### Why Separate WATCHED Relationships for Save/Share?
Initially used MERGE which overwrote actions. Changed to CREATE for save/share to preserve multiple engagement types per user-video pair (one for "saved", one for "viewed").

---

## 🗺️ Roadmap

See [GOALS.md](docs/GOALS.md) for detailed roadmap.

**High Priority:**
- [ ] Time-of-day personalization (morning → coffee, evening → bars)
- [ ] Real-time trending (engagement velocity tracking)
- [ ] Group recommendations (find a place for you + friends)
- [ ] Negative feedback (downrank content you don't like)
- [ ] Weather-aware suggestions (rainy → indoor venues)
- [ ] **Booking Agent**: Real API integrations (OpenTable, Resy) - see [BOOKING_AGENT.md](docs/BOOKING_AGENT.md)

**Medium Priority:**
- [ ] Mood-based recommendations (adventurous, romantic, casual)
- [ ] Dietary filters (vegetarian, vegan, gluten-free)
- [ ] Budget-aware filtering ($, $$, $$$, $$$$)
- [ ] Friend group clustering (work friends vs. college friends)
- [ ] Collaborative filtering (users similar to you)

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

No License / All Rights Reserved
---
