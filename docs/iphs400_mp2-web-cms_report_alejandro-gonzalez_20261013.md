# MP2 report: a CMS for La Once Mil

Alejandro González · IPHS 400 · Live site: https://algoal0507-crypto.github.io/iphs400-mp2-cms/ ·
Repo: https://github.com/algoal0507-crypto/iphs400-mp2-cms

## 1. What I built, and which grill decisions were mine

I built a CMS for the flagship La Once Mil taquería (Monte Everest 780, Lomas de
Chapultepec, Mexico City): a local admin console (FastAPI, Jinja, SQLite) and a public
site exported as plain HTML to GitHub Pages. All seven required capabilities work: login
with argon2 hashes, a Manager and an Editor role, News posts, Pages, a dashboard with a
filterable content list and Markdown preview, user management, and `cms publish` /
`cms deploy`. Nine tickets (#2 to #10) are closed, each with a code-review comment posted
before it closed. The suite has 361 passing tests, and I checked the 12 admin screenshots
(six screens at 1280 and 390 px) against a fresh clone.

Decisions that were mine (grill session 03, transcript line 186 unless noted):

- The name is **"La Once Mil"**, not the "Tacos La Oncemil" in my first brief. The
  earlier spelling was not an intentional change.
- It is a class prototype with two **fictional accounts**. The Editor drafts News but
  cannot publish, edit permanent pages, or manage users.
- A **real, dated news item** only if the Michelin Guide confirms it; anything invented
  is labelled demo content.
- The **Menu is one ordinary Markdown page**: verified dish names, no unverified prices.
- **Home carries all the visiting information**; there is no Visit Us page (line 212).
- **Photos:** I found three on the restaurant's Instagram and supplied them as
  screenshots. Their post URLs and permission are not recorded
  (`assets/images/CREDITS.md`), so I cannot claim they are cleared for reuse.

**What is not finished.** My WordPress field notes have 3 of the 5 required observations
(`notes/cms-field-notes.md` says so). The token budget plan came late: it was started on
2026-09-29 (commit `b12fd83`, actual usage only) and its estimates were written on
2026-10-12, after T01 to T03 and T08, not before the first ticket. There is no verified
phone number, so Home has no Call button.

## 2. Where the AI drifted or invented something, and what caught it

1. **Fixed pages (T02, #3).** The AI built Home, Menu and Our Story as three fixed pages
   that could not be created or deleted, following the glossary. The rubric says Pages
   have "the same fields and operations as posts". I asked it to check the manual and
   rubric against its work (session 05, line 339). It posted a "Scope correction: Pages
   CRUD" comment on #3 and wrote a migration (commit `bc48750`). My prompt plus the
   rubric text caught it, not a test.
2. **Menu text the sources did not support (T09, #10).** The first rewrite said "Grilled
   beef taco", "ask your server" and "Our signature dish"; `notes/restaurant-research.md`
   says none of that. The independent spec review compared each line with the research
   and flagged them.
3. **"First, and so far only."** Our Story claimed the only taquería with a Michelin star.
   That came from my own client brief, not the research table, which says never "the
   first taquería ever". The same review flagged it and I had the sentence replaced.
4. **A "verified" claim that was wrong.** The AI reported the live screenshots as checked,
   but the headless browser had served a cached page, so the Our Story image still showed
   the old sentence. I noticed only when I opened the image. The correction is a comment
   on #10 (2026-10-13).
## 3. Skills, prompts, and resources

- **Skills:** `/grill-with-docs` to get decisions out of me one question at a time and
  into `CONTEXT.md`; `/to-spec` and `/to-tickets` for one spec and nine tickets;
  `/implement` with `/tdd` to build each ticket test-first; `/code-review` in a fresh
  sub-agent so the author never reviewed its own code; gstack `browse` for the
  screenshot and phone-width checks.
- **Prompts:** two are quoted in the README's AI Use Statement. A third (session 07,
  line 130) set a rule for the fixes: "Do not weaken the checker to make it pass."
- **Resources:** the Michelin Guide page and article, Wikipedia and the restaurant's
  Instagram bio (all in `notes/restaurant-research.md`), the course manual and rubric,
  and WordPress Playground (only partly done).
- **Other AI help:** ChatGPT helped me understand the assignment, prepare prompts,
  troubleshoot, review content, and draft this report, which I edited. The repo does
  not record the model or dates.
- **Models:** `claude-sonnet-5` (sessions 01 to 06), `claude-sonnet-5-5` (07 on), effort
  `medium` in the ledger.

## 4. What next, and what the budget data said

**Budget** (`notes/usage-ledger.csv` through 2026-10-14T13:51Z, run through
`scripts/usage_report.py`; later rows are `submission-prep` and add 0%): about **100
percentage points** of 5-hour windows, **14%** of the weekly cap, and **1.3% of the
weekly cap per ticket** over 9 tickets. I forecast T04 to T07 at about 45% of a window.
By phase label they used 34% (T04 5, T05 2, T06 5, T07 22), but the T07 label is
inflated: the phase file stayed on T07 after that ticket closed, so later README,
screenshot and photo work was logged there. Counted only to its close, T07 is about 16%.
I did not forecast T09 (visual design) at all; it took 16%. The plan was late, so it is a record, not a forecast I made
in advance.

**If I started again,** I would be more specific about the idea I wanted from the
beginning. I would use more images showing the food and the restaurant to promote the
place.

**Next,** I would add verified prices for every dish. I could not find reliable prices
while building the site. For a restaurant selling expensive tacos, visitors should know
what each dish costs. In general, I think the website looks good. After that: real,
cleared photographs; a verified phone number for a Call button; reactivating a
deactivated user; success messages after every save; a styled "Forbidden" page for
Editors; and server-side session invalidation. A cookie copied before logout still
works for 8 hours: the T07 review noted it, and on 2026-10-15 a replay on a clean clone
still got HTTP 200 from `/admin`.
