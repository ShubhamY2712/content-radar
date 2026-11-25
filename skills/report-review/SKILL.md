---
name: report-review
description: Check the finished run before calling it done - ids, counts and evidence agree across files, every recommendation is grounded, links open, nothing is guessed - fix what fails and record the review. Step 7.
---

# Report review

## Goal
`review.json` with `"passed": true`, after fixing every issue found. The user hears "done" only after this step.

## Steps
1. **Automatic checks.** Run `python tools/review.py <run folder> --links`. Without Python, do the same checks by hand (list below). Put every issue it prints in `auto_issues`.
2. **Manual checks**, each recorded in `manual_checks` as pass / fixed / open:
   - Counts: pick 3 numbers from the synthesis ("7 of 15 …") and recount them from the analysis files.
   - Evidence: open 3 creatives named in market patterns and confirm the finding is really in the creative.
   - Brand vs market: the gaps in `brand_baseline` match the brand's own analyses.
   - Recommendations: each one is for the brand in the brief, uses a pattern or gap that exists in the synthesis, and does not copy a competitor's creative.
   - No guessing: findings marked visible are things you could actually see or read in the transcript; anything else is `visible: false`.
   - Coverage: sources skipped are listed under Coverage in the report.
3. **Fix** each failed check in the file it comes from (only the wrong lines), validate that file again, re-run `python tools/render_report.py <run folder>`, and run step 1 again.
4. Set `passed` to true only when `auto_issues` is empty (or holds only "link check by hand" lines you have opened yourself and found working) and no manual check is `open`. Write `review.json` with the time in `checked_at`.
5. Tell the user: the report path, the headline findings, the 5 idea titles, and anything left open.

## Checks to do by hand when Python is not available
Every creative has an analysis file; every id named in the synthesis and recommendations exists; no "N of M" count is larger than the number of competitor creatives; market patterns use only competitor creatives (not `C0-…`); every recommendation names a creative id or parameter; report.md was rebuilt after the last change.
