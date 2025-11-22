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
    Query Neo4j to count friends and mutuals interested in the given venues.
    Returns a dictionary mapping venue_id to social score and activity details.
    """
    query = """
    UNWIND $venue_ids AS venue_id
    MATCH (u:User {id: $user_id})
    MATCH (v:Venue {id: venue_id})
    
    // Direct friends
    OPTIONAL MATCH (u)-[:FRIENDS_WITH]-(friend)-[r:INTERESTED_IN]->(v)
    WITH venue_id, collect(DISTINCT {name: friend.name, type: r.type}) as friends_activity
    
    // Mutual friends (2nd degree)
    OPTIONAL MATCH (u)-[:FRIENDS_WITH]-(friend)-[:FRIENDS_WITH]-(mutual)-[r2:INTERESTED_IN]->(v)
    WHERE NOT (u)-[:FRIENDS_WITH]-(mutual) AND mutual.id <> u.id // Exclude direct friends and self
    WITH venue_id, friends_activity, collect(DISTINCT mutual.id) as mutual_ids, collect(DISTINCT {name: mutual.name, type: r2.type}) as mutuals_activity
    
    RETURN venue_id, friends_activity, mutuals_activity, mutual_ids
    """
    
    social_data = {}
    
    with driver.session() as session:
        result = session.run(query, venue_ids=venue_ids, user_id=user_id)
        for record in result:
            venue_id = record["venue_id"]
            friends = record["friends_activity"]
            mutuals = record["mutuals_activity"]
            mutual_ids = record["mutual_ids"]
            
            score = 0
            reasons = []
            
            # Scoring logic
            for f in friends:
                if f['name']: # Ensure friend exists
                    if f['type'] == 'going':
                        score += 10
                        reasons.append(f"{f['name']} is going")
                    elif f['type'] == 'saved':
                        score += 5
                        reasons.append(f"{f['name']} saved this")
                    else:
                        score += 3
            
            for m in mutuals:
                if m['name']: # Ensure mutual exists
                    if m['type'] == 'going':
                        score += 2
            
            if mutual_ids:
                count = len(mutual_ids)
                if count > 0:
                    reasons.append(f"{count} mutuals are interested")
            
            social_data[venue_id] = {
                "social_score": score,
                "friend_activity": ", ".join(reasons[:3]) # Top 3 reasons
            }
            
    return social_data

def create_friendship(user_id_a: str, user_id_b: str):
    query = """
    MERGE (a:User {id: $user_id_a})
    MERGE (b:User {id: $user_id_b})
    MERGE (a)-[:FRIENDS_WITH]->(b)
    """
    with driver.session() as session:
        session.run(query, user_id_a=user_id_a, user_id_b=user_id_b)

def log_interaction_to_graph(user_id: str, venue_id: str, interaction_type: str, weight: float):
    query = """
    MERGE (u:User {id: $user_id})
    MERGE (v:Venue {id: $venue_id})
    MERGE (u)-[r:INTERESTED_IN {type: $type}]->(v)
    SET r.weight = $weight, r.timestamp = datetime()
    """
    with driver.session() as session:
        session.run(query, user_id=user_id, venue_id=venue_id, type=interaction_type, weight=weight)
