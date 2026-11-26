---
name: creative-collection
description: Collect the strongest recent creatives (paid ads and organic posts, photo and video) for each approved competitor plus the brand's own as a baseline, with selection evidence, media, 1-2 fps video frames, cut times and transcripts. Step 3.
---

# Creative collection

## Goal
`creatives.json` plus `media/`: for each competitor `creatives_per_competitor` creatives, and `brand_creatives` creatives of the brand itself (ids `C0-1`, `C0-2` …) as a baseline. Each creative is openable from its link and has the evidence for why it was picked.

## Reuse first
If `media/<id>/` already holds the files for a creative recorded in an earlier pass of this run, keep it and do not fetch it again.

## Which creatives to pick (selection rule)
**Product first.** The brief is about one product, so every slot below is filled in this order of product match, and only then by popularity:
1. **Exact product**: the competitor's `product_name` (or for the brand, the brief's product). When the brief's `product_scope` is `"range"`, any model of that product line counts (e.g. Airdopes 141 for "Airdopes").
2. **Same product type**: another product of the brief's `product_type` (e.g. a Cica face wash when the brief is a Vitamin C face wash).
3. **Brand range**: any other product of the brand, as a fallback only when levels 1 and 2 have nothing left for that slot.

To find level 1 and 2 creatives, search before browsing the whole account: Ad Library keyword `<brand> <product name words>`, then `<brand> <product_type>`; on Instagram and YouTube, the product name and type in captions and titles (web search `site:instagram.com/<handle> "<product words>"`). Record the level in `product_match` and what is on screen in `product_shown` (e.g. "Vitamin C serum face wash tube"; for several products, name them all and use the best match among them). A creative with no product on screen is `No product` (allowed for the brand baseline, a last resort for competitors).

Per competitor, 5 by default (scale the numbers if different):
- **2 paid ads.** Rank active ads by days running (from "Started running on"), longest first; break ties by the number of versions ("This ad has N versions"). Ads that run 30+ days or have several versions are the ones the brand keeps paying for. Skip near-duplicates of an ad already picked.
- **2 organic posts.** Within the time window, highest views (videos) or likes (posts) first.
- **1 free pick** that adds a format or placement not yet covered.
- At least 1 photo and 1 video per competitor where they exist.
- Write `selection_reason` for every creative with the match level and the popularity evidence, e.g. "Exact product; running 64 days, 3 versions" or "Brand range (no face-wash reel in 90 days); top reel by views (1.2M)".
- "Popular" here is a public signal only (days running and versions for ads, views and likes for organic posts). The Ad Library shows no reach, spend or sales for commercial ads, so never call a creative "best performing".

For the brand itself (C0): the same rule with `brand_creatives` creatives (5 by default, so the brand is compared on the same footing as each competitor), product first.

**Say what is missing.** Write a `GAP:` line (one line each) when: the brand or a competitor has no active ad or post for the exact product (`GAP: <name> – no active ad for <product>; used <level>`); fewer creatives exist than asked for (`GAP: <name> – only <k> of <N> creatives in the window`; never pad); or a creative comes from a page other than the brand's own page for the market (`GAP: <name> – <id> from the global page`). The report lists these under Coverage.

**The market's own page.** Take ads only from the brand's own page for the market (in the Ad Library, the advertiser shown on the ad is the brand's page for that country, e.g. "Garnier India", not the global "Garnier"). A global or other-country page is a last resort: add "(global page)" to `selection_reason` and a `GAP:` line.

## Where to look (in this order; skip any you cannot reach and log `SKIPPED: <source> – <reason>`)
1. **Meta Ad Library website** (`ad_library` link, public, no login). Filter: country = market, active. For each ad: Library ID link (`https://www.facebook.com/ads/library/?id=<id>`), started running date, days running, versions, platforms, format, primary text, headline, CTA. The official API does not return ordinary ads shown only in India, so read the website.
2. **YouTube.** `python tools/youtube.py videos --channel <channel> --days <window> --max 10` (title, description, date, duration, views, likes, comments): it uses `YOUTUBE_API_KEY` when set, and yt-dlp without a key. Without Python, the channel's Videos and Shorts tabs. Rank by views within the window. A channel with no upload in the window: write `SKIPPED: YouTube <name> – no upload in <window> days`.
3. **Instagram.** With `IG_USER_ID` and `IG_ACCESS_TOKEN`: `python tools/instagram.py media --username <handle> --max 12`. Otherwise the profile in the browser (logged in through the saved `auth.json`; see the setup check in `AGENTS.md`), or posts found by web search (`site:instagram.com/<handle>`) if it shows a login wall.
4. **Google Ads Transparency** (paid YouTube, display and search ads; browser, no login). Open `https://adstransparency.google.com/?region=<country code>&domain=<website domain>&preset-date=Last+30+days`, then add `&platform=YOUTUBE&format=VIDEO` for YouTube video ads, or `&format=IMAGE` for display ads (the filters are part of the URL). Check that the advertiser shown is the brand. For each ad open its detail page and record: the ad's own URL (`.../advertiser/AR…/creative/CR…`) as `link`, platform `YouTube / Google`, format, `versions` = the number of variations shown, and the last-shown date in `notes`; when the page shows a first-shown date, set `started_running` and `days_running` (first to last shown). Rank paid Google ads like Meta ads: longest-running first, then most variations. For a YouTube video ad, also open its YouTube video and use that link for `frames.py`.

## For each creative
1. Id `C<competitor number>-<n>` (brand = `C0`). Record competitor (brand name for C0), link, `product_shown`, `product_match`, platform (`Meta` or `YouTube / Google`), placement (from `knowledge/breakdown.json` → creative_details → Placement), format (`Image`, `Carousel`, `Video`), paid or organic, date seen (today), and every selection field you have: `started_running`, `days_running`, `versions`, `published`, `views`, `likes`, `comments`. Unknown = `null`.
2. Copy the caption / primary text / title as written.
3. **Photo or carousel:** save the image or each card into `media/<id>/`.
4. **Video:** run `python tools/frames.py <link> media/<id>` with the creative's own link (Ad Library `?id=` link, reel or YouTube link); it downloads the video to `media/<id>/video.<ext>` (yt-dlp, else a direct `.mp4` link you found on the page) and extracts the frames. If the download fails, save the video yourself and pass the file. It saves 1 frame per second (up to 30 s) or 1 per 2 s, the end card, and `frames.json` with the duration and cut times. Copy `duration_s`, `frames` and `cuts_s` into the creative. Without Python or ffmpeg, save at least 6 frames by hand (0 s, 1 s, 2 s, 3 s, middle, end; for clips under 6 s, one per second) and leave `cuts_s` empty.
5. **Transcript and sound (video):** `python tools/transcript.py media/<id>/video.<ext> media/<id>/transcript.json` (words with faster-whisper, plus the sound facts: audio track, silence, speech and other sound in seconds); for a YouTube video whose file you could not save, pass its URL to get its captions. Set `transcript` to the JSON path, or `null` if it fails; the analysis then marks audio as not visible. Write the platform's audio label (e.g. "Original audio", or the song name on a reel) into `notes`.
6. **Measure (photo and video):** `python tools/measure.py media/<id> --pack <product_image of this brand in competitors.json> --hindi` (leave out `--pack` when there is no pack photo; `--hindi` for India and other markets with Devanagari text). It writes `media/<id>/measures.json`: on-creative text with positions, text share, safe zones, faces, colours, pack sightings and when each first appears. Use it to confirm `product_match`: `Exact product` needs the pack seen (`pack.found`) or the product named in the on-creative text or copy; otherwise lower the level. Without Python, skip it; the analysis then judges these by eye.
7. If a creative cannot be saved (login wall, removed), drop it and take the next one in the ranking.

## Output
Write `creatives.json` and validate it. Tell the user one line per competitor (and the brand): how many creatives, how many at each match level, from which sources, and any `GAP:` lines.

## Rules
- Load pages one at a time with a short pause; download only the creatives you picked.
- Never sign in, like, follow or comment.
