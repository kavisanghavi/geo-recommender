#!/usr/bin/env python3
"""
Enhanced NYC Seeder with Realistic Data & Engagement Simulation

This script generates:
1. 150 NYC venues across 10 neighborhoods with real coordinates
2. 200 users with interest-based embeddings
3. Simulated engagement patterns (watch times, shares, skips)
4. Social graph with realistic friendship clusters
"""

import os
import random
import time
from datetime import datetime, timedelta
from qdrant_client import QdrantClient, models
from neo4j import GraphDatabase
from faker import Faker

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = (os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Clients
qdrant = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
fake = Faker()

# Try to import OpenAI for real embeddings
USE_REAL_EMBEDDINGS = False
if OPENAI_API_KEY:
    try:
        from openai import OpenAI
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        USE_REAL_EMBEDDINGS = True
        print("✓ OpenAI API key found - will generate real embeddings")
    except ImportError:
        print("⚠ OpenAI library not installed - using mock embeddings")
else:
    print("⚠ No OpenAI API key - using mock embeddings")

# ============================================================================
# NYC NEIGHBORHOODS - Real Coordinates
# ============================================================================

NYC_NEIGHBORHOODS = [
    {
        "name": "Williamsburg",
        "lat": 40.7081,
        "lon": -73.9571,
        "vibes": ["hipster", "trendy", "artsy", "nightlife"],
        "venue_count": 25
    },
    {
        "name": "SoHo",
        "lat": 40.7233,
        "lon": -74.0030,
        "vibes": ["upscale", "artsy", "shopping", "trendy"],
        "venue_count": 20
    },
    {
        "name": "East Village",
        "lat": 40.7264,
        "lon": -73.9815,
        "vibes": ["bohemian", "diverse", "nightlife", "casual"],
        "venue_count": 20
    },
    {
        "name": "West Village",
        "lat": 40.7358,
        "lon": -74.0014,
        "vibes": ["charming", "cozy", "upscale", "quiet"],
        "venue_count": 15
    },
    {
        "name": "Bushwick",
        "lat": 40.6942,
        "lon": -73.9196,
        "vibes": ["edgy", "artsy", "warehouse", "underground"],
        "venue_count": 15
    },
    {
        "name": "Lower East Side",
        "lat": 40.7154,
        "lon": -73.9880,
        "vibes": ["historic", "dive bars", "eclectic", "nightlife"],
        "venue_count": 15
    },
    {
        "name": "Brooklyn Heights",
        "lat": 40.6958,
        "lon": -73.9936,
        "vibes": ["upscale", "quiet", "family-friendly", "scenic"],
        "venue_count": 10
    },
    {
        "name": "DUMBO",
        "lat": 40.7033,
        "lon": -73.9888,
        "vibes": ["waterfront", "modern", "scenic", "trendy"],
        "venue_count": 10
    },
    {
        "name": "Chelsea",
        "lat": 40.7465,
        "lon": -74.0014,
        "vibes": ["artsy", "gallery", "upscale", "diverse"],
        "venue_count": 10
    },
    {
        "name": "Greenpoint",
        "lat": 40.7304,
        "lon": -73.9517,
        "vibes": ["polish", "waterfront", "hipster", "quiet"],
        "venue_count": 10
    }
]

# ============================================================================
# VENUE TEMPLATES - Realistic NYC Venues
# ============================================================================

VENUE_TEMPLATES = {
    "rooftop_bar": {
        "names": ["Sky Lounge", "The Roof", "Cloud Bar", "Summit", "High Line Bar", "Skyview"],
        "descriptions": [
            "Rooftop bar with stunning Manhattan skyline views",
            "Outdoor terrace serving craft cocktails and small plates",
            "Panoramic views with DJ sets on weekends",
            "Seasonal rooftop with heated igloos in winter"
        ],
        "categories": ["bar", "rooftop", "cocktails"],
        "price_tier": [3, 4],
        "vibes": ["upscale", "trendy", "scenic"]
    },
    "jazz_club": {
        "names": ["Blue Note", "Jazz Standard", "Smalls", "Mezzrow", "Zinc Bar", "The Django"],
        "descriptions": [
            "Intimate jazz club featuring live performances nightly",
            "Classic jazz venue with acclaimed musicians",
            "Underground jazz spot with vintage ambiance",
            "Live music and craft cocktails in Greenwich Village"
        ],
        "categories": ["music", "jazz", "bar"],
        "price_tier": [2, 3],
        "vibes": ["cozy", "classic", "intimate"]
    },
    "cocktail_lounge": {
        "names": ["Dead Rabbit", "Employees Only", "Angel's Share", "PDT", "Attaboy", "Double Chicken"],
        "descriptions": [
            "Award-winning cocktail bar with Irish hospitality",
            "Speakeasy-style lounge with expert mixologists",
            "Hidden gem serving innovative cocktails",
            "Craft cocktails in an intimate setting"
        ],
        "categories": ["bar", "cocktails", "speakeasy"],
        "price_tier": [3, 4],
        "vibes": ["upscale", "intimate", "trendy"]
    },
    "wine_bar": {
        "names": ["Terroir", "Compagnie des Vins", "Amelie", "Bar Jamón", "Corkbuzz", "Vin Sur Vingt"],
        "descriptions": [
            "Natural wine bar with European small plates",
            "Extensive wine list and charcuterie",
            "Cozy wine bar with French bistro fare",
            "Wine education and tasting experiences"
        ],
        "categories": ["wine", "bar", "european"],
        "price_tier": [2, 3],
        "vibes": ["cozy", "romantic", "sophisticated"]
    },
    "coffee_shop": {
        "names": ["Blue Bottle", "Stumptown", "La Colombe", "Devoción", "Birch", "Variety"],
        "descriptions": [
            "Specialty coffee roaster with minimalist aesthetic",
            "Third-wave coffee and fresh pastries",
            "Direct-trade coffee in spacious setting",
            "Locally roasted coffee and light bites"
        ],
        "categories": ["cafe", "coffee", "breakfast"],
        "price_tier": [2, 3],
        "vibes": ["casual", "cozy", "hipster"]
    },
    "brunch_spot": {
        "names": ["Clinton St. Baking", "Sadelle's", "Jack's Wife Freda", "Buvette", "Balthazar", "The Smith"],
        "descriptions": [
            "Legendary brunch spot with famous pancakes",
            "All-day brunch and bagels in SoHo",
            "Mediterranean-inspired brunch favorites",
            "French bistro with weekend brunch"
        ],
        "categories": ["restaurant", "brunch", "american"],
        "price_tier": [2, 3],
        "vibes": ["casual", "popular", "instagram-worthy"]
    },
    "italian_restaurant": {
        "names": ["Carbone", "L'Artusi", "Via Carota", "Il Buco", "Don Angie", "Lilia"],
        "descriptions": [
            "Classic Italian-American with theatrical service",
            "Modern Italian with handmade pasta",
            "Rustic Italian trattoria in West Village",
            "Farm-to-table Italian in Brooklyn"
        ],
        "categories": ["restaurant", "italian", "pasta"],
        "price_tier": [3, 4],
        "vibes": ["romantic", "upscale", "date-night"]
    },
    "japanese_restaurant": {
        "names": ["Ippudo", "Totto Ramen", "Ichiran", "Sake Bar Hagi", "Sushi Nakazawa", "SUGARFISH"],
        "descriptions": [
            "Authentic ramen with rich tonkotsu broth",
            "Late-night ramen spot in Hell's Kitchen",
            "Individual booth ramen experience",
            "Omakase and premium sake selection"
        ],
        "categories": ["restaurant", "japanese", "ramen", "sushi"],
        "price_tier": [2, 3, 4],
        "vibes": ["authentic", "casual", "popular"]
    },
    "mexican_restaurant": {
        "names": ["Cosme", "Oxomoco", "Los Tacos No.1", "Empellón", "Casa Enrique", "La Contenta"],
        "descriptions": [
            "Modern Mexican with innovative cocktails",
            "Wood-fired Mexican in Greenpoint",
            "Authentic tacos al pastor from Tijuana",
            "Upscale Mexican with mezcal bar"
        ],
        "categories": ["restaurant", "mexican", "tacos"],
        "price_tier": [2, 3],
        "vibes": ["vibrant", "casual", "flavorful"]
    },
    "beer_garden": {
        "names": ["Radegast", "Spritzenhaus", "Studio Square", "Brooklyn Brewery", "Bohemian Hall", "Loreley"],
        "descriptions": [
            "Authentic German beer garden in Williamsburg",
            "Outdoor beer hall with communal tables",
            "Massive backyard with live music",
            "Craft brewery with tasting room tours"
        ],
        "categories": ["bar", "beer", "outdoor"],
        "price_tier": [1, 2],
        "vibes": ["casual", "social", "outdoor"]
    },
    "art_gallery": {
        "names": ["Gagosian", "David Zwirner", "Pace Gallery", "Hauser & Wirth", "Paula Cooper", "Metro Pictures"],
        "descriptions": [
            "Contemporary art gallery in Chelsea",
            "Rotating exhibitions by emerging artists",
            "Modern art gallery with global artists",
            "Avant-garde installations and performances"
        ],
        "categories": ["gallery", "art", "culture"],
        "price_tier": [1, 2],
        "vibes": ["artsy", "intellectual", "sophisticated"]
    },
    "music_venue": {
        "names": ["Bowery Ballroom", "Brooklyn Steel", "Music Hall of Williamsburg", "Elsewhere", "Mercury Lounge", "Rough Trade"],
        "descriptions": [
            "Iconic indie rock venue since 1929",
            "Large capacity venue with incredible sound",
            "Intimate shows from up-and-coming bands",
            "Multi-level club with rooftop bar"
        ],
        "categories": ["music", "concert", "nightlife"],
        "price_tier": [2, 3],
        "vibes": ["energetic", "underground", "trendy"]
    },
    "speakeasy": {
        "names": ["Please Don't Tell", "The Back Room", "Bathtub Gin", "Apotheke", "The Garret", "Little Branch"],
        "descriptions": [
            "Hidden bar behind a phone booth entrance",
            "Prohibition-era speakeasy with vintage decor",
            "Secret cocktail lounge in Chelsea",
            "Apothecary-themed bar with medicinal cocktails"
        ],
        "categories": ["bar", "speakeasy", "cocktails"],
        "price_tier": [3, 4],
        "vibes": ["hidden", "intimate", "exclusive"]
    },
    "bakery": {
        "names": ["Levain Bakery", "Dominique Ansel", "Breads Bakery", "Bien Cuit", "She Wolf", "Sullivan Street"],
        "descriptions": [
            "Famous for massive chocolate chip cookies",
            "Home of the Cronut and innovative pastries",
            "Artisan breads and babka daily",
            "Wood-fired breads and sourdough"
        ],
        "categories": ["bakery", "cafe", "dessert"],
        "price_tier": [2, 3],
        "vibes": ["cozy", "instagram-worthy", "sweet"]
    },
    "pizza_place": {
        "names": ["Di Fara", "Lucali", "Prince Street Pizza", "Roberta's", "Paulie Gee's", "L&B Spumoni"],
        "descriptions": [
            "Legendary pizza made by Dom since 1964",
            "BYOB pizzeria with fresh basil finishing",
            "Famous pepperoni square slices",
            "Wood-fired pizzas in Bushwick garden"
        ],
        "categories": ["restaurant", "pizza", "italian"],
        "price_tier": [1, 2],
        "vibes": ["casual", "authentic", "neighborhood"]
    },
    "korean_bbq": {
        "names": ["Kang Ho Dong Baekjeong", "Jongro BBQ", "Oiji Mi", "Miss Korea", "Cote", "Her Name is Han"],
        "descriptions": [
            "Upscale Korean BBQ with premium cuts",
            "Traditional Korean BBQ in K-town",
            "Modern Korean with tableside grilling",
            "Michelin-starred Korean steakhouse"
        ],
        "categories": ["restaurant", "korean", "bbq"],
        "price_tier": [3, 4],
        "vibes": ["social", "interactive", "flavorful"]
    }
}

# ============================================================================
# USER INTERESTS - Aligned with Venue Categories
# ============================================================================

USER_INTERESTS = {
    "nightlife_enthusiast": ["rooftop bars", "cocktails", "nightlife", "dancing", "DJs"],
    "foodie": ["fine dining", "brunch", "pasta", "ramen", "tacos", "pizza"],
    "music_lover": ["jazz", "live music", "concerts", "indie rock", "underground"],
    "coffee_culture": ["specialty coffee", "cafes", "breakfast", "pastries", "cozy spaces"],
    "wine_connoisseur": ["wine", "natural wine", "charcuterie", "European", "sophisticated"],
    "craft_beer_fan": ["craft beer", "beer gardens", "breweries", "outdoor seating"],
    "art_enthusiast": ["galleries", "contemporary art", "exhibitions", "culture", "museums"],
    "romantic": ["date night", "romantic", "intimate", "cozy", "candlelit"],
    "adventurous_eater": ["authentic", "international", "spicy", "experimental", "diverse"],
    "social_butterfly": ["group hangouts", "communal tables", "social", "vibrant", "popular"],
    "hidden_gem_seeker": ["speakeasy", "hidden", "exclusive", "secret", "unique"],
    "sweet_tooth": ["desserts", "pastries", "bakery", "ice cream", "sweet"]
}

# Generate personas (combinations of interests)
USER_PERSONAS = [
    {"archetype": "Nightlife Pro", "interests": ["rooftop bars", "cocktails", "nightlife", "DJs", "speakeasy"]},
    {"archetype": "Foodie Explorer", "interests": ["ramen", "tacos", "pizza", "authentic", "diverse"]},
    {"archetype": "Culture Vulture", "interests": ["jazz", "galleries", "wine", "sophisticated", "culture"]},
    {"archetype": "Coffee Snob", "interests": ["specialty coffee", "cafes", "pastries", "cozy spaces", "breakfast"]},
    {"archetype": "Beer Enthusiast", "interests": ["craft beer", "beer gardens", "outdoor seating", "casual", "social"]},
    {"archetype": "Romantic Date-Goer", "interests": ["date night", "romantic", "wine", "intimate", "fine dining"]},
    {"archetype": "Music Fanatic", "interests": ["live music", "concerts", "jazz", "indie rock", "underground"]},
    {"archetype": "Brunch Lover", "interests": ["brunch", "breakfast", "pastries", "coffee", "instagram-worthy"]},
    {"archetype": "Hidden Gem Hunter", "interests": ["speakeasy", "hidden", "exclusive", "cocktails", "unique"]},
    {"archetype": "Social Connector", "interests": ["group hangouts", "beer gardens", "vibrant", "popular", "social"]},
]

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def generate_embedding(text: str) -> list[float]:
    """Generate embedding using OpenAI or mock"""
    if USE_REAL_EMBEDDINGS:
        try:
            response = openai_client.embeddings.create(
                input=text,
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"⚠ OpenAI API error: {e}, falling back to mock")
            return [random.random() for _ in range(1536)]
    else:
        # Mock embeddings - still somewhat consistent
        random.seed(hash(text) % 2**32)
        embedding = [random.random() for _ in range(1536)]
        random.seed()  # Reset seed
        return embedding

def create_venue_description(template_key: str, name: str, neighborhood: dict) -> str:
    """Create rich venue description"""
    template = VENUE_TEMPLATES[template_key]
    desc = random.choice(template["descriptions"])
    vibes = ", ".join(random.sample(template["vibes"] + neighborhood["vibes"], 3))
    return f"{desc} in {neighborhood['name']}. Vibes: {vibes}."

# ============================================================================
# SEED VENUES
# ============================================================================

def seed_venues():
    """Seed realistic NYC venues with real embeddings"""
    print("\n" + "="*60)
    print("SEEDING NYC VENUES")
    print("="*60)

    try:
        qdrant.recreate_collection(
            collection_name="venues",
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print("✓ Created 'venues' collection in Qdrant")
    except Exception as e:
        print(f"⚠ Error creating collection: {e}")

    # Also create users collection for storing user vectors
    try:
        qdrant.recreate_collection(
            collection_name="users",
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print("✓ Created 'users' collection in Qdrant")
    except Exception as e:
        print(f"⚠ Error creating users collection: {e}")

    venue_id_counter = 0
    all_venues = []

    for neighborhood in NYC_NEIGHBORHOODS:
        print(f"\n📍 {neighborhood['name']} ({neighborhood['venue_count']} venues)")

        venues_to_create = neighborhood['venue_count']
        template_keys = list(VENUE_TEMPLATES.keys())

        for _ in range(venues_to_create):
            # Pick random template
            template_key = random.choice(template_keys)
            template = VENUE_TEMPLATES[template_key]

            # Generate venue
            venue_id = f"venue_{venue_id_counter}"
            name = random.choice(template["names"]) + " " + neighborhood['name'].split()[0]
            description = create_venue_description(template_key, name, neighborhood)

            # Coordinates within neighborhood (±0.005 degrees ≈ 500m radius)
            lat = neighborhood["lat"] + (random.random() - 0.5) * 0.01
            lon = neighborhood["lon"] + (random.random() - 0.5) * 0.01

            # Generate embedding from description + categories
            embedding_text = f"{name}. {description}. Categories: {', '.join(template['categories'])}"
            vector = generate_embedding(embedding_text)

            # Mock video URL (using Unsplash for realistic images)
            video_url = f"https://images.unsplash.com/photo-{random.randint(1000000000000, 9999999999999)}"

            payload = {
                "venue_id": venue_id,
                "name": name,
                "description": description,
                "categories": template["categories"],
                "price_tier": random.choice(template["price_tier"]),
                "neighborhood": neighborhood["name"],
                "vibes": template["vibes"],
                "location": {
                    "lat": lat,
                    "lon": lon
                },
                "video_url": video_url
            }

            all_venues.append(models.PointStruct(
                id=venue_id_counter,
                vector=vector,
                payload=payload
            ))

            venue_id_counter += 1

            if venue_id_counter % 10 == 0:
                print(f"  Generated {venue_id_counter} venues...")

    # Batch upload
    print(f"\n⬆️  Uploading {len(all_venues)} venues to Qdrant...")
    batch_size = 50
    for i in range(0, len(all_venues), batch_size):
        batch = all_venues[i:i + batch_size]
        qdrant.upsert(collection_name="venues", points=batch)
        print(f"  Uploaded batch {i//batch_size + 1}/{(len(all_venues)-1)//batch_size + 1}")

    print(f"\n✅ Seeded {len(all_venues)} venues across {len(NYC_NEIGHBORHOODS)} neighborhoods")
    return len(all_venues)

# ============================================================================
# SEED USERS
# ============================================================================

def seed_users(num_users: int = 200):
    """Seed users with realistic personas and embeddings"""
    print("\n" + "="*60)
    print(f"SEEDING {num_users} USERS")
    print("="*60)

    with driver.session() as session:
        # Clear existing users
        session.run("MATCH (u:User) DETACH DELETE u")
        print("✓ Cleared existing users")

        user_data = []
        user_vectors = []

        for i in range(num_users):
            # Assign persona (with some randomness)
            persona = random.choice(USER_PERSONAS)

            # Optionally add 1-2 extra random interests
            interests = persona["interests"].copy()
            all_interests = [item for sublist in USER_INTERESTS.values() for item in sublist]
            extra = random.sample(all_interests, random.randint(0, 2))
            interests.extend(extra)
            interests = list(set(interests))  # Remove duplicates

            user_id = f"user_{i}"
            name = fake.name()

            # Generate user embedding from interests
            interests_text = " ".join(interests)
            user_vector = generate_embedding(interests_text)

            user_data.append({
                "id": user_id,
                "name": name,
                "interests": interests,
                "archetype": persona["archetype"]
            })

            user_vectors.append(models.PointStruct(
                id=i,
                vector=user_vector,
                payload={
                    "user_id": user_id,
                    "name": name,
                    "interests": interests
                }
            ))

            if (i + 1) % 50 == 0:
                print(f"  Generated {i + 1} users...")

        # Create users in Neo4j
        print("\n⬆️  Creating users in Neo4j...")
        session.run("""
            UNWIND $users AS user
            CREATE (:User {
                id: user.id,
                name: user.name,
                interests: user.interests,
                archetype: user.archetype
            })
        """, users=user_data)

        # Upload user vectors to Qdrant
        print("⬆️  Uploading user vectors to Qdrant...")
        batch_size = 50
        for i in range(0, len(user_vectors), batch_size):
            batch = user_vectors[i:i + batch_size]
            qdrant.upsert(collection_name="users", points=batch)

        print(f"\n✅ Seeded {num_users} users with interest-based embeddings")
        return user_data

# ============================================================================
# SEED SOCIAL GRAPH
# ============================================================================

def seed_friendships(user_data: list, avg_friends: int = 8):
    """Create realistic friendship clusters"""
    print("\n" + "="*60)
    print("CREATING SOCIAL GRAPH")
    print("="*60)

    num_users = len(user_data)

    with driver.session() as session:
        friendships_created = 0

        # Strategy: Users with similar archetypes are more likely to be friends
        archetype_groups = {}
        for user in user_data:
            archetype = user["archetype"]
            if archetype not in archetype_groups:
                archetype_groups[archetype] = []
            archetype_groups[archetype].append(user["id"])

        for i, user in enumerate(user_data):
            user_id = user["id"]
            archetype = user["archetype"]

            # 60% chance friends from same archetype, 40% random
            num_friends = max(2, int(random.expovariate(1/avg_friends)))
            num_friends = min(num_friends, 15)  # Cap at 15

            same_archetype_count = int(num_friends * 0.6)
            random_count = num_friends - same_archetype_count

            friends = []

            # Same archetype friends
            same_archetype_pool = [u for u in archetype_groups.get(archetype, []) if u != user_id]
            if same_archetype_pool:
                friends.extend(random.sample(
                    same_archetype_pool,
                    min(same_archetype_count, len(same_archetype_pool))
                ))

            # Random friends
            all_other_users = [u["id"] for u in user_data if u["id"] != user_id and u["id"] not in friends]
            if all_other_users:
                friends.extend(random.sample(
                    all_other_users,
                    min(random_count, len(all_other_users))
                ))

            # Create friendships (bidirectional)
            for friend_id in friends:
                # Only create if friend_id > user_id to avoid duplicates
                if friend_id > user_id:
                    session.run("""
                        MATCH (a:User {id: $user_a}), (b:User {id: $user_b})
                        MERGE (a)-[:FRIENDS_WITH]->(b)
                        MERGE (b)-[:FRIENDS_WITH]->(a)
                    """, user_a=user_id, user_b=friend_id)
                    friendships_created += 1

            if (i + 1) % 50 == 0:
                print(f"  Processed {i + 1} users...")

        print(f"\n✅ Created {friendships_created} bidirectional friendships")

# ============================================================================
# SIMULATE ENGAGEMENT
# ============================================================================

def simulate_engagement(user_data: list, num_venues: int, interactions_per_user: int = 30):
    """Simulate realistic watch patterns, shares, saves, skips"""
    print("\n" + "="*60)
    print("SIMULATING ENGAGEMENT PATTERNS")
    print("="*60)

    engagement_types = {
        "skip": {"weight": -0.5, "watch_time_range": (0, 3)},
        "brief_view": {"weight": 0.3, "watch_time_range": (3, 10)},
        "engaged_view": {"weight": 1.0, "watch_time_range": (10, 30)},
        "full_view": {"weight": 2.0, "watch_time_range": (30, 60)},
        "save": {"weight": 1.5, "watch_time_range": (15, 60)},
        "share": {"weight": 3.0, "watch_time_range": (20, 60)},
    }

    with driver.session() as session:
        total_interactions = 0

        for i, user in enumerate(user_data):
            user_id = user["id"]

            # Each user interacts with venues
            venue_indices = random.sample(range(num_venues), min(interactions_per_user, num_venues))

            for v_idx in venue_indices:
                venue_id = f"venue_{v_idx}"

                # Determine engagement type (weighted probabilities)
                engagement_dist = [
                    ("skip", 0.20),          # 20% skip
                    ("brief_view", 0.25),    # 25% brief
                    ("engaged_view", 0.30),  # 30% engaged
                    ("full_view", 0.15),     # 15% full watch
                    ("save", 0.07),          # 7% save
                    ("share", 0.03),         # 3% share (strongest signal)
                ]

                engagement_type = random.choices(
                    [e[0] for e in engagement_dist],
                    weights=[e[1] for e in engagement_dist]
                )[0]

                config = engagement_types[engagement_type]
                watch_time = random.randint(*config["watch_time_range"])
                weight = config["weight"]

                # Determine action type for Neo4j
                if engagement_type == "share":
                    action_type = "shared"
                elif engagement_type == "save":
                    action_type = "saved"
                elif engagement_type == "skip":
                    action_type = "skipped"
                else:
                    action_type = "viewed"

                # Create timestamp (random within last 30 days)
                days_ago = random.randint(0, 30)
                timestamp = datetime.now() - timedelta(days=days_ago)

                # Log to Neo4j
                session.run("""
                    MATCH (u:User {id: $user_id})
                    MERGE (v:Venue {id: $venue_id})
                    MERGE (u)-[r:ENGAGED_WITH {timestamp: datetime($timestamp)}]->(v)
                    SET r.type = $type,
                        r.watch_time = $watch_time,
                        r.weight = $weight
                """,
                    user_id=user_id,
                    venue_id=venue_id,
                    type=action_type,
                    watch_time=watch_time,
                    weight=weight,
                    timestamp=timestamp.isoformat()
                )

                total_interactions += 1

                # Handle shares - create viral spread
                if engagement_type == "share":
                    # Get user's friends
                    friends_result = session.run("""
                        MATCH (u:User {id: $user_id})-[:FRIENDS_WITH]->(f:User)
                        RETURN f.id as friend_id
                        LIMIT 5
                    """, user_id=user_id)

                    friends = [r["friend_id"] for r in friends_result]

                    if friends:
                        # Share with 1-3 friends
                        shared_with = random.sample(friends, min(random.randint(1, 3), len(friends)))

                        for friend_id in shared_with:
                            session.run("""
                                MATCH (u:User {id: $user_id}), (f:User {id: $friend_id})
                                MERGE (v:Venue {id: $venue_id})
                                MERGE (u)-[:SHARED_WITH {timestamp: datetime($timestamp)}]->(f)
                                MERGE (f)-[:RECEIVED_SHARE {from: $user_id, timestamp: datetime($timestamp)}]->(v)
                            """,
                                user_id=user_id,
                                friend_id=friend_id,
                                venue_id=venue_id,
                                timestamp=timestamp.isoformat()
                            )

            if (i + 1) % 50 == 0:
                print(f"  Simulated engagement for {i + 1} users ({total_interactions} interactions)...")

        print(f"\n✅ Created {total_interactions} engagement records")

        # Print engagement breakdown
        breakdown = session.run("""
            MATCH ()-[r:ENGAGED_WITH]->()
            RETURN r.type as type, count(*) as count
            ORDER BY count DESC
        """)

        print("\n📊 Engagement Breakdown:")
        for record in breakdown:
            print(f"   {record['type']}: {record['count']}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enhanced NYC Seeder")
    parser.add_argument("--venues", action="store_true", help="Seed venues")
    parser.add_argument("--users", action="store_true", help="Seed users")
    parser.add_argument("--friends", action="store_true", help="Seed friendships")
    parser.add_argument("--engagement", action="store_true", help="Simulate engagement")
    parser.add_argument("--all", action="store_true", help="Seed everything")
    parser.add_argument("--num-users", type=int, default=200, help="Number of users to create")
    parser.add_argument("--interactions-per-user", type=int, default=30, help="Avg interactions per user")

    args = parser.parse_args()

    start_time = time.time()

    num_venues = 0
    user_data = []

    if args.all or args.venues:
        num_venues = seed_venues()

    if args.all or args.users:
        user_data = seed_users(args.num_users)

    if args.all or args.friends:
        if not user_data:
            # Load existing users
            with driver.session() as session:
                result = session.run("""
                    MATCH (u:User)
                    RETURN u.id as id, u.name as name, u.interests as interests, u.archetype as archetype
                """)
                user_data = [dict(r) for r in result]
        seed_friendships(user_data)

    if args.all or args.engagement:
        if not user_data:
            # Load existing users
            with driver.session() as session:
                result = session.run("""
                    MATCH (u:User)
                    RETURN u.id as id, u.name as name, u.interests as interests, u.archetype as archetype
                """)
                user_data = [dict(r) for r in result]

        if num_venues == 0:
            # Get venue count from Qdrant
            collection_info = qdrant.get_collection("venues")
            num_venues = collection_info.points_count

        simulate_engagement(user_data, num_venues, args.interactions_per_user)

    if not (args.all or args.venues or args.users or args.friends or args.engagement):
        print("Usage: python seeder_enhanced.py [--all] [--venues] [--users] [--friends] [--engagement]")
        print("\nOptions:")
        print("  --all                    Seed everything")
        print("  --venues                 Seed NYC venues")
        print("  --users                  Seed users with personas")
        print("  --friends                Create social graph")
        print("  --engagement             Simulate watch patterns")
        print("  --num-users N            Number of users (default: 200)")
        print("  --interactions-per-user N  Avg interactions per user (default: 30)")

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f}s")

    driver.close()
