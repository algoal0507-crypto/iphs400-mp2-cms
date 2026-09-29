# Handoff — pause point, 2026-09-29 (Stage 1 wrap-up)

Follows `2026-09-29-T03-handoff.md`. **`mp2-mvp` has NOT been created. Do not create it
until every Stage 1 item below is complete and checked.**

## Completed today

- **First live deploy (closes T03's deferred criterion).** Seeded the empty Home,
  Menu, Our Story pages (they were empty drafts in `cms.db`), ran `cms publish` and
  `cms deploy`. Live and verified over HTTPS:
  https://algoal0507-crypto.github.io/iphs400-mp2-cms/ (index, menu, our-story,
  style.css all 200).
- **Site title** set to "La Once Mil" (`CMS_SITE_TITLE`, quoted in the untracked
  `.env`; the malformed line is fixed). The app does not load `.env` itself: run the
  CLI as `uv run --env-file .env cms publish` / `cms deploy`.
- **Fake phone removed** (`tel:+00000000000` "Call us") from the seed and the DB row;
  no verified number exists in the research sources. `CONTEXT.md` records the Call
  button as pending. Photo placeholders were kept, as agreed.
- **T08 / issue #9 (closed, commit `e41a99a`):** admin pages now load their
  stylesheet and header link from any route depth (`app/urls.py`,
  `templates/admin/base_admin.html`, `/admin/style.css`). Also made the admin `href`s
  the checker flagged relative. Form `action=` attributes were deliberately left
  alone. TDD, `/code-review` findings and resolutions posted on #9 and #4.
  79 tests pass.
- **Process evidence committed (`2df7145`):** transcripts 01–06 renamed from
  `your-name` to `alejandro-gonzalez` (contents byte-identical), usage ledger,
  `docs/process/compaction-log.md` (states from evidence that no compaction events
  exist), `.gitignore` (`.gstack/`).
- `CMS_STUDENT=Alejandro-Gonzalez` set in `.env`. Filenames are lowercase because the
  checker's regexes require lowercase.
- Secrets review: no real secrets in any committed file. `.env` is untracked and
  still holds the template default values (`change-me-…`).

## Stage 1 status

Checker (`uv run python scripts/check_submission.py --stage 1`): 11 of 12 pass; the
only failure is the missing tag, which is intentional. Passing the checker is **not**
enough. Still incomplete against the rubric/manual:

1. **S1.1 field notes — UNFINISHED (3 of 5 observations).** See below.
2. **Token budget plan — UNFINISHED.** `notes/token-budget-plan.md` holds real ledger
   data and is explicitly labelled as written on 2026-09-29, after T01–T03 (not
   backdated). All model/effort/estimate cells and the three written answers are
   marked UNFINISHED and need Alejandro's decisions.
3. **S1.3 grill transcript — needs a decision.** Transcript 03 contains a
   `mattpocock-skills:grilling` invocation plus `to-spec` and `to-tickets`. No saved
   transcript contains the literal `/grill-with-docs` command, and none has a
   `/research` session. Do not claim otherwise; consider telling the instructor.
4. **Transcript 07 (this session)** is saved by the `SessionEnd` hook only when the
   session actually ends, so it is **not yet in the repo**. After closing, run
   `git status`; a new `..._07_alejandro-gonzalez_20260929.md` should appear
   untracked. Check it for secrets, then commit it.
5. Re-check S1.4–S1.7 once more just before tagging (spec issue #1, tickets #2–#8
   plus #9, T01–T03 closed with review comments, Pages live with no absolute paths).
6. Then, and only then: `git tag mp2-mvp && git push --tags`, and the email.

## WordPress field notes — exactly where we paused

`notes/cms-field-notes.md` records only what Alejandro actually did and said:

- Done and recorded (3): (1) draft post "La Oncemil-Example" invisible on the public
  blog; (2) after publishing, its title and content appear; (3) About page appears in
  the navigation menu while the post appears in the blog.
- **We paused on Question 4, unanswered:** open Settings → Permalinks and describe how
  the post URL is built and which part comes from the title (the slug).
- Still to do in WordPress Playground, then write what was seen: **5)** create a user
  with the Editor role, log in as them and try to open Users (write down exactly what
  happens); **6)** find where Posts → All Posts filters by status.
- Two more observations bring it to five. Do not invent any; ask one question at a
  time.

## Open items / not started

- T04 (#5 News posts) is the next ticket but **was not started**.
- Admin form `action="/..."` attributes remain root-absolute by decision.
- No public contact method exists until a verified phone number is supplied (client
  brief says phone is the only contact channel).
- The demo passwords in `.env` are the template defaults; fine locally, change them
  if the admin console ever leaves this machine (it must not).
