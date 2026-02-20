"""Mock SSE module for local testing"""
import json


def sse_event(event_type: str, data):
    """Mock SSE event - prints to console for testing"""
    if isinstance(data, dict):
        data_str = json.dumps(data, indent=2)
    else:
        data_str = str(data)
    
    print(f"\n🔔 SSE Event: {event_type}")
    print(f"   Data: {data_str}")
    
    return {
        "event": event_type,
        "data": data
    }


def sse_error(message: str):
    """Mock SSE error event"""
    print(f"\n❌ SSE Error: {message}")
    return {
        "event": "error",
        "data": {"error": message}
    }


def sse_input_required(session_id: str, question: str, input_type: str, options: list = None):
    """Mock HITL input request"""
    print(f"\n❓ Input Required:")
    print(f"   Session: {session_id}")
    print(f"   Question: {question}")
    print(f"   Type: {input_type}")
    if options:
        print(f"   Options: {options}")
    
    return {
        "event": "input_required",
        "data": {
            "session_id": session_id,
            "question": question,
            "input_type": input_type,
            "options": options
        }
    }
