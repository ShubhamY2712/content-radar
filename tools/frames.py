"""Extract analysis frames and cut times from a video (needs ffmpeg + ffprobe on PATH).

  python tools/frames.py <video file or URL> <output folder>

- Up to 30 s: 1 frame per second; longer: 1 frame every 2 s. Files are named <seconds>s.jpg.
- Also saves the last frame (end card) and writes frames.json:
  {"duration_s": .., "frames": [{"time_s": .., "file": ..}], "cuts_s": [..], "cuts_method": ..}
- Cut times come from PySceneDetect (pip install scenedetect) when installed, else from ffmpeg.
- A URL is downloaded first and kept as <output folder>/video.<ext> (for transcript.py):
  page links (Ad Library ad "?id=", Instagram reel, YouTube) with yt-dlp (pip install yt-dlp);
  a direct video file link (e.g. the .mp4 behind an Ad Library video) is fetched as is.
  If both fail, save the video yourself and pass the file.
"""
import importlib.util, json, re, shutil, subprocess, sys
from pathlib import Path


def run(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def fetch(src, out):
    if Path(src).exists():
        return Path(src)
    error = "yt-dlp not installed"
    ytdlp = ["yt-dlp"] if shutil.which("yt-dlp") else [sys.executable, "-m", "yt_dlp"] if importlib.util.find_spec("yt_dlp") else None
    if ytdlp:
        r = run([*ytdlp, "-q", "--no-playlist", "-f", "mp4/best", "-o", str(out / "video.%(ext)s"), src])
        files = list(out.glob("video.*"))
        if not r.returncode and files:
            return files[0]
        error = r.stderr.strip()[:200]
    # a direct link to the video file itself
    import requests
    try:
        resp = requests.get(src, timeout=60, headers={"User-Agent": "Mozilla/5.0"})
    except requests.RequestException as e:
        resp, error = None, f"{error}; direct download: {type(e).__name__}"
    if resp is not None and resp.ok and resp.headers.get("content-type", "").startswith("video/"):
        path = out / "video.mp4"
        path.write_bytes(resp.content)
        return path
    sys.exit(f"download failed ({error}) - save the video yourself and pass the file path")


def scene_cuts(video):
    """Cut times: PySceneDetect's AdaptiveDetector when installed (benchmarked on short web clips),
    else ffmpeg's scene score above 0.3."""
    try:
        from scenedetect import AdaptiveDetector, detect
        scenes = detect(str(video), AdaptiveDetector())
        seconds = lambda tc: tc.seconds if isinstance(getattr(type(tc), "seconds", None), property) else tc.get_seconds()
        return [round(seconds(s[0]), 2) for s in scenes[1:]], "pyscenedetect adaptive"
    except ImportError:
        log = run(["ffmpeg", "-i", str(video), "-vf", "select='gt(scene,0.3)',showinfo", "-f", "null", "-"]).stderr
        return sorted({round(float(x), 2) for x in re.findall(r"pts_time:([\d.]+)", log)}), "ffmpeg scene > 0.3"


def main(src, out):
    out = Path(out); out.mkdir(parents=True, exist_ok=True)
    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            sys.exit(f"{tool} not found - install ffmpeg, or mark frame-based parameters as not visible")
    video = fetch(src, out)
    dur = float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)]).stdout.strip() or 0)
    if not dur:
        sys.exit("could not read the video duration")
    step = 1 if dur <= 30 else 2
    frames = []
    t = 0.0
    while t < dur:
        name = f"{t:g}s.jpg"
        run(["ffmpeg", "-v", "error", "-y", "-ss", f"{t}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(out / name)])
        if (out / name).exists():
            frames.append({"time_s": t, "file": name})
        t += step
    end = max(dur - 0.2, 0)
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{end:.2f}", "-i", str(video), "-frames:v", "1", "-q:v", "3", str(out / "end.jpg")])
    if (out / "end.jpg").exists():
        frames.append({"time_s": round(end, 2), "file": "end.jpg"})
    cuts, method = scene_cuts(video)
    info = {"duration_s": round(dur, 2), "frames": frames, "cuts_s": cuts, "cuts_method": method}
    (out / "frames.json").write_text(json.dumps(info, indent=1), encoding="utf-8")
    print(f"{len(frames)} frames, {len(cuts)} cuts, {dur:.1f} s -> {out}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    main(sys.argv[1], sys.argv[2])
