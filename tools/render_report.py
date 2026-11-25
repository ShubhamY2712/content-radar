"""Write report.md for a run from its JSON files (same layout as templates/report.md).

  python tools/render_report.py runs/<brand>-<date>
"""
import json, re, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MATCH = ["Exact product", "Same product type", "Brand range", "No product"]
PARAMS = {p["id"]: p["name"] for p in json.loads((ROOT / "knowledge/parameters.json").read_text(encoding="utf-8"))}


def load(run, name):
    return json.loads((run / name).read_text(encoding="utf-8"))


def cell(x):
    return str(x if x not in (None, "") else "–").replace("|", "/").replace("\n", " ")


def link(label, url):
    return f"[{label}]({url})" if url else "–"


def table(head, rows):
    return ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(cell(c) for c in r) + " |" for r in rows]


def render(run):
    b, comp, cr = load(run, "brief.json"), load(run, "competitors.json")["competitors"], load(run, "creatives.json")["creatives"]
    syn, rec = load(run, "synthesis.json"), load(run, "recommendations.json")["recommendations"]
    analyses = {p.stem: json.loads(p.read_text(encoding="utf-8")) for p in sorted((run / "analysis").glob("*.json"))}
    log = (run / "log.md").read_text(encoding="utf-8") if (run / "log.md").exists() else ""
    skipped = [l.split("SKIPPED", 1)[1].strip(" :-.") for l in log.splitlines() if "SKIPPED" in l]
    gaps = [l.split("GAP:", 1)[1].strip(" .") for l in log.splitlines() if "GAP:" in l]
    n = lambda f: sum(1 for c in cr if f(c))
    market = [c for c in cr if not c["id"].startswith("C0-")]
    match = ", ".join(f"{sum(1 for c in market if c.get('product_match') == m)} {m.lower()}" for m in MATCH)
    # run folders are named <brand>-<YYYY-MM-DD>; the report keeps the run's date when re-rendered later
    day = re.search(r"\d{4}-\d{2}-\d{2}$", run.resolve().name)

    out = [f"# Content benchmark: {b['brand']} – {b['product']}", "",
           f"{b['market']} · {day.group() if day else date.today().isoformat()} · last {b['time_window_days']} days · Platforms: {', '.join(b['platforms'])}",
           f"Coverage: {len(comp)} competitors, {len(cr)} creatives ({n(lambda c: c['paid_or_organic'] == 'Paid')} paid, "
           f"{n(lambda c: c['paid_or_organic'] == 'Organic')} organic; {n(lambda c: c['format'] != 'Video')} photo, "
           f"{n(lambda c: c['format'] == 'Video')} video). Product match of the {len(market)} competitor creatives: {match}. "
           f"Popular = longest-running ads and most versions (paid) and most views or likes (organic); public signals only, "
           f"no reach, spend or sales data. Sources skipped: {'; '.join(skipped) or 'none'}. Gaps: {'; '.join(gaps) or 'none'}.", "",
           "## Headline findings", ""] + [f"{i}. {f}" for i, f in enumerate(syn["headline_findings"], 1)]

    out += ["", "## Competitors", ""] + table(
        ["Competitor", "Why", "Matching product", "Website", "Instagram", "YouTube", "Ad Library", "Creatives"],
        [[c["name"], c["why"], link(c.get("product_name") or "page", c.get("product_page")), link("site", c.get("website")), link("Instagram", c.get("instagram")),
          link("YouTube", c.get("youtube")), link("ads", c.get("ad_library")),
          n(lambda x, c=c: x["competitor"] == c["name"])] for c in comp])

    out += ["", "## Competitor notes"]
    for c in syn["competitor_notes"]:
        out += ["", f"### {c['competitor']}", c["note"], "", "- Recurring: " + "; ".join(c["recurring"]),
                "- Standout: " + "; ".join(c["standout_creatives"])]

    bb = syn["brand_baseline"]
    out += ["", f"## {b['brand']} vs the market", "", bb["note"], ""] + table(
        ["Parameter", b["brand"], "Market", "Gap", "Evidence"],
        [[f"{v['parameter']} {PARAMS.get(v['parameter'], '')}", v["brand"], v["market"], v["gap"], ", ".join(v["evidence"])]
         for v in bb["vs_market"]])

    out += ["", "## Sample creatives", "", f"`C0-…` are {b['brand']}'s own creatives (baseline).", ""] + table(
        ["ID", "Brand", "Product shown", "Match", "Platform · placement", "Format", "Paid / organic", "Why picked", "Date seen", "Link"],
        [[c["id"], c["competitor"], c.get("product_shown"), c.get("product_match"), f"{c['platform']} · {c['placement']}",
          c["format"] + (f", {c['duration_s']:g} s" if c.get("duration_s") else ""),
          c["paid_or_organic"], c.get("selection_reason"), c["date_seen"], link("open", c["link"])] for c in cr])

    out += ["", "## Creative notes"]
    for c in cr:
        a = analyses.get(c["id"])
        out += ["", f"### {c['id']} {c['competitor']} – {c['placement']}, {c['format']}", ""]
        if not a:
            out.append("Not analysed."); continue
        rows = []
        for pid, f in a["findings"].items():
            w = f["where"] or [{}]
            rows.append([pid, PARAMS.get(pid, ""), f["finding"] + (f" ({f['option']})" if f.get("option") else ""),
                         " / ".join(x.get("shot") or "–" for x in w), " / ".join(x.get("layer", "–") for x in w),
                         " / ".join(", ".join(x.get("assets", [])) or "–" for x in w)])
        out += table(["ID", "Parameter", "Finding", "Shot", "Layer", "Assets"], rows)

    out += ["", "## Market patterns", ""] + table(
        ["Parameter", "What most do", "Rare or missing (gaps)", "Evidence"],
        [[f"{m['parameter']} {PARAMS.get(m['parameter'], '')}", m["common"], m["rare_or_missing"], ", ".join(m["evidence"])]
         for m in syn["market_patterns"]])

    out += ["", "## Recommended content", ""] + table(
        ["#", "Idea", "Audience", "Format and platform", "Hook", "Message and proof", "Offer / CTA", "Style (layers)", "Based on"],
        [[i, r["idea"], r["audience"], r["format_platform"], r["hook"], r["message_proof"], r["offer_cta"],
          r["style_layers"], ", ".join(r["based_on"])] for i, r in enumerate(rec, 1)])

    out.append("")
    (run / "report.md").write_text("\n".join(out), encoding="utf-8")
    print(f"report.md written: {len(comp)} competitors, {len(cr)} creatives, {len(rec)} ideas")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    render(Path(sys.argv[1]))
