# Token budget plan

(Part 5.4 of the manual.)

> **STATUS: DRAFT, started 2026-09-29 (actuals only, commit `b12fd83`), estimates written 2026-10-12, updated 2026-10-13 with actual numbers for T01-T09
> (new section below), still awaiting Alejandro's review.**
> **This plan was written AFTER T01–T03 and T08 were built, not before the first
> ticket as the manual asks.** It is not a pre-implementation plan and must not be
> presented as one. "Actual" figures come from `notes/usage-ledger.csv`; everything
> labelled **estimate** is a forecast made on 2026-10-12. Cells marked
> **unconfirmed** have not been verified in this account.

## Actual so far (from `notes/usage-ledger.csv`, via `scripts/usage_report.py`)

Meters are % of a 5-hour window / % of the weekly cap. Every ledger row records
provider Anthropic, effort medium; model Sonnet 5 early on, Sonnet 5.5 from late T03.

| Work | Session (transcript) | 5-hour meter, first → last reading in session | Weekly meter |
|---|---|---|---|
| Setup, grill, spec, tickets (rows labelled `unlabelled`) | 01–03 | 1% → 14% | 2% → 4% |
| T01 (login) | 04 | 17% → 20% | 4% |
| T02 (permanent pages) | 05 | 26% → 36% | 5% → 7% |
| T03 (publish pipeline) | 06 | 39% → 41% | 7% |
| Deploy, checker fixes, T08 | 07 | 1% → 15% (meter reset mid-session) | 8% → 9% |
| Plan drafting, 2026-10-12 | 08 (this one) | 6% (fresh window) | 1% (new week) |

Report-script totals (rough, because meters also rose *between* sessions and the
script charges those rises to the next row's label): unlabelled planning 13%,
T01 3%, T02 10%, T03 21%, T08 3% of a 5-hour window; **average 1.2% of the weekly
cap per ticket** over 4 tickets.

Caveats: phase labels lag (a session-05 row labelled T03 sits before its T02 rows),
so per-ticket figures are approximate, and `/implement`, `/tdd` and `/code-review`
were not metered separately. The ledger shows only one model and effort for all
work, so the per-stage split below is a plan, not a measurement.

## Update 2026-10-13: actual usage for all nine tickets (from `notes/usage-ledger.csv`)

All nine tickets are now closed. Numbers below are from the ledger rows up to
2026-10-13T18:03Z; the ledger keeps growing while a session is open, so the last
session's figures are not final. Nothing here changes the earlier fact that this plan
was first written on 2026-10-12, after T01-T03 and T08, not before the first ticket.

| Ledger session | Transcript | Work (phase labels in the rows) | 5-hour meter, first to last reading | Weekly meter | Peak context |
|---|---|---|---|---|---|
| `a2316d11`, `15388d4a`, `6f927223` | 01-03 | setup, grill, spec, tickets (`unlabelled`) | 1% to 14% | 2% to 4% | 19% |
| `6d5bfbb1` | 04 | T01 | 17% to 20% | 4% | 12% |
| `2fa5b7df` | 05 | T02 (one row labelled T03) | 23% to 36% | 5% to 7% | 23% |
| `0f3aface` | 06 | T03 | 39% to 41% | 7% | 13% |
| `a5df01a3` | 07 | T03 deploy, T08 | 1% to 8% (meter reset) | 8% to 9% | 15% |
| `68fe07ff` | 08 | T08, T04, budget drafting | 5% to 11% | 1% (new week) | 14% |
| `b36ba01a` | 09 | T05, T06 start | 12% to 2% (meter reset) | 2% | 13% |
| `17a751d5` | none saved yet | T06, T07, T09 | 4% to 39% | 2% to 7% | 45% |

`scripts/usage_report.py` (it sums only the increases and ignores resets), run on
those rows, gives these totals per phase label:

| Phase label | Rows | 5-hour windows spent | Weekly cap spent |
|---|---|---|---|
| unlabelled (setup, grill, spec, tickets) | 20 | 13% | 2% |
| T01 | 3 | 3% | 0% |
| T02 | 4 | 10% | 2% |
| T03 | 8 | 21% | 3% |
| T04 | 3 | 5% | 0% |
| T05 | 7 | 2% | 0% |
| T06 | 5 | 5% | 1% |
| T07 | 5 | 9% | 1% |
| T08 | 10 | 3% | 0% |
| T09 | 14 | 16% | 2% |

The report's line: 9 tickets done, **average weekly cost per ticket 1.0%**. Adding the
per-label figures gives about 87 percentage points of 5-hour windows and about 11% of
the weekly cap in total, spread over two weeks (the weekly meter reset on 2026-10-12).

Caveats, same as before and still true. The labels lag the work (one session-05 row is
labelled T03 among T02 rows), the script charges meter rises that happened between
sessions to the next row's label, `/implement`, `/tdd` and `/code-review` were never
metered separately, sub-agent usage is not separated out, and every row records the
same effort (`medium`) and provider (`anthropic`). Models: `Sonnet 5` in sessions
01-06, `Sonnet 5.5` from session 07 on.

## Model / effort / estimate table

| Stage | Model | Effort | Estimate (% of a 5-hour window) |
|---|---|---|---|
| `/research`, quick lookups | Sonnet 5.5 (Haiku availability **unconfirmed**; `/model` output did not list models) | low (**unconfirmed**) | estimate: about 1–2% per lookup; no `/research` session exists yet |
| `/grill-with-docs`, `/to-spec`, `/to-tickets` | Sonnet 5 (actual, already done) | medium (actual, from ledger) | about 13% (actual) |
| `/implement` + `/tdd` (per ticket) | Sonnet 5.5 | medium (ledger shows medium) | estimate: about 8% per ticket (actual so far 3–21%, noisy) |
| `/code-review` (per ticket) | Sonnet 5.5 | high (**unconfirmed**; no review has been metered separately) | estimate: about 3% per ticket |

## Written answers (all estimates, made 2026-10-12)

- **How many 5-hour windows will the remaining tickets (T04–T07) take?**
  Estimate: about 4 tickets × (8% + 3%) ≈ 45% of one window, so roughly **1 window**
  of work, up to **2** if sessions are interrupted or a ticket needs rework. T04
  (news posts with Editor/Manager roles) and T07 (access-control and CSRF hardening)
  are likely the heaviest, because T03 alone cost 21%.
- **How much of one week is that?**
  Estimate: about **5% of the weekly cap** (4 tickets × the 1.2% observed average),
  with a pessimistic bound near **10%** if each ticket costs like T03. Remaining
  weekly budget is not the constraint; the 5-hour window is.
- **Which stage will be cut first if the estimate is wrong?**
  First, drop `/code-review` from high to medium effort. Next, skip optional
  `/research` lookups. I will not cut the review comment on each ticket, because
  `CLAUDE.md` requires it before closing a ticket, and I will not cut `/tdd`.

## Re-check of the 2026-10-12 estimates against the ledger (added 2026-10-13)

- **Estimate:** the four remaining tickets T04-T07 would take about 45% of one
  5-hour window (about 11% each) and about 5% of the weekly cap, 10% at worst.
  **Ledger:** T04 5%, T05 2%, T06 5%, T07 9%, so **21%** of a 5-hour window and
  **2%** of the weekly cap for the four. The estimate was about twice too high on the
  window and inside the weekly bound.
- **Not forecast at all:** T08 (3%, done before the plan) and T09, the visual-design
  ticket added afterwards, which cost **16%** of a window and 2% of the weekly cap,
  more than any of T04-T07. The estimate did not allow for design iteration.
- **Which stage was cut:** none. `/code-review` stayed at the effort the ledger
  records for every row (`medium`); whether any review ran at `high` is still
  **unconfirmed**.
- **Plan vs actual in one line:** forecast 8% per `/implement` ticket plus 3% for its
  review; actual average over T04-T07 about 5% per ticket for both together.

## Correction 2026-10-15: ledger snapshot through 2026-10-14T13:51Z (still DRAFT)

The 2026-10-13 update above was right for the rows it used (up to 18:03Z) but is now
out of date, and two of its figures should not be reused:

| Figure | 2026-10-13 update | Ledger now (`scripts/usage_report.py`, rows through 2026-10-14T13:51:20Z) |
|---|---|---|
| Whole project, 5-hour windows | about 87 points | **100 points** (13 + 3 + 10 + 21 + 5 + 2 + 5 + 22 + 3 + 16) |
| Whole project, weekly cap | about 11% | **14%** |
| Average weekly cost per ticket | 1.0% | **1.3%** (9 tickets) |
| T07 | 9% of a window | **22%** by label, but see below |
| T04 to T07 together | 21% | **34%** by label (5 + 2 + 5 + 22); 16% if T07 counts only to its close |

**Why T07 reads high.** The phase file stayed on `T07` after the ticket closed
(2026-10-13T17:42Z), so everything done afterwards in that session was labelled T07:
README and screenshot work, transcript commits, the photo and News follow-up. The four
ledger rows up to 17:45:58Z add up to 4% of a window and 0% weekly. The 22% is
therefore an upper bound for the ticket and includes non-ticket work; it cannot be
split further from this ledger. From 2026-10-15 the phase file reads `submission-prep`.

**Forecast vs actual, restated.** Forecast for T04 to T07: about 45% of one window.
Actual: 34% by label, or 16% with T07 cut at its close. Either way it is under the
forecast; the earlier line "about twice too high" only holds for the ticket-only reading. The weekly estimate (about 5%, worst case 10%) held: by label T04 to T07 cost 0 + 0 + 1 + 4 = 5% of the weekly cap, which includes the non-ticket work logged under T07.
