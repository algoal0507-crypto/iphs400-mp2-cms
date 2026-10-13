# La Once Mil — a small CMS (IPHS 400 Mini-Project #2)

A web CMS for **La Once Mil**, the Michelin-starred taquería at Monte Everest 780,
Lomas de Chapultepec, Mexico City. A local admin console (FastAPI, Jinja, SQLite)
writes the content. `cms publish` turns the published content into plain HTML in
`site/`, and `cms deploy` pushes that to GitHub Pages. The admin console is meant to
run on one laptop and is never put on the internet (ADR-001).

This is a student prototype. It is not affiliated with or endorsed by La Once Mil,
and its demo accounts are fictional.

## Live URL

**https://algoal0507-crypto.github.io/iphs400-mp2-cms/**

The public site only changes after `cms publish` and `cms deploy` (see below).
Publishing a post in the admin console does not by itself update this URL.

## Run locally

Needs `git` and [`uv`](https://docs.astral.sh/uv/) (it installs the dependencies and a matching Python).
These exact steps were run in a fresh clone on 2026-10-13.

```bash
git clone https://github.com/algoal0507-crypto/iphs400-mp2-cms.git
cd iphs400-mp2-cms
uv sync
cp .env.example .env
```

`uv run` does **not** read `.env` by itself, so every command below passes
`--env-file .env`. Edit `.env` first if you want other passwords; the values in
`.env.example` are public placeholders. A value with spaces (the site title) must stay
in quotes or the file cannot be read.

**Seed the demo data** (two users, three pages, three News posts; safe to run twice):

```bash
uv run --env-file .env python scripts/seed_demo.py
```

**Start the admin console:**

```bash
uv run --env-file .env cms serve
```

Open <http://localhost:8000/login>. Stop it with `Ctrl+C`.

| Demo account | Email | Password (from `.env`) | Role |
|---|---|---|---|
| Demo Manager | `manager@laoncemil.test` | `CMS_ADMIN_PASSWORD` (`change-me-admin` in `.env.example`) | admin: everything, including publishing, pages, and users |
| Demo Editor | `editor@laoncemil.test` | `CMS_EDITOR_PASSWORD` (`change-me-editor` in `.env.example`) | editor: News drafts only |

**Run the tests:**

```bash
uv run pytest
```

## Publish and deploy

```bash
uv run --env-file .env cms publish     # writes site/ from the published content
python3 -m http.server -d site 8001    # optional: preview at http://localhost:8001
uv run --env-file .env cms deploy      # pushes site/ to the gh-pages branch
```

`cms publish` writes only published pages and posts, with relative links only, and
deletes and recreates `site/` each time. `cms deploy` needs push access to the repo.
The first time, turn Pages on in GitHub: **Settings → Pages → Deploy from a branch →
`gh-pages` / root**. Then wait a few minutes for the live URL to update.

## Where things are

```text
app/            FastAPI app: auth, routes (pages, posts, users, admin), publish, db
templates/      Jinja templates and the one shared stylesheet (style.css)
scripts/        seed_demo.py, check_submission.py, usage_report.py, make_web_images.sh
assets/images/  the three site photos (originals, untouched), CREDITS.md (sources and credits), web/ (the cropped copies that `cms publish` ships)
tests/          the test suite (route sweep for access control and CSRF in test_access_control.py)
CONTEXT.md      the project glossary;  docs/adr/  decisions that are hard to undo
notes/          client brief, restaurant research, field notes, token budget and usage ledger
docs/           handoffs, transcripts, compaction log, screenshots, manual and rubric
```

Process evidence for the AI-assisted workflow lives in GitHub Issues (one `spec` issue,
nine `ticket` issues, each with a code-review comment before it closed) and in `docs/`.

## Generative AI Use Statement

> **DRAFT, written 2026-10-13 from the saved transcripts, the usage ledger, and the
> GitHub issue record. Awaiting the author's review. Anything not recorded in the repo
> is marked "unknown" rather than guessed.**

**Models and tools.**

- **Claude Code** (Anthropic) did the planning and the coding. The saved transcripts
  record the model as `claude-sonnet-5` for sessions 01–06 and `claude-sonnet-5-5` for
  sessions 07–09; session 10 (not yet saved) is logged as Sonnet 5.5 in the usage ledger.
  The ledger records effort as `medium` for every row. Whether other models or effort
  levels were used for sub-agents: **unknown, not recorded**.
- **ChatGPT** (OpenAI) was also used by the author. The author reports using it to help
  write and tidy the longer prompts that were pasted into Claude Code (several user
  prompts in the transcripts arrive as pasted blocks). **Model, version, dates, and
  which prompts it helped with: unknown, not recorded in this repo; no ChatGPT
  conversation is saved here.** [AUTHOR TO CONFIRM OR CORRECT]
- **Skills** (mattpocock/skills, run inside Claude Code): `/setup-matt-pocock-skills`,
  `/ask-matt`, `/wait-what`, `/grill-with-docs`, `/to-spec`, `/to-tickets`,
  `/implement`, `/tdd`, `/code-review`. Also the `/learn` skill, the built-in `/model` and `/clear`
  commands, and a headless browser (gstack `browse`) for the final design checks.

**Two prompts that were really sent** (quoted from the saved transcripts):

1. Session 03, starting the grill (transcript line 160):

   > /grill-with-docs I am building the Tacos La Oncemil Mexico City CMS for IPHS 400 Mini-Project 2. Read notes/client-brief.md, notes/restaurant-research.md, CONTEXT.md, and the manual’s seven required capabilities.
   >
   > Use my existing decisions: only the manager publishes, the homepage prioritizes visiting information, and customers contact the restaurant by phone.
   >
   > Keep the project small and achievable. Ask one short question at a time, only about decisions not already answered. Explain technical choices in plain English and recommend a simple option. Do not invent missing field notes or mark unfinished requirements complete.

2. Session 05, during T02 (transcript line 339):

   > Before finishing, check the manual and rubric’s Pages CRUD requirement against this implementation. The three agreed restaurant pages are the initial content; do not assume that removes required create/delete functionality. Resolve any mismatch, test the review fixes, and record the results on issue #3 before committing and pushing.

**One real model failure.** During T02 (issue #3) the model built Home, Menu, and Our
Story as three fixed pages that could not be created or deleted, following an earlier
decision in the glossary and spec. That contradicts the rubric's "Pages: same fields and
operations as posts". The second prompt above made the model compare the code with the
manual and rubric; it then posted a "Scope correction: Pages CRUD" comment on issue #3
(2026-09-29), added a migration that removes the old fixed-slug restriction from
existing databases, and corrected `CONTEXT.md` and the client brief. A later design pass
caught more: see issue #10 for dish descriptions the research notes did not support and
a "first — and so far only" claim that appeared in no source.

**Backends used.**

| Provider | Models | Used for | Evidence |
|---|---|---|---|
| Anthropic (Claude Code, Pro plan) | `claude-sonnet-5`, `claude-sonnet-5-5` | all planning, coding, and code review | `provider` column is `anthropic` on every ledger row; no `Backend:` trailer on any commit |
| OpenAI ChatGPT | unknown | prompt drafting only; not a Claude Code backend | author-reported; not recorded in the repo |

No backup provider was used as a Claude Code backend.
