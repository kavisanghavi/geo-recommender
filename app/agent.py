from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List
import random

class AgentState(TypedDict):
    user_id: str
    venue_id: str
    party_size: int
    time: str
    status: str
    message: Optional[str]
    alternatives: Optional[List[str]]

def check_availability(state: AgentState):
    """
    Mock availability check.
    Returns available for even hours, unavailable for odd hours.
    """
    time_str = state["time"]
    # Simple mock: check if the hour is even
    try:
        hour = int(time_str.split(":")[0])
        is_available = (hour % 2 == 0)
    except:
        is_available = True # Default to true if parse fails

    if is_available:
        return {"status": "available"}
    else:
        return {"status": "unavailable"}

def propose_alternatives(state: AgentState):
    """
    Generate alternative times if the requested time is unavailable.
    """
    original_time = state["time"]
    # Mock alternatives
    alternatives = [
        f"{int(original_time.split(':')[0]) + 1}:00",
        f"{int(original_time.split(':')[0]) + 2}:00",
        f"{int(original_time.split(':')[0]) - 1}:00"
    ]
    return {
        "status": "proposed_alternatives",
        "message": f"Time {original_time} is unavailable.",
        "alternatives": alternatives
    }

def confirm_booking(state: AgentState):
    """
    Confirm the booking and update the graph.
    """
    from app.graph import log_interaction_to_graph
    
    # Log 'GOING' interaction
    try:
        log_interaction_to_graph(state["user_id"], state["venue_id"], "going", 2.0)
    except Exception as e:
        print(f"Failed to log booking to graph: {e}")
        
    return {
        "status": "booked",
        "message": f"Booking confirmed for {state['party_size']} people at {state['time']}."
    }

def route_booking(state: AgentState):
    if state["status"] == "available":
        return "confirm_booking"
    else:
        return "propose_alternatives"

def booking_agent_workflow():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("check_availability", check_availability)
    workflow.add_node("propose_alternatives", propose_alternatives)
    workflow.add_node("confirm_booking", confirm_booking)
    
    workflow.set_entry_point("check_availability")
    
    workflow.add_conditional_edges(
        "check_availability",
        route_booking,
        {
            "confirm_booking": "confirm_booking",
            "propose_alternatives": "propose_alternatives"
        }
    )
    
    workflow.add_edge("propose_alternatives", END)
    workflow.add_edge("confirm_booking", END)
    
    return workflow.compile()
