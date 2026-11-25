"""Read-only export of the 10 manually analysed creatives (Creative Analysis sheet) for evaluation.

  python tools/export_reference.py "<path to Creative_Benchmark_Parameters.xlsx>" evaluation/reference_creatives.json
"""
import json, sys
import openpyxl

wb = openpyxl.load_workbook(sys.argv[1], data_only=True)  # loaded only to read; never saved
ws = wb["Creative Analysis"]

# Creative groups: header row 4 holds "Creative N", row 5 the sub-columns
groups, cur = [], None
for col in range(5, ws.max_column + 1):
    h4, h5 = ws.cell(4, col).value, ws.cell(5, col).value
    if h4 and str(h4).startswith("Creative"):
        cur = {"name": str(h4).strip(), "cols": {}}; groups.append(cur)
    if cur and h5:
        cur["cols"][str(h5).strip()] = col

details_rows, param_rows = {}, {}
for row in range(6, ws.max_row + 1):
    pid, label = ws.cell(row, 2).value, ws.cell(row, 3).value
    if pid and label and str(pid)[:1] in "BS" and str(pid)[1:].isdigit():
        param_rows[str(pid)] = row
    elif label and not pid and str(label) in ("Brand", "Industry", "Ad link", "Platform", "Placement", "Format"):
        details_rows[str(label)] = row

out = []
for g in groups:
    first = g["cols"]["Finding"]
    d = {}
    for k, r in details_rows.items():
        c = ws.cell(r, first)
        d[k] = c.hyperlink.target if (k == "Ad link" and c.hyperlink) else (c.value or "")
    findings = {}
    for pid, r in param_rows.items():
        cell = {k.lower(): str(ws.cell(r, c).value or "").strip() for k, c in g["cols"].items()}
        if any(cell.values()):
            findings[pid] = cell
    out.append({"creative": g["name"], "details": d, "findings": findings})

json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(len(out), "creatives;", [len(x["findings"]) for x in out])
