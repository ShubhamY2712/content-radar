"""Automatic checks on a finished run, before it is reported as done.

  python tools/review.py runs/<brand>-<date> [--links]

Checks that ids, names and counts across the files agree, that every recommendation and
pattern points to real evidence, and that report.md and the HTML reports are current
(report_content.json complete, no long text far over its writing guide). --links also opens every
link (social sites often block scripts: their failures are listed to check by hand).
Prints one issue per line and "0 issues" when clean. Exit 1 if there are issues.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAM_IDS = {p["id"] for p in json.loads((ROOT / "knowledge/parameters.json").read_text(encoding="utf-8"))}
ID = re.compile(r"\bC\d+-\d+\b")


def load(run, name):
    return json.loads((run / name).read_text(encoding="utf-8"))


def text_of(x):
    return json.dumps(x, ensure_ascii=False)


def check(run, links):
    issues = []
    brief, comp, cr = load(run, "brief.json"), load(run, "competitors.json"), load(run, "creatives.json")["creatives"]
    syn, rec = load(run, "synthesis.json"), load(run, "recommendations.json")["recommendations"]
    ids = {c["id"] for c in cr}
    market_ids = {i for i in ids if not i.startswith("C0-")}
    names = {c["name"] for c in comp["competitors"]}

    analysed = {p.stem for p in (run / "analysis").glob("*.json")}
    issues += [f"creative {i} has no analysis" for i in sorted(ids - analysed)]
    issues += [f"analysis {i} has no creative in creatives.json" for i in sorted(analysed - ids)]
    if not any(i.startswith("C0-") for i in ids):
        issues.append("no brand baseline creatives (C0-…)")
    for c in cr:
        if c["competitor"] not in names and not c["id"].startswith("C0-"):
            issues.append(f"{c['id']}: competitor {c['competitor']!r} is not in competitors.json")
        if c["format"] == "Video":
            # 1 frame per second is enough for very short clips
            need = min(6, int(c.get("duration_s") or 6) + 1)
            if len(c.get("frames", [])) < need:
                issues.append(f"{c['id']}: video has only {len(c.get('frames', []))} frames (need {need}+)")

    # fewer creatives than asked, or a global-page ad, must be said in a GAP line (never padded or hidden)
    log = (run / "log.md").read_text(encoding="utf-8") if (run / "log.md").exists() else ""
    gaps = [l for l in log.splitlines() if "GAP:" in l]
    asked = [(c["name"], brief["creatives_per_competitor"]) for c in comp["competitors"]]
    asked.append((comp["brand"]["name"], brief.get("brand_creatives", 3)))  # runs before 19 Nov 2026 used 3
    for name, want in asked:
        have = sum(1 for c in cr if c["competitor"] == name)
        if have < want and not any(name in g for g in gaps):
            issues.append(f"{name}: {have} of {want} creatives and no GAP line in log.md")
    for c in cr:
        if "global page" in c.get("selection_reason", "") and not any(c["id"] in g for g in gaps):
            issues.append(f"{c['id']} is from a global page and has no GAP line in log.md")

    # "Exact product" needs proof when the creative was measured: the pack seen, or the product type read
    words = brief.get("product_type", "").lower().replace(" ", "")
    for c in cr:
        mpath = run / "media" / c["id"] / "measures.json"
        if c.get("product_match") != "Exact product" or not mpath.exists():
            continue
        frames = json.loads(mpath.read_text(encoding="utf-8"))["frames"]
        seen = any(f.get("pack", {}).get("found") and not f["pack"].get("partial") for f in frames)
        text = (" ".join(l["text"] for f in frames for l in f["text"]) + " " + c.get("copy", "")).lower().replace(" ", "")
        pname = next((x.get("product_name", "") for x in comp["competitors"] if x["name"] == c.get("competitor")), "")
        brand_words = set(re.findall(r"\w+", c.get("competitor", "").lower()))
        pname = "".join(w for w in re.findall(r"\w+", pname.lower()) if w not in brand_words)
        if not seen and not (words and words in text) and not (pname and pname in text):
            issues.append(f"{c['id']} is marked Exact product, but measures show no pack match and no "
                          f"'{brief.get('product_type')}' or product name text: check it or lower the match level")

    # numbers in the synthesis must be the ones tools/stats.py counted
    if (run / "stats.json").exists():
        st = load(run, "stats.json")["parameters"]
        rows = [("market pattern", m) for m in syn["market_patterns"]] + \
               [("brand vs market", v) for v in syn["brand_baseline"]["vs_market"]]
        for kind, row in rows:
            pid = row["parameter"]
            if pid in st and not row.get("stats"):
                issues.append(f"{kind} {pid} has no stats copied from stats.json")
            for s in row.get("stats", []):
                g = st.get(pid, {}).get(s["group"], {})
                n = len(g.get("options", {}).get(s["option"], []))
                if (s["n"], s["of"]) != (n, g.get("of")):
                    issues.append(f"{kind} {pid}: '{s['option']}' {s['n']} of {s['of']} ({s['group']}), "
                                  f"stats.json says {n} of {g.get('of')}")

    for n in syn["competitor_notes"]:
        if n["competitor"] not in names:
            issues.append(f"competitor note for unknown competitor {n['competitor']!r}")
    for i in sorted(set(ID.findall(text_of(syn))) - ids):
        issues.append(f"synthesis mentions {i}, which is not a collected creative")
    for m in syn["market_patterns"]:
        if m["parameter"] not in PARAM_IDS:
            issues.append(f"market pattern on unknown parameter {m['parameter']}")
        if any(e.startswith("C0-") for e in m["evidence"]):
            issues.append(f"market pattern {m['parameter']} uses brand creatives as market evidence")
    # "N of M" counts can never exceed the creatives that exist
    for n, m in re.findall(r"\b(\d+) of (\d+)\b", text_of(syn)):
        if int(n) > int(m) or int(m) > len(market_ids):
            issues.append(f"count '{n} of {m}' does not fit {len(market_ids)} competitor creatives")

    for k, r in enumerate(rec, 1):
        if not any(ID.fullmatch(b) and b in ids or b in PARAM_IDS or ID.search(b) for b in r["based_on"]):
            issues.append(f"recommendation {k} is not based on a creative id or parameter")
        issues += [f"recommendation {k}: unknown parameter {p}" for p in r["parameters"] if p not in PARAM_IDS]
        issues += [f"recommendation {k} cites {i}, which is not a collected creative"
                   for i in set(ID.findall(text_of(r))) - ids]

    report = run / "report.md"
    if not report.exists():
        issues.append("report.md missing")
    else:
        newest = max((run / f).stat().st_mtime for f in ("synthesis.json", "recommendations.json", "creatives.json"))
        if report.stat().st_mtime < newest:
            issues.append("report.md is older than the data - run tools/render_report.py again")
        if re.search(r"\{[a-z_ ]+\}", report.read_text(encoding="utf-8")):
            issues.append("report.md still has template placeholders")
        if not (run / "creative_notes.md").exists():
            issues.append("creative_notes.md missing - run tools/render_report.py again")

    issues += html_issues(run, ids)

    if links:
        import requests
        urls = {c["link"] for c in cr} | {v for c in comp["competitors"] + [comp["brand"]]
                                           for k, v in c.items() if isinstance(v, str) and v.startswith("http")}
        for u in sorted(urls):
            try:
                r = requests.get(u, timeout=15, allow_redirects=True, headers={"User-Agent": "Mozilla/5.0"})
                # social sites answer 200 with a login page instead of the post
                code = "login wall" if re.search(r"/(accounts/)?login", r.url) else r.status_code
            except requests.RequestException as e:
                code = type(e).__name__
            if code != 200:
                issues.append(f"link check by hand ({code}): {u}")
    return issues


# Writing guides from skills/report-document/SKILL.md; text over 1.5x its guide is flagged to shorten.
LONG = 1.5
GUIDES = {"dek": 25, "brief.method_note": 60, "findings.lede": 25, "findings.items.key_line": 35,
          "findings.items.detail": 45, "competitors.selection_rule": 60, "competitors.creative_rule": 70,
          "competitors.why": 30, "competitors.gaps": 30, "competitor_notes.summary": 80,
          "competitor_notes.brands.strategy": 40, "brand_vs_market.gaps.meaning": 35,
          "brand_vs_market.strengths.meaning": 35, "positioning_map.reason": 40,
          "business_table.rows.market": 30, "business_table.rows.brand": 30, "business_table.rows.gap": 30,
          "style_table.rows.market": 30, "style_table.rows.brand": 30, "style_table.rows.gap": 30,
          "funnel_note": 30, "ideas.items.title": 9, "ideas.items.why": 40, "why_selected": 14, "story.what": 20}


def long_text(content):
    """Yield (field, words, guide) for text far over its writing guide."""
    keyed = ("competitors.why", "why_selected", "story")  # maps keyed by brand or creative id

    def walk(x, path, in_map=False):
        if isinstance(x, dict):
            for k, v in x.items():
                if path in keyed and not in_map:
                    yield from walk(v, path, True)
                else:
                    yield from walk(v, f"{path}.{k}" if path else k)
        elif isinstance(x, list):
            for v in x:
                yield from walk(v, path, in_map)
        elif isinstance(x, str) and path in GUIDES:
            n = len(x.split())
            if n > GUIDES[path] * LONG:
                yield path, n, GUIDES[path]
    yield from walk(content, "")
    paras = content.get("brief", {}).get("paragraphs", [])
    n = sum(len(p.split()) for p in paras)
    if n > 110 * LONG:
        yield "brief.paragraphs", n, 110


def html_issues(run, ids):
    """Step 7 outputs: report_content.json is complete and both HTML reports are current."""
    path = run / "report_content.json"
    if not path.exists():
        return ["report_content.json missing - run step 7 (report-document)"]
    issues = []
    content = json.loads(path.read_text(encoding="utf-8"))
    for i in sorted(set(ID.findall(text_of(content))) - ids):
        issues.append(f"report_content.json mentions {i}, which is not a collected creative")
    for n, m in re.findall(r"\b(\d+) of (\d+)\b", text_of(content)):
        if int(n) > int(m):
            issues.append(f"report_content.json: count '{n} of {m}' is impossible")
    for field, n, guide in long_text(content):
        issues.append(f"long text in {field}: {n} words (guide {guide}) - shorten it")
    sys.path.insert(0, str(ROOT / "tools"))
    from render_html import Report
    try:
        rep = Report(run)
        rep.context(detailed=True)
        issues += [f"report: {p}" for p in dict.fromkeys(rep.problems)]
    except (KeyError, TypeError, ValueError) as e:
        issues.append(f"report_content.json cannot be rendered ({type(e).__name__}: {e}) - check it with tools/validate.py")
    newest = max((run / f).stat().st_mtime for f in ("report_content.json", "synthesis.json", "recommendations.json", "creatives.json"))
    for name in ("report.html", "report_detailed.html"):
        out = run / name
        if not out.exists():
            issues.append(f"{name} missing - run tools/render_html.py")
        elif out.stat().st_mtime < newest:
            issues.append(f"{name} is older than the data - run tools/render_html.py again")
    return issues


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--links"]
    if len(args) != 1:
        print(__doc__); sys.exit(1)
    found = check(Path(args[0]), "--links" in sys.argv)
    for i in found:
        print(i)
    print(f"{len(found)} issues")
    sys.exit(1 if found else 0)
