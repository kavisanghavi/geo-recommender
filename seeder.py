import os
import random
from qdrant_client import QdrantClient, models
from neo4j import GraphDatabase
from faker import Faker

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

# Clients
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
fake = Faker()

# Constants
NUM_VENUES = 150
NUM_USERS = 200
NYC_LAT = 40.7128
NYC_LON = -74.0060

def seed_vectors():
    print("Seeding Qdrant...")
    try:
        qdrant.recreate_collection(
            collection_name="venues",
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
    except Exception as e:
        print(f"Collection might already exist or error: {e}")
    
    venues = []
    print(f"Generating {NUM_VENUES} venues...")
    for i in range(NUM_VENUES):
        venue_id = f"venue_{i}"
        vector = [random.random() for _ in range(1536)] # Mock embeddings
        
        category = random.choice(["bar", "restaurant", "club", "cafe", "park", "museum"])
        name = f"{fake.company()} {category.capitalize()}"
        
        # Random location within ~5km of NYC center
        lat = NYC_LAT + (random.random() - 0.5) * 0.1
        lon = NYC_LON + (random.random() - 0.5) * 0.1
        
        payload = {
            "venue_id": venue_id,
            "name": name,
            "description": fake.catch_phrase(),
            "category": category,
            "price_tier": random.randint(1, 4),
            "location": {
                "lat": lat,
                "lon": lon
            }
        }
        venues.append(models.PointStruct(id=i, vector=vector, payload=payload))
        
        if (i + 1) % 50 == 0:
            qdrant.upsert(collection_name="venues", points=venues)
            venues = []
            print(f"Upserted batch {i+1}")
            
    if venues:
        qdrant.upsert(collection_name="venues", points=venues)
    print("Seeded venues in Qdrant.")

def seed_graph():
    print("Seeding Neo4j...")
    with driver.session() as session:
        # Clear Users only (to preserve venues if we are just reseeding users)
        session.run("MATCH (u:User) DETACH DELETE u")
        
        # Create Users
        print(f"Creating {NUM_USERS} users...")
        
        interests_list = ["Italian", "Mexican", "Japanese", "Burgers", "Coffee", "Cocktails", "Jazz", "Techno", "Pop", "Rock", "Museums", "Parks", "Theater", "Sports"]
        
        user_data = []
        for i in range(NUM_USERS):
            # Pick 2-5 random interests
            user_interests = random.sample(interests_list, random.randint(2, 5))
            user_data.append({
                "id": f"user_{i}", 
                "name": fake.name(),
                "interests": user_interests
            })
            
        session.run("""
            UNWIND $users AS user
            CREATE (:User {id: user.id, name: user.name, interests: user.interests})
        """, users=user_data)
        
        # Create Friendships (Power Law / Preferential Attachmentish)
        print("Creating friendships...")
        # Simple logic: User 0 has many friends, User N has fewer
        for i in range(NUM_USERS):
            # Number of friends varies - reduced for sparser graph
            # expovariate(0.2) gives mean of 5
            num_friends = max(0, int(random.expovariate(0.2))) 
            num_friends = min(num_friends, 10) # Cap at 10 for this MVP
            
            friends = random.sample(range(NUM_USERS), num_friends)
            for friend_idx in friends:
                if friend_idx > i: # Only create edge if friend_idx > i to avoid duplicates
                    session.run("""
                        MATCH (a:User {id: $id_a}), (b:User {id: $id_b})
                        MERGE (a)-[:FRIENDS_WITH]->(b)
                    """, id_a=f"user_{i}", id_b=f"user_{friend_idx}")
        
        # Create Interactions
        print("Creating interactions...")
        for i in range(NUM_USERS):
            # Each user interacts with 5-15 venues
            num_interactions = random.randint(5, 15)
            venue_indices = random.sample(range(NUM_VENUES), num_interactions)
            
            for v_idx in venue_indices:
                interaction_type = random.choice(["viewed", "saved", "going"])
                weight = 0.2
                if interaction_type == "saved": weight = 1.0
                if interaction_type == "going": weight = 1.5
                
                session.run("""
                    MATCH (u:User {id: $u_id})
                    MERGE (v:Venue {id: $v_id})
                    MERGE (u)-[:INTERESTED_IN {type: $type, weight: $weight}]->(v)
                """, u_id=f"user_{i}", v_id=f"venue_{v_idx}", type=interaction_type, weight=weight)
        
    print("Seeded graph data.")

def clear_users():
    print("Clearing users from Neo4j...")
    with driver.session() as session:
        session.run("MATCH (u:User) DETACH DELETE u")
    print("Users cleared.")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--venues", action="store_true", help="Seed venues (clears existing)")
    parser.add_argument("--users", action="store_true", help="Seed users (clears existing users)")
    parser.add_argument("--clear-users", action="store_true", help="Only clear users (no seeding)")
    parser.add_argument("--all", action="store_true", help="Seed everything")
    args = parser.parse_args()

    if args.all or args.venues:
        seed_vectors()
    
    if args.clear_users:
        clear_users()
    elif args.all or args.users:
        seed_graph()
        
    if not (args.all or args.venues or args.users or args.clear_users):
        print("Please specify --venues, --users, --clear-users, or --all")
    
    driver.close()
