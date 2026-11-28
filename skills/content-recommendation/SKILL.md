---
name: content-recommendation
description: Recommend content ideas for the brand on the same benchmark parameters, based on competitor patterns and gaps, and write the final benchmark report. Step 6.
---

# Content recommendation and report

## Goal
`recommendations.json` (5 ideas by default), the final `report.md` (summary) and `creative_notes.md` (each creative's notes, the appendix).

## Steps
1. Read `brief.json` and `synthesis.json` (and analyses when you need detail).
2. Write 5 content ideas for the brand's product. Start from `brand_baseline`: what the brand is missing compared with the market. Mix:
   - 2 that **use a proven pattern** from the market (common and long-running) that the brand does not use yet,
   - 2 that **fill a gap** (rare or missing in the market and in the brand's own content),
   - 1 for a **different funnel stage or format** than the others.
3. For each idea fill every field in the parameter language:
   - `idea`: one line.
   - `audience`: who it speaks to (B08, B09).
   - `format_platform`: format, aspect ratio, placement, length for video (S01, S19, S23).
   - `hook`: the opening (B01, B02, S21; first 0–3 s for video).
   - `message_proof`: value proposition, supporting facts, proof (B03, B05, B16).
   - `offer_cta`: offer and CTA (B14, B23) - "No offer" is allowed.
   - `style_layers`: the look by layer - background, people, text, graphics, brand, lighting, (video) footage, audio, edit (L1–L14).
   - `parameters`: the parameter IDs the idea is built on.
   - `based_on`: the creative ids or the market pattern it comes from (required).
4. Write `recommendations.json` and validate it.
5. Build the report: `python tools/render_report.py <run folder>` when Python is available; otherwise fill `templates/report.md` by hand in the same order. Every creative and competitor in the report links to its source.
6. Continue to step 7 (report-document), which builds the HTML reports, then step 8 (report-review), before telling the user the run is done.

## Rules
- Ideas are for the brand in the brief, never copies of a competitor's creative - take the pattern, not the content.
- Ideas are for the product in the brief: the named model, or for a range the whole line (a model may lead an idea only if the user named it). Never switch to a model the brief did not name.
- Do not promise results. Recommendations are hypotheses to test.
