#!/usr/bin/env python3
import sys
import os
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from podcast_clip_agent.executor import execute

async def test():
    openai_key = os.getenv("OPENAI_API_KEY")
    
    # Try a SHORT tech talk/interview (not music!)
    # Using a 2-3 minute video for faster testing
    test_case = {
        "prompt": "Create 2 clips from https://www.youtube.com/watch?v=8jLOx1hD3_E",  # Short TEDx talk
        "keys": {"OPENAI_API_KEY": openai_key, "OPENAI_WHISPER_KEY": openai_key},
        "options": {
            "num_clips": 2,
            "max_duration": 30,
            "min_duration": 15,
            "aspect_ratio": "9:16",
            "add_captions": False,
            "virality_threshold": 5.0
        }
    }
    
    print("\n🎙️ Testing with short TEDx talk...\n")
    
    events = []
    async for event in execute(**test_case):
        events.append(event)
        if event.get('event') == 'status':
            print(f"  {event.get('data')}")
    
    result_events = [e for e in events if e.get('event') == 'result']
    error_events = [e for e in events if e.get('event') == 'error']
    
    if error_events:
        print(f"\n❌ Error: {error_events[0].get('data')}")
        return False
    
    if result_events:
        result = result_events[0].get('data', {})
        clips = result.get('clips', [])
        print(f"\n✅ Success! Created {len(clips)} clips:")
        for i, clip in enumerate(clips, 1):
            print(f"\n  Clip {i}:")
            print(f"    Duration: {clip.get('duration')}s ({clip.get('start_time')}s - {clip.get('end_time')}s)")
            print(f"    Score: {clip.get('score')}/10")
            print(f"    Title: {clip.get('title')}")
            print(f"    File: {clip.get('file_path')}")
        return True
    
    return False

if __name__ == "__main__":
    try:
        import dotenv
    except ImportError:
        os.system("pip3 install python-dotenv")
    
    success = asyncio.run(test())
    sys.exit(0 if success else 1)
