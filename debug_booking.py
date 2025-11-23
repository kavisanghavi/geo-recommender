import sys
import os
from app.agent import booking_agent

# Add project root to path
sys.path.append(os.getcwd())

def debug_mock_flow():
    print("🚀 Starting Booking Agent Debugging with MOCK DATA (Testing None video_type)...")
    
    # Mock data with None video_type to simulate potential DB issue
    video_id = "mock_video_123"
    user_id = "mock_user_123"
    
    venue_info = {
        "venue_id": "mock_venue_123",
        "venue_name": "Test Venue",
        "title": "Test Video",
        "description": "Test Description",
        "video_type": None,  # <--- TESTING THIS
        "categories": ["brunch"]
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
    
    print(f"\n🔄 Invoking Agent...")
    try:
        final_state = booking_agent.invoke(initial_state)
        
        print("\n📊 Final State Analysis:")
        print(f"   Step: {final_state.get('step')}")
        
        if final_state.get("booking_proposal"):
            print(f"   ✅ Proposal: {final_state['booking_proposal']}")
        else:
            print("   ❌ NO PROPOSAL IN FINAL STATE")
            print(f"   Availability: {final_state.get('availability_check')}")
            print(f"   Intent: {final_state.get('booking_intent')}")

    except Exception as e:
        print(f"❌ Agent Error: {e}")

if __name__ == "__main__":
    debug_mock_flow()
