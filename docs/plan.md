MVP Implementation Plan: Local Social Recommendation Engine

1. System Architecture

This architecture runs entirely on your local machine using Docker. It separates the "Thinking" (API/Agents) from the "Memory" (Graph/Vector DBs).

graph TD
    Client[Frontend / Mobile] -->|HTTP POST / Interactions| API[FastAPI Backend]
    Client -->|HTTP GET / Feed| API

    subgraph "Local Docker Network"
        API -->|Async Task| Redis[Redis Queue]
        Redis -->|Process| Worker[Celery Worker]
        
        Worker -->|Update Profile| Neo4j[(Neo4j Graph DB)]
        Worker -->|Update Embeddings| Qdrant[(Qdrant Vector DB)]
        
        API -->|Query Social| Neo4j
        API -->|Query Vibe| Qdrant
        
        API -->|Trigger| Agent[LangGraph Agent]
    end
    
    Agent -->|Tool Call| BookingAPI[Mock Booking System]


2. Data Strategy: The "Social-Spatial" Model

We need to bridge the gap between "What I like" and "Who I know".

The Graph Model (Social)

We prioritize Implicit Signals (Time Spent) and Explicit Signals (Saved/Going).

graph LR
    U1((User: You)) -- "FRIENDS_WITH" --> U2((User: Sarah))
    U2 -- "FRIENDS_WITH" --> U3((User: Mike))
    
    U1 -- "VIEWED {time: 45s}" --> V1[Venue: The Archer]
    U2 -- "SAVED" --> V1
    U3 -- "GOING" --> V1
    
    style V1 fill:#f9f,stroke:#333,stroke-width:4px


Recommendation Logic: Even if you haven't explicitly liked "The Archer," the fact that your friend Sarah saved it and her friend Mike is going makes it a high-priority recommendation for you.

3. Step-by-Step Build Phases

Phase 1: Infrastructure Scaffold (Day 1)

Goal: Get all databases talking to each other locally.

Create docker-compose.yml with:

fastapi-app (Build context: ./backend)

neo4j (Ports: 7474, 7687)

qdrant (Ports: 6333)

redis (Ports: 6379)

Verify connection:

Access Neo4j Browser at http://localhost:7474.

Access Qdrant Dashboard at http://localhost:6333/dashboard.

Phase 2: The Ingestion Loop (Day 2-3)

Goal: Capture user behavior.

Build POST /ingest endpoint.

Implement Celery Worker:

When a user views a post about "Jazz" for > 10s:

Update Qdrant: Move User Vector slightly toward the "Jazz" centroid.

Update Neo4j: Create/Update a :VIEWED relationship with a weight property.

Phase 3: The Recommendation Engine (Day 4-5)

Goal: The "Convincer" Feed.

Retrieval: Fetch top 100 candidates from Qdrant (Geo-filtered + Vibe-matched).

Ranking (The Social Boost):

For each candidate, run a Cypher query:

MATCH (u:User {id: $user_id})-[:FRIENDS_WITH*1..2]-(friend)-[r:INTERESTED_IN]->(v:Venue {id: $venue_id})
RETURN count(friend) as social_score, collect(friend.name) as friend_names


Serialization: Return JSON that includes the friend_names so the Frontend can display: "Recommended because Sarah and 2 others liked this."

Phase 4: The Agentic Layer (Day 6)

Goal: Close the loop.

Set up LangGraph.

Define a state class AgentState(TypedDict): messages: list.

Define Tools:

check_availability(venue_id, time)

book_table(venue_id, user_id)

Create the endpoint POST /act that initializes the Agent execution graph.

4. MVP Testing Strategy

Since this is local, we don't need real users to test the math.

Seed Data: Create a script seed_data.py that generates:

10 Fake Venues in Jersey City (Lat/Lon near Grove St).

5 Fake Users (Alice, Bob, Charlie, etc.).

Hardcode connections: Alice knows Bob. Bob knows Charlie.

Simulate: Have Bob "Save" a venue.

Verify: Log in as Alice. Ensure that venue appears at the top of her feed with the badge "Bob saved this."