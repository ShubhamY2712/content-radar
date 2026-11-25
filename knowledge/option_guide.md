# Option guide (codebook)

How to choose an option so that two readers judge the same creative the same way. For every parameter with options: what each option means, what does **not** count (`Not:`), where a measure decides it (`Measure:`), and examples from the two worked creatives (`Ex:` C1 = Ray-Ban Meta static, Feed 1:1; C2 = Mamaearth baby sunscreen video, Feed 1:1, 15.5 s). Creatives 3–10 of the reference set are kept out on purpose: they are the test set for `evaluation/compare.py`.

Times are from the start of the video; "first screen" = what shows before any scroll or swipe on a photo or the first carousel card.

## General rules
- **Evidence first.** Write where you saw it before you choose (see the creative-analysis skill). A measured fact (`measures.json`, transcript) beats an eye judgment; when a frame clearly shows the measure is wrong (OCR misread), say so.
- **Absence is a normal answer.** Choose an option only when its rule below is met; otherwise choose the "none / absent / not shown" option. Do not lean towards yes.
- Pick the option that fits best. Join two with " + " only when both clearly apply (e.g. hook type "Problem call-out + Before / after").
- Parameters whose options cover several dimensions (B23, B24, S07, S10, S17, S18, S19) take one option per dimension, joined by " + " (e.g. S18 "Top-left + Subtle").
- Parameters that list everything present (B05, B16, B21, B22) join all that apply, in order of prominence.
- When the evidence is not in the creative (sound with no transcript, a cropped placement), set `visible: false`; never pick the closest option.
- Judge the creative as the viewer sees it in its placement, not the brand's other content.

## Business

**B02 Hook type** (the opener's tactic: first 3 s of a video, the headline / first screen of a photo)
- Bold claim: a strong statement of superiority or result ("#1 selling", "Best sunscreen for babies"). Ex: C1 "THE #1 SELLING AI GLASSES".
- Problem call-out: names the viewer's problem ("Tired of oily skin?" — the problem, with or without a question mark).
- Question: the opener is a literal question and the question itself is the hook (not a problem call-out phrased as a question).
- Statistic: a number is the hook ("97% saw clearer skin").
- Curiosity gap: withholds the answer ("The one thing dermats never tell you").
- Pattern interrupt: an unexpected visual or sound that breaks the scroll, not tied to the message.
- Testimonial: opens with a user's words or reaction.
- Contrarian: goes against common belief ("Stop using face wash twice a day").
- Before / after: opens on the change.
- Demo / product in action: opens on the product working.
- Offer-led: the discount or price is the opener.
- Persona call-out: addresses a group by who they are ("New moms,", "For oily skin"). Ex: C2 "SUN PROTECT YOUR BABY'S SKIN" calls out parents.
- Story open: starts a narrative ("Last year I…").
- Trend / pop-culture: opens on a trend format, meme or sound.
- Not: a logo or brand name alone is not a hook type (B25 = No).

**B03 Value proposition**: the single benefit the creative wants remembered. If two are equal, choose the one in the headline. Price / savings = cheaper or a deal is the point; Quality = better made, premium; Convenience = easier, faster to use (Ex: C1 hands-free "Hey Meta"); Speed = fast results or delivery; Results / transformation = a visible change (glow, fewer spots); Safety / trust = gentle, safe, protective (Ex: C2 SPF 50 for babies); Health = well-being; Status = prestige; Identity = who you are, values.

**B04 Single clear message**
- Clear and early: the main message can be said in one sentence and is readable or heard within 3 s (video) or in the first screen (photo). Ex: C1, C2.
- Clear but buried: one message, but it appears after 3 s, below the fold, or only in the caption.
- Several competing messages: two or more unrelated claims with equal weight.

**B05 Supporting facts** (list all present): Problem = the problem is stated; Feature = what the product has; Benefit = what it does for the viewer; Spec / ingredient = a named ingredient, %, size or number (Vitamin C, SPF 50, 175 ml); How it works = the mechanism; Comparison = against another product or the old way; Proof point = test result, rating, award. Ex: C1 "Feature; Benefit"; C2 "Benefit; Feature" (SPF 50, water resistant 120 min).

**B06 Problem–solution clarity**
- Clear: the problem is shown or said AND the product is presented as the fix.
- Partial: only the problem or only the solution is explicit; the link is implied. Ex: C1 (hands-free use implied, no problem stated), C2 (sun on baby skin implied).
- Absent: no problem is shown or implied.

**B07 Product shown and role**
- Hero: the product is the largest subject or the focus of the first screen / opening shot. Ex: C1. Measure: `pack.size_pct` 30 or more in the key frame supports Hero.
- Visible, secondary: on screen and recognisable, but not the focus. Ex: C2 (tube beside graphics and models).
- In use / demo: shown being applied, worn, cooked or operated (wins over Visible, secondary when both happen; join with " + " when the product is also the hero).
- Incidental: appears briefly (under 1 s) or small (under about 10 % of the frame) in a lifestyle scene.
- Not shown: no product anywhere (logos on clothes do not count).

**B09 Awareness stage** (Schwartz)
- Unaware: talks about life or emotion; no problem or product named.
- Problem-aware: names the problem, not a solution type.
- Solution-aware: talks about the type of solution (e.g. "vitamin C serum", "AI glasses"), brand secondary. Ex: C1, C2.
- Product-aware: about this product's features, proof or comparison.
- Most aware: offer, price or "buy now" only, assumes the viewer knows the product.

**B10 Funnel stage**
- Awareness: brand, story or entertainment; no offer, soft or no CTA.
- Consideration: features, proof, comparison, or a list price; "Learn more" type CTA, or only the platform's button. Ex: C1 "Starting at ₹39,900" + platform "Shop now" = Consideration.
- Action: an incentive (discount, code, deal, free gift), urgency, or a buy CTA on the creative itself. Ex: C2 "Upto 25% Off", code SAVE25 = Action.
- Full funnel: clearly carries all three in one creative (long YouTube ads).
- Not: a list price alone does not make it Action.

**B11 Appeal and emotion**: Rational = facts, specs, price lead. Choose an emotional option only when the emotion is clearly the driver (music, faces, story): Emotional – humour (a joke or comic situation), Emotional – aspiration (a better self or lifestyle), Emotional – FOMO (others have it, don't miss out), Emotional – relief (a pain or worry goes away), Emotional – belonging (family, friends, community), Emotional – surprise (an unexpected reveal), Emotional – fear (a risk or threat), Emotional – nostalgia (the past, childhood). "Mixed" when facts and one emotion share equal weight. Ex: C1 Mixed (status claim + product style); C2 Mixed (smiling baby + SPF numbers).

**B12 Occasion, season or trend**: Festival / holiday = names or shows a festival (Diwali lights, "Holi sale"); Sale event = a named sale (Big Billion Days, End of Season); Launch = "new", "introducing", "Gen 2" (Ex: C1); Season = summer, monsoon, winter cue; Pop-culture trend = a trending format, sound or meme; Evergreen = no time cue (Ex: C2). Not: a sun graphic alone is not a season (C2 = Evergreen).

**B13 Language and localisation**: from the on-creative text (`measures.json` text) and speech (transcript). English = all English (Ex: C1, C2); Hindi = Devanagari or Hindi speech only; Hinglish = Hindi words in Latin script, or Hindi and English mixed in one line; Regional language = another Indian language; Multi-language = separate lines or versions in two or more languages. Speech and text in different languages = Multi-language, unless one is a single word.

**B14 Offer and price**: Discount % = a percentage off (Ex: C2 "Upto 25% Off"); Flat price = a stated price or "₹X off"; Price anchoring (MRP struck) = the old price crossed out; Starting at = a lowest price (Ex: C1); EMI / pay later; BOGO / bundle = buy-x-get-y, combos, "any 2 for ₹699"; Free gift; Free shipping; Free trial / demo; No offer. A promo code goes with the offer it carries. List all present, joined by " + ".

**B15 Urgency**: Time-limited = a stated end ("today", "till Sunday", "sale is live" with an end date); Countdown = a visible timer; Limited stock = "few left", "while stocks last"; None (Ex: C1, C2). Not: "Shop now" alone is not urgency.

**B16 Social proof and trust** (list all present): Rating / stars, Review count, Testimonial (a user's words), Customer numbers ("10 lakh+ customers"), Expert / doctor, Celebrity, Creator / UGC (only when a person speaks as a user; a model in a scene is not proof), Awards / records, Press / Shark Tank, Certification (dermatologically tested, seals), Guarantee; None (Ex: C1, C2).

**B17 Differentiation**
- Explicit and credible: a specific reason this brand is different, backed by a fact (ingredient %, patent, test, comparison, a ranking such as "#1 selling"). Ex: C1.
- Implied: a claim of being different without a fact ("unlike others").
- Category-generic: says what any brand in the category could say. Ex: C2 (standard sunscreen benefits).

**B18 Claims and disclaimers**: Superlative claim = best / #1 / most (Ex: C1 "#1 selling", no source); Numeric claim = a figure as a claim (Ex: C2 "SPF 50", "120 Min"); Before / after = a shown change; Claim with asterisk and T&C; No claims. Note in the finding if T&C or asterisks are unreadable.

**B19 Talent / messenger**: who delivers the message. Celebrity; Founder; Creator / influencer (a known creator, or a creator partnership label); Expert (doctor, dermatologist, with credentials shown); Customer (a real user); Presenter / actor (speaks to camera, scripted); Model (on screen, does not speak; Ex: C2 mother + baby); Mascot; No person (Ex: C1). Measure: `faces` empty in every frame supports No person.

**B20 Advertiser and partners**: Brand page = run by the brand's own page (Ex: C2); Creator partnership = "Paid partnership" label or run from a creator's page with the brand; Retailer / marketplace = run by Amazon, Nykaa, Flipkart etc.; Co-brand = two brands' logos as partners (Ex: C1 Ray-Ban + Meta); Financing partner = a bank or EMI partner named.

**B21 Brand presence and cues** (list all present): Logo, Brand colours (only when the brand's own colours lead), Pack / product, Spoken name, Tagline, Mascot, Sonic logo. Ex: C1 "Logo; Pack / product"; C2 "Logo; Brand colours; Pack / product".

**B22 Availability / where to buy** (list all present): Own website (brand site link or platform CTA to it; Ex: C1, C2), Own app, Marketplace logos (Amazon, Flipkart, Nykaa shown or linked), Quick commerce (Blinkit, Zepto, Instamart), Offline store, Delivery promise ("delivery in 10 min"); Not shown.

**B23 CTA**: one option for the wording (Specific verb (Shop now, Book demo) / Generic (Learn more) / Soft / implied / None) + one for the form (In-image button / Text only / End card / Spoken / Platform button only). Ex: C1, C2 "Specific verb (Shop now) / Platform button only" — the platform button's wording counts when the creative has no CTA of its own.

**B24 Copy tone and length**: one tone (Casual / Formal / Humorous / Urgent / Calm / Energetic) + one length. Within limit = primary text up to about 125 characters and headline up to about 40, or no "…more" cut before the key message; Truncated = the key message is cut off. Ex: C1 "Casual / Within limit"; C2 "Calm / Within limit".

**B25 Hook in first 0–3 s**: Yes – visual = an image, text or action carries the hook in 0–3 s (Ex: C2 kinetic "SUN"); Yes – spoken = only the voice carries it; Yes – both; No = the first 3 s are logo, slow scene or blank. Measure: `text` in frames 0–3 s and transcript segments starting before 3 s.

**B26 Brand first appears at**: the first time the logo, brand name or spoken name is recognisable. Measure: the first frame whose `text` contains the brand name, or the transcript's first mention; check the logo by eye. Bands: Under 1 s (Ex: C2, watermark from 0 s) / 1–2 s / 2–5 s / 5–10 s / Later (after 10 s) / End card only (only in the last 3 s) / Not shown.

**B27 Product first appears at**: the first time the product is recognisable. Measure: `summary.first_pack_s` when the pack was matched; otherwise by eye from the frames. Bands: Under 2 s / 2–5 s (Ex: C2, tube at 2 s; a value on the boundary goes to the later band) / Later (after 5 s) / Never (no product).

**B28 Story structure**: the overall shape. Hook–context–demo–proof–CTA = at least four of SH1–SH7 in that order. Problem–agitate–solve = the problem is dwelt on before the product. Demo = mostly the product working. Testimonial = mostly a user speaking. Founder story. Skit / film = acted scenes with a plot. Listicle = numbered points. Unboxing. Before / after. Podcast / talk clip. Montage = a sequence of shots with no narrative (Ex: C2 cuts between graphic cards and footage).

**B29 CTA timing**: Early = before 25 % of the runtime; Middle = 25–75 %; End card = only in the last 3 s; Throughout = shown in at least two of these. When the only CTA is the platform button, say so in the finding and set `visible: false` (no CTA in the video itself).

## Style

**S01 Creative format**
- Catalogue packshot: product photo on a plain background with little or no design.
- Designed static: a laid-out graphic with text, badges, product. Ex: C1.
- Carousel: two or more swipeable cards.
- Cinemagraph: a still with one small looping movement.
- Static-to-motion: a static design with small animation.
- UGC: filmed like a user (phone camera, home setting, direct talk).
- Talking head: one person speaking to camera, produced (not phone-style).
- Film / skit: acted scenes with a story.
- Podcast clip.
- Animation / motion graphics: animated graphics carry the video, with or without footage. Ex: C2 (animation cards + B-roll).
- App montage: screen recordings of an app.

**S02 Visual style**: the dominant look. Minimal / clean = plenty of space, few elements, plain background (Ex: C1); Bold graphic = strong flat colours and big type (Ex: C2 yellow sunburst); Polished photo = professional photography and retouch; Illustrated; 3D / CGI; UGC / lo-fi = phone camera, natural light, little editing; Editorial = magazine-like composition and type; Meme / native = imitates platform-native formats; Collage; Infographic.

**S03 Production level**
- High (commercial): studio lighting, actors, multiple locations, professional grade and sound, or studio packshot / 3D render with retouch (Ex: C1).
- Medium: professional camera and edit, simple set, one location, or stock-style footage with motion graphics (Ex: C2).
- Low (native / UGC): phone footage, natural light, minimal edit.

**S04 Product imagery type**: Packshot on plain; 3D render; Lifestyle in use = the product used in a real scene; Hand-held = held by a hand or person, not in use; Serving / usage suggestion = shown as served, dispensed or with the result; Variant line-up = several variants together (Ex: C1 four colourways); Not shown. Join when two clearly appear (Ex: C2 "Lifestyle in use; Packshot").

**S05 Background and setting**: Plain / solid (Ex: C1 off-white); Gradient; Studio = a built set; Lifestyle scene = a styled real-looking room or place; Real-world / UGC = an actual home, street, phone-filmed place; Abstract / graphic = a designed graphic background (Ex: C2 yellow sunburst); Texture = a material surface (marble, foam, fabric). Measure: `colours` with one colour of 60 % or more supports Plain / solid.

**S06 Brand colour use**: Dominant = brand colour covers about 30 % or more of the frame or all key elements; Accent only = in logo, buttons or small elements (Ex: C1, C2); Absent; Off-brand = colours that clash with the brand's usual palette. Measure: `colours` shares.

**S07 Colour palette**: one mood option (Bright / saturated, Pastel / muted, Dark / moody, Monochrome, High contrast) + one count option (1–2 colours / 3–4 colours / 5+ colours). Measure: count the `colours` entries with a share of 0.10 or more, ignoring skin tones and plain black or white text. Ex: C1 "Pastel / muted / 3–4 colours"; C2 "Bright / saturated / 3–4 colours".

**S08 Contrast and legibility**
- High: all key text 4.5:1 or better and readable at phone size at a glance. Ex: C1 black on off-white.
- Medium: key text between 3:1 and 4.5:1, or one element weak. Ex: C2 white text on yellow.
- Low: key text under 3:1 (light on light, text over busy image).
- Measure: `text[].contrast` of the headline, offer and CTA lines (ignore pack print and tiny legal text).

**S09 Text vs image ratio**: the share of the frame covered by the boxes around overlaid text (not product packaging text). Measure: `text_area_pct` minus the pack's own printed text where the pack box overlaps; use the key frame for a photo and the typical frame for a video. No text = 0; Up to 10%; 10–20% (Ex: C2); 20–40% (Ex: C1); Over 40%.

**S10 Typography**: font count (1 font / 2 fonts / 3+ fonts) + hierarchy (Clear hierarchy / Weak / Flat) + size (Legible on mobile / Borderline / Too small). Ex: C1, C2 "2 fonts / Clear hierarchy / Legible on mobile". Measure: line heights in `text[].box` — key text under about 2.5 % of the frame height is Borderline, under 1.5 % Too small.

**S11 Graphic elements and badges** (list all present): NEW / launch tag; Price sticker (a designed sticker that is not the main offer, e.g. a "₹" burst beside a list price); Rating stars; Record / award badge; Icons (Ex: C1 sound-wave icon, "Hey Meta" pill); Emoji; None. Not: the main offer sticker counted in B14 is not repeated here (Ex: C2 "Upto 25% Off" sticker → None).

**S12 Focal point**: Single focal point = the eye goes to one element first (Ex: C1, C2); Two competing = two elements pull equally; None / cluttered = no clear first element.

**S13 Visual hierarchy**: the intended reading order is focal point → headline → proof → CTA. Intended order followed (Ex: C1, C2) / Partly (one step out of order) / Not followed.

**S14 Layout / composition**: Centred = main elements on the vertical centre line (Ex: C1, C2); Rule of thirds; Z-pattern; F-pattern; Split screen = two halves with different content; Close-up = the subject fills the frame; Wide = a full scene with small subjects.

**S15 Space use**: Generous = more than about 40 % empty space; Balanced = 20–40 % (Ex: C1, C2); Busy = under 20 %; Cluttered = elements overlap or touch.

**S16 Product / subject size in frame**: share of the frame taken by the product or main subject, whichever is larger, in the key frame. Measure: `pack.size_pct` for the product, `faces[].size_pct` × about 3 for a person framed head-and-shoulders. 60% or more (Ex: C1, frames about 65 %); 30–59% (Ex: C2, tube about 50 % of the height); 10–29%; Under 10%.

**S17 People**: presence (No people / Hands only / Face visible / Multiple people) + gaze (Gaze at camera / Gaze at product, only when a face is visible) + expression (Positive / Neutral / Negative). Measure: `faces` count per frame (`null` = judge by eye). Ex: C1 "No people"; C2 "Multiple people / Positive".

**S18 Logo placement and size**: position (Top-left / Top-centre / Top-right / Centre / Bottom / On product / Persistent watermark / Absent) + size (Dominant = wider than about 10 % of the frame / Moderate / Subtle = under about 5 %). Ex: C1 "Top-centre / Moderate"; C2 "Persistent watermark / Subtle".

**S19 Aspect ratio and native fit**: the ratio (1:1 / 4:5 / 9:16 / 16:9 / 1.91:1) + fit (Native = built for this placement / Cropped / letterboxed = bars or a cut-off subject). Measure: `size` in `measures.json`. Ex: C1, C2 "1:1 / Native".

**S20 Safe zones** (9:16): Fully clear = no key text, logo or CTA in the top 14 %, bottom 35 % or side 6 %; Minor overlap = a secondary element there; Key element covered = headline, logo, offer or CTA there. Measure: `safe_zone` lists every text line inside those margins; decide which are key. For 1:1, 4:5 and 16:9 judge against the platform's own buttons and captions (Ex: C1, C2 Fully clear).

**S21 Opening frame**: Strong = the first frame alone shows the hook, a face, the product or bold text (Ex: C2 bright sunburst + "SUN"); Weak = generic scene, logo only, or slow fade; Blank / dark = black, white or a plain colour. Measure: the 0 s frame's `text`, `faces`, `pack`.

**S22 Pacing / cuts**: from `cuts_s` (shot changes; animated transitions inside one designed card are not cuts). Fast cuts = a cut every 2 s or less on average, or 3+ shots in the first 5 s; Moderate = every 2–5 s; Slow build = longer than 5 s per shot; Single take = no cuts. Ex: C2 Moderate (cuts every 1–2 s with animation; check this against the rule in the calibration run).

**S23 Length**: from `duration_s`. Under 6 s / 6–15 s / 15–30 s (Ex: C2 15.5 s) / 30–60 s / Over 60 s. A boundary value goes to the upper band (15.0 s = 15–30 s).

**S24 Audio type**: from the transcript file (`segments`, the `audio` block and its `tags`) and visible cues (the platform's audio label in the creative's notes, a music sticker, captions of speech).
- No audio: `has_audio: false`.
- Speech (transcript segments or `tags.speech_s` of 2 s or more): the person on screen speaking to camera = Creator voice; two or more people talking = Dialogue; a voice with no speaker on screen = Voiceover.
- Music: `tags.music_s` or `tags.singing_s` of 2 s or more = Trending music when the audio label names a song (not "Original audio"), otherwise Background music.
- Sound effects: non-speech sound tied to on-screen actions (pump, splash, pop) while `tags.music_s` is under 2 s.
- Without `tags` (no tagger), `other_sound_s` of 2 s or more = Background music or Sound effects by the cues above; say that it was told apart by cues, not by listening.
- Join two with " + " (e.g. "Voiceover + Background music"). With no transcript file and no visible cue, `visible: false` (Ex: C2 was judged without sound: "Audio track present", which is not an option).

**S25 Sound-off readiness / captions**: Burned-in captions = speech captioned word for word; Kinetic text = animated key words carry the message (Ex: C2); Supers / lower thirds = static titles only; Partial = some speech uncaptioned; None = the message needs sound. Measure: compare the frames' `text` lines with the transcript segments at the same times.
