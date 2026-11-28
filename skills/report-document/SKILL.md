---
name: report-document
description: Turn the finished analysis into two client-ready HTML reports - a summary report and a detailed report with every creative's 54 findings - by writing report_content.json and rendering it with the report kit. Step 7.
---

# Report document

## Goal
Two self-contained HTML files in the run folder, written for the brand's marketing team:
- `report.html` (summary): sections 01–09 below.
- `report_detailed.html` (detailed): the same 01–09, then 10 "Creative notes" with every creative's 54 findings.

You write only the words and choices, in `report_content.json` (shape: `schemas/report_content.schema.json`). `python tools/render_html.py <run folder>` builds both files from it plus the run files: layout, icons, charts, counts, thumbnails and links are done by the tool, so never write HTML yourself.

## Before you write
1. Read `brief.json`, `competitors.json`, `creatives.json`, `synthesis.json`, `stats.json`, `recommendations.json`, `log.md`, and the analyses you need. Every number you write comes from these files (prefer `stats.json` counts); never recount by memory.
2. **Logos.** For the brand (`C0`) and each competitor (`C1`, `C2` … in `competitors.json` order) run `python tools/fetch_logo.py <run folder> C<n> <website>` (the `website` from `competitors.json`); it saves the site's largest icon as `media/logos/C<n>.png`. If it finds none, open the brand's Instagram page in the browser, copy the profile picture's image URL and run the same command with that URL. Put the paths in `logos` (`{"C0": "media/logos/C0.png", …}`); use `null` when there is no clean logo (the report then shows the brand's initials). Read only: never sign in to get a logo.
3. **Thumbnails.** For each creative pick one image that shows it best (`thumbnails`): for a photo its main image; for a video the frame where the product or the key line is clearest, not a black or blurred frame (look at the frames). Use paths that exist under `media/`.
4. **Key frames (optional).** For a video where the even spread the tool picks would miss the hook, product or end card, list 4–6 frame paths in `key_frames` in time order.

## What goes in each section
Write for a brand manager who reads fast. Short sentences, one idea each, plain words, a number wherever there is one ("8 of 15", never "most"). Cite creatives by id (C1-2) so the report can show their thumbnails. Lengths below are guides, not caps; `tools/review.py` flags text far over them.

| Field | What to write | Guide |
|---|---|---|
| `dek` | One line under the title: what is compared with what, on how many creatives. | ≤ 25 words |
| **01 Product brief** `brief.paragraphs` | 1–2 short paragraphs: brand, product (the named model, or the whole range), market, period, platforms, competitors; the matched product per brand with price when known. | ≤ 110 words in all |
| `brief.method_note` | How "popular" was picked (paid: days running and versions; organic: views or likes), that these are public signals only, and the 54 parameters (29 business, 25 style). | ≤ 60 words |
| **02 Headline findings** `findings.items` | 5 by default, most important first; use 3–7 when the data clearly has fewer or more findings worth a manager's time (never pad). `headline`: the point in under 9 words. `stat`: the one number that proves it (`value` digits only, `of` when it is a count, `suffix` like "M" for views, `label` what it counts). `key_line`: the finding in one sentence with its numbers. `highlight`: the exact words inside `key_line` to mark. `detail`: one or two sentences of what it means or the exception. `creatives`: 1–3 ids that show it. `icon`: a file name from `report_kit/icons/phosphor-regular/` without `.svg`. | key_line ≤ 35, detail ≤ 45 words |
| `findings.lede` | One line on how to read the cards. | ≤ 25 words |
| **03 Competitors and why** `competitors.selection_rule` | How competitors were found and approved: market rank, same price band, same product type, active in the window. | ≤ 60 words |
| `competitors.why` | One short reason per competitor, keyed by its exact name in `competitors.json`; `baseline_why` says the brand is the baseline. | ≤ 30 words each |
| `competitors.creative_rule` | How creatives were picked (exact product → same type → range; paid by days running and versions, organic by views or likes; free picks for missing formats). | ≤ 70 words |
| `competitors.gaps` | Every `SKIPPED:` and `GAP:` line from `log.md`, rewritten as one plain sentence each (what was not covered and why). | ≤ 30 words each |
| **04 Competitor notes** `competitor_notes.summary` | How the competitors differ from each other, in one paragraph. | ≤ 80 words |
| `competitor_notes.brands` | Per competitor: `strategy` (its approach in one or two sentences), `repeats` (2–4 things it does again and again, each with `n` of `of` its own creatives), `standout` (one creative id and why it stands out), `does_not` (1–3 things it never does). | strategy ≤ 40 words |
| **05 Brand vs market** `brand_vs_market` | `gaps` (where the brand is behind) and `strengths` (where it leads), as many as the data shows (usually 2–4 each, strongest first; leave a list empty if there is truly none). Each: `parameter`, a short `title`, `brand` and `market` counts from `stats.json`, `meaning` (what it means for the brand), `creatives` (the brand creative and a market creative that show it). | meaning ≤ 35 words |
| `positioning_map` | Choose the two parameters (or option pairs) that separate the brands most in this run - there is no default - and say why in `reason`. Give each axis a `label` and its `low` and `high` ends. Place every brand (exact names, the brand included) from 0 to 1 on each axis from its share of creatives at each end. | reason ≤ 40 words |
| **06 Business view** `business_table` | One row for each business parameter that applies to this run's formats (B01–B29; B25–B29 are video-only, so a run with no video leaves them out), most important for the brand first. `market`: what most competitors do, with counts. `brand`: what the brand does. `gap`: what it means. `status`: `gap` (brand behind), `lead` (brand ahead) or `parity`. `evidence`: 1–3 creative ids. `lede`: one line on how the rows are ordered. | each cell ≤ 30 words |
| `funnel_note` | One sentence on what the funnel chart shows for the brand (the chart and the funnel map are drawn from B10). | ≤ 30 words |
| **07 Creative and style view** `style_table` | The same for the style parameters (S01–S25; S21–S25 are video-only). Add `swatches_market` / `swatches_brand` (hex colours from the measures) on colour rows (S06, S07). | each cell ≤ 30 words |
| **08 Recommended content** `ideas.items` | One entry per idea in `recommendations.json`, same order: `type` (Proven pattern / Fill a gap / New funnel stage or format), a short `title`, and `why` it should work (the gap or pattern behind it, with its numbers). The rest of each card comes from `recommendations.json`. | title ≤ 9, why ≤ 40 words |
| **09 Sample creatives** `why_selected` | For every creative, why it was picked, in a few words ("Longest-running Noise ad", "Only Spektra reel in the window"). The tile already shows days running, versions, views, likes and comments, so do not repeat those numbers. `gallery_lede`: one line. | ≤ 14 words each |
| **10 Creative notes** `hooks` | For every creative, the hook (first words seen or heard). Quote it as written or said, in its own script; when it is not English, add `translation`. | |
| `story` | For every video, its beats in time order: `beat` is a shot name from `knowledge/breakdown.json` (e.g. "SH1 Hook"), `from` and `to` in seconds, `what` happens. | ≤ 20 words each |
| `creatives_lede` | One line on how to use the filters. | |

## Nothing is fixed to one category
The report's structure (sections, the 54 parameters, funnel stages, match levels, idea types) comes from the framework files, so reports stay comparable. Everything inside it comes from this run: which findings matter and how many, which parameters lead the tables, the map's axes, the gaps and strengths, the words, the currency, the platforms and the languages quoted. Write for this brand's category and market; never carry over wording, numbers or examples from another run or from the examples in this skill.

## Writing rules
- Facts only from the run files. If a count is not in `stats.json` or the analyses, do not write it.
- Hindi or Hinglish quotes stay in their own script, with the English meaning right after (in `translation` for hooks, in brackets elsewhere).
- No filler, no hype words (powerful, seamless, game-changer, leverage, unlock), no "In conclusion", no instructions to the reader about the report itself.
- Name the brand and competitors exactly as in `competitors.json`.
- Ideas stay hypotheses to test; do not promise results.

## Steps
1. Do "Before you write", then write `report_content.json` and check it: `python tools/validate.py <run folder> report_content.json`.
2. Render: `python tools/render_html.py <run folder>`. It prints `PROBLEM` lines (a missing thumbnail, an unknown id, a table missing a parameter, a highlight not found in its key line …). Fix each in `report_content.json` and render again until it prints `0 problems`.
3. Look at both files if you can open a browser (open the file path): the first screen, one finding card, a table and one creative note. Fix anything that reads badly.
4. Continue to step 8 (report-review). After any fix to the run files, render again.

Without Python, write `report_content.json` anyway and tell the user to run `python tools/render_html.py <run folder>` on a computer that has it; the markdown `report.md` stays the fallback.
