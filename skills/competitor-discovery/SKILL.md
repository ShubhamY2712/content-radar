---
name: competitor-discovery
description: Find (or check) the brand's competitors and every link where their content lives - website, Instagram, Facebook page, YouTube channel, Meta Ad Library and Google Ads Transparency pages. Step 2; needs user approval.
---

# Competitor discovery

## Goal
`competitors.json` with 3 relevant competitors (or the ones the user gave) and their content links, approved by the user.

## Steps
1. Read `brief.json`.
2. **If competitors are given**, use only those (do not add more unless the user asks). Go to step 4.
3. **Otherwise find 3.** Search the web for the product category in the market (e.g. "best vitamin C face wash India", "<brand> alternatives", "<brand> vs"), marketplace category pages and recent comparison articles. Pick brands that:
   - sell the same product type to the same buyer,
   - are in a similar price band,
   - are active on Instagram or YouTube in the time window.
   Write one line in `why` for each (e.g. "Same category, similar price, 3 recent reels on vitamin C").
4. **Find the links for each competitor** (leave `null` when it does not exist):
   - `product_name` and `product_page`: the competitor's own product that matches the brief, on its official website (else a marketplace page). Look for the exact product first (same type and same key ingredient or claim, e.g. its Vitamin C face wash); if it has none, its closest product of the same `product_type`, and say so in `why`. Step 3 searches for creatives by this name. When the brief's `product_scope` is `"range"`, match a range with a range: the competitor's comparable product line (e.g. Noise Buds for boAt Airdopes), with the line's collection page as `product_page`; never narrow it to one model.
   - `product_image`: save the product's main pack photo from that page (the front of the pack on a plain background, the largest size offered) as `media/products/C<n>.<ext>` (`C0` for the brand) and put that path here; `tools/measure.py` uses it to find the pack in every creative. `null` if the page has no usable photo.
   - `website`: official site.
   - `instagram`: `https://www.instagram.com/<handle>/` - check the handle from the brand website footer or a search; prefer the verified account.
   - `facebook`: the brand's Facebook page URL.
   - `youtube`: channel URL.
   - `ad_library`: `https://www.facebook.com/ads/library/?active_status=active&ad_type=all&country=IN&q=<brand name>&search_type=keyword_unordered` (use the market's country code). If you can open it, replace with the page's own Ad Library link (`...&view_all_page_id=<id>`).
   - `google_ads_transparency`: `https://adstransparency.google.com/?region=IN&domain=<website domain>`.
   - `sources`: the pages that confirmed this competitor and its links.
5. Find the same links, including `product_name`, `product_page` and `product_image` for the brief's product, for the **brand itself** (`product_name` is exactly the brief's product: the named model, or for a range the range name, never a model you chose; for a range, `product_image` is the pack of the range's best-selling model and only helps find that model) and put them in `brand` (it is the baseline in step 3, not a competitor).
6. Write `competitors.json` with `"approved_by_user": false` and validate it.
7. **Stop and ask.** Show a short table (name, why, matching product, Instagram, YouTube) and ask the user to confirm, remove or add competitors. Apply their answer, set `"approved_by_user": true`, save, then continue.

## Rules
- Do not sign in anywhere. If Instagram or Facebook shows a login wall, keep the URL and note it; step 3 uses other routes.
- Never include the brand itself as a competitor.
- At most 5 competitors.
