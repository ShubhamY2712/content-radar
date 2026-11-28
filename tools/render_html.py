"""Render a Content Radar run into two self-contained HTML reports.

  python tools/render_html.py runs/<brand>-<date>

Reads the run files plus report_content.json (written by the report-document skill)
and writes report.html (summary) and report_detailed.html (summary + every creative's
54 findings) in the run folder. Prints the problems it finds and exits 1 if any.
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from report_kit import kit  # noqa: E402

PARAMS = {p["id"]: p for p in json.loads((ROOT / "knowledge/parameters.json").read_text(encoding="utf-8"))}
PHOTO_FORMATS = {"Image", "Carousel"}
BRAND_COLOR = "#B7791F"
COMPETITOR_COLORS = ["#1F4D3A", "#3E5C76", "#6B4A5E", "#3F6E6A", "#5A5A4F"]
# Funnel stages are the B10 options in knowledge/parameters.json; colours follow their order.
STAGE_COLORS = [("#8DB3A0", True), ("#4F8A6E", False), ("#1F4D3A", False), ("#3E5C76", False), ("#6B4A5E", False)]
CORE_STAGES = 3  # always shown, so an empty stage is visible; later options only when used
# Product match levels come from schemas/creatives.schema.json, closest match first.
MATCH_LEVELS = json.loads((ROOT / "schemas/creatives.schema.json").read_text(encoding="utf-8"))[
    "properties"]["creatives"]["items"]["properties"]["product_match"]["enum"]
MATCH_STYLE = [("exact", "#1F4D3A", False), ("type", "#DCE8DF", True), ("range", "#EFE8DA", True), ("range", "#D9D0BF", True)]
MATCH = [(m, *MATCH_STYLE[min(i, len(MATCH_STYLE) - 1)]) for i, m in enumerate(MATCH_LEVELS)]
STATUS = {"gap": "Brand is behind", "lead": "Brand leads", "parity": "On par"}
IDEA_TYPES = {"Proven pattern": "lead", "Fill a gap": "gap", "New funnel stage or format": "parity"}
# recommendations.json ideas may start with their type ("Fill a gap - ..."); the card shows it as a tag
IDEA_PREFIX = re.compile(r"^\s*(proven pattern|fill a gap|(different|new) funnel stage[^-–:]*)\s*[-–:]\s*", re.I)
SHOT_COLORS = {"SH1": "#1F4D3A", "SH2": "#3F6E6A", "SH3": "#4F8A6E", "SH4": "#3E5C76",
               "SH5": "#6B4A5E", "SH6": "#B7791F", "SH7": "#86321F"}
LINKS = [("website", "globe", "Website"), ("instagram", "instagram-logo", "Instagram"),
         ("facebook", "facebook-logo", "Facebook"), ("youtube", "youtube-logo", "YouTube"),
         ("ad_library", "megaphone", "Meta Ad Library"), ("google_ads_transparency", "magnifying-glass", "Google Ads")]
IDEA_FIELDS = [("audience", "users-three", "Audience"), ("format_platform", "devices", "Format and platform"),
               ("hook", "play-circle", "Hook"), ("message_proof", "seal-check", "Message and proof"),
               ("offer_cta", "cursor-click", "Offer and CTA"), ("style_layers", "palette", "Style")]


class Report:
    def __init__(self, run):
        self.run = run
        self.problems = []
        load = lambda n: json.loads((run / n).read_text(encoding="utf-8"))
        self.brief, self.comps = load("brief.json"), load("competitors.json")
        self.creatives = {c["id"]: c for c in load("creatives.json")["creatives"]}
        self.recs = load("recommendations.json")["recommendations"]
        self.content = load("report_content.json")
        self.analysis = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in (run / "analysis").glob("*.json")}
        self.brand_name = self.comps["brand"]["name"]
        self.thumbs = self.content.get("thumbnails", {})
        self.brands = self._brands()

    # ---------- helpers ----------
    def need(self, cond, msg):
        if not cond:
            self.problems.append(msg)
        return cond

    def _brands(self):
        """C0 = the brand, C1.. = competitors in competitors.json order."""
        logos = self.content.get("logos", {})
        entries = [("C0", self.comps["brand"], BRAND_COLOR)] + \
                  [(f"C{i}", c, COMPETITOR_COLORS[(i - 1) % len(COMPETITOR_COLORS)])
                   for i, c in enumerate(self.comps["competitors"], 1)]
        out = {}
        for key, c, color in entries:
            path = logos.get(key)
            logo = None
            if path and self.need((self.run / path).exists(), f"logo for {c['name']} not found: {path}"):
                logo = kit.image_uri(self.run / path, max_w=96, quality=88)
            words = re.findall(r"[A-Za-z0-9]+", c["name"])
            initials = (words[0][:2] if len(words) == 1 else words[0][0] + words[1][0]).upper() if words else "?"
            out[c["name"]] = {"key": key, "name": c["name"], "data": c, "color": color, "logo": logo, "initials": initials}
        return out

    def brand_of(self, cid):
        return self.brands[self.creatives[cid]["competitor"]]

    def thumb(self, cid, w):
        path = self.thumbs.get(cid)
        if not self.need(path, f"no thumbnail chosen for {cid}"):
            return None
        if not self.need((self.run / path).exists(), f"thumbnail for {cid} not found: {path}"):
            return None
        return kit.image_uri(self.run / path, max_w=w)

    @staticmethod
    def kind(c):
        return "photo" if c["format"] in PHOTO_FORMATS else "video"

    def chips(self, ids, detailed):
        out = []
        for cid in ids:
            if not self.need(cid in self.creatives, f"unknown creative {cid}"):
                continue
            c = self.creatives[cid]
            out.append({"id": cid, "brand": c["competitor"], "kind": f'{c["paid_or_organic"].lower()} {self.kind(c)}',
                        "is_brand": c["competitor"] == self.brand_name, "thumb": self.thumb(cid, 120),
                        "href": f"#c-{cid}" if detailed else f"#tile-{cid}", "external": False,
                        "title": f'{cid}: {c["competitor"]}, {c["placement"]}'})
        return out

    def option(self, cid, pid):
        f = self.analysis.get(cid, {}).get("findings", {}).get(pid, {})
        return f.get("option") if f.get("visible") else None

    # ---------- sections ----------
    def cover(self):
        b = self.brief
        d = date.fromisoformat(max(c["date_seen"] for c in self.creatives.values()))
        self.date_text = f"{d.day} {d:%b %Y}"
        return {"eyebrow": "Content benchmark", "title": f'{self.brand_name} {b["product"]}', "dek": self.content["dek"],
                "meta": [{"icon": "map-pin", "text": b["market"]},
                         {"icon": "calendar-blank", "text": f'{self.date_text} · last {b["time_window_days"]} days'},
                         {"icon": "devices", "text": ", ".join(b["platforms"])}]}

    def brief_section(self):
        cr = list(self.creatives.values())
        total, market = len(cr), [c for c in cr if c["competitor"] != self.brand_name]
        paid = sum(c["paid_or_organic"] == "Paid" for c in cr)
        videos = sum(self.kind(c) == "video" for c in cr)
        exact = sum(c.get("product_match") == "Exact product" for c in market)
        same = sum(c.get("product_match") == "Same product type" for c in market)
        pct = lambda n: round(100 * n / total) if total else 0
        stats = [
            {"icon": "users-three", "value": len(self.comps["competitors"]), "label": f"competitors, plus {self.brand_name} as the baseline",
             "logos": [b for b in self.brands.values()]},
            {"icon": "images-square", "value": total, "label": f"creatives analysed ({len(market)} competitor, {total - len(market)} {self.brand_name})"},
            {"icon": "megaphone", "value": paid, "of": total, "label": f"paid ads · {total - paid} organic posts",
             "split": [{"pct": pct(paid), "color": "var(--ochre)"}, {"pct": 100 - pct(paid), "color": "var(--forest)"}]},
            {"icon": "video-camera", "value": videos, "of": total, "label": f"videos · {total - videos} photos or carousels",
             "split": [{"pct": pct(videos), "color": "var(--slate)"}, {"pct": 100 - pct(videos), "color": "var(--rule)"}]},
            {"icon": "target", "value": exact, "of": len(market),
             "label": f"competitor creatives show the exact matched product · {same} the same product type"},
        ]
        b = self.content["brief"]
        return {"paragraphs": b["paragraphs"], "method_note": b["method_note"], "stats": stats}

    def findings(self, detailed):
        f = self.content["findings"]
        self.need(3 <= len(f["items"]) <= 7, f'findings: {len(f["items"])} items, expected 3 to 7')
        items = []
        for it in f["items"]:
            self.need(it["highlight"] in it["key_line"], f'finding "{it["headline"]}": highlight is not part of the key line')
            items.append({**it, "chips": self.chips(it["creatives"], detailed)})
        return {"lede": f["lede"], "items": items}

    def competitors(self):
        c = self.content["competitors"]
        rows = []
        for b in self.brands.values():
            d = b["data"]
            mine = [x for x in self.creatives.values() if x["competitor"] == b["name"]]
            why = c["why"].get(b["name"]) if b["key"] != "C0" else c.get("baseline_why")
            self.need(why, f'competitors: no "why" for {b["name"]}')
            rows.append({"brand": b, "is_brand": b["key"] == "C0", "why": why or "",
                         "product": d.get("product_name") or "", "product_page": d.get("product_page"),
                         "links": [{"url": d[k], "icon": i, "label": l} for k, i, l in LINKS if d.get(k)],
                         "paid": sum(x["paid_or_organic"] == "Paid" for x in mine),
                         "organic": sum(x["paid_or_organic"] != "Paid" for x in mine)})
        rows = rows[1:] + rows[:1]  # competitors first, baseline last
        market = [x for x in self.creatives.values() if x["competitor"] != self.brand_name]
        n = len(market) or 1
        match = []
        for label, _, color, light in MATCH:
            k = sum(x.get("product_match") == label for x in market)
            match.append({"label": label, "n": k, "pct": round(100 * k / n), "color": color, "light": light})
        return {"lede": c["lede"], "selection_rule": c["selection_rule"], "creative_rule": c["creative_rule"],
                "rows": rows, "match": match, "match_total": len(market), "gaps": c.get("gaps", [])}

    def notes(self, detailed):
        n = self.content["competitor_notes"]
        brands = []
        for b in n["brands"]:
            if not self.need(b["name"] in self.brands, f'competitor note for unknown brand {b["name"]}'):
                continue
            sid = b["standout"]["creative"]
            ok = self.need(sid in self.creatives, f"standout creative {sid} unknown")
            brands.append({**b, "brand": self.brands[b["name"]],
                           "standout": {"id": sid, "why": b["standout"]["why"],
                                        "thumb": self.thumb(sid, 160) if ok else None,
                                        "href": f"#c-{sid}" if detailed else f"#tile-{sid}"}})
        return {"summary": n["summary"], "brands": brands}

    def brand_vs_market(self, detailed):
        v = self.content["brand_vs_market"]
        def items(rows):
            out = []
            for it in rows:
                self.need(it["parameter"] in PARAMS, f'brand vs market: unknown parameter {it["parameter"]}')
                out.append({**it, "chips": self.chips(it["creatives"], detailed)})
            return out
        cols = [{"title": f"Where {self.brand_name} is behind", "icon": "trend-down", "lead": False, "items": items(v["gaps"]),
                 "empty": f"No parameter in this set where {self.brand_name} is clearly behind."},
                {"title": f"Where {self.brand_name} leads", "icon": "trend-up", "lead": True, "items": items(v["strengths"]),
                 "empty": f"No parameter in this set where {self.brand_name} clearly leads."}]
        out = {"lede": v["lede"], "columns": cols, "brand_name": self.brand_name, "map": None}
        m = self.content.get("positioning_map")
        if m:
            pts = []
            for p in m["points"]:
                if self.need(p["brand"] in self.brands, f'positioning map: unknown brand {p["brand"]}'):
                    b = self.brands[p["brand"]]
                    pts.append({"label": b["name"], "x": p["x"], "y": p["y"], "color": b["color"], "emphasis": b["key"] == "C0"})
            out["map"] = {"svg": kit.scatter_map(pts, m["x"], m["y"]), "reason": m["reason"],
                          "subtitle": f'{m["x"]["label"]} (across) and {m["y"]["label"]} (up), placed from each brand\'s creatives'}
        return out

    def funnel(self, detailed):
        options = PARAMS["B10"]["options"]
        used = {self.option(cid, "B10") for cid in self.creatives}
        STAGES = [(o, *STAGE_COLORS[i % len(STAGE_COLORS)]) for i, o in enumerate(options)
                  if i < CORE_STAGES or o in used]
        rows, stage_ids = [], {s: [] for s, _, _ in STAGES}
        for b in self.brands.values():
            mine = [cid for cid, c in self.creatives.items() if c["competitor"] == b["name"]]
            counts = {s: 0 for s, _, _ in STAGES}
            for cid in mine:
                opt = self.option(cid, "B10")
                if opt in counts:
                    counts[opt] += 1
                    stage_ids[opt].append(cid)
            total = len(mine) or 1
            rows.append({"brand": b, "total": len(mine), "stages": [
                {"label": s, "n": counts[s], "pct": round(100 * counts[s] / total), "color": col, "light": light}
                for s, col, light in STAGES]})
        rows = rows[1:] + rows[:1]
        return {"subtitle": "Share of each brand's creatives built for each stage (B10)", "rows": rows,
                "stages": [{"label": s, "color": col} for s, col, _ in STAGES],
                "map": [{"label": s, "color": col, "chips": self.chips(sorted(stage_ids[s]), detailed)} for s, col, _ in STAGES],
                "note": self.content.get("funnel_note")}

    def table(self, key, part, detailed):
        t = self.content[key]
        fmts = {"Video" if c["format"] == "Video" else "Image" for c in self.creatives.values()}
        expected = {pid for pid, p in PARAMS.items() if pid.startswith(part)
                    and (p["applies_to"] == "Both" or p["applies_to"] in fmts)}
        seen = [r["parameter"] for r in t["rows"]]
        self.need(set(seen) == expected and len(seen) == len(expected),
                  f"{key}: needs each {part} parameter that applies to this run's formats once; missing {sorted(expected - set(seen))}, extra {sorted(set(seen) - expected)}")
        rows = []
        for r in t["rows"]:
            self.need(r["status"] in STATUS, f'{key} {r["parameter"]}: status must be gap, lead or parity')
            rows.append({**r, "id": r["parameter"], "name": PARAMS.get(r["parameter"], {}).get("name", ""),
                         "status_label": STATUS.get(r["status"], r["status"]),
                         "chips": self.chips(r.get("evidence", []), detailed)})
        return {"lede": t["lede"], "rows": rows}

    def clean_idea(self, text):
        """Drop a leading type label; capitalise unless it now starts with a brand name (boAt stays boAt)."""
        rest = IDEA_PREFIX.sub("", text, count=1)
        if rest == text or any(rest.startswith(n) for n in self.brands):
            return rest
        return rest[:1].upper() + rest[1:]

    def ideas(self, detailed):
        meta = self.content["ideas"]["items"]
        self.need(len(meta) == len(self.recs), f"ideas: {len(meta)} items for {len(self.recs)} recommendations")
        items = []
        for k, (r, m) in enumerate(zip(self.recs, meta), 1):
            self.need(m["type"] in IDEA_TYPES, f'idea {k}: type must be one of {list(IDEA_TYPES)}')
            ids = [b for b in r["based_on"] if b in self.creatives]
            items.append({"no": f"{k:02d}", "type": m["type"], "type_class": IDEA_TYPES.get(m["type"], "parity"),
                          "title": m["title"], "why": m["why"], "idea": self.clean_idea(r["idea"]),
                          "fields": [{"icon": i, "label": l, "text": r[f]} for f, i, l in IDEA_FIELDS],
                          "chips": self.chips(ids, detailed)})
        return {"lede": self.content["ideas"]["lede"], "items": items}

    def signal(self, c):
        bits = []
        if c.get("days_running"):
            bits.append(f'running {c["days_running"]} days')
        if c.get("versions"):
            bits.append(f'{c["versions"]} versions')
        if c.get("views"):
            bits.append(f'{compact(c["views"])} views')
        elif c.get("likes"):
            bits.append(f'{compact(c["likes"])} likes')
        if c.get("comments"):
            bits.append(f'{compact(c["comments"])} comments')
        return ", ".join(bits)

    def gallery(self):
        why = self.content.get("why_selected", {})
        tiles = []
        order = sorted(self.creatives, key=lambda i: (i.startswith("C0-"), i))
        for cid in order:
            c = self.creatives[cid]
            self.need(why.get(cid), f"why_selected missing for {cid}")
            m = next((x for x in MATCH if x[0] == c.get("product_match")), MATCH[-1])
            tiles.append({"id": cid, "brand": self.brand_of(cid), "is_brand": c["competitor"] == self.brand_name,
                          "thumb": self.thumb(cid, 420), "paid": c["paid_or_organic"] == "Paid",
                          "format": c["format"], "placement": c["placement"], "match": m[0], "match_class": m[1],
                          "signal": self.signal(c), "why": why.get(cid, ""), "link": c["link"]})
        return {"lede": self.content["gallery_lede"], "tiles": tiles}

    def frames(self, cid):
        c = self.creatives[cid]
        chosen = self.content.get("key_frames", {}).get(cid)
        if chosen is None:
            if c.get("frames"):
                fr = c["frames"]
                idx = sorted({round(k * (len(fr) - 1) / 5) for k in range(6)}) if len(fr) > 1 else [0]
                chosen = [fr[i]["file"] for i in idx]
            else:
                chosen = [m for m in c.get("media", []) if m.lower().endswith((".jpg", ".jpeg", ".png", ".webp"))]
        times = {f["file"]: f["time_s"] for f in c.get("frames", [])}
        out = []
        for k, path in enumerate(chosen, 1):
            if self.need((self.run / path).exists(), f"{cid}: frame not found {path}"):
                label = f"{times[path]:g} s" if path in times else (f"Version {k}" if len(chosen) > 1 else "Image")
                out.append({"src": kit.image_uri(self.run / path, max_w=360), "label": label})
        return out

    def creative_notes(self):
        why = self.content.get("why_selected", {})
        hooks, stories = self.content.get("hooks", {}), self.content.get("story", {})
        items = []
        for cid in sorted(self.creatives, key=lambda i: (i.startswith("C0-"), i)):
            c = self.creatives[cid]
            a = self.analysis.get(cid)
            if not self.need(a, f"{cid}: no analysis file"):
                continue
            m = next((x for x in MATCH if x[0] == c.get("product_match")), MATCH[-1])
            facts = [("Brand", c["competitor"]), ("Platform", f'{c["platform"]} · {c["placement"]}'),
                     ("Product shown", c.get("product_shown")), ("Product match", c.get("product_match")),
                     ("Started running", c.get("started_running")), ("Popularity", self.signal(c)),
                     ("Length", f'{c["duration_s"]:.0f} s' if c.get("duration_s") else None),
                     ("Seen on", c.get("date_seen")), ("Why selected", why.get(cid) or c.get("selection_reason"))]
            facts = [{"label": l, "text": t} for l, t in facts if t]
            facts.append({"label": "Original", "text": "Open the original", "url": c["link"]})
            story = []
            beats = stories.get(cid, [])
            if c["format"] == "Video":
                self.need(beats, f"{cid}: story beats missing for a video")
            for s in beats:
                shot = s["beat"].split()[0]
                self.need(shot in SHOT_COLORS, f'{cid}: story beat {s["beat"]!r} must start with SH1-SH7')
                story.append({"beat": s["beat"], "short": shot, "what": s["what"], "color": SHOT_COLORS.get(shot, "#6B655A"),
                              "span": f'{s["from"]:g}–{s["to"]:g} s', "width": max(0.5, float(s["to"]) - float(s["from"]))})
            tables = []
            for part, label in (("B", "Business"), ("S", "Style")):
                rows = []
                pids = sorted(p for p in a["findings"] if p.startswith(part))
                title = f"{label}: {len(pids)} parameters"
                for pid in pids:
                    f = a["findings"][pid]
                    rows.append({"id": pid, "name": PARAMS[pid]["name"], "visible": f["visible"],
                                 "options": (f.get("option") or "").split(" + ") if f.get("option") else [],
                                 "finding": f["finding"]})
                tables.append({"title": title, "rows": rows})
            items.append({"id": cid, "brand": self.brand_of(cid), "brand_key": self.brand_of(cid)["key"],
                          "is_brand": c["competitor"] == self.brand_name, "paid": c["paid_or_organic"] == "Paid",
                          "paid_key": c["paid_or_organic"].lower(), "kind": self.kind(c), "format": c["format"],
                          "placement": c["placement"], "match": m[0], "match_class": m[1],
                          "thumb": self.thumb(cid, 160), "frames": self.frames(cid), "facts": facts,
                          "hook": hooks.get(cid), "story": story, "tables": tables})
        filters = [{"key": "brand", "label": "Brand", "values": [{"value": b["key"], "label": b["name"]} for b in self.brands.values()]},
                   {"key": "type", "label": "Type", "values": [{"value": "paid", "label": "Paid"}, {"value": "organic", "label": "Organic"}]},
                   {"key": "format", "label": "Format", "values": [{"value": "photo", "label": "Photo"}, {"value": "video", "label": "Video"}]}]
        return {"lede": self.content["creatives_lede"], "items": items, "filters": filters}

    # ---------- assembly ----------
    def context(self, detailed):
        sections = [("brief", "Product brief"), ("findings", "Headline findings"),
                    ("competitors", "Competitors and why"), ("notes", "Competitor notes"),
                    ("vs", f"{self.brand_name} vs the market"), ("business", "Business view"),
                    ("style", "Creative and style view"), ("ideas", "Recommended content"),
                    ("gallery", "Sample creatives")]
        if detailed:
            sections.append(("creatives", "Creative notes"))
        S = {k: {"id": k, "num": f"{i:02d}", "title": t} for i, (k, t) in enumerate(sections, 1)}
        cover = self.cover()
        kind = "Detailed report" if detailed else "Summary report"
        cover["eyebrow"] = f"Content benchmark · {kind}"
        ctx = {"page_title": f'{self.brand_name} {self.brief["product"]}: content benchmark ({kind.lower()})',
               "side_title": f'{self.brand_name} · {self.brief["product"]}', "side_sub": f"{kind} · {self.date_text}",
               "toc": list(S.values()), "S": S, "cover": cover, "brief": self.brief_section(),
               "findings": self.findings(detailed), "competitors": self.competitors(), "notes": self.notes(detailed),
               "vs": self.brand_vs_market(detailed), "funnel": self.funnel(detailed),
               "business": self.table("business_table", "B", detailed), "style": self.table("style_table", "S", detailed),
               "ideas": self.ideas(detailed), "gallery": self.gallery()}
        if detailed:
            ctx["creatives"] = self.creative_notes()
        return ctx


def compact(n):
    n = int(n)
    for div, suf in ((1_000_000, "M"), (1_000, "K")):
        if n >= div:
            return f"{n / div:.1f}".rstrip("0").rstrip(".") + suf
    return str(n)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    run = Path(sys.argv[1]).resolve()
    rep = Report(run)
    for name, layout, detailed in (("report.html", "content_radar_summary.html.j2", False),
                                   ("report_detailed.html", "content_radar_detailed.html.j2", True)):
        html = kit.render(layout, rep.context(detailed))
        (run / name).write_text(html, encoding="utf-8")
        print(f"wrote {name} ({(run / name).stat().st_size // 1024} KB)")
    problems = list(dict.fromkeys(rep.problems))
    for p in problems:
        print("PROBLEM", p)
    print(f"{len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
