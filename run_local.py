"""
Podcast Clip Agent — Standalone Local Runner
Run the full pipeline without the Nextbase marketplace framework.

Usage:
    python run_local.py "https://youtube.com/watch?v=VIDEO_ID"
    python run_local.py "https://youtube.com/watch?v=VIDEO_ID" --clips 5 --ratio 1:1 --no-captions
"""
import argparse
import asyncio
import httpx
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ─────────────────────────────────────────────────────────────────
load_dotenv()

# ── Import pipeline modules directly (bypassing marketplace executor) ─────────
sys.path.insert(0, str(Path(__file__).parent))

from podcast_clip_agent.downloader import download_video
from podcast_clip_agent.transcriber import transcribe_audio
from podcast_clip_agent.viral_detector import detect_viral_moments
from podcast_clip_agent.clipper import create_clips_from_moments
from podcast_clip_agent.caption_generator import generate_captions_for_clips


# ── Helpers ───────────────────────────────────────────────────────────────────

def log(emoji: str, msg: str):
    """Pretty-print a status line."""
    print(f"\n{emoji}  {msg}")


def extract_url(text: str) -> str | None:
    """Extract a YouTube or direct video URL from text."""
    yt = re.search(
        r'(?:https?://)?(?:www\.|m\.)?'
        r'(?:youtube\.com/(?:watch\?v=|shorts/|live/|embed/)|youtu\.be/)'
        r'([\w\-]{11})',
        text, re.IGNORECASE
    )
    if yt:
        return f"https://www.youtube.com/watch?v={yt.group(1)}"

    direct = re.search(r'https?://[^\s]+\.(?:mp4|webm|mkv|avi|mov|m4v)(?:\?[^\s]*)?', text, re.IGNORECASE)
    if direct:
        return direct.group(0)

    return None


def check_deps():
    """Ensure yt-dlp, ffmpeg, ffprobe are on PATH."""
    missing = []
    for name, cmd in [("yt-dlp", ["yt-dlp", "--version"]), ("ffmpeg", ["ffmpeg", "-version"]), ("ffprobe", ["ffprobe", "-version"])]:
        try:
            subprocess.run(cmd, capture_output=True, check=True, timeout=5)
        except Exception:
            missing.append(name)
    if missing:
        print(f"\n❌ Missing system dependencies: {', '.join(missing)}")
        print("   Install with:  pip install yt-dlp   and   https://ffmpeg.org/download.html")
        sys.exit(1)


# ── Main Pipeline ─────────────────────────────────────────────────────────────

async def run_pipeline(
    video_url: str,
    openai_key: str,
    whisper_key: str,
    num_clips: int = 3,
    min_duration: int = 15,
    max_duration: int = 60,
    aspect_ratio: str = "9:16",
    add_captions: bool = True,
    virality_threshold: float = 7.0,
    output_dir: str = "output"
):
    """Run the full clip pipeline and save results to output_dir."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    start_time = time.time()

    # Use a persistent temp dir so we can copy clips out at the end
    import tempfile
    temp_dir = tempfile.mkdtemp(prefix="podcast_clip_")
    temp_path = Path(temp_dir)

    try:
        async with httpx.AsyncClient(timeout=300) as client:

            # Step 1 — Download
            log("⬇️", f"Downloading: {video_url}")
            video_file = await download_video(video_url, str(temp_path))
            log("✅", f"Downloaded: {Path(video_file).name}")

            # Step 2 — Transcribe
            log("🎤", "Transcribing with Whisper API...")
            transcript = await transcribe_audio(client, whisper_key, video_file)
            words = len(transcript.get("text", "").split())
            log("✅", f"Transcription complete — {words} words")

            # Step 3 — Detect viral moments
            log("🤖", f"Detecting top {num_clips} viral moments (threshold: {virality_threshold})...")
            moments = await detect_viral_moments(
                client, openai_key, transcript,
                num_clips=num_clips,
                min_duration=min_duration,
                max_duration=max_duration,
                threshold=virality_threshold
            )

            if not moments:
                log("⚠️", "No viral moments found. Try lowering --threshold (e.g. 5.0)")
                return

            log("✅", f"Found {len(moments)} viral moments:")
            for i, m in enumerate(moments, 1):
                print(f"     {i}. [{m['start_time']:.1f}s–{m['end_time']:.1f}s] "
                      f"score={m['score']:.1f}  \"{m.get('title', '')}\"")

            # Step 4 — Create clips (parallel)
            log("✂️", f"Creating {len(moments)} clips in parallel ({aspect_ratio})...")
            clips = await create_clips_from_moments(video_file, moments, str(temp_path), aspect_ratio=aspect_ratio)
            log("✅", f"Created {len(clips)} clips")

            # Step 5 — Captions (parallel, optional)
            if add_captions:
                log("📝", "Burning captions into clips (parallel)...")
                clips = await generate_captions_for_clips(client, openai_key, clips, transcript)
                ok = sum(1 for c in clips if c.get("has_captions"))
                log("✅", f"Captions added to {ok}/{len(clips)} clips")

            # Step 6 — Copy to output
            log("📁", f"Saving clips to ./{output_dir}/")
            for clip in clips:
                # In run_local, we are bypassing the executor endpoint, so files are still on disk here
                src = Path(clip["file_path"])
                if src.exists():
                    dst = output_path / src.name
                    shutil.copy2(str(src), str(dst))
                    size_mb = dst.stat().st_size / (1024 * 1024)
                    print(f"     → {dst.name}  ({size_mb:.1f} MB)")
                else:
                    print(f"     → Error: {src.name} not found")

    finally:
        # Clean up temp files
        shutil.rmtree(temp_dir, ignore_errors=True)

    elapsed = time.time() - start_time
    log("🎬", f"Done! {len(clips)} clips saved to ./{output_dir}/  ({elapsed:.0f}s total)")


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Podcast Clip Agent — create viral clips from any YouTube video",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python run_local.py \"https://youtube.com/watch?v=dQw4w9WgXcQ\"\n"
               "  python run_local.py \"https://youtu.be/abc123\" --clips 5 --ratio 1:1\n"
               "  python run_local.py \"https://youtube.com/shorts/xyz\" --no-captions --threshold 5.0\n"
    )
    parser.add_argument("url", help="YouTube URL or direct video URL")
    parser.add_argument("--clips",     type=int,   default=3,    help="Number of clips (1-10, default: 3)")
    parser.add_argument("--min-dur",   type=int,   default=15,   help="Min clip duration in seconds (default: 15)")
    parser.add_argument("--max-dur",   type=int,   default=60,   help="Max clip duration in seconds (default: 60)")
    parser.add_argument("--ratio",     type=str,   default="9:16",
                        choices=["9:16", "1:1", "16:9"],         help="Aspect ratio (default: 9:16)")
    parser.add_argument("--no-captions", action="store_true",    help="Skip caption burning")
    parser.add_argument("--threshold", type=float, default=7.0,  help="Virality threshold 1-10 (default: 7.0)")
    parser.add_argument("--output",    type=str,   default="output", help="Output directory (default: output)")

    args = parser.parse_args()

    # Validate URL
    video_url = extract_url(args.url)
    if not video_url:
        print("❌ Could not find a valid video URL. Provide a YouTube or direct video link.")
        sys.exit(1)

    # ── Keys ──────────────────────────────────────────────────────────────────
    openai_key = os.getenv("OPENAI_API_KEY")
    whisper_key = openai_key  # Use the same key for transcription

    if not openai_key:
        print("❌ Error: OPENAI_API_KEY is required in .env or environment.", file=sys.stderr)
        sys.exit(1)

    # Check dependencies
    check_deps()

    print("=" * 60)
    print("🎬 Podcast Clip Agent — Local Runner")
    print("=" * 60)
    print(f"  URL:        {video_url}")
    print(f"  Clips:      {args.clips}")
    print(f"  Duration:   {args.min_dur}–{args.max_dur}s")
    print(f"  Ratio:      {args.ratio}")
    print(f"  Captions:   {'Yes' if not args.no_captions else 'No'}")
    print(f"  Threshold:  {args.threshold}")
    print(f"  Output:     ./{args.output}/")
    print("=" * 60)

    asyncio.run(run_pipeline(
        video_url=video_url,
        openai_key=openai_key,
        whisper_key=whisper_key,
        num_clips=args.clips,
        min_duration=args.min_dur,
        max_duration=args.max_dur,
        aspect_ratio=args.ratio,
        add_captions=not args.no_captions,
        virality_threshold=args.threshold,
        output_dir=args.output
    ))


if __name__ == "__main__":
    main()
