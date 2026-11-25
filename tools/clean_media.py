"""Free disk space after a finished run: delete the downloaded video and audio files.

  python tools/clean_media.py runs/<run>

Runs only when review.json says passed. Keeps everything the report and the evidence use:
frames, images, measures, transcripts and all JSON. Each creative's link still points to the original post.
"""
import json, sys
from pathlib import Path

MEDIA = {".mp4", ".webm", ".mkv", ".mov", ".m4v", ".m4a", ".mp3", ".wav", ".aac", ".opus", ".ogg"}


def main(run):
    run = Path(run)
    try:
        passed = json.loads((run / "review.json").read_text(encoding="utf-8")).get("passed") is True
    except (OSError, ValueError):
        passed = False
    if not passed:
        sys.exit("review.json has not passed yet - nothing deleted (the videos may still be needed)")
    files = [f for f in (run / "media").rglob("*") if f.is_file() and f.suffix.lower() in MEDIA]
    freed = sum(f.stat().st_size for f in files)
    for f in files:
        f.unlink()
    print(f"deleted {len(files)} video/audio files, freed {freed / 1e6:.0f} MB; frames, measures and transcripts kept")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
