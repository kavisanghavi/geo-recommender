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
    Get user profile including friends and interactions.
    """
    from app.graph import driver
    from app.vector import client
    
    try:
        with driver.session() as session:
            # Get User & Interests
            user_result = session.run("MATCH (u:User {id: $id}) RETURN u.name as name, u.interests as interests", id=user_id).single()
            if not user_result:
                raise HTTPException(status_code=404, detail="User not found")
            
            user_data = {
                "id": user_id,
                "name": user_result["name"],
                "interests": user_result["interests"] or []
            }
            
            # Get Friends
            friends_result = session.run("""
                MATCH (u:User {id: $id})-[:FRIENDS_WITH]-(f:User)
                RETURN f.id as id, f.name as name
            """, id=user_id)
            friends = [{"id": r["id"], "name": r["name"]} for r in friends_result]
            
            # Get Interactions (Going/Saved)
            interactions_result = session.run("""
                MATCH (u:User {id: $id})-[r:INTERESTED_IN]->(v:Venue)
                RETURN v.id as venue_id, r.type as type
            """, id=user_id)
            
            interactions = []
            for r in interactions_result:
                # Fetch venue details from Qdrant
                # Note: In a real app, we might cache this or store minimal venue data in Neo4j
                # For MVP, we'll fetch individually or batch if possible. 
                # Qdrant scroll/retrieve is better.
                interactions.append({"venue_id": r["venue_id"], "type": r["type"]})
                
            # Enrich interactions with Venue Data
            if interactions:
                # Qdrant uses integer IDs (0..N) but we store "venue_N" strings in Neo4j
                # We need to convert "venue_5" -> 5 to retrieve from Qdrant
                point_ids = []
                venue_id_to_point_id = {}
                
                for i in interactions:
                    try:
                        # Extract int from "venue_123"
                        pid = int(i["venue_id"].split("_")[1])
                        point_ids.append(pid)
                        venue_id_to_point_id[i["venue_id"]] = pid
                    except:
                        pass
                
                if point_ids:
                    points = client.retrieve(
                        collection_name="venues",
                        ids=point_ids,
                        with_payload=True
                    )
                    
                    # Map back: Point ID -> Payload
                    # We need to match the original interaction venue_id (string) to the payload
                    point_map = {p.id: p.payload for p in points}
                    
                    for i in interactions:
                        pid = venue_id_to_point_id.get(i["venue_id"])
                        if pid is not None and pid in point_map:
                            i["venue"] = point_map[pid]

            return {
                "user": user_data,
                "friends": friends,
                "interactions": interactions
            }
            
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
    process_interaction.delay(
        interaction.user_id,
        interaction.venue_id,
        interaction.interaction_type,
        interaction.duration
    )
    return {"status": "queued"}

@app.post("/social/connect")
async def social_connect(connection: Connection):
    from app.graph import create_friendship
    try:
        create_friendship(connection.user_id_a, connection.user_id_b)
        return {"status": "connected"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/feed")
async def get_feed(user_id: str, lat: float, lon: float):
    from app.vector import get_user_vector, search_venues
    from app.graph import get_social_scores
    
    # 1. Get User Vector
    user_vector = get_user_vector(user_id)
    
    # 2. Vector Search (Candidate Generation)
    candidates = search_venues(user_vector, lat, lon)
    
    if not candidates:
        return {"feed": []}
        
    venue_ids = [c["venue_id"] for c in candidates]
    
    # 3. Social Reranking
    social_scores = get_social_scores(venue_ids, user_id)
    
    # 4. Merge and Sort
    feed = []
    for candidate in candidates:
        venue_id = candidate["venue_id"]
        vibe_score = candidate["score"]
        
        social_data = social_scores.get(venue_id, {"social_score": 0, "friend_activity": ""})
        social_score = social_data["social_score"]
        
        # Final Score Formula: (VectorSimilarity * 0.7) + (SocialProofCount * 0.3)
        # Note: Vector score is usually 0-1 (cosine), Social score can be higher.
        # We might need to normalize social score, but for MVP we'll use raw.
        # Assuming social score is roughly 0-20 range.
        # Let's normalize social score by dividing by 20 (capping at 1.0) for the formula
        norm_social = min(social_score / 20.0, 1.0)
        
        final_score = (vibe_score * 0.7) + (norm_social * 0.3)
        
        feed.append({
            "venue_id": venue_id,
            "name": candidate["payload"].get("name", "Unknown Venue"),
            "description": candidate["payload"].get("description", ""),
            "match_score": round(final_score, 2),
            "friend_activity": social_data["friend_activity"],
            "vibe_match": round(vibe_score, 2),
            "social_score": social_score
        })
    
    # Sort by final score descending
    feed.sort(key=lambda x: x["match_score"], reverse=True)
    
    return {"feed": feed}

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
