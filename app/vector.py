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
    Retrieve the user's interest vector.
    For MVP, we return a random vector if not found (or mock it).
    In production, this would query Qdrant 'users' collection.
    """
    # Mock: Return a random 1536-dim vector
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
