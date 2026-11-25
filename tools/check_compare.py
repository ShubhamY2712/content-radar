"""Compare an analysis with the checker's independent reading (step 4, chain of verification).

  python tools/check_compare.py runs/<brand>-<date> <creative id>

For every parameter the checker answered, the two readings disagree when their options differ
(options joined by " + " are compared as sets) or one says visible and the other not. Writes the
list into checks/<id>.json -> "disagreements" (a resolution already given for the same pair is kept)
and prints the agreement rate. The analyst then resolves each one: "changed" or "kept: <why>".
"""
import json, sys
from pathlib import Path


def options(f):
    if not f.get("visible", True):
        return ("not visible",)
    return tuple(sorted(o.strip() for o in (f.get("option") or "").split(" + ") if o.strip()))


def compare(run, cid):
    a = json.loads((run / "analysis" / f"{cid}.json").read_text(encoding="utf-8"))
    path = run / "checks" / f"{cid}.json"
    c = json.loads(path.read_text(encoding="utf-8"))
    before = {(d["parameter"], d["analyst_option"], d["checker_option"]): d["resolution"]
              for d in c.get("disagreements", [])}
    out = []
    for pid, answer in sorted(c["answers"].items()):
        mine = a["findings"].get(pid, {"visible": False})
        if options(mine) != options(answer):
            key = (pid, mine.get("option"), answer.get("option"))
            out.append({"parameter": pid, "analyst_option": key[1], "checker_option": key[2],
                        "resolution": before.get(key)})
    c["disagreements"] = out
    path.write_text(json.dumps(c, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    n = len(c["answers"])
    open_ = sum(1 for d in out if not d["resolution"])
    print(f"{cid}: {n - len(out)} of {n} agree ({(n - len(out)) / n:.0%}); {len(out)} disagreements, {open_} unresolved")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print(__doc__); sys.exit(1)
    compare(Path(sys.argv[1]), sys.argv[2])
