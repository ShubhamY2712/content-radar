"""Count the analysis files, so the synthesis never counts by hand (step 5).

  python tools/stats.py runs/<brand>-<date>

Writes stats.json: for every parameter with options, which creatives chose each option, for the
market (competitor creatives) and the brand (C0-...) separately, how many creatives the parameter
applies to ("of"), and which were not visible; plus product-match counts. Options joined with " + "
count for each option. Synthesis copies its numbers from here ("7 of 15" = n and of).
"""
import json, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAMS = {p["id"]: p for p in json.loads((ROOT / "knowledge/parameters.json").read_text(encoding="utf-8"))}


def stats(run):
    creatives = json.loads((run / "creatives.json").read_text(encoding="utf-8"))["creatives"]
    out = {"market_n": 0, "brand_n": 0, "product_match": {"market": defaultdict(list), "brand": defaultdict(list)},
           "parameters": {}}
    for c in creatives:
        group = "brand" if c["id"].startswith("C0-") else "market"
        out[f"{group}_n"] += 1
        out["product_match"][group][c.get("product_match") or "not recorded"].append(c["id"])
        path = run / "analysis" / f"{c['id']}.json"
        if not path.exists():
            continue
        for pid, f in json.loads(path.read_text(encoding="utf-8"))["findings"].items():
            if not PARAMS.get(pid, {}).get("options"):
                continue
            p = out["parameters"].setdefault(pid, {g: {"of": 0, "options": defaultdict(list), "not_visible": []}
                                                  for g in ("market", "brand")})
            p[group]["of"] += 1
            if not f.get("visible") or not f.get("option"):
                p[group]["not_visible"].append(c["id"]); continue
            for o in f["option"].split(" + "):
                p[group]["options"][o.strip()].append(c["id"])
    (run / "stats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"stats.json: {out['market_n']} market + {out['brand_n']} brand creatives, {len(out['parameters'])} parameters")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    stats(Path(sys.argv[1]))
