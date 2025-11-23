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

class ClearActivityRequest(BaseModel):
    user_id: str

@app.post("/debug/clear-activity")
async def clear_user_activity(req: ClearActivityRequest):
    """
    Clear all engagement/activity for a specific user.
    Supports both video-level (WATCHED) and legacy venue-level (ENGAGED_WITH).
    Useful for testing how watch time affects recommendations.
    """
    from app.graph import driver, clear_user_video_activity

    try:
        with driver.session() as session:
            # Remove all WATCHED relationships (video-level)
            session.run("""
                MATCH (u:User {id: $user_id})-[r:WATCHED]->()
                DELETE r
            """, user_id=req.user_id)

            # Remove all ENGAGED_WITH relationships (legacy venue-level)
            session.run("""
                MATCH (u:User {id: $user_id})-[r:ENGAGED_WITH]->()
                DELETE r
            """, user_id=req.user_id)

            # Remove all SHARED_WITH and RECEIVED_SHARE relationships
            session.run("""
                MATCH (u:User {id: $user_id})-[r:SHARED_WITH]->()
                DELETE r
            """, user_id=req.user_id)

            session.run("""
                MATCH ()-[r:RECEIVED_SHARE]->(v:Venue)
                WHERE r.from = $user_id
                DELETE r
            """, user_id=req.user_id)

        return {"status": "activity_cleared", "user_id": req.user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CreateUserRequest(BaseModel):
    name: str = None
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
    name = request.name if request.name else fake.name()

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
    Enhanced user profile with VIDEO watch history and engagement details.
    """
    from app.graph import driver, get_user_video_history
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

            # Get Friends (use DISTINCT to avoid duplicates from bidirectional relationships)
            friends_result = session.run("""
                MATCH (u:User {id: $id})-[:FRIENDS_WITH]-(f:User)
                RETURN DISTINCT f.id as id, f.name as name, f.interests as interests
                ORDER BY f.name
            """, id=user_id)
            friends = [{"id": r["id"], "name": r["name"], "interests": r["interests"]} for r in friends_result]

            # Get VIDEO Watch History (using new WATCHED relationships)
            video_history = get_user_video_history(user_id, limit=50)

            # Enrich video history with video details from Qdrant
            if video_history:
                video_ids = []
                video_id_to_point_id = {}

                for item in video_history:
                    try:
                        # Extract numeric ID from video_id (e.g., "video_123" -> 123)
                        vid = item["video_id"]
                        pid = int(vid.split("_")[1])
                        video_ids.append(pid)
                        video_id_to_point_id[vid] = pid
                    except:
                        pass

                if video_ids:
                    # Retrieve video data from Qdrant
                    points = client.retrieve(
                        collection_name="videos",
                        ids=video_ids,
                        with_payload=True
                    )

                    point_map = {p.id: p.payload for p in points}

                    for item in video_history:
                        pid = video_id_to_point_id.get(item["video_id"])
                        if pid is not None and pid in point_map:
                            video_data = point_map[pid]
                            item["video"] = {
                                "video_id": video_data.get("video_id"),
                                "title": video_data.get("title"),
                                "description": video_data.get("description"),
                                "video_type": video_data.get("video_type"),
                                "categories": video_data.get("categories"),
                                "gradient": video_data.get("gradient"),
                                "venue_id": video_data.get("venue_id"),
                                "venue_name": video_data.get("venue_name"),
                                "neighborhood": video_data.get("neighborhood"),
                                "location": video_data.get("location")
                            }

            return {
                "user": user_data,
                "friends": friends,
                "watch_history": video_history  # Now contains video data
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

@app.get("/venues-with-videos")
async def get_venues_with_videos(limit: int = 20):
    """
    Get venues along with their sample videos for user onboarding.
    Each venue includes 1-2 sample videos for engagement.
    """
    from app.vector import client
    from app.graph import driver

    try:
        # Fetch venues from Qdrant
        points, _ = client.scroll(
            collection_name="venues",
            limit=limit,
            with_payload=True
        )

        venues_data = []

        with driver.session() as session:
            for p in points:
                venue_id = p.payload.get("venue_id")

                # Get videos for this venue from Neo4j
                videos_result = session.run("""
                    MATCH (venue:Venue {id: $venue_id})-[:POSTED]->(video:Video)
                    RETURN video.id as id, video.title as title, video.description as description
                    LIMIT 2
                """, venue_id=venue_id)

                videos = [{"id": r["id"], "title": r["title"], "description": r["description"]}
                          for r in videos_result]

                venues_data.append({
                    "venue_id": venue_id,
                    "name": p.payload.get("name"),
                    "category": p.payload.get("category"),
                    "description": p.payload.get("description"),
                    "location": p.payload.get("location"),
                    "videos": videos
                })

        return {"venues": venues_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/businesses")
async def get_all_businesses():
    """
    Get all venues/businesses with complete information and all their videos.
    Includes engagement stats for each video.
    Uses Neo4j as source of truth for venues to ensure all venues are included.
    """
    from app.vector import client
    from app.graph import driver

    try:
        businesses = []

        with driver.session() as session:
            # Get all venues from Neo4j (source of truth)
            venues_result = session.run("""
                MATCH (venue:Venue)
                RETURN venue.id as venue_id,
                       venue.name as name,
                       venue.category as category,
                       venue.description as description,
                       venue.location as location,
                       venue.address as address,
                       venue.neighborhood as neighborhood,
                       venue.price_tier as price_tier
                ORDER BY venue.name
            """)

            for venue_record in venues_result:
                venue_id = venue_record["venue_id"]

                # Get all videos and engagement stats for this venue
                videos_result = session.run("""
                    MATCH (venue:Venue {id: $venue_id})-[:POSTED]->(video:Video)
                    OPTIONAL MATCH (video)<-[r:WATCHED]-(u:User)
                    WITH video,
                         COUNT(DISTINCT u) as total_views,
                         COUNT(DISTINCT CASE WHEN r.action = 'saved' THEN u END) as saves,
                         COUNT(DISTINCT CASE WHEN r.action = 'shared' THEN u END) as shares,
                         SUM(CASE WHEN r.watch_time >= 10 THEN 1 ELSE 0 END) as quality_views
                    RETURN video.id as id,
                           video.title as title,
                           video.description as description,
                           video.video_type as video_type,
                           video.categories as categories,
                           video.created_at as created_at,
                           total_views, saves, shares, quality_views
                    ORDER BY video.created_at DESC
                """, venue_id=venue_id)

                videos = []
                for r in videos_result:
                    videos.append({
                        "id": r["id"],
                        "title": r["title"],
                        "description": r["description"],
                        "video_type": r["video_type"],
                        "categories": r["categories"] or [],
                        "created_at": r["created_at"],
                        "engagement": {
                            "total_views": r["total_views"] or 0,
                            "saves": r["saves"] or 0,
                            "shares": r["shares"] or 0,
                            "quality_views": r["quality_views"] or 0
                        }
                    })

                # Try to get additional metadata from Qdrant if available
                try:
                    qdrant_data = client.scroll(
                        collection_name="venues",
                        scroll_filter={
                            "must": [
                                {
                                    "key": "venue_id",
                                    "match": {"value": venue_id}
                                }
                            ]
                        },
                        limit=1,
                        with_payload=True
                    )
                    if qdrant_data[0]:
                        qdrant_payload = qdrant_data[0][0].payload
                        # Enhance with Qdrant data if Neo4j data is missing
                        if not venue_record["category"] and qdrant_payload.get("category"):
                            venue_record["category"] = qdrant_payload.get("category")
                        if not venue_record["description"] and qdrant_payload.get("description"):
                            venue_record["description"] = qdrant_payload.get("description")
                except:
                    pass  # If Qdrant doesn't have this venue, just use Neo4j data

                businesses.append({
                    "venue_id": venue_id,
                    "name": venue_record["name"],
                    "category": venue_record["category"],
                    "description": venue_record["description"],
                    "location": venue_record["location"],
                    "address": venue_record["address"],
                    "neighborhood": venue_record["neighborhood"],
                    "price_tier": venue_record["price_tier"],
                    "total_videos": len(videos),
                    "videos": videos
                })

        # Sort by total videos (most active first)
        businesses.sort(key=lambda x: x["total_videos"], reverse=True)

        return {"businesses": businesses, "total": len(businesses)}
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
        
    # Fetch Users from Neo4j (filter out null names)
    users = []
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User)
                WHERE u.name IS NOT NULL
                RETURN u.id as id, u.name as name
                ORDER BY u.name
                LIMIT 100
            """)
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

class VideoEngagementRequest(BaseModel):
    user_id: str
    video_id: str
    watch_time_seconds: int
    action: str  # 'view', 'skip', 'save', 'share'

@app.post("/engage-video")
async def log_video_engagement_endpoint(req: VideoEngagementRequest):
    """
    Log user engagement with video-level tracking.
    Primary endpoint for short-video interactions.
    """
    from app.graph import log_video_engagement

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

    # Log to graph
    try:
        log_video_engagement(req.user_id, req.video_id, action_type, req.watch_time_seconds, weight)
        return {"status": "logged", "action": action_type, "weight": weight}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class EngagementRequest(BaseModel):
    user_id: str
    venue_id: str
    watch_time_seconds: int
    action: str  # 'view', 'skip', 'save', 'share'

@app.post("/engage")
async def log_engagement_endpoint(req: EngagementRequest):
    """
    LEGACY: Log user engagement with watch time tracking.
    This is the primary endpoint for short-video interactions.
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

@app.get("/feed-video")
async def get_video_feed(user_id: str, lat: float, lon: float, radius_km: float = 2.0, limit: int = 20):
    """
    Video-centric feed with full algorithm transparency.
    Returns videos (not venues) ranked by multi-factor algorithm.
    Filters out seen videos and deduplicates (max 1 video per venue per batch).
    """
    from app.vector import get_user_vector
    from app.graph import get_social_scores_for_videos, get_seen_videos
    from qdrant_client import models as qmodels
    import math

    # 1. Get User Vector
    user_vector = get_user_vector(user_id)

    # 2. Get seen videos to filter out
    seen_video_ids = get_seen_videos(user_id)
    seen_video_ids_set = set(seen_video_ids)

    # 3. Search for video candidates (fetch more than needed for filtering)
    from app.vector import client
    from qdrant_client.models import PointIdsList, Filter, FieldCondition, MatchValue

    search_results = client.query_points(
        collection_name="videos",
        query=user_vector,
        limit=limit * 4,  # Fetch extra to account for seen videos and deduplication
        with_payload=True
    ).points

    # 4. Filter out seen videos and build candidates
    candidates = []
    candidate_video_ids = set()

    for result in search_results:
        video_id = result.payload.get("video_id")
        if video_id not in seen_video_ids_set:
            # Check proximity
            venue_lat = result.payload.get("location", {}).get("lat", lat)
            venue_lon = result.payload.get("location", {}).get("lon", lon)
            distance_km = haversine_distance(lat, lon, venue_lat, venue_lon)

            if distance_km <= radius_km:
                candidates.append({
                    "video_id": video_id,
                    "venue_id": result.payload.get("venue_id"),
                    "score": result.score,
                    "payload": result.payload,
                    "distance_km": distance_km
                })
                candidate_video_ids.add(video_id)

    # 4b. Inject friend-engaged videos (social proof boost)
    # Query for videos that friends have engaged with but aren't in candidates yet
    from app.graph import driver
    friend_video_query = """
    MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]-(friend)-[r:WATCHED]->(vid:Video)
    WHERE r.watch_time >= 10 OR r.action IN ['saved', 'shared']
    WITH vid, MAX(r.watch_time) as max_watch_time
    RETURN vid.id as video_id
    ORDER BY max_watch_time DESC
    LIMIT 50
    """

    with driver.session() as session:
        result = session.run(friend_video_query, user_id=user_id)
        all_friend_videos = [record["video_id"] for record in result]
        friend_video_ids = [vid for vid in all_friend_videos if vid not in candidate_video_ids and vid not in seen_video_ids_set]

    # Fetch friend-engaged videos from Qdrant and add to candidates
    if friend_video_ids:
        try:
            point_ids = [int(vid.split("_")[1]) for vid in friend_video_ids]
            friend_videos = client.retrieve(
                collection_name="videos",
                ids=point_ids,
                with_payload=True
            )

            for point in friend_videos:
                video_id = point.payload.get("video_id")
                if video_id and video_id not in candidate_video_ids:
                    venue_lat = point.payload.get("location", {}).get("lat", lat)
                    venue_lon = point.payload.get("location", {}).get("lon", lon)
                    distance_km = haversine_distance(lat, lon, venue_lat, venue_lon)

                    if distance_km <= radius_km * 1.5:  # Slightly larger radius for friend content
                        candidates.append({
                            "video_id": video_id,
                            "venue_id": point.payload.get("venue_id"),
                            "score": 0.5,  # Default taste score for friend-injected content
                            "payload": point.payload,
                            "distance_km": distance_km
                        })
                        candidate_video_ids.add(video_id)
        except Exception as e:
            print(f"Failed to inject friend videos: {e}")

    if not candidates:
        return {"feed": []}

    # 5. Get video IDs and social scores
    video_ids = [c["video_id"] for c in candidates]
    social_scores = get_social_scores_for_videos(video_ids, user_id)

    # 6. Calculate freshness/trending scores
    def calculate_video_freshness(created_at_str: str) -> float:
        """Calculate freshness score based on video age"""
        from datetime import datetime
        try:
            created_at = datetime.fromisoformat(created_at_str.replace('Z', '+00:00'))
            age_days = (datetime.now(created_at.tzinfo) - created_at).days
            # Newer = higher score (exponential decay)
            if age_days < 2:
                return 1.0  # Brand new
            elif age_days < 7:
                return 0.7
            elif age_days < 14:
                return 0.5
            elif age_days < 30:
                return 0.3
            else:
                return 0.1
        except:
            return 0.5

    # 7. Multi-factor ranking
    feed = []
    for candidate in candidates:
        video_id = candidate["video_id"]
        venue_id = candidate["venue_id"]
        payload = candidate["payload"]
        distance_km = candidate["distance_km"]

        # Taste match (vector similarity)
        taste_score = candidate["score"]

        # Social proof (video-specific + venue-level context)
        social_data = social_scores.get(video_id, {"social_score": 0, "contributors": [], "friend_activity": ""})
        social_raw = social_data["social_score"]
        social_norm = min(social_raw / 50.0, 1.0)

        # Proximity
        proximity_score = max(0, 1.0 - (distance_km / (radius_km * 2)))

        # Freshness/Trending
        created_at = payload.get("created_at", "")
        freshness_score = calculate_video_freshness(created_at)

        # Final weighted score
        final_score = (
            taste_score * 0.30 +
            social_norm * 0.40 +
            proximity_score * 0.20 +
            freshness_score * 0.10
        )

        # Build explanation
        explanation = {
            "taste_match": {
                "score": round(taste_score, 2),
                "reason": f"Matches your interests: {', '.join(payload.get('categories', [])[:3])}"
            },
            "social_proof": {
                "score": round(social_norm, 2),
                "raw_score": social_raw,
                "contributors": social_data.get("contributors", []),
                "reason": social_data.get("friend_activity", "No friend activity yet")
            },
            "proximity": {
                "score": round(proximity_score, 2),
                "distance_km": round(distance_km, 2),
                "reason": f"{round(distance_km, 1)}km away (~{int(distance_km * 12)} min walk)"
            },
            "trending": {
                "score": round(freshness_score, 2),
                "reason": f"Posted {payload.get('created_at', 'recently')[:10]}"
            }
        }

        feed.append({
            "video_id": video_id,
            "venue_id": venue_id,
            "name": payload.get("venue_name", "Unknown Venue"),
            "title": payload.get("title", ""),
            "description": payload.get("description", ""),
            "video_type": payload.get("video_type", ""),
            "categories": payload.get("categories", []),
            "neighborhood": payload.get("neighborhood", ""),
            "price_tier": payload.get("price_tier", 2),
            "gradient": payload.get("gradient", "from-purple-500 to-pink-500"),
            "location": payload.get("location", {}),
            "final_score": round(final_score, 3),
            "explanation": explanation
        })

    # 8. Sort by final score
    feed.sort(key=lambda x: x["final_score"], reverse=True)


    # 9. Deduplication: Max 1 video per venue, prioritizing friend-engaged videos
    venue_best_video = {}

    # First pass: For each venue, keep the video with highest social proof (friend engagement)
    for item in feed:
        venue_id = item["venue_id"]
        social_raw = item["explanation"]["social_proof"]["raw_score"]

        if venue_id not in venue_best_video:
            venue_best_video[venue_id] = item
        else:
            # If this video has more friend engagement, replace the current best
            current_social = venue_best_video[venue_id]["explanation"]["social_proof"]["raw_score"]
            if social_raw > current_social:
                venue_best_video[venue_id] = item
            # If equal social proof, keep the one with higher final score
            elif social_raw == current_social and item["final_score"] > venue_best_video[venue_id]["final_score"]:
                venue_best_video[venue_id] = item

    # Second pass: Build deduplicated feed from best videos per venue, sorted by final score
    deduped_feed = list(venue_best_video.values())
    deduped_feed.sort(key=lambda x: x["final_score"], reverse=True)
    deduped_feed = deduped_feed[:limit]

    return {"feed": deduped_feed}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate distance in km between two lat/lon points"""
    import math
    R = 6371  # Earth's radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

@app.get("/feed")
async def get_feed(user_id: str, lat: float, lon: float, radius_km: float = 2.0, limit: int = 20):
    """
    LEGACY: Enhanced feed with full algorithm transparency and explainability.
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
