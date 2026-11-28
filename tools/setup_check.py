"""Check that this machine has everything a run needs, before the run starts.

  python tools/setup_check.py          report only
  python tools/setup_check.py --fix    also do the fixes that need no person (installs, copies, downloads)

Each line is OK, MISSING or WARN with what a gap costs the run and how to fix it.
Exit code 0 = ready (no required item missing), 1 = not ready.

Fixed by --fix: Python packages (requirements.txt + faster-whisper, an old yt-dlp updated), .env from
.env.example, Claude Code files (.claude/agents, .claude/settings.json, .mcp.json), browsers pointed at
auth.json, measuring and speech models.
Only a person can fix: ffmpeg, Node.js, Chrome, internet access, disk space and the logins in auth.json.
The live checks (browsers start, logins still work) are done by the agent at the start of the run.
"""
import datetime, importlib.util, json, os, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUTH = ROOT / "auth.json"
CODEGEN = ("npx.cmd" if os.name == "nt" else "npx") + \
    " -y playwright@latest codegen --channel chrome --save-storage=auth.json https://www.instagram.com"
PACKAGES = {"jsonschema": "jsonschema", "requests": "requests", "youtube_transcript_api": "youtube-transcript-api",
            "yt_dlp": "yt-dlp", "numpy": "numpy", "cv2": "opencv-python-headless", "rapidocr": "rapidocr",
            "onnxruntime": "onnxruntime", "scenedetect": "scenedetect", "jinja2": "jinja2", "PIL": "Pillow"}

results = []  # (status, item, detail, fix)


def add(ok, item, cost, fix, required=True):
    results.append(("OK" if ok else "MISSING" if required else "WARN", item, "" if ok else cost, "" if ok else fix))
    return ok


def pip(*args):
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *args])


def ytdlp_age_days():
    try:
        from importlib.metadata import version as dist_version
        y, m, d = (int(x) for x in dist_version("yt-dlp").split(".")[:3])
        return (datetime.date.today() - datetime.date(y, m, d)).days
    except Exception:
        return None


def whisper_cached():
    try:
        from huggingface_hub import try_to_load_from_cache
        return isinstance(try_to_load_from_cache("Systran/faster-whisper-small", "model.bin"), str)
    except Exception:
        return False


def reachable(url):
    import requests
    try:
        return requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"}).status_code < 500
    except requests.RequestException:
        return False


def version(cmd):
    try:
        out = subprocess.run([*cmd, "--version"], capture_output=True, text=True, timeout=30).stdout
        return re.search(r"(\d+)\.(\d+)", out)
    except (OSError, subprocess.TimeoutExpired):
        return None


def chrome_installed():
    if os.name == "nt":
        bases = [os.environ.get(k, "") for k in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA")]
        return any(Path(b, "Google", "Chrome", "Application", "chrome.exe").exists() for b in bases if b)
    if sys.platform == "darwin":
        return Path("/Applications/Google Chrome.app").exists()
    return any(shutil.which(n) for n in ("google-chrome", "google-chrome-stable"))


def logins():
    """Which sites auth.json is logged in to, by their session cookies (not expired)."""
    try:
        cookies = json.loads(AUTH.read_text(encoding="utf-8")).get("cookies", [])
    except (OSError, ValueError):
        return None
    now = time.time()
    live = {(c["domain"].lstrip("."), c["name"]) for c in cookies if c.get("expires", -1) in (-1, None) or c["expires"] > now}
    return {"Instagram": ("instagram.com", "sessionid") in live,
            "Facebook": ("facebook.com", "c_user") in live and ("facebook.com", "xs") in live}


def read_json(path):
    text = path.read_text(encoding="utf-8")
    return json.loads(re.sub(r"^\s*//.*$", "", text, flags=re.M))


def browser_configs():
    """(file, servers key, args field, storage-state path) for each browser config on this machine."""
    out = []
    oc = ROOT / "opencode.jsonc"
    if oc.exists():
        out.append((oc, "mcp", "command", "auth.json"))
    mc = ROOT / ".mcp.json"
    if mc.exists():
        out.append((mc, "mcpServers", "args", str(AUTH)))
    return out


def point_browsers(fix):
    """Browsers must load auth.json when it exists, and must not ask for it when it does not
    (a missing --storage-state file stops the browser from starting)."""
    for path, key, field, value in browser_configs():
        data = read_json(path)
        changed = False
        for name, server in data.get(key, {}).items():
            args = server.get(field, [])
            if not name.startswith("browser"):
                continue
            if AUTH.exists() and "--storage-state" not in args:
                args += ["--storage-state", value]
                changed = True
            elif AUTH.exists() and args[args.index("--storage-state") + 1] != value:
                args[args.index("--storage-state") + 1] = value  # stale path, e.g. after the folder was moved
                changed = True
            elif not AUTH.exists() and "--storage-state" in args:
                i = args.index("--storage-state")
                del args[i:i + 2]
                changed = True
        if changed and fix:
            path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        add(not changed or fix, f"Browsers in {path.name} match auth.json",
            "browsers start without the saved logins" if AUTH.exists() else "browsers fail to start (auth.json is missing)",
            "python tools/setup_check.py --fix")


def main(fix):
    # Python and packages
    add(sys.version_info >= (3, 10), "Python 3.10+", "the tools do not run", "install Python 3.10 or newer")
    missing = [pkg for mod, pkg in PACKAGES.items() if importlib.util.find_spec(mod) is None]
    if missing and fix:
        pip("-r", str(ROOT / "requirements.txt"))
        missing = [pkg for mod, pkg in PACKAGES.items() if importlib.util.find_spec(mod) is None]
    add(not missing, "Python packages", f"missing {', '.join(missing)}: no frames, measures or YouTube lists",
        "pip install -r requirements.txt")
    if importlib.util.find_spec("faster_whisper") is None and fix:
        pip("faster-whisper")
    add(importlib.util.find_spec("faster_whisper") is not None, "faster-whisper (speech to text)",
        "spoken words of Instagram, Facebook and ad videos are not transcribed", "pip install faster-whisper",
        required=False)
    age = ytdlp_age_days()
    if age is not None and age > 45 and fix:
        pip("-U", "yt-dlp")
        age = ytdlp_age_days()
    add(age is None or age <= 45, "yt-dlp up to date",
        f"yt-dlp is {age} days old: sites change often, so video downloads may fail", "pip install -U yt-dlp",
        required=False)

    # programs
    winget = os.name == "nt"
    add(bool(shutil.which("ffmpeg") and shutil.which("ffprobe")), "ffmpeg + ffprobe",
        "no frames, cut times or sound facts from videos",
        "winget install ffmpeg (then open a new terminal)" if winget else "install ffmpeg (brew / apt)")
    node = version(["node"])
    add(bool(node and int(node.group(1)) >= 18 and shutil.which("npx")), "Node.js 18+ (npx)",
        "the browsers cannot start: no Instagram, Facebook, Ad Library or Google Ads pages",
        "winget install OpenJS.NodeJS.LTS" if winget else "install Node.js 18+ from nodejs.org")
    add(chrome_installed(), "Google Chrome", "the browsers cannot start", "install Google Chrome")

    # host files
    claude_agents = ROOT / ".claude" / "agents"
    have = claude_agents.exists() and all((claude_agents / f.name).exists()
                                          for f in (ROOT / "setup/claude-code/agents").glob("*.md"))
    if fix and not have:
        claude_agents.mkdir(parents=True, exist_ok=True)
        for f in (ROOT / "setup/claude-code/agents").glob("*.md"):
            shutil.copy(f, claude_agents / f.name)
        have = True
    if fix and not (ROOT / ".mcp.json").exists():
        shutil.copy(ROOT / "setup/claude-code/mcp.json", ROOT / ".mcp.json")
    settings = ROOT / ".claude" / "settings.json"
    if fix and not settings.exists():
        settings.parent.mkdir(exist_ok=True)
        shutil.copy(ROOT / "setup/claude-code/settings.json", settings)
    add(have and (ROOT / ".mcp.json").exists() and settings.exists(),
        "Claude Code team, browsers and permissions (.claude/, .mcp.json)",
        "in Claude Code: no workers or browsers, or the run stops at every tool for your approval "
        "(OpenCode does not need these)", "python tools/setup_check.py --fix", required=False)
    if fix and not (ROOT / ".env").exists() and (ROOT / ".env.example").exists():
        shutil.copy(ROOT / ".env.example", ROOT / ".env")

    # logins
    state = logins()
    if state is None:
        add(False, "Saved logins (auth.json)",
            "Instagram, Facebook pages and Meta Ad Library show a login wall: most ads and posts are lost",
            f"run {CODEGEN} and log in to Instagram, then Facebook, in that window (use a spare account); close it")
    else:
        add(state["Instagram"], "Instagram login in auth.json", "Instagram posts and Reels are lost",
            f"run {CODEGEN} again and log in to Instagram and Facebook in the same window")
        add(state["Facebook"], "Facebook login in auth.json",
            "Facebook pages, and Meta Ad Library when it asks for a login, are lost",
            f"run {CODEGEN} again and log in to Instagram and Facebook in the same window", required=False)
    point_browsers(fix)

    # measuring models (downloaded once)
    sys.path.insert(0, str(ROOT / "tools"))
    models = ROOT / "tools" / "models"
    if fix and importlib.util.find_spec("cv2"):
        import measure
        measure.model_file(*measure.YUNET)
        try:
            measure.ocr_engines(True)
        except Exception:
            pass
    if fix and importlib.util.find_spec("onnxruntime"):
        import transcript
        transcript.yamnet_session()
    if fix and importlib.util.find_spec("faster_whisper") and not whisper_cached():
        try:
            from faster_whisper import WhisperModel
            WhisperModel("small", device="cpu", compute_type="int8")  # about 0.5 GB, once
        except Exception:
            pass
    add((models / "face_detection_yunet_2023mar.onnx").exists(), "Face model", "faces are judged by eye",
        "python tools/setup_check.py --fix", required=False)
    add((models / "yamnet.onnx").exists(), "Sound model (YAMNet)", "music vs speech is judged without measures",
        "python tools/setup_check.py --fix", required=False)
    spec = importlib.util.find_spec("rapidocr")
    hindi = spec and any("devanagari" in p.name.lower() for p in Path(spec.origin).parent.glob("models/*"))
    add(bool(hindi), "Hindi OCR model", "Hindi on-creative text is read by eye",
        "python tools/setup_check.py --fix", required=False)

    if importlib.util.find_spec("faster_whisper"):
        add(whisper_cached(), "Speech model (Whisper small)",
            "downloaded during the run instead (about 0.5 GB); fails if the download is blocked",
            "python tools/setup_check.py --fix", required=False)

    # machine
    free_gb = shutil.disk_usage(ROOT).free / 1e9
    add(free_gb >= 3, "Free disk space (3 GB+)", f"only {free_gb:.1f} GB free: videos and frames may not save",
        "free some space on this drive")
    if importlib.util.find_spec("requests"):
        sites = {"YouTube": "https://www.youtube.com", "Instagram": "https://www.instagram.com",
                 "Meta Ad Library": "https://www.facebook.com/ads/library/",
                 "Google Ads Transparency": "https://adstransparency.google.com"}
        down = [name for name, url in sites.items() if not reachable(url)]
        add(not down, "Internet: YouTube, Instagram, Ad Library, Google Ads",
            f"cannot reach {', '.join(down)}", "check the internet connection, VPN or firewall")

    # optional keys
    env = (ROOT / ".env").read_text(encoding="utf-8") if (ROOT / ".env").exists() else ""
    def key(name):
        return bool(os.environ.get(name) or re.search(rf"^{name}=\S+", env, re.M))
    add(key("YOUTUBE_API_KEY"), "YOUTUBE_API_KEY (optional)", "YouTube lists come from yt-dlp instead (works, slower)",
        "add the key to .env", required=False)
    add(key("IG_USER_ID") and key("IG_ACCESS_TOKEN"), "Instagram API keys (optional)",
        "organic posts are read through the logged-in browser instead", "see README > Before your first run",
        required=False)

    width = max(len(r[1]) for r in results)
    for status, item, cost, todo in results:
        line = f"{status:8} {item:{width}}"
        if cost:
            line += f"  - {cost}. Fix: {todo}"
        print(line)
    ready = not any(r[0] == "MISSING" for r in results)
    print("\nREADY" if ready else "\nNOT READY: fix the MISSING lines before the run")
    return 0 if ready else 1


if __name__ == "__main__":
    sys.exit(main("--fix" in sys.argv[1:]))
