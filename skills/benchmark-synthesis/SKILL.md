---
name: benchmark-synthesis
description: Turn all creative analyses into a short note per competitor, market patterns per parameter (what most do, what few do) and 3-5 headline findings. Step 5.
---

# Benchmark synthesis

## Goal
`synthesis.json`: what each competitor does, what the market does as a whole, and where the gaps are, each backed by creative ids.

## Steps
1. Run `python tools/stats.py <run folder>`: it counts every option of every parameter across the analysis files (market and brand separately) and writes `stats.json`. Then read `competitors.json`, `creatives.json`, `stats.json` and the analysis files, one competitor at a time. Every number you write ("7 of 15") comes from `stats.json`, never from your own count. Without Python, count from the files with the files open.
2. **Per competitor** (`competitor_notes`):
   - `recurring`: 3–5 things that repeat across its creatives (hook type, offer style, format, people, colours, CTA), each with the count, e.g. "Bold-claim hook in 4 of 5 (C1-1, C1-2, C1-4, C1-5)".
   - `standout_creatives`: 1–2 creative ids that are the strongest examples, with one reason each.
   - `note`: 2–3 sentences on its content approach.
3. **Market patterns** (`market_patterns`): for the parameters where creatives differ in a useful way (at least B01, B02, B03, B10, B11, B14, B16, B23, S01, S02, S03, S09, S17, S22), write:
   - `common`: what most creatives do, with a count ("7 of 15 use UGC creators").
   - `rare_or_missing`: what few or none do - these are the content gaps.
   - `evidence`: the creative ids behind it.
   - `stats`: the counts the pattern states, copied from `stats.json` as `{"option", "n", "of", "group": "market"}` (n = creatives with that option, of = creatives the parameter applies to). `tools/review.py` checks them.
4. **Brand baseline** (`brand_baseline`), from the brand's own creatives (`C0-…`), which are not counted in the market patterns:
   - `note`: 2–3 sentences on how the brand's content compares with the market.
   - `vs_market`: for each parameter where the brand differs from the market in a useful way: what the brand does, what the market does, the gap ("Brand uses no social proof; 9 of 15 competitor creatives do"), the evidence ids, and `stats` for both groups (`"group": "brand"` and `"market"`) from `stats.json`.
5. **Headline findings**: 3–5 one-line findings a brand manager should read first, including the biggest brand-vs-market gap.
6. Write `synthesis.json` and validate it.

## Rules
- Count, don't estimate: every number must match the analysis files.
- Product focus: check `product_match` in `creatives.json`. When a pattern or headline finding rests mostly on `Brand range` creatives, say so in it (e.g. "… 4 of 5 are serum ads, not face wash").
- No performance claims (no "this works better", "best performing") - Meta does not show reach or spend for commercial ads. Longevity (ads running for weeks) or engagement shown publicly may be mentioned as a signal, with the number.
