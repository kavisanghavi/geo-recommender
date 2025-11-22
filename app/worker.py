import os
from celery import Celery

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery = Celery(__name__, broker=REDIS_URL, backend=REDIS_URL)

@celery.task
def process_interaction(user_id: str, venue_id: str, interaction_type: str, duration: int):
    from app.graph import log_interaction_to_graph
    
    print(f"Processing interaction: {user_id} -> {venue_id} ({interaction_type}, {duration}s)")
    
    # Calculate weight based on duration/type
    weight = 0.0
    if interaction_type == "viewed":
        if duration > 30:
            weight = 0.8
        else:
            weight = 0.2
    elif interaction_type == "saved":
        weight = 1.0
    elif interaction_type == "going":
        weight = 1.5
        
    # Update Graph
    try:
        log_interaction_to_graph(user_id, venue_id, interaction_type, weight)
        print(f"Updated graph for {user_id} -> {venue_id}")
    except Exception as e:
        print(f"Error updating graph: {e}")

    # TODO: Update User Vector in Qdrant (Nudge towards venue category)
    # For MVP, we skip the vector update as we are using random user vectors.
