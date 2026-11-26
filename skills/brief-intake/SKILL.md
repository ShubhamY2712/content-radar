---
name: brief-intake
description: Turn the user's request (brand + product, optional competitors and settings) into a complete research brief. Step 1 of the content benchmark run.
---

# Brief intake

## Goal
A complete `brief.json` in the run folder, so later steps never have to ask the user again.

## Steps
1. Read the user's request. The only required fields are **brand** and **product** (or category). If either is missing, ask for it in one short question and stop.
2. Fill the optional fields from the request when given; otherwise use these defaults:
   - `market`: "India"
   - `platforms`: ["Instagram", "Facebook", "YouTube"]
   - `time_window_days`: 90
   - `creatives_per_competitor`: 5
   - `brand_creatives`: 5 (the brand's own creatives, the baseline)
   - `competitors_given`: [] (step 2 will find them)
   - `brand_links`: [] (step 2 will find them)
3. Set `product_type` to the generic type of the product, without brand, ingredient or variant (e.g. "Vitamin C face wash" → "face wash", "Onion hair oil" → "hair oil"). Step 3 uses it to keep creatives on the product.
4. Set `product_scope`: `"model"` when the product is one item (one SKU or one model, e.g. "Vitamin C face wash", "Airdopes 141"), `"range"` when it names a line with several models (e.g. "Airdopes", "Rockerz headphones"). If the product names a line and the user did not say which model, **ask one short question and wait**: "<product> has several models. Benchmark one model (which one?) or the whole range?" Never pick a model yourself. Use the user's answer: a model → put it in `product`, scope `"model"`; the whole range → keep the range name, scope `"range"`.
5. Put anything else the user said (audience, price band, campaign goal) in `notes`, in their words.
6. Write `brief.json` and validate it against `schemas/brief.schema.json`.
7. Show the user the brief in 3–4 lines (brand, product and scope, competitors given or "to be found", platforms, window). Do not wait for approval; continue to step 2.

## Output
`brief.json`, for example:
```json
{"brand": "Mamaearth", "product": "Vitamin C face wash", "product_type": "face wash", "product_scope": "model", "brand_links": [],
 "competitors_given": [], "market": "India", "platforms": ["Instagram", "Facebook", "YouTube"],
 "time_window_days": 90, "creatives_per_competitor": 5, "brand_creatives": 5, "notes": ""}
```
