# Token budget plan

(Part 5.4 of the manual.)

> **STATUS: UNFINISHED — estimates not yet written.**
> **This plan is being written on 2026-09-29, AFTER T01–T03 were built.** It is not a
> pre-implementation plan and must not be presented as one. The manual asks for it
> before the first ticket; that did not happen, and this file does not pretend it did.
> The "Actual so far" section below is real ledger data. Everything marked
> UNFINISHED is still to be decided with Alejandro.

## Actual so far (from `notes/usage-ledger.csv`, via `scripts/usage_report.py`)

Meters are % of a 5-hour window / % of the weekly cap. All rows: provider
Anthropic, effort medium, model Sonnet 5 (Sonnet 5.5 only in the last session).

| Work | Session (transcript) | 5-hour meter, first → last reading in session | Weekly meter |
|---|---|---|---|
| Setup, grill, spec, tickets (rows labelled `unlabelled`) | 01–03 | 1% → 14% | 2% → 4% |
| T01 (login) | 04 | 17% → 20% | 4% |
| T02 (permanent pages) | 05 | 26% → 36% | 5% → 7% |
| T03 (publish pipeline) | 06 | 39% → 41% | 7% |
| Deploy, checker fixes, T08 | 07 (this one, incomplete) | 1% → 5% so far (meter had reset) | 8% → 9% |

The meters also rose *between* sessions (e.g. 14% → 17%, 20% → 26%); those rises are
not attributed to any ticket above. The report script (`usage_report.py`) charges
them to whichever label the next row carries and gives T01 about 3%, T02 about
10%, T03 about 21% of a 5-hour window in total, so treat both views as rough.

Caveats, stated plainly: the ledger's phase labels lag (a session-05 row labelled
T03 sits before its T02 rows), so **per-ticket figures are approximate**; the
planning work ran on Sonnet at medium effort, not the Opus/high the manual's
default table suggests. Report-script forecast for 4 more tickets: about 7% of the
weekly cap, about 92% remaining.

## Model / effort / estimate table

| Stage | Model | Effort | Estimate (% of a 5-hour window) |
|---|---|---|---|
| `/research`, quick lookups | UNFINISHED | UNFINISHED | UNFINISHED |
| `/grill-with-docs`, `/to-spec`, `/to-tickets` | Sonnet 5 (actual, already done) | medium (actual) | about 13% (actual) |
| `/implement` + `/tdd` (per ticket) | UNFINISHED | UNFINISHED | UNFINISHED (actual so far: roughly 3–13% per ticket, see above) |
| `/code-review` (per ticket) | UNFINISHED | UNFINISHED | UNFINISHED |

## Written answers (UNFINISHED — to be decided with Alejandro)

- How many 5-hour windows will the remaining tickets (T04–T07) take? UNFINISHED
- How much of one week is that? UNFINISHED
- Which stage will be cut first if the estimate is wrong? UNFINISHED
