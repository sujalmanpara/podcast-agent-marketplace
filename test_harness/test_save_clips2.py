#!/usr/bin/env python3
"""Save clips by patching the executor to keep temp files"""
import sys, os, asyncio, shutil, tempfile, glob
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

# Monkey-patch tempfile to keep files
_original_td = tempfile.TemporaryDirectory
class PersistentTempDir:
    def __init__(self, **kwargs):
        self.name = tempfile.mkdtemp(**{k:v for k,v in kwargs.items() if k in ['suffix','prefix','dir']})
    def __enter__(self): return self.name
    def __exit__(self, *args): pass  # Don't delete!
    def cleanup(self): pass

tempfile.TemporaryDirectory = PersistentTempDir

from podcast_clip_agent.executor import execute

SAVE_DIR = Path.home() / ".openclaw" / "workspace" / "podcast_clips"

async def test():
    key = os.getenv("OPENAI_API_KEY")
    SAVE_DIR.mkdir(exist_ok=True)
    
    events = []
    async for event in execute(
        prompt="Create 2 clips from https://www.youtube.com/watch?v=ZXsQAXx_ao0",
        keys={"OPENAI_API_KEY": key, "OPENAI_WHISPER_KEY": key},
        options={
            "num_clips": 2, "max_duration": 30, "min_duration": 15,
            "aspect_ratio": "9:16", "add_captions": False, "virality_threshold": 5.0
        }
    ):
        events.append(event)
        if event.get('event') == 'status':
            print(f"  {event.get('data')}")
    
    for e in events:
        if e.get('event') == 'result':
            clips = e['data'].get('clips', [])
            print(f"\n✅ Created {len(clips)} clips! Saving...")
            for i, c in enumerate(clips, 1):
                src = c.get('file_path', '')
                if src and os.path.exists(src):
                    dst = SAVE_DIR / f"clip_{i}.mp4"
                    shutil.copy2(src, dst)
                    print(f"  ✅ Clip {i}: saved to {dst} ({c.get('file_size_mb')}MB)")
                    print(f"     {c.get('duration')}s | Score {c.get('score')}/10 | {c.get('title')}")
                else:
                    print(f"  ❌ Clip {i}: file not found at {src}")
            return True
        elif e.get('event') == 'error':
            print(f"\n❌ {e.get('data')}")
            return False
    return False

if __name__ == "__main__":
    try: import dotenv
    except: os.system("pip3 install python-dotenv")
    success = asyncio.run(test())
    if success:
        print(f"\n📁 Clips saved to: {SAVE_DIR}")
        for f in sorted(SAVE_DIR.glob("*.mp4")):
            print(f"  {f.name} ({f.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"\n{'✅ DONE' if success else '❌ FAILED'}")
