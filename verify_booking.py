import sys
import os
import asyncio
from datetime import datetime

# Add project root to path
sys.path.append(os.getcwd())

from app.agent import booking_agent, confirm_booking

def test_booking_flow():
    print("🚀 Starting Booking Agent Verification...")
    
    # Mock Data
    video_id = "video_123"
    user_id = "user_test"
    venue_info = {
        "venue_id": "venue_123",
        "venue_name": "Test Bistro",
        "title": "Amazing Brunch Spot",
        "description": "Best eggs benedict in town, great for weekends.",
        "video_type": "review",
        "categories": ["brunch", "breakfast"]
    }
    
    initial_state = {
        "video_id": video_id,
        "user_id": user_id,
        "venue_info": venue_info,
        "booking_intent": None,
        "availability_check": None,
        "booking_proposal": None,
        "booking_confirmation": None,
        "step": "start"
    }
    
    print(f"\n1. Invoking Agent with initial state for {venue_info['venue_name']}...")
    try:
        state = booking_agent.invoke(initial_state)
        
        print(f"✅ Agent finished. Current step: {state.get('step')}")
        
        if state.get("booking_intent"):
            print(f"   Intent Extracted: {state['booking_intent']}")
        else:
            print("   ❌ No intent extracted")
            
        if state.get("availability_check"):
            print(f"   Availability: {state['availability_check']['status']}")
        else:
            print("   ❌ No availability check")
            
        if state.get("booking_proposal"):
            print(f"   Proposal: {state['booking_proposal']['message']}")
            proposal = state["booking_proposal"]
        else:
            print("   ❌ No proposal created")
            return

        # Test Confirmation
        print("\n2. Testing Confirmation...")
        # Simulate user confirming
        state["booking_proposal"]["action_required"] = "confirm"
        
        # We need to mock the Neo4j driver or expect it to fail if DB not running
        # But the confirm_booking function handles exceptions gracefully
        
        final_state = confirm_booking(state)
        
        if final_state.get("booking_confirmation"):
            conf = final_state["booking_confirmation"]
            print(f"✅ Booking Confirmed!")
            print(f"   ID: {conf.get('booking_id')}")
            print(f"   Message: {conf.get('message')}")
        else:
            print("   ❌ Confirmation failed")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")

if __name__ == "__main__":
    test_booking_flow()
