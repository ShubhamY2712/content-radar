# Content Radar · Agent 1 — Content Benchmark Research Agent

Give it a brand and a product. It finds the competitors, collects their strongest recent ads and organic posts (plus the brand's own as a baseline), analyses every creative on 54 creative benchmark parameters (story beat × layer × assets), compares the brand with the market, and writes a benchmark report with content recommendations, which it reviews before calling the run done.

The agent is a folder, not an app: Markdown instructions, a skill registry, knowledge files and small read-only Python tools. Any AI that can read files and browse the web can run it (OpenCode, Claude Code, Gemini CLI, ChatGPT / Gemini apps). The AI you run it in does the thinking, so no model API key is needed.

An overview of the design for readers is in [`docs/Content_Radar_Agent1.html`](docs/Content_Radar_Agent1.html) (open in a browser), with the run flow in [`docs/Content_Radar_Run_Flow.html`](docs/Content_Radar_Run_Flow.html). What it does not do yet is listed in [`docs/KNOWN_LIMITATIONS.md`](docs/KNOWN_LIMITATIONS.md).

## How a run works

| # | Step (skill) | Output | Done by |
|---|---|---|---|
| 1 | brief-intake | `brief.json` | main agent |
| 2 | competitor-discovery | `competitors.json` (you approve the list) | main agent |
| 3 | creative-collection | `creatives.json`, `media/` with frames, transcripts and measures | collectors, one per brand, in parallel |
| 4 | creative-analysis | `analysis/<id>.json`, `checks/<id>.json` | 2 analysts (Business, Style) + 1 independent checker per creative |
| 5 | benchmark-synthesis | `stats.json`, `synthesis.json` | main agent |
| 6 | content-recommendation | `recommendations.json`, `report.md`, `creative_notes.md` | main agent |
| 7 | report-review | `review.json` | main agent |

Everything a run writes goes to `runs/<brand>-<date>/`, so a stopped run resumes where it left off. Once the review passes, the downloaded videos are deleted to save space (about 1 GB per run); frames, measures, transcripts and the report stay, about 100 MB per run. The report is `runs/<brand>-<date>/report.md` (summary: findings, competitors, brand vs market, patterns, ideas); every creative's 54-parameter notes are in `creative_notes.md` next to it.

Accuracy features: creatives are picked for the exact product first; on-screen text, safe zones, faces, colours, product sightings, cuts and sound are measured by code rather than guessed; every finding cites its evidence; a checker re-reads each creative without seeing the analysis and every disagreement is resolved; all counts in the report come from code; `evaluation/compare.py` scores the agent against manual analyses.

## Folder structure

```
AGENTS.md              the agent: role, setup and capability checks, 7-step run, team, rules (read by every AI)
CLAUDE.md, GEMINI.md   pointers to AGENTS.md for Claude Code and Gemini CLI
opencode.jsonc         OpenCode: four isolated Playwright browsers (browser1-browser4)
requirements.txt       Python packages for the tools
.env.example           API keys template (copied to .env by the setup check; never commit .env)
auth.json              your saved Instagram / Facebook logins (made once, never committed)
agents/                worker briefs: collector.md, analyst.md, checker.md
.opencode/agents/      the three workers registered as OpenCode sub-agents
setup/claude-code/     the same sub-agents, browsers and tool permissions for Claude Code (copied by the setup check)
skills/                7 skills (SKILL.md + skill.json each) and registry.json
knowledge/             54 parameters, story beats, layers, assets, option guide (codebook), 2 worked examples
schemas/               JSON schema for every file a run writes
templates/report.md    report layout
tools/                 Python tools (see "Tools"); models are downloaded into tools/models/ on first use
evaluation/            10 manually analysed reference creatives, test briefs, compare.py
runs/                  run outputs, one folder per run (not committed)
docs/                  overview page and run-flow diagram for readers
```

## Before your first run

Run the setup check in this folder. It lists what is ready and what is missing, says what each gap costs the run, and fixes what it can by itself:

```
python tools/setup_check.py --fix
```

The agent runs the same check at the start of every run and does not start collecting until it prints `READY`.

| Item | Needed? | If missing | How to set it up |
|---|---|---|---|
| Python 3.10+ | Required | Tools do not run | python.org |
| Python packages | Required | No frames, measures or YouTube lists | Fixed by `--fix` (`pip install -r requirements.txt`) |
| ffmpeg + ffprobe | Required | No frames, cut times or sound facts | Windows: `winget install ffmpeg`, then open a new terminal |
| Node.js 18+ and Google Chrome | Required | Browsers cannot start | nodejs.org, google.com/chrome |
| Instagram login | Required | Instagram posts and Reels are lost | See "Saved logins" below |
| Facebook login | Strongly recommended | Facebook pages, and Meta Ad Library when it asks for a login, are lost | See "Saved logins" below |
| Claude Code team, browsers and permissions | Required in Claude Code | No workers or browsers, or the run stops at every tool to ask for approval | Fixed by `--fix` (copies `setup/claude-code` to `.claude/agents`, `.claude/settings.json` and `.mcp.json`; the permissions allow only the agent's tools, browsers, web reading and writing inside `runs/`) |
| faster-whisper | Recommended | Spoken words of Instagram, Facebook and ad videos are not transcribed | Fixed by `--fix` (large download) |
| Speech model (Whisper small, about 0.5 GB) | Recommended | Downloaded in the middle of the run instead | Fixed by `--fix` |
| yt-dlp up to date | Recommended | Video downloads fail when sites change | Fixed by `--fix` (updates a yt-dlp older than 45 days) |
| Face, sound and Hindi OCR models | Recommended | Faces, music vs speech and Hindi text are judged by eye | Fixed by `--fix` (downloaded into `tools/models/`) |
| Free disk space (3 GB+) | Required | Videos and frames may not save | Free some space |
| Internet: YouTube, Instagram, Ad Library, Google Ads | Required | Those sources are lost | Check the connection, VPN or firewall |
| `YOUTUBE_API_KEY` | Optional | YouTube lists come from yt-dlp (works, slower) | Google Cloud Console → enable "YouTube Data API v3" → API key → put it in `.env` |
| `IG_USER_ID`, `IG_ACCESS_TOKEN` | Optional | Organic posts are read through the logged-in browser | Instagram Business Discovery: a professional Instagram account linked to a Facebook Page and a Meta app token, in `.env` |

### Saved logins (`auth.json`)

Instagram, Facebook pages and often the Meta Ad Library show a login wall to a fresh browser. Save a login once, using a spare account, not your personal one (automated browsing can get an account flagged):

```
npx -y playwright@latest codegen --channel chrome --save-storage=auth.json https://www.instagram.com
```

(Windows PowerShell: use `npx.cmd` instead of `npx`.) In the window that opens, log in to Instagram, then open facebook.com in the same window and log in there too, then close the window. Run `python tools/setup_check.py --fix` again: it points all four browsers at `auth.json`, then restart the AI tool. Logins expire after some weeks; the check and the agent tell you when to save them again.

During a run keep the computer awake and plugged in. If a run stops (sleep, usage limit, network), say "Resume runs/<run folder>": it continues from the last finished step.

`.env` and `auth.json` hold your keys and logins: never share them or commit them (both are in `.gitignore`). The agent never types a password; it only uses the saved logins.

The Meta Ad Library is read on its website: the official API does not return commercial ads shown only in India.

## Run it

Ask: **"Run the content benchmark for <brand>, <product>."** Optional: competitors, market, platforms, time window, creatives per competitor, brand creatives.

| AI | How |
|---|---|
| OpenCode | Run `opencode` in this folder. It reads `AGENTS.md`, the skills, the sub-agents in `.opencode/agents/` and the browsers in `opencode.jsonc`. |
| Claude Code / Claude desktop | Open this folder (the setup check copies the team and browser files once). |
| Gemini CLI | Run `gemini` in this folder. |
| ChatGPT / Gemini app | Upload `AGENTS.md`, `agents/`, `skills/` and `knowledge/` to a Project, Custom GPT or Gem with the instruction "Follow AGENTS.md". Without Python the agent does the tools' work by hand and says what it could not measure. |

The agent first runs the setup check, then checks what the AI can do (web, images, files, Python, sub-agents, browsers) and adapts. It stops once for your approval of the competitor list and finishes only after review has passed.

## Team: main agent and workers

The main agent runs steps 1, 2 and 5–7 and hands the slow steps to workers, up to 4 at a time:

- **Collectors** (step 3): one per brand, each with its own browser, writing `parts/C<n>.json` and its own media; `tools/merge_parts.py` joins the parts.
- **Analysts** (step 4): one for the 29 Business and one for the 25 Style parameters per creative, evidence first, measured facts first.
- **Checker** (step 4): an independent second reading per creative; `tools/check_compare.py` lists disagreements and an analyst resolves each one.

Each worker writes only its own files and checks them with `tools/validate.py`. Without sub-agents (ChatGPT, Gemini apps) the main agent does the same jobs one after another; with a single browser, collectors take turns.

## Tools

```
python tools/setup_check.py [--fix]               what this machine is missing before a run; fixes what it can
python tools/registry.py list | search <text> | show <name> | check | build    skill registry
python tools/validate.py runs/<run> [<file>]       steps done, errors, where to resume; or one worker's file
python tools/frames.py <link or video> runs/<run>/media/<id>     download, frames, cut times
python tools/transcript.py <video or YouTube link> <out.json>     words, sound facts, speech/music tags
python tools/measure.py runs/<run>/media/<id> --pack <pack photo> --hindi   text, safe zones, faces, colours, pack
python tools/youtube.py videos --channel <channel> --days 90       recent videos and Shorts with views
python tools/merge_parts.py runs/<run> [--analysis <id>]           join workers' parts
python tools/check_compare.py runs/<run> <id>      analysis vs checker
python tools/stats.py runs/<run>                   option counts for the synthesis
python tools/render_report.py runs/<run>           rebuild report.md and creative_notes.md
python tools/review.py runs/<run> --links          cross-file checks and link check
python tools/clean_media.py runs/<run>             after review passes: delete downloaded videos, keep frames and evidence
```

## Accuracy check

```
python evaluation/compare.py <folder of "Creative N.json"> --report accuracy.md
```

Scores the agent's analyses of the reference creatives in `evaluation/reference_creatives.json` against the manual analyses: exact and partial option match, kappa (agreement above guessing) and layer overlap, with the weakest parameters and every disagreement. Creatives 1–2 are the worked examples, so test on Creatives 3–10, fix what it shows in `knowledge/option_guide.md`, and test again.

## Knowledge source

`knowledge/` and `evaluation/reference_creatives.json` are exported read-only from the Creative Benchmark Parameters workbook. When the workbook changes, export again instead of editing the JSON:

```
python tools/export_knowledge.py "<path to Creative_Benchmark_Parameters.xlsx>" knowledge
python tools/export_reference.py "<path to Creative_Benchmark_Parameters.xlsx>" evaluation/reference_creatives.json
python tools/registry.py build
```

## Data and sharing
- The agent is read-only on the web: it never signs in, posts, likes, follows or buys.

## License

All rights reserved. See [`LICENSE`](LICENSE).
