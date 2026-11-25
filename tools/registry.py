"""Skill registry and loader.

  python tools/registry.py build          check every skill and write skills/registry.json
  python tools/registry.py check          check only (exit 1 on errors)
  python tools/registry.py list           skills in run order
  python tools/registry.py search <text>  find skills by name or description
  python tools/registry.py show <name>    print a skill's metadata and SKILL.md (the loader)
"""
import json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILLS = ROOT / "skills"
FIELDS = ["name", "version", "order", "depends_on", "inputs", "outputs", "schemas",
          "knowledge", "tools", "permissions", "human_approval"]
ALLOWED_PERMISSIONS = {"internet_read", "file_write_run"}


def frontmatter(text):
    if not text.startswith("---\n"):
        return {}
    head = text[4:text.index("\n---", 4)]
    return dict(line.split(": ", 1) for line in head.splitlines() if ": " in line)


def collect():
    skills, errors = [], []
    for folder in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        md, meta = folder / "SKILL.md", folder / "skill.json"
        if not md.exists() or not meta.exists():
            errors.append(f"{folder.name}: needs SKILL.md and skill.json"); continue
        fm, m = frontmatter(md.read_text(encoding="utf-8")), json.loads(meta.read_text(encoding="utf-8"))
        err = lambda msg: errors.append(f"{folder.name}: {msg}")
        missing = [f for f in FIELDS if f not in m]
        if missing:
            err(f"skill.json missing {missing}")
        if not (fm.get("name") == m.get("name") == folder.name):
            err("folder name, SKILL.md name and skill.json name must match")
        if not fm.get("description"):
            err("SKILL.md needs a description")
        for s in m.get("schemas", []):
            if not (ROOT / "schemas" / s).exists():
                err(f"schema not found: {s}")
        for k in m.get("knowledge", []):
            if not (ROOT / "knowledge" / k).exists():
                err(f"knowledge file not found: {k}")
        for t in m.get("tools", []):
            if t.startswith("tools/") and not (ROOT / t).exists():
                err(f"tool not found: {t}")
        workers = m.get("worker") or []
        for w in [workers] if isinstance(workers, str) else workers:
            if not (ROOT / w).exists():
                err(f"worker brief not found: {w}")
        bad = set(m.get("permissions", [])) - ALLOWED_PERMISSIONS
        if bad:
            err(f"permission not allowed: {sorted(bad)}")
        skills.append({**m, "description": fm.get("description", ""), "path": f"skills/{folder.name}/SKILL.md"})

    by_name = {s["name"]: s for s in skills}
    orders = [s.get("order") for s in skills]
    if len(set(orders)) != len(orders):
        errors.append("two skills share the same order")
    for s in skills:
        for d in s.get("depends_on", []):
            if d not in by_name:
                errors.append(f"{s['name']}: depends on unknown skill {d}")
            elif by_name[d]["order"] >= s["order"]:
                errors.append(f"{s['name']}: depends on {d}, which runs later")
    return sorted(skills, key=lambda s: s.get("order", 0)), errors


def main(args):
    cmd = args[0] if args else "list"
    skills, errors = collect()
    if cmd in ("build", "check"):
        for e in errors:
            print("ERROR", e)
        if errors:
            return 1
        if cmd == "build":
            reg = {"agent": "content-benchmark", "order": [s["name"] for s in skills], "skills": skills}
            (SKILLS / "registry.json").write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"{cmd}: {len(skills)} skills OK")
    elif cmd == "list":
        for s in skills:
            gate = "  [approval]" if s.get("human_approval") else ""
            print(f"{s['order']}. {s['name']} v{s['version']} -> {', '.join(s['outputs'])}{gate}")
    elif cmd == "search":
        q = " ".join(args[1:]).lower()
        for s in skills:
            if q in s["name"].lower() or q in s["description"].lower():
                print(f"{s['name']}: {s['description']}")
    elif cmd == "show":
        s = next((s for s in skills if s["name"] == (args[1] if len(args) > 1 else "")), None)
        if not s:
            print("unknown skill"); return 1
        print(json.dumps({k: s[k] for k in FIELDS}, indent=1))
        print((ROOT / s["path"]).read_text(encoding="utf-8"))
    else:
        print(__doc__); return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
