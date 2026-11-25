"""Read-only Instagram Business Discovery helper.

Needs IG_USER_ID and IG_ACCESS_TOKEN (environment or .env): your own Instagram professional
(Business or Creator) account, linked to a Facebook Page, and a Meta developer app token with
instagram_basic + pages_read_engagement. Works only for public Business / Creator accounts.

  python tools/instagram.py media --username <handle> [--max 12]

Prints JSON: the account's follower count and its recent posts (link, type, caption, date,
likes, comments, media URL or thumbnail).
"""
import argparse, json, os, sys
from pathlib import Path
import requests

GRAPH = "https://graph.facebook.com/v26.0/"
FIELDS = "id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count,media_url,thumbnail_url"


def env(name):
    f = Path(__file__).resolve().parent.parent / ".env"
    if f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.startswith(name + "="):
                os.environ.setdefault(name, line.split("=", 1)[1].strip())
    v = os.environ.get(name)
    if not v:
        sys.exit(f"{name} not set - skip this source and note it in log.md")
    return v


def media(username, limit):
    q = f"business_discovery.username({username}){{followers_count,media_count,media.limit({limit}){{{FIELDS}}}}}"
    r = requests.get(GRAPH + env("IG_USER_ID"), params={"fields": q, "access_token": env("IG_ACCESS_TOKEN")}, timeout=30)
    if r.status_code != 200:
        sys.exit(f"Instagram API error {r.status_code}: {r.json().get('error', {}).get('message', r.text[:200])}")
    bd = r.json()["business_discovery"]
    posts = [{"link": m["permalink"], "type": m.get("media_product_type") or m["media_type"],
              "caption": m.get("caption", ""), "published": m["timestamp"][:10],
              "likes": m.get("like_count"), "comments": m.get("comments_count"),
              "media": m.get("media_url") or m.get("thumbnail_url")}
             for m in bd.get("media", {}).get("data", [])]
    return {"username": username, "followers": bd.get("followers_count"), "posts": posts}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["media"])
    ap.add_argument("--username", required=True)
    ap.add_argument("--max", type=int, default=12)
    a = ap.parse_args()
    print(json.dumps(media(a.username.lstrip("@"), a.max), ensure_ascii=False, indent=1))
