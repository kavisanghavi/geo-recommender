from qdrant_client import QdrantClient, models
import random
import os

QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))

client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def get_vector_client():
    return client

def get_user_vector(user_id: str) -> list[float]:
    """
    Retrieve the user's interest vector from Qdrant users collection.
    Falls back to random vector if not found (for backwards compatibility).
    """
    try:
        # Extract user index from user_id (e.g., "user_42" -> 42)
        user_index = int(user_id.split("_")[1])

        # Retrieve from Qdrant users collection
        points = client.retrieve(
            collection_name="users",
            ids=[user_index],
            with_vectors=True
        )

        if points and len(points) > 0:
            return points[0].vector
        else:
            print(f"Warning: User {user_id} not found in Qdrant, using random vector")
            return [random.random() for _ in range(1536)]
    except Exception as e:
        print(f"Error retrieving user vector: {e}, using random vector")
        return [random.random() for _ in range(1536)]

def search_venues(user_vector: list[float], lat: float, lon: float, radius_km: float = 5.0, limit: int = 50) -> list[dict]:
    """
    Search for venues in Qdrant that match the user's vector and are within the radius.
    """
    try:
        results = client.query_points(
            collection_name="venues",
            query=user_vector,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="location",
                        geo_radius=models.GeoRadius(
                            center=models.GeoPoint(lat=lat, lon=lon),
                            radius=radius_km * 1000.0 # meters
                        )
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        ).points
        return [
            {
                "venue_id": point.payload.get("venue_id"),
                "score": point.score,
                "payload": point.payload
            }
            for point in results
        ]
    except Exception as e:
        print(f"Error searching venues: {e}")
        return []
