#!/usr/bin/env python3
"""
Local test harness for podcast-clip-agent
Tests the agent without needing the full marketplace backend
"""
import sys
import os
import asyncio
from pathlib import Path

# Add test_harness to path so app.core imports work
sys.path.insert(0, str(Path(__file__).parent))

# Add parent dir so we can import podcast_clip_agent
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env file
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Now import the agent
from podcast_clip_agent.executor import execute


async def test_agent():
    """Test the podcast clip agent with sample input"""
    
    print("=" * 60)
    print("🎙️ PODCAST CLIP AGENT LOCAL TEST")
    print("=" * 60)
    
    # Get API keys from environment
    openai_key = os.getenv("OPENAI_API_KEY")
    whisper_key = os.getenv("OPENAI_WHISPER_KEY", openai_key)
    
    if not openai_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        return False
    
    print(f"\n✅ OpenAI Key loaded: {openai_key[:20]}...")
    if whisper_key:
        print(f"✅ Whisper Key loaded: {whisper_key[:20]}...")
    
    # Test configuration
    # Using a short test video (educational/public domain)
    test_cases = [
        {
            "name": "Short YouTube Test",
            "prompt": "Create 2 viral clips from https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "keys": {
                "OPENAI_API_KEY": openai_key,
                "OPENAI_WHISPER_KEY": whisper_key
            },
            "options": {
                "num_clips": 2,
                "max_duration": 30,
                "min_duration": 10,
                "aspect_ratio": "9:16",
                "add_captions": False,  # Faster test without captions
                "virality_threshold": 5.0  # Lower threshold for test
            }
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 60}")
        print(f"Test {i}/{len(test_cases)}: {test_case['name']}")
        print(f"{'=' * 60}")
        print(f"Prompt: {test_case['prompt']}")
        print(f"Options: {test_case['options']}")
        print()
        
        try:
            # Call the executor
            events = []
            async for event in execute(
                prompt=test_case['prompt'],
                keys=test_case['keys'],
                options=test_case['options']
            ):
                events.append(event)
            
            # Check results
            print(f"\n{'=' * 60}")
            print(f"✅ Test {i} completed!")
            print(f"   Total events: {len(events)}")
            
            # Check for result event
            result_events = [e for e in events if e.get('event') == 'result']
            error_events = [e for e in events if e.get('event') == 'error']
            
            if error_events:
                print(f"   ❌ Errors: {len(error_events)}")
                for err in error_events:
                    print(f"      {err.get('data')}")
                return False
            
            if result_events:
                print(f"   ✅ Success! Result received:")
                result = result_events[0].get('data', {})
                if isinstance(result, dict):
                    for key, value in result.items():
                        if key == "clips":
                            print(f"      {key}: {len(value)} clips")
                            for idx, clip in enumerate(value, 1):
                                print(f"         Clip {idx}: {clip.get('file_path', 'unknown')}")
                        else:
                            print(f"      {key}: {value}")
                else:
                    print(f"      {result}")
                return True
            else:
                print(f"   ⚠️  No result event found")
                return False
                
        except Exception as e:
            print(f"\n❌ Test {i} failed with exception:")
            print(f"   {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


if __name__ == "__main__":
    print("\n🚀 Starting podcast clip agent test...\n")
    
    # Check if python-dotenv is installed
    try:
        import dotenv
    except ImportError:
        print("❌ python-dotenv not installed. Installing...")
        os.system("pip3 install python-dotenv")
        print()
    
    success = asyncio.run(test_agent())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED!")
        print("🎉 Agent is ready for marketplace deployment")
    else:
        print("❌ TESTS FAILED")
        print("🔧 Fix the issues before deploying")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
