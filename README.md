# GeoSocial Recommendation Engine

A social-first recommendation engine that combines vector similarity search with social graph analysis to provide personalized venue recommendations based on both user preferences and friend activity.

## Overview

This MVP demonstrates a recommendation system that answers: **"Where should I go based on what my friends are doing and what I like?"**

The system uses:
- **Vector Search** (Qdrant) for semantic similarity matching
- **Social Graph** (Neo4j) for friend connections and social proof
- **Async Processing** (Celery + Redis) for scalable interaction logging
- **Agentic Booking** (LangGraph) for intelligent reservation handling

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 18+ (for frontend)
- OpenAI API Key (for agentic features)

### 1. Environment Setup
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 2. Start Backend Services
```bash
docker-compose up --build -d
```

### 3. Seed Data
```bash
# Seed 150 venues in NYC
docker-compose exec -e NEO4J_URI=bolt://neo4j:7687 -e QDRANT_HOST=qdrant api python seeder.py --venues

# Or seed everything (venues + 200 users with social connections)
docker-compose exec -e NEO4J_URI=bolt://neo4j:7687 -e QDRANT_HOST=qdrant api python seeder.py --all
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173)

## Architecture

### Backend (FastAPI)
- **`/feed`** - Get personalized recommendations
- **`/ingest/interaction`** - Log user interactions (viewed, saved, going)
- **`/social/connect`** - Create friend connections
- **`/agent/action`** - Agentic booking workflow

### Data Stores
- **Qdrant** (port 6333) - Vector embeddings for venues
- **Neo4j** (port 7474) - Social graph (users, friendships, interactions)
- **Redis** (port 6379) - Task queue for Celery

### Frontend (React + Vite)
- **Feed** - Smart recommendations with social proof badges
- **Create User** - 3-step wizard (Identity → Circle → Taste)
- **Profiles** - User dashboard (friends, interests, places)

## Key Features

### Social-First Ranking
Recommendations are ranked by:
```
Final Score = (Vector Similarity × 0.7) + (Social Proof × 0.3)
```

Social proof includes:
- Friends who are "going" (+10 points)
- Friends who "saved" it (+5 points)
- Mutual friends interested (+2 points each)

### Simulation Mode
Create test users and simulate social interactions to see how the recommendation engine adapts in real-time.

## Development

### Reset Data
```bash
# Clear users but keep venues
docker-compose exec -e NEO4J_URI=bolt://neo4j:7687 -e QDRANT_HOST=qdrant api python seeder.py --venues --clear-users

# Full reset
docker-compose exec -e NEO4J_URI=bolt://neo4j:7687 -e QDRANT_HOST=qdrant api python seeder.py --all
```

### View Logs
```bash
docker-compose logs -f api
docker-compose logs -f worker
```

### Access Databases
- **Neo4j Browser**: http://localhost:7474 (user: `neo4j`, password: `password`)
- **Qdrant Dashboard**: http://localhost:6333/dashboard

## Project Structure

```
├── app/
│   ├── main.py          # FastAPI endpoints
│   ├── graph.py         # Neo4j social graph logic
│   ├── vector.py        # Qdrant vector search
│   ├── agent.py         # LangGraph booking agent
│   └── worker.py        # Celery async tasks
├── frontend/
│   └── src/
│       ├── pages/       # Feed, CreateUser, UserProfile
│       └── components/  # Reusable UI components
├── seeder.py            # Data generation script
├── docker-compose.yml   # Service orchestration
└── requirements.txt     # Python dependencies
```

## Documentation

- [GOALS.md](./GOALS.md) - High-level objectives and use cases
- [ARCHITECTURE.md](./ARCHITECTURE.md) - Detailed backend architecture
- [walkthrough.md](./.gemini/antigravity/brain/4b8b97d7-dd71-4540-9b6c-79f549fd2a25/walkthrough.md) - Implementation walkthrough

## License

MIT
