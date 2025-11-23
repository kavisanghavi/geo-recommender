from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional, List, Dict, Any
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import random
import os
import json
from datetime import datetime, timedelta
import uuid

# Initialize LLM (will gracefully degrade if no API key)
try:
    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.7)
    LLM_AVAILABLE = True
except Exception as e:
    print(f"OpenAI not configured: {e}. Using rule-based fallback.")
    LLM_AVAILABLE = False


class BookingState(TypedDict):
    """State for the booking agent workflow"""
    video_id: str
    user_id: str
    venue_info: Dict[str, Any]
    booking_intent: Optional[Dict[str, Any]]
    availability_check: Optional[Dict[str, Any]]
    booking_proposal: Optional[Dict[str, Any]]
    booking_confirmation: Optional[Dict[str, Any]]
    step: str  # Current step in workflow
    logs: List[str]  # Execution trace for UI


def extract_booking_intent(state: BookingState) -> BookingState:
    """
    Use LLM to intelligently extract booking intent from video context.
    Falls back to rule-based logic if LLM unavailable.
    """
    video = state["venue_info"]

    if LLM_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        try:
            system_prompt = """You are a booking assistant that extracts intent from video content.
Given a video about a venue, suggest appropriate booking parameters.

Consider:
- Video type (event, promo, ambiance, special) suggests timing
- Categories suggest party size and occasion
- Description may contain specific event times or offers

Return JSON only, no other text:
{
    "party_size": <1-8>,
    "suggested_date": "<YYYY-MM-DD>",
    "suggested_time": "<HH:MM>",
    "occasion": "<casual|date_night|group_outing|business|celebration>",
    "special_requests": "<any relevant notes from video>",
    "reasoning": "<brief explanation>"
}"""

            user_prompt = f"""Video Title: {video.get('title', 'Untitled')}
Video Description: {video.get('description', 'No description')}
Video Type: {video.get('video_type', 'general')}
Categories: {', '.join(video.get('categories', []))}
Venue: {video.get('venue_name', 'Unknown')}

Extract booking intent."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            response = llm.invoke(messages)
            intent = json.loads(response.content)

        except Exception as e:
            print(f"LLM intent extraction failed: {e}, using fallback")
            intent = _rule_based_intent(video)
    else:
        # Rule-based fallback
        intent = _rule_based_intent(video)

    state["booking_intent"] = intent
    state["step"] = "intent_extracted"
    state.setdefault("logs", []).append(f"🧠 Extracted intent: Party of {intent.get('party_size', '?')} for {intent.get('occasion', 'visit')}")
    print(f"DEBUG: Intent extracted: {intent}")
    return state


def _rule_based_intent(video: Dict[str, Any]) -> Dict[str, Any]:
    """Fallback rule-based intent extraction"""
    video_type = (video.get('video_type') or 'general').lower()
    categories = [(c or '').lower() for c in video.get('categories') or []]

    # Determine party size based on venue type
    if any(cat in ['bar', 'cocktails', 'nightlife'] for cat in categories):
        party_size = random.choice([2, 2, 4, 4, 6])  # Weighted toward 2 and 4
        occasion = "group_outing"
    elif any(cat in ['cafe', 'coffee', 'bakery'] for cat in categories):
        party_size = random.choice([1, 2, 2])
        occasion = "casual"
    elif any(cat in ['fine dining', 'upscale', 'michelin'] for cat in categories):
        party_size = 2
        occasion = "date_night"
    else:
        party_size = random.choice([2, 3, 4])
        occasion = "casual"

    # Determine time based on video type and categories
    now = datetime.now()
    if video_type == 'event':
        # Events are usually evening
        suggested_date = (now + timedelta(days=random.randint(3, 10))).strftime('%Y-%m-%d')
        suggested_time = "19:00"
    elif any(cat in ['brunch', 'breakfast'] for cat in categories):
        suggested_date = (now + timedelta(days=random.randint(2, 7))).strftime('%Y-%m-%d')
        suggested_time = "11:00"
    elif any(cat in ['coffee', 'cafe'] for cat in categories):
        suggested_date = (now + timedelta(days=1)).strftime('%Y-%m-%d')
        suggested_time = "09:30"
    elif any(cat in ['happy hour'] for cat in categories):
        suggested_date = (now + timedelta(days=random.randint(1, 5))).strftime('%Y-%m-%d')
        suggested_time = "17:30"
    else:
        # Default dinner
        suggested_date = (now + timedelta(days=random.randint(2, 7))).strftime('%Y-%m-%d')
        suggested_time = "19:30"

    special_requests = f"Interested after watching: {video.get('title', 'video')}"

    return {
        "party_size": party_size,
        "suggested_date": suggested_date,
        "suggested_time": suggested_time,
        "occasion": occasion,
        "special_requests": special_requests,
        "reasoning": f"Based on {video_type} video type and {', '.join(categories[:2])} categories"
    }


def check_availability(state: BookingState) -> BookingState:
    """
    Mock availability check with realistic logic.
    In production: integrate with OpenTable, Resy, Toast, etc.
    """
    intent = state["booking_intent"]
    venue_id = state["venue_info"]["venue_id"]

    # Parse datetime
    try:
        booking_datetime = datetime.strptime(
            f"{intent['suggested_date']} {intent['suggested_time']}",
            "%Y-%m-%d %H:%M"
        )
    except:
        booking_datetime = datetime.now() + timedelta(days=3, hours=19)

    # Realistic availability logic
    hour = booking_datetime.hour
    day_of_week = booking_datetime.weekday()  # 0=Monday, 6=Sunday
    party_size = intent['party_size']

    # Calculate availability score
    availability_score = 1.0

    # Prime dinner times (7-9pm) are harder to book
    if 19 <= hour <= 21:
        availability_score *= 0.6

    # Weekend evenings are harder
    if day_of_week >= 5 and hour >= 18:  # Friday/Saturday evening
        availability_score *= 0.5

    # Large parties are harder
    if party_size >= 6:
        availability_score *= 0.7

    # Weekday lunch is easy
    if day_of_week < 5 and 11 <= hour <= 14:
        availability_score *= 1.3

    is_available = random.random() < availability_score

    if is_available:
        state["availability_check"] = {
            "status": "available",
            "booking_datetime": booking_datetime.isoformat(),
            "message": f"Perfect! {state['venue_info']['venue_name']} has availability."
        }
    else:
        # Generate alternatives
        alternatives = []

        # Try 1 hour later
        alt1 = booking_datetime + timedelta(hours=1)
        alternatives.append({
            "datetime": alt1.isoformat(),
            "display": alt1.strftime("%A, %B %d at %I:%M %p"),
            "reason": "Same day, slightly later"
        })

        # Try same time next day
        alt2 = booking_datetime + timedelta(days=1)
        alternatives.append({
            "datetime": alt2.isoformat(),
            "display": alt2.strftime("%A, %B %d at %I:%M %p"),
            "reason": "Next day, same time"
        })

        # Try same day of week, different time
        if hour >= 19:
            alt3 = booking_datetime.replace(hour=17, minute=30)
        else:
            alt3 = booking_datetime.replace(hour=20, minute=0)
        alternatives.append({
            "datetime": alt3.isoformat(),
            "display": alt3.strftime("%A, %B %d at %I:%M %p"),
            "reason": "Same day, different time"
        })

        state["availability_check"] = {
            "status": "unavailable",
            "booking_datetime": booking_datetime.isoformat(),
            "message": f"That time is fully booked at {state['venue_info']['venue_name']}.",
            "alternatives": alternatives
        }

    state["step"] = "availability_checked"
    status_icon = "✅" if state.get("availability_check", {}).get("status") == "available" else "❌"
    state.setdefault("logs", []).append(f"{status_icon} Checked availability: {state.get('availability_check', {}).get('status')}")
    print(f"DEBUG: Availability checked: {state['availability_check']}")
    return state


def create_booking_proposal(state: BookingState) -> BookingState:
    """
    Generate user-friendly booking proposal with all details.
    """
    venue = state["venue_info"]
    intent = state["booking_intent"]
    availability = state["availability_check"]

    if availability["status"] == "available":
        booking_datetime = datetime.fromisoformat(availability["booking_datetime"])

        proposal = {
            "status": "ready_to_book",
            "title": f"Book {venue['venue_name']}",
            "venue_name": venue["venue_name"],
            "venue_id": venue["venue_id"],
            "venue_category": venue.get("category", "Restaurant"),
            "party_size": intent["party_size"],
            "date": booking_datetime.strftime("%A, %B %d, %Y"),
            "time": booking_datetime.strftime("%I:%M %p"),
            "datetime_iso": booking_datetime.isoformat(),
            "occasion": intent.get("occasion", "casual").replace("_", " ").title(),
            "special_requests": intent.get("special_requests", ""),
            "message": f"Great choice! Ready to book a table for {intent['party_size']} on {booking_datetime.strftime('%A, %b %d at %I:%M %p')}?",
            "action_required": "confirm_or_modify"
        }
    else:
        proposal = {
            "status": "alternatives_available",
            "title": f"Alternative Times at {venue['venue_name']}",
            "venue_name": venue["venue_name"],
            "venue_id": venue["venue_id"],
            "party_size": intent["party_size"],
            "original_request": datetime.fromisoformat(availability["booking_datetime"]).strftime("%A, %b %d at %I:%M %p"),
            "message": availability["message"] + " Here are some alternatives:",
            "alternatives": availability["alternatives"],
            "action_required": "choose_alternative"
        }

    state["booking_proposal"] = proposal
    state["step"] = "proposal_created"
    state.setdefault("logs", []).append("📝 Generated booking proposal")
    print(f"DEBUG: Proposal created: {proposal}")
    return state


def confirm_booking(state: BookingState) -> BookingState:
    """
    Finalize booking and store in Neo4j.
    In production: call venue API, send confirmation email, etc.
    """
    from app.graph import driver

    proposal = state["booking_proposal"]
    booking_id = f"booking_{uuid.uuid4().hex[:12]}"

    # Store booking in Neo4j
    try:
        with driver.session() as session:
            result = session.run("""
                MATCH (u:User {id: $user_id})
                MATCH (v:Venue {id: $venue_id})
                MATCH (video:Video {id: $video_id})
                CREATE (u)-[b:BOOKED {
                    booking_id: $booking_id,
                    party_size: $party_size,
                    booking_datetime: datetime($datetime_iso),
                    occasion: $occasion,
                    special_requests: $special_requests,
                    status: 'confirmed',
                    created_at: datetime(),
                    video_source: $video_id
                }]->(v)
                CREATE (u)-[:WATCHED {
                    action: 'booked',
                    watch_time: 0,
                    timestamp: datetime(),
                    booking_id: $booking_id
                }]->(video)
                RETURN b.booking_id as booking_id
            """,
                user_id=state["user_id"],
                venue_id=proposal["venue_id"],
                video_id=state["video_id"],
                booking_id=booking_id,
                party_size=proposal["party_size"],
                datetime_iso=proposal["datetime_iso"],
                occasion=proposal.get("occasion", "casual"),
                special_requests=proposal.get("special_requests", "")
            )

            confirmation_created = result.single() is not None
    except Exception as e:
        print(f"Failed to store booking in Neo4j: {e}")
        confirmation_created = False

    # Generate confirmation
    state["booking_confirmation"] = {
        "status": "confirmed",
        "booking_id": booking_id,
        "venue_name": proposal["venue_name"],
        "party_size": proposal["party_size"],
        "date": proposal["date"],
        "time": proposal["time"],
        "message": f"🎉 Booking confirmed! Your table for {proposal['party_size']} at {proposal['venue_name']} is reserved for {proposal['date']} at {proposal['time']}.",
        "confirmation_number": booking_id[-8:].upper(),
        "next_steps": [
            "You'll receive a confirmation email shortly",
            "Add to your calendar (coming soon!)",
            "View booking details in your profile"
        ],
        "stored_in_db": confirmation_created
    }

    state["step"] = "booking_confirmed"
    state.setdefault("logs", []).append(f"🎉 Booking confirmed: {booking_id}")
    return state


def route_after_availability(state: BookingState) -> str:
    """Conditional routing based on availability"""
    if state["availability_check"]["status"] == "available":
        return "create_proposal"
    else:
        return "create_proposal"  # Still create proposal with alternatives


def build_booking_agent() -> StateGraph:
    """
    Build the complete booking agent workflow.

    Workflow:
    1. Extract Intent: Analyze video context to determine booking parameters
    2. Check Availability: Mock availability check (pluggable with real APIs)
    3. Create Proposal: Generate user-friendly booking proposal or alternatives
    4. Confirm Booking: Finalize and store in Neo4j
    """
    workflow = StateGraph(BookingState)

    # Add nodes
    workflow.add_node("extract_intent", extract_booking_intent)
    workflow.add_node("check_availability", check_availability)
    workflow.add_node("create_proposal", create_booking_proposal)
    workflow.add_node("confirm_booking", confirm_booking)

    # Define workflow edges
    workflow.set_entry_point("extract_intent")
    workflow.add_edge("extract_intent", "check_availability")
    workflow.add_conditional_edges(
        "check_availability",
        route_after_availability,
        {
            "create_proposal": "create_proposal"
        }
    )
    workflow.add_edge("create_proposal", END)  # User must confirm before booking
    workflow.add_edge("confirm_booking", END)

    return workflow.compile()


# Initialize the agent
booking_agent = build_booking_agent()


# Legacy function for backward compatibility
def booking_agent_workflow():
    """Legacy function - returns the new agent"""
    return booking_agent
