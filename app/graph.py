import os
from neo4j import GraphDatabase

URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

driver = GraphDatabase.driver(URI, auth=AUTH)

def get_db_driver():
    return driver

def close_db_driver():
    driver.close()

def get_social_scores(venue_ids: list[str], user_id: str) -> dict[str, dict]:
    """
    Query Neo4j to count friends and mutuals engaged with venues.
    Returns detailed breakdown for algorithm explainability.
    """
    query = """
    UNWIND $venue_ids AS venue_id
    MATCH (u:User {id: $user_id})
    MATCH (v:Venue {id: venue_id})

    // Direct friends engagement
    OPTIONAL MATCH (u)-[:FRIENDS_WITH]-(friend)-[r:ENGAGED_WITH]->(v)
    WITH u, v, venue_id, collect(DISTINCT {
        name: friend.name,
        type: r.type,
        watch_time: r.watch_time,
        weight: r.weight
    }) as friends_activity

    // Friends who shared this venue
    OPTIONAL MATCH (u)-[:FRIENDS_WITH]-(friend)-[s:SHARED_WITH]->(other)
    WHERE EXISTS((other)-[:RECEIVED_SHARE]->(v))
    WITH u, v, venue_id, friends_activity, collect(DISTINCT {
        name: friend.name,
        type: 'shared'
    }) as shares

    // Mutual friends (2nd degree)
    OPTIONAL MATCH (u)-[:FRIENDS_WITH]-(friend)-[:FRIENDS_WITH]-(mutual)-[r2:ENGAGED_WITH]->(v)
    WHERE NOT (u)-[:FRIENDS_WITH]-(mutual) AND mutual.id <> u.id
    WITH venue_id, friends_activity, shares, collect(DISTINCT mutual.id) as mutual_ids

    RETURN venue_id, friends_activity, shares, mutual_ids
    """

    social_data = {}

    with driver.session() as session:
        result = session.run(query, venue_ids=venue_ids, user_id=user_id)
        for record in result:
            venue_id = record["venue_id"]
            friends = record["friends_activity"]
            shares = record["shares"]
            mutual_ids = record["mutual_ids"]

            score = 0
            contributors = []

            # Scoring logic (updated for new engagement model)
            for f in friends:
                if f['name']:
                    if f['type'] == 'shared':
                        boost = 15
                        score += boost
                        contributors.append({
                            "friend": f['name'],
                            "action": "shared",
                            "boost": boost
                        })
                    elif f['type'] == 'saved':
                        boost = 8
                        score += boost
                        contributors.append({
                            "friend": f['name'],
                            "action": "saved",
                            "boost": boost
                        })
                    elif f['type'] == 'viewed':
                        # Only count engaged views (watch_time > 10s)
                        watch_time = f.get('watch_time', 0)
                        if watch_time >= 10:
                            boost = 5
                            score += boost
                            contributors.append({
                                "friend": f['name'],
                                "action": "viewed",
                                "boost": boost
                            })

            # Add shares
            for s in shares:
                if s['name']:
                    boost = 15
                    score += boost
                    contributors.append({
                        "friend": s['name'],
                        "action": "shared",
                        "boost": boost
                    })

            # Mutual friends boost
            mutual_count = len(mutual_ids) if mutual_ids else 0
            if mutual_count > 0:
                boost = mutual_count * 2
                score += boost
                contributors.append({
                    "mutuals": mutual_count,
                    "action": "interested",
                    "boost": boost
                })

            social_data[venue_id] = {
                "social_score": score,
                "contributors": contributors[:5],  # Top 5 contributors
                "friend_activity": _format_friend_activity(contributors)
            }

    return social_data

def _format_friend_activity(contributors: list) -> str:
    """Format contributor list into human-readable string"""
    if not contributors:
        return ""

    messages = []
    for c in contributors[:3]:  # Top 3
        if "friend" in c:
            action_verb = "shared this" if c["action"] == "shared" else "saved this" if c["action"] == "saved" else "watched this"
            messages.append(f"{c['friend']} {action_verb}")
        elif "mutuals" in c:
            messages.append(f"{c['mutuals']} mutual friends interested")

    return ", ".join(messages)

def create_friendship(user_id_a: str, user_id_b: str):
    query = """
    MERGE (a:User {id: $user_id_a})
    MERGE (b:User {id: $user_id_b})
    MERGE (a)-[:FRIENDS_WITH]->(b)
    """
    with driver.session() as session:
        session.run(query, user_id_a=user_id_a, user_id_b=user_id_b)

def log_interaction_to_graph(user_id: str, venue_id: str, interaction_type: str, weight: float):
    """Legacy function for backwards compatibility"""
    log_engagement(user_id, venue_id, interaction_type, 0, weight)

def log_engagement(user_id: str, venue_id: str, action_type: str, watch_time: int, weight: float):
    """
    Log user engagement with watch_time tracking.
    action_type: 'viewed', 'skipped', 'saved', 'shared'
    """
    query = """
    MERGE (u:User {id: $user_id})
    MERGE (v:Venue {id: $venue_id})
    MERGE (u)-[r:ENGAGED_WITH]->(v)
    SET r.type = $type,
        r.watch_time = $watch_time,
        r.weight = $weight,
        r.timestamp = datetime()
    """
    with driver.session() as session:
        session.run(
            query,
            user_id=user_id,
            venue_id=venue_id,
            type=action_type,
            watch_time=watch_time,
            weight=weight
        )

def log_share(user_id: str, venue_id: str, shared_with_ids: list[str]):
    """
    Log venue share action - creates viral spread in graph
    """
    query = """
    MATCH (u:User {id: $user_id})
    MERGE (v:Venue {id: $venue_id})
    UNWIND $shared_with_ids AS friend_id
        MATCH (f:User {id: friend_id})
        MERGE (u)-[:SHARED_WITH {timestamp: datetime()}]->(f)
        MERGE (f)-[:RECEIVED_SHARE {from: $user_id, timestamp: datetime()}]->(v)
    """
    with driver.session() as session:
        session.run(
            query,
            user_id=user_id,
            venue_id=venue_id,
            shared_with_ids=shared_with_ids
        )

def get_trending_scores(venue_ids: list[str], hours: int = 24) -> dict[str, dict]:
    """
    Get trending scores based on recent engagement (last N hours)
    """
    query = """
    UNWIND $venue_ids AS venue_id
    MATCH (v:Venue {id: venue_id})
    OPTIONAL MATCH ()-[r:ENGAGED_WITH]->(v)
    WHERE r.timestamp > datetime() - duration({hours: $hours})
    WITH venue_id, count(r) as recent_engagements
    RETURN venue_id, recent_engagements
    """

    trending_data = {}

    with driver.session() as session:
        result = session.run(query, venue_ids=venue_ids, hours=hours)
        for record in result:
            venue_id = record["venue_id"]
            count = record["recent_engagements"] or 0

            # Normalize to 0-1 scale (assuming max 50 engagements in 24h is high)
            score = min(count / 50.0, 1.0)

            trending_data[venue_id] = {
                "trending_score": score,
                "recent_count": count,
                "reason": f"{count} people engaged in last {hours}h" if count > 0 else "No recent activity"
            }

    return trending_data

def get_user_watch_history(user_id: str, limit: int = 50) -> list[dict]:
    """
    Get user's watch history with engagement details
    """
    query = """
    MATCH (u:User {id: $user_id})-[r:ENGAGED_WITH]->(v:Venue)
    RETURN v.id as venue_id,
           r.type as action,
           r.watch_time as watch_time,
           r.timestamp as timestamp
    ORDER BY r.timestamp DESC
    LIMIT $limit
    """

    with driver.session() as session:
        result = session.run(query, user_id=user_id, limit=limit)
        return [dict(r) for r in result]

def get_all_users() -> list[dict]:
    """
    Get all users for friend discovery
    """
    query = """
    MATCH (u:User)
    RETURN u.id as id, u.name as name, u.interests as interests, u.archetype as archetype
    ORDER BY u.name
    """

    with driver.session() as session:
        result = session.run(query)
        return [dict(r) for r in result]
