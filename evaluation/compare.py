"""Compare the agent's analyses of reference creatives with the manual analyses (accuracy check).

  python evaluation/compare.py <analysis json> "Creative 3"        one creative
  python evaluation/compare.py <folder> [--report <file.md>]        every "Creative N.json" in the folder

Test on Creatives 3-10: Creatives 1 and 2 are the worked examples in knowledge/ and option_guide.md.
Per parameter with an option list (both sides filled and visible):
  exact      the agent's options are the manual options (" + " / "; " lists compared as sets)
  partial    they share at least one option
  kappa      chance-corrected agreement on exact matches (Brennan-Prediger: chance = 1 / number of
             options of the parameter); 0 = no better than guessing, 1 = perfect
Also layer overlap (at least one same layer L1-L14) and, with --report, a Markdown file listing
every disagreement and the parameters the agent gets wrong most (fix those in option_guide.md).
"""
import json, re, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PARAMS = {p["id"]: p for p in json.loads((ROOT / "knowledge/parameters.json").read_text(encoding="utf-8"))}
REF = {r["creative"]: r for r in json.loads((ROOT / "evaluation/reference_creatives.json").read_text(encoding="utf-8"))}


def layers(text):
    return set(re.findall(r"\bL\d{1,2}\b", text))


def manual_options(pid, text):
    """Option names found in the manual finding, longest first so 'Partly' never hides inside 'Partial'."""
    found, rest = set(), " " + text.split("\n")[0] + " "
    for o in sorted(PARAMS[pid]["options"], key=len, reverse=True):
        if o in rest:
            found.add(o)
            rest = rest.replace(o, " ")
    return found


def rows_for(agent, ref):
    rows = []
    for pid, r in ref.items():
        a = agent.get(pid)
        if not a or not a.get("visible") or pid not in PARAMS:
            continue
        row = {"pid": pid, "layer_ok": bool(layers(" ".join(w["layer"] for w in a["where"])) & layers(r.get("layer", "")))}
        if PARAMS[pid]["options"] and a.get("option"):
            mine = {o.strip() for o in a["option"].split(" + ")}
            theirs = manual_options(pid, r["finding"])
            if theirs:  # a manual note that names no option (e.g. "Audio track present") is not scored
                row.update(agent=sorted(mine), manual=sorted(theirs), exact=mine == theirs, partial=bool(mine & theirs))
        rows.append(row)
    return rows


def kappa(rows):
    """Brennan-Prediger kappa on exact matches: chance = 1 / (number of options) of each parameter.
    Suited to small test sets (8 creatives), where chance estimated from the data is unstable."""
    scored = [r for r in rows if "exact" in r]
    if not scored:
        return None
    po = sum(r["exact"] for r in scored) / len(scored)
    pe = sum(1 / len(PARAMS[r["pid"]]["options"]) for r in scored) / len(scored)
    return round((po - pe) / (1 - pe), 2)


def summary(name, rows):
    scored = [r for r in rows if "exact" in r]
    ex, pa = sum(r["exact"] for r in scored), sum(r["partial"] for r in scored)
    lay = sum(r["layer_ok"] for r in rows)
    return (f"{name}: exact {ex}/{len(scored)} ({ex / max(len(scored), 1):.0%}), partial {pa}/{len(scored)}, "
            f"kappa {kappa(rows)}, layer overlap {lay}/{len(rows)}")


def main(target, name=None, report=None):
    target = Path(target)
    files = [(target, name)] if target.is_file() else [(p, p.stem) for p in sorted(target.glob("Creative *.json"))]
    if not files:
        sys.exit(f"no 'Creative N.json' files in {target}")
    all_rows, per_param, misses = [], defaultdict(lambda: [0, 0]), []
    for path, name in files:
        if name in ("Creative 1", "Creative 2"):
            print(f"note: {name} is a worked example in knowledge/, so its score is not a fair test")
        rows = rows_for(json.loads(path.read_text(encoding="utf-8"))["findings"], REF[name]["findings"])
        print(summary(name, rows))
        for r in rows:
            if "exact" in r:
                per_param[r["pid"]][0] += r["exact"]
                per_param[r["pid"]][1] += 1
                if not r["exact"]:
                    misses.append((name, r))
        all_rows += rows
    if len(files) > 1:
        print(summary("ALL", all_rows))
    worst = sorted((ok / n, pid, ok, n) for pid, (ok, n) in per_param.items() if ok < n)
    print("weakest parameters:", ", ".join(f"{pid} {ok}/{n}" for _, pid, ok, n in worst[:8]) or "none")
    if report:
        lines = [f"# Accuracy check: agent vs manual", "", summary("All creatives", all_rows), "",
                 "## Parameters by exact agreement (weakest first)", "", "| Parameter | Exact | Of |", "|---|---|---|"]
        lines += [f"| {pid} {PARAMS[pid]['name']} | {ok} | {n} |" for _, pid, ok, n in
                  sorted((ok / n, pid, ok, n) for pid, (ok, n) in per_param.items())]
        lines += ["", "## Disagreements", "", "| Creative | Parameter | Agent | Manual | Partial |", "|---|---|---|---|---|"]
        lines += [f"| {name} | {r['pid']} {PARAMS[r['pid']]['name']} | {' + '.join(r['agent'])} | {' + '.join(r['manual'])} | "
                  f"{'yes' if r['partial'] else 'no'} |" for name, r in misses]
        Path(report).write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"report written: {report}")


if __name__ == "__main__":
    args = sys.argv[1:]
    report = args[args.index("--report") + 1] if "--report" in args else None
    if not args or (Path(args[0]).is_file() and (len(args) < 2 or args[1] == "--report")):
        print(__doc__); sys.exit(1)
    main(args[0], args[1] if Path(args[0]).is_file() else None, report)
