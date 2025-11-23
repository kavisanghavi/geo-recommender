#!/usr/bin/env python3
"""
Video-Centric NYC Seeder - Short Video/Reels for Local Businesses

This script generates:
1. 150 NYC venues (businesses) across 10 neighborhoods
2. 3-5 videos per venue (businesses are content creators)
3. 10-15 users with clear personas (manageable for demos)
4. Video-level engagement (watches, saves, shares)
5. Social graph with realistic friendships
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
    {"name": "Williamsburg", "lat": 40.7081, "lon": -73.9571, "vibes": ["hipster", "trendy", "artsy", "nightlife"], "venue_count": 25},
    {"name": "SoHo", "lat": 40.7233, "lon": -74.0030, "vibes": ["upscale", "artsy", "shopping", "trendy"], "venue_count": 20},
    {"name": "East Village", "lat": 40.7264, "lon": -73.9815, "vibes": ["bohemian", "diverse", "nightlife", "casual"], "venue_count": 20},
    {"name": "West Village", "lat": 40.7358, "lon": -74.0014, "vibes": ["charming", "cozy", "upscale", "quiet"], "venue_count": 15},
    {"name": "Bushwick", "lat": 40.6942, "lon": -73.9196, "vibes": ["edgy", "artsy", "warehouse", "underground"], "venue_count": 15},
    {"name": "Lower East Side", "lat": 40.7154, "lon": -73.9880, "vibes": ["historic", "dive bars", "eclectic", "nightlife"], "venue_count": 15},
    {"name": "Brooklyn Heights", "lat": 40.6958, "lon": -73.9936, "vibes": ["upscale", "quiet", "family-friendly", "scenic"], "venue_count": 10},
    {"name": "DUMBO", "lat": 40.7033, "lon": -73.9888, "vibes": ["waterfront", "modern", "scenic", "trendy"], "venue_count": 10},
    {"name": "Chelsea", "lat": 40.7465, "lon": -74.0014, "vibes": ["artsy", "gallery", "upscale", "diverse"], "venue_count": 10},
    {"name": "Greenpoint", "lat": 40.7304, "lon": -73.9517, "vibes": ["polish", "waterfront", "hipster", "quiet"], "venue_count": 10}
]

# ============================================================================
# VENUE TEMPLATES & VIDEO CONTENT TYPES
# ============================================================================

VENUE_TEMPLATES = {
    "jazz_club": {
        "names": ["Blue Note", "Jazz Standard", "Smalls", "Mezzrow", "Zinc Bar"],
        "descriptions": ["Intimate jazz club featuring live performances nightly", "Classic jazz venue with acclaimed musicians"],
        "categories": ["music", "jazz", "bar"],
        "price_tier": [2, 3],
        "vibes": ["cozy", "classic", "intimate"]
    },
    "cocktail_lounge": {
        "names": ["Dead Rabbit", "Employees Only", "Angel's Share", "PDT", "Attaboy"],
        "descriptions": ["Award-winning cocktail bar", "Speakeasy-style lounge with expert mixologists"],
        "categories": ["bar", "cocktails", "speakeasy"],
        "price_tier": [3, 4],
        "vibes": ["upscale", "intimate", "trendy"]
    },
    "coffee_shop": {
        "names": ["Blue Bottle", "Stumptown", "La Colombe", "Devoción", "Birch"],
        "descriptions": ["Specialty coffee roaster with minimalist aesthetic", "Third-wave coffee and fresh pastries"],
        "categories": ["cafe", "coffee", "breakfast"],
        "price_tier": [2, 3],
        "vibes": ["casual", "cozy", "hipster"]
    },
    "italian_restaurant": {
        "names": ["Carbone", "L'Artusi", "Via Carota", "Il Buco", "Lilia"],
        "descriptions": ["Modern Italian with handmade pasta", "Rustic Italian trattoria"],
        "categories": ["restaurant", "italian", "pasta"],
        "price_tier": [3, 4],
        "vibes": ["romantic", "upscale", "date-night"]
    },
    "pizza_place": {
        "names": ["Di Fara", "Lucali", "Prince Street", "Roberta's", "Paulie Gee's"],
        "descriptions": ["Wood-fired pizzas in Brooklyn garden", "Famous pepperoni square slices"],
        "categories": ["restaurant", "pizza", "italian"],
        "price_tier": [1, 2],
        "vibes": ["casual", "authentic", "neighborhood"]
    },
    "brunch_spot": {
        "names": ["Clinton St. Baking", "Sadelle's", "Jack's Wife Freda", "Buvette", "The Smith"],
        "descriptions": ["Legendary brunch spot with famous pancakes", "Mediterranean-inspired brunch favorites"],
        "categories": ["restaurant", "brunch", "american"],
        "price_tier": [2, 3],
        "vibes": ["casual", "popular", "instagram-worthy"]
    },
    "art_gallery": {
        "names": ["Gagosian", "David Zwirner", "Pace Gallery", "Paula Cooper", "Metro Pictures"],
        "descriptions": ["Contemporary art gallery", "Rotating exhibitions by emerging artists"],
        "categories": ["gallery", "art", "culture"],
        "price_tier": [1, 2],
        "vibes": ["artsy", "intellectual", "sophisticated"]
    },
    "bakery": {
        "names": ["Levain Bakery", "Dominique Ansel", "Breads Bakery", "Bien Cuit", "She Wolf"],
        "descriptions": ["Famous for massive chocolate chip cookies", "Home of innovative pastries"],
        "categories": ["bakery", "cafe", "dessert"],
        "price_tier": [2, 3],
        "vibes": ["cozy", "instagram-worthy", "sweet"]
    },
    "ramen_shop": {
        "names": ["Ippudo", "Totto Ramen", "Ichiran", "Hide-Chan", "Ivan Ramen"],
        "descriptions": ["Authentic ramen with rich tonkotsu broth", "Late-night ramen spot"],
        "categories": ["restaurant", "japanese", "ramen"],
        "price_tier": [2, 3],
        "vibes": ["authentic", "casual", "popular"]
    },
    "beer_garden": {
        "names": ["Radegast", "Spritzenhaus", "Brooklyn Brewery", "Bohemian Hall", "Loreley"],
        "descriptions": ["Authentic German beer garden", "Craft brewery with tasting room"],
        "categories": ["bar", "beer", "outdoor"],
        "price_tier": [1, 2],
        "vibes": ["casual", "social", "outdoor"]
    }
}

# Video content types that venues can post
VIDEO_TYPES = {
    "live_event": {
        "templates": [
            "Live {genre} Tonight at {time}!",
            "Join us for {event_name} - {day} nights",
            "Special performance: {artist_type} at {venue}",
            "Weekly {event_type} - Every {day}"
        ],
        "descriptions": [
            "Don't miss out on tonight's special performance!",
            "Reserve your spot for an unforgettable night",
            "Experience live entertainment in an intimate setting",
            "Join the crowd for our signature event"
        ],
        "valid_days": 7  # Valid for next 7 days
    },
    "new_menu": {
        "templates": [
            "New {season} Menu Just Dropped!",
            "Chef's Special: {dish_name}",
            "Try Our New {item_type}",
            "Limited Time: {seasonal_item}"
        ],
        "descriptions": [
            "Our chef has been experimenting with seasonal ingredients",
            "Fresh takes on classic favorites",
            "You won't want to miss this limited offering",
            "Crafted with locally sourced ingredients"
        ],
        "valid_days": 30
    },
    "ambiance": {
        "templates": [
            "Cozy Corner Vibes at {venue}",
            "The Perfect Spot for {occasion}",
            "Weekend Mornings at {venue}",
            "{time_of_day} Atmosphere You'll Love"
        ],
        "descriptions": [
            "See why locals love this hidden gem",
            "The vibe speaks for itself",
            "Your new favorite neighborhood spot",
            "Where good times and great people meet"
        ],
        "valid_days": 365  # Evergreen content
    },
    "behind_scenes": {
        "templates": [
            "Behind the Scenes: {process}",
            "How We Make Our {signature_item}",
            "Meet the Team at {venue}",
            "A Day in the Life at {venue}"
        ],
        "descriptions": [
            "Get to know the people behind your favorite spot",
            "See the craft and care that goes into everything we do",
            "We're pulling back the curtain",
            "Authenticity you can taste"
        ],
        "valid_days": 90
    },
    "special_offer": {
        "templates": [
            "Happy Hour: {discount} Off {items}!",
            "{day} Special: {offer}",
            "Limited Time: {promotion}",
            "Early Bird Special - {time_range}"
        ],
        "descriptions": [
            "Don't miss out on this exclusive deal",
            "Best value in the neighborhood",
            "Treat yourself without breaking the bank",
            "Share with friends and save even more"
        ],
        "valid_days": 14
    }
}

# ============================================================================
# USER PERSONAS (10-15 users with distinct personalities)
# ============================================================================

USER_PERSONAS = [
    {"name": "Sarah Chen", "archetype": "Jazz & Wine Lover", "interests": ["jazz", "wine", "galleries", "intimate", "sophisticated"]},
    {"name": "Mike Rodriguez", "archetype": "Pizza & Beer Guy", "interests": ["pizza", "beer", "sports bars", "casual", "neighborhood"]},
    {"name": "Lisa Kim", "archetype": "Brunch Enthusiast", "interests": ["brunch", "coffee", "pastries", "instagram-worthy", "breakfast"]},
    {"name": "James Wilson", "archetype": "Cocktail Connoisseur", "interests": ["cocktails", "speakeasy", "upscale", "mixology", "trendy"]},
    {"name": "Emma Thompson", "archetype": "Art & Culture", "interests": ["galleries", "art", "culture", "intellectual", "exhibitions"]},
    {"name": "David Park", "archetype": "Foodie Explorer", "interests": ["ramen", "authentic", "diverse", "experimental", "international"]},
    {"name": "Rachel Green", "archetype": "Social Butterfly", "interests": ["rooftop bars", "nightlife", "social", "popular", "vibrant"]},
    {"name": "Tom Anderson", "archetype": "Coffee Snob", "interests": ["specialty coffee", "cafes", "cozy spaces", "hipster", "third-wave"]},
    {"name": "Nina Patel", "archetype": "Sweet Tooth", "interests": ["bakery", "dessert", "pastries", "sweet", "instagram-worthy"]},
    {"name": "Chris Martinez", "archetype": "Live Music Fan", "interests": ["live music", "concerts", "jazz", "indie", "underground"]},
    {"name": "Amanda White", "archetype": "Romantic Date-Goer", "interests": ["date night", "romantic", "intimate", "italian", "wine"]},
    {"name": "Kevin Nguyen", "archetype": "Hidden Gem Hunter", "interests": ["speakeasy", "hidden", "exclusive", "unique", "off-the-beaten-path"]},
    {"name": "Sophie Martinez", "archetype": "Neighborhood Regular", "interests": ["casual", "neighborhood", "cozy", "authentic", "friendly"]}
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

def generate_video_content(venue_name: str, venue_categories: list, video_type: str) -> dict:
    """Generate video title and description based on type"""
    video_config = VIDEO_TYPES[video_type]

    template = random.choice(video_config["templates"])
    description = random.choice(video_config["descriptions"])

    # Fill in template variables
    replacements = {
        "{venue}": venue_name,
        "{genre}": random.choice(["Jazz", "Blues", "Soul", "Acoustic"]),
        "{time}": random.choice(["8pm", "9pm", "7:30pm"]),
        "{event_name}": random.choice(["Open Mic Night", "Trivia Tuesday", "Wine Tasting"]),
        "{day}": random.choice(["Thursday", "Friday", "Saturday", "Tuesday"]),
        "{artist_type}": random.choice(["local artists", "emerging talent", "acclaimed musicians"]),
        "{event_type}": random.choice(["Live Music", "Comedy Night", "DJ Set"]),
        "{season}": random.choice(["Fall", "Winter", "Spring", "Summer"]),
        "{dish_name}": random.choice(["Truffle Pasta", "Wagyu Burger", "Seasonal Risotto"]),
        "{item_type}": random.choice(["Cocktail Menu", "Brunch Items", "Desserts"]),
        "{seasonal_item}": random.choice(["Pumpkin Spice Latte", "Summer Sangria", "Holiday Cookie"]),
        "{occasion}": random.choice(["Date Night", "Catching Up", "Weekend Brunch"]),
        "{time_of_day}": random.choice(["Morning", "Evening", "Afternoon", "Late Night"]),
        "{process}": random.choice(["Making Fresh Pasta", "Roasting Coffee", "Crafting Cocktails"]),
        "{signature_item}": random.choice(["Famous Pizza", "Signature Cocktail", "House Special"]),
        "{discount}": random.choice(["20%", "30%", "50%"]),
        "{items}": random.choice(["All Drinks", "Select Appetizers", "Wine & Beer"]),
        "{offer}": random.choice(["2-for-1 Drinks", "Free Appetizer", "$5 Cocktails"]),
        "{promotion}": random.choice(["Buy One Get One", "Happy Hour Extended", "Student Discount"]),
        "{time_range}": random.choice(["4-6pm", "5-7pm", "Before 7pm"])
    }

    title = template
    for placeholder, value in replacements.items():
        title = title.replace(placeholder, value)

    return {
        "title": title,
        "description": description,
        "video_type": video_type,
        "valid_days": video_config["valid_days"]
    }

# ============================================================================
# SEED VENUES & VIDEOS
# ============================================================================

def seed_venues_and_videos():
    """Seed venues and their videos"""
    print("\n" + "="*60)
    print("SEEDING NYC VENUES & VIDEOS")
    print("="*60)

    # Recreate Qdrant collections
    try:
        qdrant.recreate_collection(
            collection_name="videos",
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print("✓ Created 'videos' collection in Qdrant")
    except Exception as e:
        print(f"⚠ Error creating videos collection: {e}")

    try:
        qdrant.recreate_collection(
            collection_name="users",
            vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE)
        )
        print("✓ Created 'users' collection in Qdrant")
    except Exception as e:
        print(f"⚠ Error creating users collection: {e}")

    # Clear Neo4j
    with driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        print("✓ Cleared Neo4j database")

    venue_id_counter = 0
    video_id_counter = 0
    all_videos = []

    # Create video type distribution
    video_type_weights = {
        "ambiance": 0.3,
        "new_menu": 0.25,
        "live_event": 0.2,
        "behind_scenes": 0.15,
        "special_offer": 0.1
    }

    for neighborhood in NYC_NEIGHBORHOODS:
        print(f"\n📍 {neighborhood['name']} ({neighborhood['venue_count']} venues)")

        template_keys = list(VENUE_TEMPLATES.keys())

        for _ in range(neighborhood['venue_count']):
            # Create venue
            template_key = random.choice(template_keys)
            template = VENUE_TEMPLATES[template_key]

            venue_id = f"venue_{venue_id_counter}"
            venue_name = random.choice(template["names"]) + " " + neighborhood['name'].split()[0]
            venue_description = random.choice(template["descriptions"]) + f" in {neighborhood['name']}"

            # Coordinates within neighborhood
            lat = neighborhood["lat"] + (random.random() - 0.5) * 0.01
            lon = neighborhood["lon"] + (random.random() - 0.5) * 0.01

            # Create venue in Neo4j
            with driver.session() as session:
                session.run("""
                    CREATE (v:Venue {
                        id: $venue_id,
                        name: $name,
                        description: $description,
                        categories: $categories,
                        price_tier: $price_tier,
                        neighborhood: $neighborhood,
                        lat: $lat,
                        lon: $lon
                    })
                """,
                    venue_id=venue_id,
                    name=venue_name,
                    description=venue_description,
                    categories=template["categories"],
                    price_tier=random.choice(template["price_tier"]),
                    neighborhood=neighborhood["name"],
                    lat=lat,
                    lon=lon
                )

            # Create 3-5 videos for this venue
            num_videos = random.randint(3, 5)

            for vid_idx in range(num_videos):
                video_type = random.choices(
                    list(video_type_weights.keys()),
                    weights=list(video_type_weights.values())
                )[0]

                video_content = generate_video_content(venue_name, template["categories"], video_type)
                video_id = f"video_{video_id_counter}"

                # Video created some time in the last 30 days
                days_old = random.randint(0, 30)
                created_at = datetime.now() - timedelta(days=days_old)
                valid_until = created_at + timedelta(days=video_content["valid_days"])

                # Generate embedding from video content
                embedding_text = f"{video_content['title']}. {video_content['description']}. At {venue_name}. Categories: {', '.join(template['categories'])}"
                vector = generate_embedding(embedding_text)

                # Gradient for visual variety
                gradients = [
                    "from-purple-500 to-pink-500",
                    "from-blue-500 to-cyan-500",
                    "from-green-500 to-emerald-500",
                    "from-orange-500 to-red-500",
                    "from-indigo-500 to-purple-500",
                    "from-yellow-500 to-orange-500"
                ]

                payload = {
                    "video_id": video_id,
                    "venue_id": venue_id,
                    "venue_name": venue_name,
                    "title": video_content["title"],
                    "description": video_content["description"],
                    "video_type": video_content["video_type"],
                    "created_at": created_at.isoformat(),
                    "valid_until": valid_until.isoformat(),
                    "categories": template["categories"],
                    "neighborhood": neighborhood["name"],
                    "price_tier": random.choice(template["price_tier"]),
                    "location": {"lat": lat, "lon": lon},
                    "gradient": random.choice(gradients)
                }

                all_videos.append(models.PointStruct(
                    id=video_id_counter,
                    vector=vector,
                    payload=payload
                ))

                # Create video in Neo4j
                with driver.session() as session:
                    session.run("""
                        MATCH (v:Venue {id: $venue_id})
                        CREATE (vid:Video {
                            id: $video_id,
                            title: $title,
                            description: $description,
                            video_type: $video_type,
                            created_at: datetime($created_at),
                            valid_until: datetime($valid_until)
                        })
                        CREATE (v)-[:POSTED]->(vid)
                    """,
                        venue_id=venue_id,
                        video_id=video_id,
                        title=video_content["title"],
                        description=video_content["description"],
                        video_type=video_content["video_type"],
                        created_at=created_at.isoformat(),
                        valid_until=valid_until.isoformat()
                    )

                video_id_counter += 1

            venue_id_counter += 1

            if venue_id_counter % 10 == 0:
                print(f"  Generated {venue_id_counter} venues with {video_id_counter} videos...")

    # Batch upload videos to Qdrant
    print(f"\n⬆️  Uploading {len(all_videos)} videos to Qdrant...")
    batch_size = 50
    for i in range(0, len(all_videos), batch_size):
        batch = all_videos[i:i + batch_size]
        qdrant.upsert(collection_name="videos", points=batch)
        print(f"  Uploaded batch {i//batch_size + 1}/{(len(all_videos)-1)//batch_size + 1}")

    print(f"\n✅ Seeded {venue_id_counter} venues with {video_id_counter} videos")
    return venue_id_counter, video_id_counter

# ============================================================================
# SEED USERS
# ============================================================================

def seed_users():
    """Seed 10-15 users with distinct personas"""
    print("\n" + "="*60)
    print(f"SEEDING {len(USER_PERSONAS)} USERS")
    print("="*60)

    user_vectors = []

    with driver.session() as session:
        for i, persona in enumerate(USER_PERSONAS):
            user_id = f"user_{i}"

            # Generate user embedding from interests
            interests_text = " ".join(persona["interests"])
            user_vector = generate_embedding(interests_text)

            # Create user in Neo4j
            session.run("""
                CREATE (u:User {
                    id: $user_id,
                    name: $name,
                    interests: $interests,
                    archetype: $archetype
                })
            """,
                user_id=user_id,
                name=persona["name"],
                interests=persona["interests"],
                archetype=persona["archetype"]
            )

            user_vectors.append(models.PointStruct(
                id=i,
                vector=user_vector,
                payload={
                    "user_id": user_id,
                    "name": persona["name"],
                    "interests": persona["interests"]
                }
            ))

            print(f"  ✓ Created {persona['name']} ({persona['archetype']})")

    # Upload user vectors to Qdrant
    print("\n⬆️  Uploading user vectors to Qdrant...")
    qdrant.upsert(collection_name="users", points=user_vectors)

    print(f"\n✅ Seeded {len(USER_PERSONAS)} users")
    return USER_PERSONAS

# ============================================================================
# SEED FRIENDSHIPS
# ============================================================================

def seed_friendships(user_data: list):
    """Create friendships - each user has 3-5 friends"""
    print("\n" + "="*60)
    print("CREATING SOCIAL GRAPH")
    print("="*60)

    num_users = len(user_data)
    friendships_created = 0

    with driver.session() as session:
        for i, user in enumerate(user_data):
            user_id = f"user_{i}"

            # Each user gets 3-5 friends
            num_friends = random.randint(3, 5)

            # Avoid self-friendship
            possible_friends = [j for j in range(num_users) if j != i]
            friend_indices = random.sample(possible_friends, min(num_friends, len(possible_friends)))

            for friend_idx in friend_indices:
                friend_id = f"user_{friend_idx}"

                # Only create if user_id < friend_id to avoid duplicates
                if user_id < friend_id:
                    session.run("""
                        MATCH (a:User {id: $user_a}), (b:User {id: $user_b})
                        MERGE (a)-[:FRIENDS_WITH]->(b)
                        MERGE (b)-[:FRIENDS_WITH]->(a)
                    """, user_a=user_id, user_b=friend_id)
                    friendships_created += 1

        print(f"\n✅ Created {friendships_created} bidirectional friendships")

        # Print friend summary
        result = session.run("""
            MATCH (u:User)
            OPTIONAL MATCH (u)-[:FRIENDS_WITH]-(f)
            WITH u, count(f) as friend_count
            RETURN u.name as name, friend_count
            ORDER BY u.name
        """)

        print("\n👥 Friend Summary:")
        for record in result:
            print(f"   {record['name']}: {record['friend_count']} friends")

# ============================================================================
# SIMULATE VIDEO ENGAGEMENT
# ============================================================================

def simulate_video_engagement(user_data: list, num_videos: int):
    """Simulate video-level engagement (watches, saves, shares)"""
    print("\n" + "="*60)
    print("SIMULATING VIDEO ENGAGEMENT")
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
            user_id = f"user_{i}"

            # Each user watches 20-40 videos
            num_watches = random.randint(20, 40)
            video_indices = random.sample(range(num_videos), min(num_watches, num_videos))

            for v_idx in video_indices:
                video_id = f"video_{v_idx}"

                # Determine engagement type
                engagement_dist = [
                    ("skip", 0.15),
                    ("brief_view", 0.25),
                    ("engaged_view", 0.35),
                    ("full_view", 0.15),
                    ("save", 0.07),
                    ("share", 0.03),
                ]

                engagement_type = random.choices(
                    [e[0] for e in engagement_dist],
                    weights=[e[1] for e in engagement_dist]
                )[0]

                config = engagement_types[engagement_type]
                watch_time = random.randint(*config["watch_time_range"])
                weight = config["weight"]

                # Determine action type
                if engagement_type == "share":
                    action_type = "shared"
                elif engagement_type == "save":
                    action_type = "saved"
                elif engagement_type == "skip":
                    action_type = "skipped"
                else:
                    action_type = "viewed"

                # Timestamp (random within last 30 days)
                days_ago = random.randint(0, 30)
                timestamp = datetime.now() - timedelta(days=days_ago)

                # Log to Neo4j (video-level engagement)
                session.run("""
                    MATCH (u:User {id: $user_id})
                    MATCH (vid:Video {id: $video_id})
                    MERGE (u)-[r:WATCHED {timestamp: datetime($timestamp)}]->(vid)
                    SET r.watch_time = $watch_time,
                        r.action = $action,
                        r.weight = $weight
                """,
                    user_id=user_id,
                    video_id=video_id,
                    watch_time=watch_time,
                    action=action_type,
                    weight=weight,
                    timestamp=timestamp.isoformat()
                )

                total_interactions += 1

            if (i + 1) % 5 == 0:
                print(f"  Simulated engagement for {i + 1} users ({total_interactions} interactions)...")

        print(f"\n✅ Created {total_interactions} video engagement records")

        # Print engagement breakdown
        breakdown = session.run("""
            MATCH ()-[r:WATCHED]->()
            RETURN r.action as action, count(*) as count
            ORDER BY count DESC
        """)

        print("\n📊 Engagement Breakdown:")
        for record in breakdown:
            print(f"   {record['action']}: {record['count']}")

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Video-Centric NYC Seeder")
    parser.add_argument("--venues", action="store_true", help="Seed venues and videos")
    parser.add_argument("--users", action="store_true", help="Seed users")
    parser.add_argument("--friends", action="store_true", help="Seed friendships")
    parser.add_argument("--engagement", action="store_true", help="Simulate video engagement")
    parser.add_argument("--all", action="store_true", help="Seed everything")

    args = parser.parse_args()

    start_time = time.time()

    num_venues = 0
    num_videos = 0
    user_data = []

    if args.all or args.venues:
        num_venues, num_videos = seed_venues_and_videos()

    if args.all or args.users:
        user_data = seed_users()

    if args.all or args.friends:
        if not user_data:
            user_data = USER_PERSONAS
        seed_friendships(user_data)

    if args.all or args.engagement:
        if num_videos == 0:
            # Get video count from Neo4j
            with driver.session() as session:
                result = session.run("MATCH (v:Video) RETURN count(v) as count")
                num_videos = result.single()["count"]

        if not user_data:
            user_data = USER_PERSONAS

        simulate_video_engagement(user_data, num_videos)

    if not (args.all or args.venues or args.users or args.friends or args.engagement):
        print("Usage: python seeder_video.py [--all] [--venues] [--users] [--friends] [--engagement]")
        print("\nOptions:")
        print("  --all          Seed everything")
        print("  --venues       Seed NYC venues and videos")
        print("  --users        Seed 10-15 users with personas")
        print("  --friends      Create social graph")
        print("  --engagement   Simulate video-level engagement")

    elapsed = time.time() - start_time
    print(f"\n⏱️  Total time: {elapsed:.2f}s")

    driver.close()
