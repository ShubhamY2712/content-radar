"""Report kit: turns a Jinja2 layout plus data into one self-contained HTML file.

Fonts, icons, CSS, JS and images are all embedded, so the output opens anywhere
with no internet and no extra files.
"""
import base64
import io
import re
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup
from PIL import Image

KIT = Path(__file__).resolve().parent

FONTS = [
    ("Fraunces", 400, "normal", "fraunces-latin-400-normal.woff2"),
    ("Fraunces", 500, "normal", "fraunces-latin-500-normal.woff2"),
    ("Fraunces", 600, "normal", "fraunces-latin-600-normal.woff2"),
    ("IBM Plex Sans", 400, "normal", "ibm-plex-sans-latin-400-normal.woff2"),
    ("IBM Plex Sans", 500, "normal", "ibm-plex-sans-latin-500-normal.woff2"),
    ("IBM Plex Sans", 600, "normal", "ibm-plex-sans-latin-600-normal.woff2"),
    ("IBM Plex Sans Devanagari", 400, "normal", "ibm-plex-sans-devanagari-devanagari-400-normal.woff2"),
    ("IBM Plex Sans Devanagari", 500, "normal", "ibm-plex-sans-devanagari-devanagari-500-normal.woff2"),
]


def font_css():
    rules = []
    for family, weight, style, file in FONTS:
        data = base64.b64encode((KIT / "fonts" / file).read_bytes()).decode()
        rules.append(
            f"@font-face{{font-family:'{family}';font-style:{style};font-weight:{weight};"
            f"font-display:swap;src:url(data:font/woff2;base64,{data}) format('woff2');}}"
        )
    return "\n".join(rules)


def icon(name, cls="rk-icon"):
    """Inline a Phosphor icon (regular weight) by name."""
    path = KIT / "icons" / "phosphor-regular" / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(f"Icon not in kit: {name}")
    svg = path.read_text(encoding="utf-8")
    svg = svg.replace("<svg ", f'<svg class="{cls}" aria-hidden="true" focusable="false" ', 1)
    return Markup(svg)


_image_cache = {}


def image_uri(path, max_w=480, quality=74):
    """Downscale an image and return it as a JPEG data URI (cached per call args)."""
    key = (str(path), max_w, quality)
    if key not in _image_cache:
        im = Image.open(path).convert("RGB")
        if im.width > max_w:
            im = im.resize((max_w, round(im.height * max_w / im.width)), Image.LANCZOS)
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=quality, optimize=True, progressive=True)
        _image_cache[key] = "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()
    return _image_cache[key]


def mark(text, phrase):
    """Wrap the first occurrence of phrase in text with the highlight mark."""
    from markupsafe import escape
    text, phrase = str(escape(text)), str(escape(phrase))
    if phrase and phrase in text:
        text = text.replace(phrase, f'<mark class="rk-mark">{phrase}</mark>', 1)
    return Markup(text)


def scatter_map(points, x_axis, y_axis, width=760, height=440):
    """Two-axis positioning map as inline SVG.

    points: [{"label", "x", "y" (0-1), "color", "emphasis": bool}]
    x_axis / y_axis: {"label", "low", "high"}
    """
    from markupsafe import escape as e
    pad_l, pad_r, pad_t, pad_b = 44, 20, 16, 56
    w, h = width - pad_l - pad_r, height - pad_t - pad_b
    inset = 0.08  # keep points off the frame and the corner labels
    span = lambda v: inset + (1 - 2 * inset) * max(0.0, min(1.0, float(v)))
    px = lambda v: pad_l + span(v) * w
    py = lambda v: pad_t + (1 - span(v)) * h
    out = [f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="Positioning map: '
           f'{e(x_axis["label"])} against {e(y_axis["label"])}" font-family="IBM Plex Sans, sans-serif">']
    out.append(f'<rect x="{pad_l}" y="{pad_t}" width="{w}" height="{h}" fill="#FCFAF5" stroke="#D9D0BF"/>')
    out.append(f'<line x1="{pad_l + w / 2}" y1="{pad_t}" x2="{pad_l + w / 2}" y2="{pad_t + h}" stroke="#D9D0BF" stroke-dasharray="4 4"/>')
    out.append(f'<line x1="{pad_l}" y1="{pad_t + h / 2}" x2="{pad_l + w}" y2="{pad_t + h / 2}" stroke="#D9D0BF" stroke-dasharray="4 4"/>')
    out.append(f'<text x="{pad_l}" y="{height - 30}" font-size="12" fill="#6B655A">{e(x_axis["low"])}</text>')
    out.append(f'<text x="{pad_l + w}" y="{height - 30}" font-size="12" fill="#6B655A" text-anchor="end">{e(x_axis["high"])}</text>')
    out.append(f'<text x="{pad_l + w / 2}" y="{height - 10}" font-size="13" font-weight="500" fill="#4A463E" text-anchor="middle">{e(x_axis["label"])}</text>')
    out.append(f'<text x="{pad_l + 8}" y="{pad_t + h - 10}" font-size="12" fill="#6B655A">{e(y_axis["low"])}</text>')
    out.append(f'<text x="{pad_l + 8}" y="{pad_t + 18}" font-size="12" fill="#6B655A">{e(y_axis["high"])}</text>')
    out.append(f'<text transform="translate(16 {pad_t + h / 2}) rotate(-90)" font-size="13" font-weight="500" fill="#4A463E" text-anchor="middle">{e(y_axis["label"])}</text>')
    for p in points:
        x, y, r = px(p["x"]), py(p["y"]), 13 if p.get("emphasis") else 10
        anchor, dx = ("end", -r - 6) if x > pad_l + w * 0.8 else ("start", r + 6)
        out.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{r}" fill="{p["color"]}" stroke="#fff" stroke-width="2"/>')
        out.append(f'<text x="{x + dx:.1f}" y="{y + 4:.1f}" font-size="13" font-weight="500" fill="#1C1B18" text-anchor="{anchor}">{e(p["label"])}</text>')
    out.append("</svg>")
    return Markup("".join(out))


def render(layout, context, extra_template_dirs=()):
    env = Environment(
        loader=FileSystemLoader([str(KIT / "layouts"), *map(str, extra_template_dirs)]),
        autoescape=select_autoescape(["html", "j2"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )
    env.globals.update(icon=icon, image_uri=image_uri, mark=mark)
    html = env.get_template(layout).render(
        kit_fonts=Markup(font_css()),
        kit_css=Markup((KIT / "kit.css").read_text(encoding="utf-8")),
        kit_js=Markup((KIT / "kit.js").read_text(encoding="utf-8")),
        **context,
    )
    return re.sub(r"\n\s*\n+", "\n", html)
