---
name: creative-analysis
description: Analyse one creative on the 54 benchmark parameters - evidence first, measured facts before eye judgement - for each the evidence, finding, option and where it sits (shot for video, layer, assets); a Business analyst and a Style analyst split the work and an independent checker re-reads it. Step 4; run per creative.
---

# Creative analysis

## Goal
One file `analysis/<creative id>.json` per creative (`"version": 2`), filled the same way as the manual Creative Analysis sheet, every visible finding backed by evidence and checked by a second, independent reading.

## Who does what (team mode; see AGENTS.md → Team)
1. Two analysts per creative, in parallel: `analyse B` writes `analysis/parts/<id>-B.json` (B01–B29), `analyse S` writes `analysis/parts/<id>-S.json` (S01–S25). One focus per pass gives better judgements than all 54 at once.
2. The boss merges them: `python tools/merge_parts.py <run> --analysis <id>`.
3. A checker (`agents/checker.md`) answers every parameter with an option list on its own, without seeing the analysis: `checks/<id>.json`.
4. The boss compares: `python tools/check_compare.py <run> <id>`.
5. An analyst resolves each disagreement: changes the finding, or keeps it with the evidence for why.
Without sub-agents, do the same jobs one after another, in this order, with the same files; do the checker's job before you look at the merged analysis again.

## Before you start
Read `knowledge/parameters.md` (or `parameters.json`), `knowledge/breakdown.json` and `knowledge/option_guide.md` (your half is enough). Use only their parameter IDs, options, shots, layers and assets, and choose options by the definitions, include/exclude rules and examples in the option guide. Read `knowledge/examples/example_photo.md` and `example_video.md` once for the level of detail expected.

**One creative per pass.** Do not keep earlier creatives in mind; the synthesis step reads the saved files.

## Measured parameters (use the numbers, not your eye)
`media/<id>/measures.json` (from `tools/measure.py`) and `transcript.json` (from `tools/transcript.py`) measure things vision models misjudge: small text, counts, sizes, positions, time. When a measure exists, the finding must agree with it and cite it; judge by eye only what is not measured (and say so). A measure that is `null` was not taken.

| Parameter | Use |
|---|---|
| B01 Hook message, B14 Offer, B23 CTA, S10 Typography, S25 Captions | `text` lines (exact words, position, time) |
| B13 Language | `text` lines + transcript `language` and words |
| B26 Brand first appears at | first frame whose `text` holds the brand name, or the logo seen |
| B27 Product first appears at | `summary.first_pack_s` (pack match); else first frame with the product by eye |
| S07 Colour palette, S06 Brand colour use | `colours` (main colours with shares) |
| S08 Contrast and legibility | `text[].contrast` (4.5 or more = easy; 3 = minimum for large text) |
| S09 Text vs image ratio | `text_area_pct` (largest and typical frame) |
| S16 Product / subject size in frame | `pack.size_pct`; for people, `faces[].size_pct` |
| S17 People | `faces` (count, size, first time); null = judge by eye |
| S19 Aspect ratio | `size` (width × height) |
| S20 Safe zones | `safe_zone` (9:16 only: text in the top 14 %, bottom 35 % or 6 % sides) |
| S21 Opening frame | the 0 s frame's `text`, `faces`, `pack` |
| S22 Pacing / cuts | `summary.cuts_s` |
| S23 Length | `duration_s` in `creatives.json` |
| S24 Audio type | transcript `audio` (`has_audio`, `tags`: speech, music, singing seconds) + segments |

## Steps (per creative, your half)
1. Open, in this order: the creative's entry in `creatives.json` (copy, notes, `product_shown`), `measures.json`, the transcript, then the images or all frames in time order with their times.
2. Go through your half's parameters in order. Skip parameters whose `applies_to` does not match the format (Video-only parameters for an image; `Image` parameters for a video). A carousel counts as an image.
3. For each parameter write, **in this order**:
   - `evidence`: where you saw it, one item per source: `measure: <field> <value>` (e.g. `measure: text 'Glow in 7 days' top, 0 s`), `frame 2 s`, `transcript 0.4–1.6 s`, `copy`, `image`. A visible finding with no evidence fails validation.
   - `finding`: what you see, specific and short. Quote on-screen text in quotes. For video include the time (e.g. "0–2 s: close-up of oily T-zone").
   - `option`: one option from the parameter's list (or two joined by " + " when both clearly apply), chosen by the option guide's rule. `null` for free-text parameters. Absence is a normal answer: when the guide's "present" rule is not met, choose the "none / absent" option; do not lean towards yes.
   - `visible`: `false` when it cannot be judged from what you have (e.g. audio with no transcript); then `finding` = "Not visible" plus why, and `option` = null.
   - `where`: one line per place it shows up. Each line = the **layer** (L1–L14, or "Full frame (L1–L9)") and its **assets** - names from that layer's asset list, or a property term the parameter's own mapping uses (e.g. "Colours", "Position", "All text"). For video also the **shot**: the actual beat where you saw it (SH1–SH7, or "All beats (SH1–SH7)"); where the mapping says something like "Beat where brand first appears", write that beat. Use the parameter's `photo` / `video` mapping as the starting point and keep only the lines that are true for this creative.
4. Check against the benchmark line of each parameter and note clear misses in the finding (e.g. "Brand first appears at 6 s - later than the 2 s benchmark for Meta").
5. Write your file with `"creative_id"`, `"version": 2`, `"format"` and `"findings"`, and validate it (`python tools/validate.py <run> analysis/parts/<id>-<B or S>.json`).

## Example (video, B01 Hook message)
```json
"B01": {"evidence": ["measure: text 'SUN PROTECT YOUR BABY'S SKIN' centre, 0-2 s", "frame 0 s"],
        "finding": "0–2 s kinetic text \"SUN PROTECT YOUR BABY'S SKIN\" over a baby close-up",
        "option": null, "visible": true,
        "where": [{"shot": "SH1 Hook", "layer": "L5 On-creative text", "assets": ["Headline"]},
                  {"shot": "SH1 Hook", "layer": "L4 People / characters", "assets": ["Face close-up"]}]}
```

## Rules
- Judge only what is in the creative, its copy and its measures; no outside assumptions about the brand.
- Measured facts beat eye judgement. If the frames clearly contradict a measure (e.g. OCR misread a word), say so in the finding and quote what the frame shows.
- Without a transcript, audio cannot be judged: for S24 and audio lines write only what is visible (captions, a music sticker) or set `visible: false`.
- Brand creatives (`C0-…`) are analysed exactly like competitor creatives.
