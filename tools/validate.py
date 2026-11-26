"""Check a run folder: which steps are done, and whether each output matches its schema and the knowledge.

  python tools/validate.py runs/<brand>-<date>                  whole run
  python tools/validate.py runs/<brand>-<date> <file in run>    one file (workers): parts/C2.json, analysis/parts/C2-3-B.json,
                                                                analysis/C2-3.json or checks/C2-3.json
  python tools/validate.py --judged <Image|Video>              the parameters a checker answers

Prints one line per step (OK / MISSING / ERROR) and the step to resume from. Exit 1 if any error.
"""
import json, sys
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker

ROOT = Path(__file__).resolve().parent.parent
PARAMS = {p["id"]: p for p in json.loads((ROOT / "knowledge/parameters.json").read_text(encoding="utf-8"))}
BD = json.loads((ROOT / "knowledge/breakdown.json").read_text(encoding="utf-8"))
SHOTS = set(BD["shots"])
ASSETS = {l["layer"]: set(l["assets"]) for l in BD["layers"]}
# parameters that may join options with " + " (knowledge/option_guide.md -> General rules)
MULTI = {"B23", "B24", "S07", "S10", "S17", "S18", "S19", "B05", "B07", "B16", "B18", "B20", "B21", "B22", "S04", "S11", "S24"}


def schema_errors(data, name):
    schema = json.loads((ROOT / "schemas" / f"{name}.schema.json").read_text(encoding="utf-8"))
    v = Draft202012Validator(schema, format_checker=FormatChecker())
    return [f"{'/'.join(map(str, e.path)) or '(root)'}: {e.message}" for e in v.iter_errors(data)]


def applies(p, fmt):
    return p["applies_to"] == "Both" or p["applies_to"] == ("Video" if fmt == "Video" else "Image")


def judged(fmt):
    """Parameters with an option list that apply to this format: the ones the checker re-reads."""
    return sorted(pid for pid, p in PARAMS.items() if p["options"] and applies(p, fmt))


def analysis_errors(a, part=None):
    """Knowledge checks the schema cannot express: IDs, options, shots, layers, assets.
    part = "B" or "S" checks one analyst's half (analysis/parts/<id>-B.json)."""
    errs, fmt = [], a.get("format")
    for pid, f in a.get("findings", {}).items():
        p = PARAMS.get(pid)
        if not p:
            errs.append(f"{pid}: unknown parameter"); continue
        if part and not pid.startswith(part):
            errs.append(f"{pid}: not a {part} parameter (this file is the {part} half)")
        if a.get("version") == 2 and f.get("visible") and not f.get("evidence"):
            errs.append(f"{pid}: visible finding without evidence (say where it was seen)")
        if (p["applies_to"] == "Video" and fmt != "Video") or (p["applies_to"] == "Image" and fmt == "Video"):
            errs.append(f"{pid}: applies to {p['applies_to']}, creative is {fmt}")
        if f.get("visible") and p["options"] and f.get("option"):
            bad = [o for o in f["option"].split(" + ") if o not in p["options"]]
            if bad:
                errs.append(f"{pid}: option not in list: {bad}")
            if " + " in f["option"] and pid not in MULTI:
                errs.append(f"{pid}: one option only (\" + \" is for {', '.join(sorted(MULTI))})")
        for w in f.get("where", []):
            if w["layer"] not in ASSETS:
                errs.append(f"{pid}: unknown layer {w['layer']}")
            else:
                # allowed: the layer's asset list + property terms this parameter's mapping uses for the layer (e.g. Colours, Position)
                own = {a for m in p["photo"] + p["video"] if m["layer"] == w["layer"] for a in m["assets"]}
                extra = set(w["assets"]) - ASSETS[w["layer"]] - own
                if ASSETS[w["layer"]] and extra:
                    errs.append(f"{pid}: assets not in {w['layer']}: {sorted(extra)}")
            if fmt == "Video" and w.get("shot") not in SHOTS:
                errs.append(f"{pid}: video needs a shot from the list, got {w.get('shot')!r}")
    expected = {pid for pid, p in PARAMS.items() if applies(p, fmt) and (not part or pid.startswith(part))}
    missing = sorted(expected - set(a.get("findings", {})))
    if missing:
        errs.append(f"missing parameters: {missing}")
    return errs


def checks_errors(run, cid, fmt, analysis=None):
    """checks/<id>.json: the checker answered every judged parameter; with the analysis, every
    disagreement found by tools/check_compare.py has a resolution."""
    path = Path(run) / "checks" / f"{cid}.json"
    if not path.exists():
        return [f"checks/{cid}.json missing (checker has not run)"]
    c = json.loads(path.read_text(encoding="utf-8"))
    errs = schema_errors(c, "checks")
    missing = sorted(set(judged(fmt)) - set(c.get("answers", {})))
    if missing:
        errs.append(f"checks/{cid}.json: checker did not answer {missing}")
    for pid, a in c.get("answers", {}).items():
        if pid in PARAMS and a.get("visible") and PARAMS[pid]["options"] and a.get("option"):
            bad = [o for o in a["option"].split(" + ") if o not in PARAMS[pid]["options"]]
            if bad:
                errs.append(f"{pid}: option not in list: {bad}")
            if " + " in a["option"] and pid not in MULTI:
                errs.append(f"{pid}: one option only (\" + \" is for {', '.join(sorted(MULTI))})")
    if analysis is not None:
        if "disagreements" not in c:
            errs.append(f"checks/{cid}.json: run tools/check_compare.py {run} {cid}")
        for d in c.get("disagreements", []):
            r = d.get("resolution") or ""
            now = analysis["findings"].get(d["parameter"], {}).get("option")
            if not (r == "changed" or (r.startswith("kept:") and len(r) > 10)):
                errs.append(f"{d['parameter']}: disagreement not resolved (analyst {d['analyst_option']!r}, "
                            f"checker {d['checker_option']!r})")
            elif r == "changed" and now == d["analyst_option"]:
                errs.append(f"{d['parameter']}: marked changed but the analysis still says {now!r}")
    return errs


def check_file(run, rel):
    """One worker output: parts/C<n>.json, analysis/parts/<id>-B|S.json, analysis/<id>.json or checks/<id>.json."""
    path = Path(run) / rel
    rel = rel.replace("\\", "/")
    if not path.exists():
        print(f"MISSING {rel}"); return 1
    data = json.loads(path.read_text(encoding="utf-8"))
    if rel.startswith("analysis/parts/"):
        errs = schema_errors(data, "analysis") + analysis_errors(data, part=path.stem[-1])
    elif rel.startswith("analysis/"):
        errs = schema_errors(data, "analysis") + analysis_errors(data)
        if data.get("version") == 2:
            errs += checks_errors(run, data["creative_id"], data["format"], data)
    elif rel.startswith("checks/"):
        errs = checks_errors(run, data.get("creative_id", path.stem), fmt_of(run, path.stem))
    else:
        from merge_parts import brand_names, part_problems  # same checks the boss's merge runs
        n = int(Path(rel).stem.lstrip("Cc"))
        errs = part_problems(Path(run), n, brand_names(Path(run)))[0]
    print(f"{'ERROR' if errs else 'OK':7} {rel}")
    for e in errs:
        print("        ", e)
    return 1 if errs else 0


def fmt_of(run, cid):
    cr = json.loads((Path(run) / "creatives.json").read_text(encoding="utf-8"))["creatives"]
    return next((c["format"] for c in cr if c["id"] == cid), None)


def main(run):
    run = Path(run)
    steps = [("brief-intake", ["brief.json"]), ("competitor-discovery", ["competitors.json"]),
             ("creative-collection", ["creatives.json"]), ("creative-analysis", ["analysis/"]),
             ("benchmark-synthesis", ["synthesis.json"]), ("content-recommendation", ["recommendations.json", "report.md"]),
             ("report-review", ["review.json"])]
    resume, failed = None, False
    creative_ids = []
    for step, files in steps:
        errs, missing = [], []
        for f in files:
            path = run / f
            if f == "analysis/":
                done = {p.stem for p in path.glob("*.json")} if path.exists() else set()
                todo = [c for c in creative_ids if c not in done]
                if not done or todo:
                    missing.append(f"analysis for {todo or 'all creatives'}")
                for p in sorted(path.glob("*.json")) if path.exists() else []:
                    a = json.loads(p.read_text(encoding="utf-8"))
                    errs += [f"{p.name} {e}" for e in schema_errors(a, "analysis") + analysis_errors(a)]
                    if a.get("version") == 2:
                        errs += [f"{p.name} {e}" for e in checks_errors(run, a["creative_id"], a["format"], a)]
            elif not path.exists():
                parts = sorted(p.stem for p in (run / "parts").glob("C*.json")) if f == "creatives.json" else []
                missing.append(f + (f" (team mode: parts done {', '.join(parts)}; merge with tools/merge_parts.py when all are in)"
                                    if parts else ""))
            elif f.endswith(".json"):
                data = json.loads(path.read_text(encoding="utf-8"))
                errs += [f"{f} {e}" for e in schema_errors(data, f.removesuffix(".json"))]
                if f == "creatives.json":
                    creative_ids = [c["id"] for c in data.get("creatives", [])]
                if f == "competitors.json" and not data.get("approved_by_user"):
                    errs.append("competitors.json: waiting for user approval")
                if f == "review.json" and not data.get("passed"):
                    errs.append("review.json: review has not passed yet")
        status = "ERROR" if errs else ("MISSING" if missing else "OK")
        print(f"{status:7} {step}" + (f"  ({'; '.join(missing)})" if missing and not errs else ""))
        for e in errs[:20]:
            print("        ", e)
        if status != "OK" and resume is None:
            resume = step
        failed |= bool(errs)
    print("resume from:", resume or "done")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--judged":  # the parameters a checker answers for a format
        print(" ".join(judged(sys.argv[2]))); sys.exit(0)
    if len(sys.argv) == 3:
        sys.exit(check_file(sys.argv[1], sys.argv[2]))
    if len(sys.argv) != 2:
        print(__doc__); sys.exit(1)
    sys.exit(main(sys.argv[1]))
