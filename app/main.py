from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from app.worker import process_interaction
from app.graph import get_db_driver
from app.vector import get_vector_client
# from app.agent import booking_agent_workflow # Commented out until fully implemented

from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for MVP
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Interaction(BaseModel):
    user_id: str
    venue_id: str
    interaction_type: str
    duration: int

class Connection(BaseModel):
    user_id_a: str
    user_id_b: str

class AgentAction(BaseModel):
    user_id: str
    venue_id: str
    party_size: int
    time: str

@app.post("/debug/reset")
async def debug_reset(clear_venues: bool = False):
    """
    Clear data. By default, preserves venues and only clears users/interactions.
    Set clear_venues=True to wipe everything.
    """
    from app.vector import client
    from app.graph import driver
    
    try:
        if clear_venues:
            # Clear Qdrant
            client.delete_collection("venues")
            # Recreate empty
            from qdrant_client import models
            client.create_collection(
                collection_name="venues",
                vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
            )
            
            # Clear Neo4j completely
            with driver.session() as session:
                session.run("MATCH (n) DETACH DELETE n")
        else:
            # Only clear Users and their relationships in Neo4j
            # This preserves Venue nodes if they exist, but removes all User activity
            with driver.session() as session:
                session.run("MATCH (u:User) DETACH DELETE u")
            
        return {"status": "reset_complete", "venues_cleared": clear_venues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateUserRequest(BaseModel):
    interests: list[str] = None

@app.post("/debug/user")
async def debug_create_user(request: CreateUserRequest = Body(...)):
    """
    Create a new random user. Optional interests list.
    """
    from app.graph import driver
    from faker import Faker
    import uuid
    import random
    
    fake = Faker()
    user_id = f"user_{uuid.uuid4().hex[:8]}"
    name = fake.name()
    
    interests = request.interests
    if interests is None:
        possible_interests = ["Italian", "Mexican", "Japanese", "Burgers", "Coffee", "Cocktails", "Jazz", "Techno", "Pop", "Rock", "Museums", "Parks", "Theater", "Sports"]
        interests = random.sample(possible_interests, random.randint(2, 5))
    
    try:
        with driver.session() as session:
            session.run("CREATE (:User {id: $id, name: $name, interests: $interests})", id=user_id, name=name, interests=interests)
        return {"id": user_id, "name": name, "interests": interests}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/user/{user_id}")
async def get_user_profile(user_id: str):
    """
    Enhanced user profile with watch history and engagement details.
    """
    from app.graph import driver, get_user_watch_history
    from app.vector import client

    try:
        with driver.session() as session:
            # Get User & Interests
            user_result = session.run("""
                MATCH (u:User {id: $id})
                RETURN u.name as name, u.interests as interests, u.archetype as archetype
            """, id=user_id).single()

            if not user_result:
                raise HTTPException(status_code=404, detail="User not found")

            user_data = {
                "id": user_id,
                "name": user_result["name"],
                "interests": user_result["interests"] or [],
                "archetype": user_result.get("archetype", "Unknown")
            }

            # Get Friends
            friends_result = session.run("""
                MATCH (u:User {id: $id})-[:FRIENDS_WITH]-(f:User)
                RETURN f.id as id, f.name as name, f.interests as interests
                ORDER BY f.name
            """, id=user_id)
            friends = [{"id": r["id"], "name": r["name"], "interests": r["interests"]} for r in friends_result]

            # Get Watch History (using new ENGAGED_WITH relationships)
            watch_history = get_user_watch_history(user_id, limit=50)

            # Enrich watch history with venue details
            if watch_history:
                point_ids = []
                venue_id_to_point_id = {}

                for item in watch_history:
                    try:
                        pid = int(item["venue_id"].split("_")[1])
                        point_ids.append(pid)
                        venue_id_to_point_id[item["venue_id"]] = pid
                    except:
                        pass

                if point_ids:
                    points = client.retrieve(
                        collection_name="venues",
                        ids=point_ids,
                        with_payload=True
                    )

                    point_map = {p.id: p.payload for p in points}

                    for item in watch_history:
                        pid = venue_id_to_point_id.get(item["venue_id"])
                        if pid is not None and pid in point_map:
                            item["venue"] = point_map[pid]

            return {
                "user": user_data,
                "friends": friends,
                "watch_history": watch_history
            }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/users")
async def get_all_users(current_user_id: str = None):
    """
    Get all users for friend discovery.
    If current_user_id is provided, marks which users are already friends.
    """
    from app.graph import get_all_users, driver

    try:
        all_users = get_all_users()

        # If current_user_id provided, mark existing friends
        if current_user_id:
            with driver.session() as session:
                friends_result = session.run("""
                    MATCH (u:User {id: $id})-[:FRIENDS_WITH]-(f:User)
                    RETURN f.id as friend_id
                """, id=current_user_id)

                friend_ids = set([r["friend_id"] for r in friends_result])

                for user in all_users:
                    user["is_friend"] = user["id"] in friend_ids
                    user["is_self"] = user["id"] == current_user_id

        return {"users": all_users}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class AddFriendRequest(BaseModel):
    user_id: str
    friend_id: str

@app.post("/friends/add")
async def add_friend(req: AddFriendRequest):
    """
    Add a friend connection (bidirectional).
    """
    from app.graph import create_friendship

    try:
        create_friendship(req.user_id, req.friend_id)
        # Also create reverse for bidirectional
        create_friendship(req.friend_id, req.user_id)
        return {"status": "friendship_created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/venues")
async def get_venues(search: str = None):
    """
    Get all venues, optionally filtered by search term.
    """
    from app.vector import client
    
    try:
        # Fetch all (limit 1000 for MVP)
        points, _ = client.scroll(
            collection_name="venues",
            limit=1000,
            with_payload=True
        )
        
        venues = [
            {
                "venue_id": p.payload.get("venue_id"),
                "name": p.payload.get("name"),
                "category": p.payload.get("category"),
                "description": p.payload.get("description"),
                "location": p.payload.get("location")
            }
            for p in points
        ]
        
        if search:
            search_lower = search.lower()
            venues = [
                v for v in venues 
                if search_lower in v["name"].lower() or 
                   search_lower in v["category"].lower() or
                   search_lower in v["description"].lower()
            ]
            
        return {"venues": venues}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/debug/map-data")
async def get_map_data():
    """
    Fetch all venues and users for visualization.
    """
    from app.vector import client
    from app.graph import driver
    
    # Fetch Venues from Qdrant
    try:
        # Scroll through all points
        points, _ = client.scroll(
            collection_name="venues",
            limit=100,
            with_payload=True
        )
        venues = [
            {
                "venue_id": p.payload.get("venue_id"),
                "name": p.payload.get("name"),
                "category": p.payload.get("category"),
                "description": p.payload.get("description"),
                "location": p.payload.get("location")
            }
            for p in points
        ]
    except Exception as e:
        print(f"Error fetching venues: {e}")
        venues = []
        
    # Fetch Users from Neo4j
    users = []
    try:
        with driver.session() as session:
            result = session.run("MATCH (u:User) RETURN u.id as id, u.name as name LIMIT 100")
            users = [{"id": r["id"], "name": r["name"]} for r in result]
    except Exception as e:
        print(f"Error fetching users: {e}")
        
    return {"venues": venues, "users": users}

@app.post("/ingest/interaction")
async def ingest_interaction(interaction: Interaction):
    """Legacy endpoint for backwards compatibility"""
    process_interaction.delay(
        interaction.user_id,
        interaction.venue_id,
        interaction.interaction_type,
        interaction.duration
    )
    return {"status": "queued"}

class EngagementRequest(BaseModel):
    user_id: str
    venue_id: str
    watch_time_seconds: int
    action: str  # 'view', 'skip', 'save', 'share'

@app.post("/engage")
async def log_engagement_endpoint(req: EngagementRequest):
    """
    Log user engagement with watch time tracking.
    This is the primary endpoint for TikTok-style interactions.
    """
    from app.graph import log_engagement

    # Calculate weight based on action and watch time
    weight = 0.0
    action_type = req.action

    if req.action == "skip" or req.watch_time_seconds < 3:
        weight = -0.5
        action_type = "skipped"
    elif req.action == "share":
        weight = 3.0
        action_type = "shared"
    elif req.action == "save":
        weight = 1.5
        action_type = "saved"
    else:  # view
        # Weight based on watch time
        if req.watch_time_seconds >= 30:
            weight = 2.0  # Full view
        elif req.watch_time_seconds >= 10:
            weight = 1.0  # Engaged view
        elif req.watch_time_seconds >= 3:
            weight = 0.3  # Brief view
        action_type = "viewed"

    # Log to graph (async via Celery in production, sync for demo)
    try:
        log_engagement(req.user_id, req.venue_id, action_type, req.watch_time_seconds, weight)
        return {"status": "logged", "action": action_type, "weight": weight}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ShareRequest(BaseModel):
    user_id: str
    venue_id: str
    shared_with: list[str]  # List of friend user_ids

@app.post("/share")
async def share_venue(req: ShareRequest):
    """
    Share a venue with friends - creates viral spread in the graph.
    Also logs engagement for the sharer.
    """
    from app.graph import log_share, log_engagement

    try:
        # Log as share engagement for the user
        log_engagement(req.user_id, req.venue_id, "shared", 30, 3.0)

        # Create share relationships in graph
        log_share(req.user_id, req.venue_id, req.shared_with)

        return {
            "status": "shared",
            "shared_with_count": len(req.shared_with)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/social/connect")
async def social_connect(connection: Connection):
    from app.graph import create_friendship
    try:
        create_friendship(connection.user_id_a, connection.user_id_b)
        return {"status": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/feed")
async def get_feed(user_id: str, lat: float, lon: float, radius_km: float = 2.0, limit: int = 20):
    """
    Enhanced feed with full algorithm transparency and explainability.
    Returns venues ranked by multi-factor algorithm with detailed breakdown.
    """
    from app.vector import get_user_vector, search_venues
    from app.graph import get_social_scores, get_trending_scores
    import math

    # 1. Get User Vector (real embeddings from Qdrant)
    user_vector = get_user_vector(user_id)

    # 2. Vector Search (Candidate Generation)
    candidates = search_venues(user_vector, lat, lon, radius_km=radius_km, limit=limit*2)

    if not candidates:
        return {"feed": []}

    venue_ids = [c["venue_id"] for c in candidates]

    # 3. Get all scoring factors
    social_scores = get_social_scores(venue_ids, user_id)
    trending_scores = get_trending_scores(venue_ids, hours=24)

    # 4. Calculate proximity scores
    def haversine_distance(lat1, lon1, lat2, lon2):
        """Calculate distance in km between two lat/lon points"""
        R = 6371  # Earth's radius in km
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c

    # 5. Multi-factor ranking with explainability
    feed = []
    for candidate in candidates:
        venue_id = candidate["venue_id"]
        payload = candidate["payload"]

        # Vector similarity (0-1, higher is better)
        taste_score = candidate["score"]

        # Social proof (normalize to 0-1, max expected ~50 points)
        social_data = social_scores.get(venue_id, {"social_score": 0, "contributors": [], "friend_activity": ""})
        social_raw = social_data["social_score"]
        social_norm = min(social_raw / 50.0, 1.0)

        # Proximity (0-1, closer is better)
        venue_lat = payload.get("location", {}).get("lat", lat)
        venue_lon = payload.get("location", {}).get("lon", lon)
        distance_km = haversine_distance(lat, lon, venue_lat, venue_lon)
        # Normalize: 0km = 1.0, 2km = 0.5, 4km+ = 0.0
        proximity_score = max(0, 1.0 - (distance_km / (radius_km * 2)))

        # Trending (0-1)
        trending_data = trending_scores.get(venue_id, {"trending_score": 0, "recent_count": 0, "reason": ""})
        trending_score = trending_data["trending_score"]

        # Final weighted score
        final_score = (
            taste_score * 0.30 +
            social_norm * 0.35 +
            proximity_score * 0.20 +
            trending_score * 0.10 +
            0.05  # Diversity bonus (placeholder)
        )

        # Build explanation object
        explanation = {
            "taste_match": {
                "score": round(taste_score, 2),
                "reason": f"Matches your interests: {', '.join(payload.get('categories', [])[:3])}"
            },
            "social_proof": {
                "score": round(social_norm, 2),
                "raw_score": social_raw,
                "contributors": social_data.get("contributors", []),
                "reason": social_data.get("friend_activity", "No friend activity")
            },
            "proximity": {
                "score": round(proximity_score, 2),
                "distance_km": round(distance_km, 2),
                "reason": f"{round(distance_km, 1)}km away (~{int(distance_km * 12)} min walk)"
            },
            "trending": {
                "score": round(trending_score, 2),
                "recent_count": trending_data.get("recent_count", 0),
                "reason": trending_data.get("reason", "No recent activity")
            }
        }

        feed.append({
            "venue_id": venue_id,
            "name": payload.get("name", "Unknown Venue"),
            "description": payload.get("description", ""),
            "categories": payload.get("categories", []),
            "neighborhood": payload.get("neighborhood", ""),
            "price_tier": payload.get("price_tier", 2),
            "video_url": payload.get("video_url", ""),
            "location": payload.get("location", {}),
            "final_score": round(final_score, 3),
            "explanation": explanation
        })

    # Sort by final score descending
    feed.sort(key=lambda x: x["final_score"], reverse=True)

    # Return top N
    return {"feed": feed[:limit]}

@app.post("/agent/action")
async def agent_action(action: AgentAction):
    from app.agent import booking_agent_workflow
    
    agent = booking_agent_workflow()
    
    initial_state = {
        "user_id": action.user_id,
        "venue_id": action.venue_id,
        "party_size": action.party_size,
        "time": action.time,
        "status": "started",
        "message": None,
        "alternatives": []
    }
    
    result = agent.invoke(initial_state)
    
    return result

@app.get("/")
async def root():
    return {"message": "Social-First Recommendation Engine API"}
