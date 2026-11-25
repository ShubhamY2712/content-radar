"""Join workers' parts (team mode).

  python tools/merge_parts.py runs/<brand>-<date>                    step 3: parts/C<n>.json -> creatives.json
  python tools/merge_parts.py runs/<brand>-<date> --analysis <id>    step 4: analysis/parts/<id>-B.json + -S.json
                                                                     -> analysis/<id>.json (version 2)

Each collector writes parts/C<n>.json for one brand (C0 = the brand itself, C1.. = the competitors
in competitors.json order). This checks every part and writes creatives.json (C1.., then C0) only
when all parts are present and clean. Prints one problem per line; exit 1 if any.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from validate import analysis_errors, schema_errors


def brand_names(run):
    comp = json.loads((run / "competitors.json").read_text(encoding="utf-8"))
    return {0: comp["brand"]["name"], **{i: c["name"] for i, c in enumerate(comp["competitors"], 1)}}


def part_problems(run, n, names):
    """Problems in parts/C<n>.json (also used by validate.py when a collector checks its own part)."""
    part = run / "parts" / f"C{n}.json"
    if not part.exists():
        return [f"parts/C{n}.json missing ({names[n]})"], []
    data = json.loads(part.read_text(encoding="utf-8"))
    problems = [f"parts/C{n}.json {e}" for e in schema_errors(data, "creatives")]
    for c in data.get("creatives", []):
        cid = c.get("id", "?")
        if not cid.startswith(f"C{n}-"):
            problems.append(f"parts/C{n}.json: {cid} does not belong to C{n}")
        if c.get("competitor") != names[n]:
            problems.append(f"parts/C{n}.json: {cid} competitor {c.get('competitor')!r}, expected {names[n]!r}")
        for f in c.get("media", []) + [x["file"] for x in c.get("frames", [])]:
            if not (run / f).exists():
                problems.append(f"parts/C{n}.json: {cid} media file not found: {f}")
    ids = [c.get("id") for c in data.get("creatives", [])]
    problems += [f"parts/C{n}.json: duplicate id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})]
    return problems, data.get("creatives", [])


def problems_and_creatives(run):
    names = brand_names(run)
    problems, creatives = [], []
    for n in sorted(names, key=lambda k: (k == 0, k)):
        p, c = part_problems(run, n, names)
        problems += p
        creatives += c
    ids = [c.get("id") for c in creatives]
    problems += [f"duplicate id {i}" for i in sorted({i for i in ids if ids.count(i) > 1})
                 if not any(f"duplicate id {i}" in p for p in problems)]
    return problems, creatives


def merge_analysis(run, cid):
    """Business half + Style half of one creative's analysis -> analysis/<id>.json."""
    halves, problems = {}, []
    for part in "BS":
        path = run / "analysis" / "parts" / f"{cid}-{part}.json"
        if not path.exists():
            problems.append(f"analysis/parts/{cid}-{part}.json missing"); continue
        data = json.loads(path.read_text(encoding="utf-8"))
        problems += [f"analysis/parts/{cid}-{part}.json {e}"
                     for e in schema_errors(data, "analysis") + analysis_errors(data, part=part)]
        halves[part] = data
    if not problems and halves["B"]["format"] != halves["S"]["format"]:
        problems.append(f"{cid}: the two halves disagree on the format")
    for p in problems:
        print(p)
    if problems:
        print(f"{len(problems)} problems; analysis/{cid}.json not written"); sys.exit(1)
    merged = {"creative_id": cid, "version": 2, "format": halves["B"]["format"],
              "findings": {**halves["B"]["findings"], **halves["S"]["findings"]}}
    (run / "analysis" / f"{cid}.json").write_text(json.dumps(merged, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"analysis/{cid}.json written: {len(merged['findings'])} parameters")


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[2] == "--analysis":
        merge_analysis(Path(sys.argv[1]), sys.argv[3]); sys.exit(0)
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    run = Path(sys.argv[1])
    problems, creatives = problems_and_creatives(run)
    for p in problems:
        print(p)
    if problems:
        print(f"{len(problems)} problems; creatives.json not written"); sys.exit(1)
    (run / "creatives.json").write_text(json.dumps({"creatives": creatives}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"creatives.json written: {len(creatives)} creatives from {len(set(c['id'].split('-')[0] for c in creatives))} parts")
