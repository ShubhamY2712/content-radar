"""Read-only export of the Creative Benchmark workbook into knowledge/ files.

  python tools/export_knowledge.py "<path to Creative_Benchmark_Parameters.xlsx>" knowledge
"""
import json, re, sys
from pathlib import Path
import openpyxl

src, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
wb = openpyxl.load_workbook(src, read_only=True, data_only=True)

# Lists sheet: section -> list name -> options (also keyed by parameter ID)
lists, by_id, section, name, pid = {}, {}, None, None, None
for r in wb["Lists"].iter_rows(min_row=6, values_only=True):
    c = [x if x is not None else "" for x in r[1:5]]
    if not any(c):
        continue
    if c[0] and not c[1] and not c[2]:          # section header row
        section = str(c[0]); lists[section] = {}; continue
    if c[1]:
        name = str(c[1]); pid = str(c[0]) or None
        lists[section][name] = []
        if pid:
            by_id[pid] = lists[section][name]
    lists[section][name].append(str(c[3]))

def lines(v):
    return [s.strip() for s in str(v or "").split("\n")]

def split_assets(x):  # split on commas outside parentheses
    return [a.strip() for a in re.split(r",\s*(?![^()]*\))", x) if a.strip() and a.strip() != "—"]

def fill_shots(shots, n):  # an empty shot line means "same shot as the line above"
    out, last = [], ""
    for s in (shots + [""] * n)[:n]:
        last = s or last; out.append(last)
    return out

bd = lists["Creative breakdown"]
CANON = {l: bd.get("Assets – " + l, []) for l in bd["Layer"]}

def canon(layer, asset):  # short form -> the one list name that starts with it (e.g. A-roll -> A-roll (main / talking head))
    hits = [a for a in CANON.get(layer, []) if a.startswith(asset)] if asset not in CANON.get(layer, []) else []
    if not hits:  # also match "Paid partnership label" -> "Sponsored / Paid partnership label"
        hits = [a for a in CANON.get(layer, []) if asset in a and asset not in CANON.get(layer, [])]
    return hits[0] if len(hits) == 1 else asset

def expand(entries):  # a layer range such as "L1–L4 Image layers" becomes one entry per real layer
    out = []
    for e in entries:
        m = re.match(r"^L(\d+)–L(\d+)\b", e["layer"])
        if m and e["layer"] not in CANON:
            out += [{**e, "layer": next(l for l in CANON if l.startswith(f"L{i} "))}
                    for i in range(int(m.group(1)), int(m.group(2)) + 1)]
        else:
            out.append(e)
    return out

params, part, group = [], None, None
for r in wb["Parameters"].iter_rows(min_row=7, values_only=True):
    c = [x if x is not None else "" for x in r[1:12]]
    if not any(c):
        continue
    if not c[1]:                                   # part or group banner
        if str(c[0]) in ("Business", "Style"):
            part = str(c[0])
        else:
            group = str(c[0])
        continue
    pl, pa = lines(c[6]), lines(c[7])
    vs, vl, va = lines(c[8]), lines(c[9]), lines(c[10])
    params.append({
        "id": str(c[0]), "part": part, "group": group, "name": str(c[1]),
        "applies_to": str(c[2]), "what_to_check": str(c[3]),
        "options": by_id.get(str(c[0])) or ([] if str(c[4]) in ("", "Free text", "–") else [str(c[4])]),
        "free_text": str(c[4]) == "Free text",
        "benchmark": str(c[5]),
        "photo": expand([{"layer": l, "assets": [canon(l, a) for a in split_assets(x)]}
                  for l, x in zip(pl, pa + [""] * len(pl)) if l and l != "—"]),
        "video": expand([{"shot": s, "layer": l, "assets": [canon(l, a) for a in split_assets(x)]}
                  for s, l, x in zip(fill_shots(vs, len(vl)), vl, va + [""] * len(vl)) if l and l != "—"]),
    })

breakdown = {
    "shots": bd["Shot (story beat)"],
    "layers": [{"layer": l, "assets": bd.get("Assets – " + l, [])} for l in bd["Layer"]],
    "creative_details": lists["Creative details"],
}
(out / "parameters.json").write_text(json.dumps(params, ensure_ascii=False, indent=1), encoding="utf-8")
(out / "breakdown.json").write_text(json.dumps(breakdown, ensure_ascii=False, indent=1), encoding="utf-8")

# Human-readable copy for hosts that only read text
md = ["# Creative benchmark parameters", "",
      f"{sum(p['part']=='Business' for p in params)} business and {sum(p['part']=='Style' for p in params)} style parameters. "
      "Each parameter is checked on a layer of the creative; for video also on a shot (story beat).", ""]
cur = None
for p in params:
    if (p["part"], p["group"]) != cur:
        cur = (p["part"], p["group"]); md += [f"## {p['part']} – {p['group']}", ""]
    md.append(f"### {p['id']} {p['name']} ({p['applies_to']})")
    md.append(f"- Check: {p['what_to_check']}")
    md.append(f"- Options: {'free text' if p['free_text'] else '; '.join(p['options']) or '–'}")
    md.append(f"- Benchmark: {p['benchmark']}")
    if p["photo"]:
        md.append("- Photo: " + " | ".join(f"{x['layer']} → {', '.join(x['assets'])}" for x in p["photo"]))
    if p["video"]:
        md.append("- Video: " + " | ".join(f"{x['shot']} · {x['layer']} → {', '.join(x['assets'])}" for x in p["video"]))
    md.append("")
md += ["## Shots (story beats)", "", *[f"- {s}" for s in breakdown["shots"]], "", "## Layers and assets", ""]
md += [f"- **{l['layer']}**: {', '.join(l['assets']) or '–'}" for l in breakdown["layers"]]
md += ["", "## Creative details", ""] + [f"- **{k}**: {', '.join(v)}" for k, v in breakdown["creative_details"].items()]
(out / "parameters.md").write_text("\n".join(md) + "\n", encoding="utf-8")
print(len(params), "parameters;", len(breakdown["shots"]), "shots;", len(breakdown["layers"]), "layers")
