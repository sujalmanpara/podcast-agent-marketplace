#!/usr/bin/env python3
"""
Test podcast agent with a REAL podcast/interview
"""
import sys
import os
import asyncio
from pathlib import Path

# Add test_harness to path so app.core imports work
sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from podcast_clip_agent.executor import execute


async def test_real_podcast():
    """Test with a real podcast/interview"""
    
    print("=" * 60)
    print("🎙️ REAL PODCAST TEST")
    print("=" * 60)
    
    openai_key = os.getenv("OPENAI_API_KEY")
    whisper_key = os.getenv("OPENAI_WHISPER_KEY", openai_key)
    
    if not openai_key:
        print("❌ ERROR: OPENAI_API_KEY not found")
        return False
    
    print(f"\n✅ Keys loaded\n")
    
    # Test with a short tech interview/podcast
    # Using a short video to keep test time reasonable
    test_case = {
        "name": "Real Podcast/Interview Test",
        # Replace with a real short podcast/interview URL (5-10 min)
        "prompt": "Create 3 viral clips from https://www.youtube.com/watch?v=kCc8FmEb1nY",
        "keys": {
            "OPENAI_API_KEY": openai_key,
            "OPENAI_WHISPER_KEY": whisper_key
        },
        "options": {
            "num_clips": 3,
            "max_duration": 45,  # Longer clips for better context
            "min_duration": 20,  # At least 20 seconds
            "aspect_ratio": "9:16",
            "add_captions": False,  # Skip captions for faster test
            "virality_threshold": 6.5  # Reasonable threshold
        }
    }
    
    print(f"Test: {test_case['name']}")
    print(f"Prompt: {test_case['prompt']}")
    print(f"Options: {test_case['options']}\n")
    
    try:
        events = []
        async for event in execute(
            prompt=test_case['prompt'],
            keys=test_case['keys'],
            options=test_case['options']
        ):
            events.append(event)
        
        print(f"\n{'=' * 60}")
        print(f"Test completed! Total events: {len(events)}")
        
        result_events = [e for e in events if e.get('event') == 'result']
        error_events = [e for e in events if e.get('event') == 'error']
        
        if error_events:
            print(f"\n❌ Errors:")
            for err in error_events:
                print(f"   {err.get('data')}")
            return False
        
        if result_events:
            print(f"\n✅ Success!\n")
            result = result_events[0].get('data', {})
            
            clips = result.get('clips', [])
            print(f"📊 Analysis of {len(clips)} clips:\n")
            
            for idx, clip in enumerate(clips, 1):
                print(f"Clip {idx}:")
                print(f"  Title: {clip.get('title', 'N/A')}")
                print(f"  Score: {clip.get('score', 0)}/10")
                print(f"  Duration: {clip.get('duration', 0)}s")
                print(f"  Time: {clip.get('start_time', 0)}s - {clip.get('end_time', 0)}s")
                print(f"  Reason: {clip.get('reason', 'N/A')}")
                print(f"  Text preview: {clip.get('text', '')[:100]}...")
                print(f"  File: {clip.get('file_path', 'N/A')}")
                print()
            
            # Check for duplicates
            start_times = [c.get('start_time', 0) for c in clips]
            if len(start_times) != len(set(start_times)):
                print("⚠️  WARNING: Some clips have the same start time (duplicates!)")
            else:
                print("✅ All clips are from different time segments")
            
            # Check score variation
            scores = [c.get('score', 0) for c in clips]
            if len(set(scores)) == 1:
                print(f"⚠️  WARNING: All clips have the same score ({scores[0]}) - LLM may not be differentiating")
            else:
                print(f"✅ Clips have varied scores: {scores}")
            
            return True
        else:
            print("⚠️  No result event found")
            return False
            
    except Exception as e:
        print(f"\n❌ Test failed:")
        print(f"   {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 Testing with real podcast content...\n")
    
    try:
        import dotenv
    except ImportError:
        print("Installing python-dotenv...")
        os.system("pip3 install python-dotenv")
    
    success = asyncio.run(test_real_podcast())
    
    print("\n" + "=" * 60)
    if success:
        print("✅ TEST PASSED - Check clip quality above")
    else:
        print("❌ TEST FAILED")
    print("=" * 60 + "\n")
    
    sys.exit(0 if success else 1)
