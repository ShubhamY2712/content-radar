# Known limitations

What Content Radar does not do yet, or does only partly. Each item is a known decision or gap, not an unnoticed bug.

## Data sources
- **Facebook pages are not collected.** The saved browser login covers Instagram only. Meta Ad Library still opens without a login, so paid Meta ads are collected; organic Facebook page posts are not.
- **No reach, spend or sales data.** "Popular" means longest-running ads and most ad versions (paid) and most views or likes (organic). These are public signals, not performance.
- **Fresh campaigns rank weakly.** When a brand's ads all started a few days ago, days running cannot separate them; the agent ranks by number of versions and logs a `GAP:` line.
- **Old paid ads can be used.** If a brand has no paid ad for the product inside the time window, the agent may use its latest one from before the window and flags it in Coverage.
- **YouTube without an API key** uses yt-dlp. It is slower and hides likes and comments on some videos.
- **Instagram Business Discovery API** needs a Facebook Page and Meta app token, so the logged-in browser is used instead.

## Measuring creatives (`tools/measure.py`, `tools/transcript.py`)
- **OCR can still misread shapes as text.** Junk lines of 1–2 characters covering over 15% of the frame, tall low-confidence lines and Chinese-script glyphs from the Latin reader are dropped. Small 1–2 character misreads can remain. Analysts check text against the frames and set misreads aside.
- **Large display numbers can be missed by OCR** (e.g. a big "42"). They are then judged by eye.
- **Pack matching finds one model.** It matches the pack photo of the product in `competitors.json`. Other models of the same range are not found, and their size is judged by eye.
- **A partial pack match has no size.** When only a small part of the pack (often the logo) matches, `pack.partial` is true, the size is left empty and the match does not count as proof of the exact product.
- **The face detector misses CGI or stylised people.** The analysts then judge talent and faces by eye.
- **Hindi and Hinglish transcripts can be garbled**, mainly over loud music. Spoken findings on those videos are checked against the frames and marked when unsure.

## Analysis
- **Accuracy against a human coder is not measured yet.** `evaluation/compare.py` scores the agent on the 8 held-out reference creatives (Creatives 3–10). That run has not been done.
- **Agreement is between the agent's own readers.** The 86% average in the boAt test run (25–26 Nov 2026) is analyst vs independent checker, not agent vs human.
- **Some options are judgment calls.** `knowledge/option_guide.md` defines every option, and the boAt run's three open coding questions are now settled there:
  - `" + "` only on the listed multi-dimension and list parameters
  - a brand's own test-lab footnote is a disclaimer, not a proof point
  - a slogan with no way to buy is a soft CTA

  Runs made before this change may break the stricter one-option rule when re-validated.

## Engineering
- **No automated test suite.** The tools were tested by hand on copies of real runs and on generated cases (planted faults, pasted packs, synthetic clips). There is no `tests/` folder.
- **Cost.** A full run (about 20–25 creatives, with 2 analysts, 1 checker and a resolver per creative) uses a large share of a Claude Pro 5-hour limit. Expect one or more resumes. Progress is saved in the run folder, so a stopped run continues where it left off.
- **Run outputs are not in the repository.** `runs/` holds other brands' ads and is git-ignored. Reports are for internal use.
