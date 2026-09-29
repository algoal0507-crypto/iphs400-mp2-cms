# Handoff — end of session, 2026-09-29

## Finished this session

- **T03: Publish pipeline** (issue #4) — implemented, code-reviewed, committed,
  pushed, and closed.
  - `render_site()` (`app/publish.py`) now exports real published Pages from the
    database instead of the old hard-coded placeholder: `home` → `index.html`,
    every other published slug → `<slug>.html`, each page carrying a relative
    nav to every other published page. Draft pages are never written.
  - New `templates/public/page.html`; `templates/base.html` gained an optional
    nav block.
  - `app/db.py`: reserved the `"index"` slug (`_RESERVED_SLUGS`) — a page with
    that slug would silently overwrite Home's exported `index.html`. Found by
    `/code-review`, fixed, regression-tested.
  - `tests/test_publish.py` (new): draft exclusion, relative paths, nav
    reachability, unpublish-then-republish, Markdown sanitization, freely
    creatable extra pages, the reserved-slug fix, and the draft-Home nav
    fallback fix.
  - Full suite: 56 passed.
  - Commit `a4bbf63` on `main`, pushed to `origin/main`. Message starts `T03:`,
    ends `Closes #4`. Code-review findings and their resolution posted as a
    comment on issue #4 before committing, per this repo's CLAUDE.md.

## Not done — explicitly out of scope tonight

- **`uv run cms deploy` was not run.** The code path exists (from T00's
  `cli.py`, unchanged this session) and is exercised by the new tests at the
  file level, but nobody has pushed `site/` to the real `gh-pages` branch or
  confirmed the Pages URL serves Home over HTTPS yet. That's a real, visible
  push to a shared branch — left for you to trigger explicitly. When ready:
  `uv run cms publish` then `uv run cms deploy`, then verify the Pages URL in
  Settings → Pages (see `cli.py`'s printed instructions).
- No new ticket was started.

## Uncommitted / untracked at end of session

- `.gitignore` — modified (adds `.gstack/`), **predates this session**, not
  touched by T03 work. Still sitting uncommitted; your call whether to keep it.
- `notes/usage-ledger.csv` — untracked, predates this session.
- `docs/transcripts/` — untracked. Session transcripts 01–05 are already
  there from earlier sessions; this session's transcript will be added
  automatically as `..._06_...md` by the `SessionEnd` hook
  (`.claude/hooks/save_transcript.py`) once this session actually ends — that
  happens outside my control, so it won't exist until you close out. None of
  the transcript files are committed to git yet.

None of the above are related to T03 and none were touched or committed this
session, to keep the ticket-closing commit clean.

## Next steps (do not start yet, per tonight's instruction)

1. **T04: News posts** (issue #5, "News posts with Editor drafts and Manager
   publish") is now unblocked — its only blocker, #4, is closed. It's the
   natural next ticket.
2. Before starting T04: read issue #5, the spec (#1), and `CONTEXT.md`, per
   this repo's normal workflow (see CLAUDE.md).
3. Whenever you're ready for the first live deploy: run `uv run cms publish`
   then `uv run cms deploy`, and confirm the GitHub Pages URL serves Home over
   HTTPS (T03's last acceptance criterion — deferred, not forgotten).
4. Consider whether to commit `docs/transcripts/` (including tonight's,
   once it lands) and `notes/usage-ledger.csv`, and whether to keep the
   pending `.gitignore` change — all three predate this session and are still
   sitting uncommitted.
