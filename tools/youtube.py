"""Read-only YouTube helper: a channel's recent videos and Shorts with their public numbers.

  python tools/youtube.py videos --channel <channel URL | @handle | channel id> [--days 90] [--max 10]

Prints JSON: one item per recent video (uploads and Shorts), newest first, with link, title,
description, published date, duration in seconds, views, likes, comments and thumbnail URL.
- With YOUTUBE_API_KEY (environment or .env): YouTube Data API v3, about 3 quota units per call.
- Without a key: yt-dlp (pip install yt-dlp) reads the channel's Videos and Shorts tabs;
  slower (one page per video) and likes/comments are null when YouTube hides them.
"""
import argparse, json, os, re, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

API = "https://www.googleapis.com/youtube/v3/"


def key():
    env = Path(__file__).resolve().parent.parent / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            if line.startswith("YOUTUBE_API_KEY="):
                os.environ.setdefault("YOUTUBE_API_KEY", line.split("=", 1)[1].strip())
    return os.environ.get("YOUTUBE_API_KEY")


def get(path, **params):
    r = requests.get(API + path, params={**params, "key": key()}, timeout=30)
    if r.status_code != 200:
        sys.exit(f"YouTube API error {r.status_code}: {r.json().get('error', {}).get('message', r.text[:200])}")
    return r.json()


def channel_id(ref):
    m = re.search(r"(UC[\w-]{22})", ref)
    if m:
        return m.group(1)
    handle = re.search(r"@([\w.-]+)", ref)
    items = get("channels", part="id", forHandle="@" + handle.group(1)).get("items") if handle else None
    if not items:
        sys.exit(f"channel not found: {ref}")
    return items[0]["id"]


def seconds(iso):
    h, m, s = (int(x or 0) for x in re.fullmatch(r"P(?:\d+D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso).groups())
    return h * 3600 + m * 60 + s


def videos(ref, days, limit):
    cid = channel_id(ref)
    uploads = "UU" + cid[2:]  # the channel's uploads playlist
    items = get("playlistItems", part="contentDetails", playlistId=uploads, maxResults=50)["items"]
    since = datetime.now(timezone.utc) - timedelta(days=days)
    ids = [i["contentDetails"]["videoId"] for i in items
           if datetime.fromisoformat(i["contentDetails"]["videoPublishedAt"].replace("Z", "+00:00")) >= since][:limit]
    if not ids:
        return []
    out = []
    for v in get("videos", part="snippet,contentDetails,statistics", id=",".join(ids))["items"]:
        s, st = v["snippet"], v.get("statistics", {})
        out.append({"link": f"https://www.youtube.com/watch?v={v['id']}", "title": s["title"],
                    "description": s["description"], "published": s["publishedAt"][:10],
                    "duration_s": seconds(v["contentDetails"]["duration"]),
                    "views": int(st.get("viewCount", 0)), "likes": int(st.get("likeCount", 0)),
                    "comments": int(st.get("commentCount", 0)),
                    "thumbnail": max(s["thumbnails"].values(), key=lambda t: t.get("width", 0))["url"]})
    return out


def channel_url(ref):
    if ref.startswith("http"):
        return ref.rstrip("/").removesuffix("/videos").removesuffix("/shorts")
    if re.fullmatch(r"UC[\w-]{22}", ref):
        return f"https://www.youtube.com/channel/{ref}"
    return "https://www.youtube.com/@" + ref.lstrip("@")


def videos_ytdlp(ref, days, limit):
    try:
        import yt_dlp
    except ImportError:
        sys.exit("no YOUTUBE_API_KEY and yt-dlp not installed - use the channel's Videos and Shorts tabs in the browser")
    since = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y%m%d")
    quiet = {"quiet": True, "no_warnings": True, "skip_download": True}
    out = []
    for tab in ("videos", "shorts"):
        try:
            with yt_dlp.YoutubeDL({**quiet, "extract_flat": True, "playlistend": 50}) as y:
                entries = (y.extract_info(f"{channel_url(ref)}/{tab}", download=False) or {}).get("entries") or []
        except yt_dlp.utils.DownloadError:
            continue  # the channel has no such tab
        with yt_dlp.YoutubeDL(quiet) as y:
            for e in entries[:limit]:  # each tab lists newest first
                try:
                    v = y.extract_info(f"https://www.youtube.com/watch?v={e['id']}", download=False)
                except yt_dlp.utils.DownloadError:
                    continue  # unavailable, private or members-only video: skip it, keep the rest
                if (v.get("upload_date") or "0") < since:
                    break
                d = v["upload_date"]
                out.append({"link": f"https://www.youtube.com/watch?v={v['id']}", "title": v.get("title"),
                            "description": v.get("description"), "published": f"{d[:4]}-{d[4:6]}-{d[6:]}",
                            "duration_s": v.get("duration"), "views": v.get("view_count"),
                            "likes": v.get("like_count"), "comments": v.get("comment_count"),
                            "thumbnail": v.get("thumbnail")})
    return sorted(out, key=lambda x: x["published"], reverse=True)[:limit]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["videos"])
    ap.add_argument("--channel", required=True)
    ap.add_argument("--days", type=int, default=90)
    ap.add_argument("--max", type=int, default=10)
    a = ap.parse_args()
    fetch = videos if key() else videos_ytdlp
    print(json.dumps(fetch(a.channel, a.days, a.max), ensure_ascii=False, indent=1))
