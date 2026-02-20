#!/usr/bin/env python3
import sys, os, asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")
from podcast_clip_agent.executor import execute

async def test():
    key = os.getenv("OPENAI_API_KEY")
    # Using a short motivational speech (public, no copyright issues)
    events = []
    async for event in execute(
        prompt="Create 2 clips from https://www.youtube.com/watch?v=ZXsQAXx_ao0",
        keys={"OPENAI_API_KEY": key, "OPENAI_WHISPER_KEY": key},
        options={
            "num_clips": 2,
            "max_duration": 30,
            "min_duration": 15,
            "aspect_ratio": "9:16",
            "add_captions": False,
            "virality_threshold": 5.0
        }
    ):
        events.append(event)
    
    for e in events:
        evt_type = e.get('event', '')
        data = e.get('data', '')
        if evt_type == 'result':
            clips = data.get('clips', [])
            print(f"\n✅ SUCCESS! Created {len(clips)} clips:")
            for i, c in enumerate(clips, 1):
                dur = c.get('end_time', 0) - c.get('start_time', 0)
                print(f"  Clip {i}: {dur:.1f}s | Score: {c.get('score')}/10 | {c.get('title')}")
                print(f"    Time: {c.get('start_time')}s - {c.get('end_time')}s")
                print(f"    File: {c.get('file_path')}")
            return True
        elif evt_type == 'error':
            print(f"\n❌ Error: {data}")
            return False
        elif evt_type == 'status':
            print(f"  {data}")
    return False

if __name__ == "__main__":
    try: import dotenv
    except: os.system("pip3 install python-dotenv")
    success = asyncio.run(test())
    print(f"\n{'✅ PASSED' if success else '❌ FAILED'}")
    sys.exit(0 if success else 1)
