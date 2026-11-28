"""Save a brand logo for the HTML report (read-only download).

  python tools/fetch_logo.py runs/<run> C<n> <website or image URL>

Given a website, picks its largest apple-touch-icon / icon link (falls back to
/apple-touch-icon.png and /favicon.ico). Given an image URL (for example an Instagram
profile picture), uses it directly. Saves a square PNG as media/logos/C<n>.png and
prints the path to put in report_content.json "logos". Exit 1 if no usable image.
"""
import io
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin

import requests
from PIL import Image

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/131 Safari/537.36"}
MIN_SIZE = 48


class Icons(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        rel = (a.get("rel") or "").lower()
        if tag == "link" and a.get("href") and ("icon" in rel):
            sizes = re.findall(r"(\d+)x\d+", a.get("sizes") or "")
            size = max(map(int, sizes)) if sizes else (180 if "apple" in rel else 32)
            self.found.append((size, a["href"]))


def image_from(url):
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    if "svg" in r.headers.get("content-type", "") or url.lower().endswith(".svg"):
        return None  # vector icons need a browser to rasterise; try the next candidate
    im = Image.open(io.BytesIO(r.content))
    if getattr(im, "n_frames", 1) > 1 or im.format == "ICO":
        im.seek(0)
        if im.format == "ICO" and hasattr(im, "ico"):
            im = im.ico.getimage(max(im.ico.sizes()))
    return im.convert("RGBA")


def candidates(url):
    if re.search(r"\.(png|jpe?g|webp|ico)(\?|$)", url, re.I) or "cdninstagram" in url or "fbcdn" in url:
        return [url]
    r = requests.get(url, headers=UA, timeout=20)
    r.raise_for_status()
    p = Icons()
    p.feed(r.text)
    found = [urljoin(r.url, h) for _, h in sorted(p.found, reverse=True)]
    return found + [urljoin(r.url, "/apple-touch-icon.png"), urljoin(r.url, "/favicon.ico")]


def square(im, size=256):
    side = max(im.size)
    canvas = Image.new("RGBA", (side, side), (255, 255, 255, 0))
    canvas.paste(im, ((side - im.width) // 2, (side - im.height) // 2))
    return canvas.resize((size, size), Image.LANCZOS) if side > size else canvas


def main(run, key, url):
    if not re.fullmatch(r"C\d+", key):
        sys.exit("second argument must be C0, C1, C2 ...")
    for cand in candidates(url):
        try:
            im = image_from(cand)
        except (requests.RequestException, OSError):
            continue
        if im is None or min(im.size) < MIN_SIZE:
            continue
        out = Path(run) / "media" / "logos" / f"{key}.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        square(im).save(out)
        print(f"media/logos/{key}.png  ({im.size[0]}x{im.size[1]} from {cand})")
        return 0
    print(f"no usable logo at {url} (need a PNG/JPG/ICO of {MIN_SIZE}px or more); try the brand's Instagram profile picture URL")
    return 1


if __name__ == "__main__":
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    sys.exit(main(*sys.argv[1:]))
