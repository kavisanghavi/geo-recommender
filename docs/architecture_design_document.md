Social-First Recommendation Engine: MVP Architecture Document

Version: 1.0

Status: Draft / MVP

Author: AI Architect

1. Executive Summary

1.1 Product Goal

To develop a recommendation engine that solves the coordination problem of "Where should we go?" by combining two distinct signals:

Spatial/Vibe Compatibility: Is this place cool and convenient?

Social Proof: Are my friends or compatible people going?

The system aims to not just show places, but convince users to attend by highlighting social activity, and then facilitate the outing via AI agents that handle reservations.

1.2 MVP Scope

This architecture is designed for a Local-First MVP using Docker. It simulates a production cloud environment (like AWS) on a single machine to allow for zero-cost iteration while maintaining the complexity required for social graph analysis.

2. System Architecture

2.1 High-Level Overview

The system follows an Event-Driven Architecture. User interactions (viewing, saving, filtering) are treated as events that update a "state," which in turn drives the recommendations. We decouple the API (fast response) from the Intelligence (slow processing) using a message queue.

graph TD
    subgraph "Frontend Layer"
        Mobile[Mobile App / Web]
    end

    subgraph "API Layer (FastAPI)"
        API[Main Backend API]
        Ingest[Ingestion Endpoint]
        Feed[Feed Generation Endpoint]
    end

    subgraph "Async Processing Layer"
        Redis[Redis Message Queue]
        Celery[Celery Workers]
    end

    subgraph "Intelligence & Storage Layer"
        Neo4j[("Neo4j (Social Graph)"))]
        Qdrant[("Qdrant (Vector DB)"))]
    end

    subgraph "Agentic Layer"
        LangGraph[LangGraph Agent]
        Tools[Booking Tools]
    end

    Mobile -->|1. User Action (View/Save)| Ingest
    Mobile -->|2. Request Feed| Feed
    Mobile -->|3. Click 'Book'| API
    
    Ingest -->|4. Push Task| Redis
    Redis -->|5. Pick up Task| Celery
    
    Celery -->|6. Update Weights| Neo4j
    Celery -->|7. Update User Vector| Qdrant
    
    Feed -->|8. Spatial Query| Qdrant
    Feed -->|9. Social Rerank| Neo4j
    
    API -->|10. Trigger Booking| LangGraph
    LangGraph --> Tools


3. Component Breakdown

3.1 The "Brain": FastAPI Backend

Role: The central orchestrator.

Responsibilities: * Validates incoming data.

Serves the Feed (combining results from Qdrant and Neo4j).

Routes "Action" requests to the Agent.

3.2 The "Memory": Dual Database Strategy

We use a Hybrid Architecture because SQL cannot efficiently handle the two core questions we need to ask:

Component

Technology

Purpose

Query Example

Vector Memory

Qdrant

Semantic/Vibe Matching

"Find places that feel like 'cozy jazz bar' near User A."

Social Memory

Neo4j

Relationship Mapping

"Find users connected to User A (Depth 2) who liked this place."

3.3 The "Reflexes": Async Workers (Celery + Redis)

Role: Processes user behavior without slowing down the app.

Logic: When a user lingers on a post for 30 seconds, the worker:

Calculates a "Interest Score" (0.0 - 1.0).

Updates the edge in Neo4j (:VIEWED {weight: 0.8}).

Nudges the User's Vector in Qdrant towards the venue's category.

3.4 The "Hands": Agentic Layer (LangGraph)

Role: Executes real-world tasks.

Trigger: User explicitly clicks "Book" or "Join".

Logic: A State Machine (ReAct pattern) that reasons about time and availability.

4. Data Strategy: The "Social-Spatial" Graph

The effectiveness of the recommendation engine relies on the schema connecting People to Places.

4.1 The Graph Schema (Neo4j)

graph LR
    UserA((User: You))
    UserB((User: Friend))
    UserC((User: Mutual))
    Venue1[Venue: Jazz Club]
    
    UserA --"FRIENDS_WITH"--> UserB
    UserB --"FRIENDS_WITH"--> UserC
    
    UserA --"VIEWED {time: 45s}"--> Venue1
    UserB --"SAVED"--> Venue1
    UserC --"GOING"--> Venue1
    
    style Venue1 fill:#ff9900,stroke:#333


4.2 Vector Embeddings (Qdrant)

Venue Vector: Created from description, category, price, and aggregate reviews.

User Vector: A dynamic vector that moves over time based on interaction. If you save 3 coffee shops, your vector moves into the "Coffee Cluster."

5. Core Algorithms

5.1 The "Convincer" Feed Algorithm

This is the core IP. It runs every time the feed is requested.

Candidate Generation (Qdrant):

Input: User Lat/Lon, User Vector.

Operation: search(collection="venues", vector=user_vector, filter={geo_radius: 5km})

Output: Top 50 "Vibe-Matched" venues.

Social Reranking (Neo4j):

Input: List of 50 venue_ids.

Operation: For each venue, count connections (Friends/Mutuals) who have interacting edges (SAVED, GOING, LIKED).

Weighting: * Direct Friend "Going": +10 points

Direct Friend "Saved": +5 points

Mutual "Going": +2 points

Final Sort:

Score = (VibeMatch * 0.6) + (SocialScore * 0.4)

Outcome: A jazz bar that is slightly further away but has 3 friends going will outrank a closer jazz bar with 0 social activity.

5.2 The Booking Agent Algorithm

Triggered when the user accepts a recommendation.

State Initialization: Agent receives {venue_name, party_size, target_time}.

Availability Check: Agent calls tool check_availability(venue_id, time).

Reasoning Branch:

If Available: Proceed to booking tool.

If Unavailable: Agent generates 3 alternative slots closest to target_time and asks User for confirmation.

Execution: Agent calls confirm_booking() and updates Neo4j with a :GOING edge for the user.

6. Implementation Roadmap (MVP)

Phase 1: The Skeleton (Docker)

Set up docker-compose.yml with API, Neo4j, Qdrant, Redis.

Verify containers can "ping" each other.

Phase 2: The Brain (FastAPI)

Create main.py with the 4 endpoints defined in the Prompt.

Connect Python drivers to Neo4j and Qdrant.

Phase 3: The Memory (Ingestion)

Write the "Seeder Script" to populate fake venues and users.

Implement the ingest endpoint to track "Time Spent."

Phase 4: The Magic (Recommendation Logic)

Implement the Hybrid Query (Qdrant Search -> Neo4j Filter).

Format the JSON response to include "Social Reason" strings.

Phase 5: The Hands (Agent)

Implement LangGraph simple workflow.

Mock the "Booking API" (return True for even hours, False for odd hours to test reasoning).