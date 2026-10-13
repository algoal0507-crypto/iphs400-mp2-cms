# Compaction log

> **No compaction events have been recorded.** This is a statement of evidence
> reviewed on 2026-09-29, not a template left blank:
>
> - The six saved transcripts in `docs/transcripts/` (sessions 01-06) contain no
>   compaction markers: no `compact_boundary` system events, no
>   compaction-summary messages, and no `/compact` commands.
> - `notes/usage-ledger.csv` (33 rows, sessions labelled `T01`-`T03` and
>   `unlabelled`) peaks at 23% context use. The course rule only calls for
>   compacting once context passes 50-60%, so this ticket work never reached that
>   range.
> - The `PreCompact` hook (`.claude/hooks/ctx_compact_log.py`) is configured in
>   `.claude/settings.json`. It appends a row below whenever a compaction happens,
>   so an empty table means none were logged by the hook either.
>
> Limits of this claim: it covers the sessions above only. Any session whose
> transcript was not saved, or that is still in progress, is not covered.

> **Update, 2026-10-13 (evidence re-checked; the 2026-09-29 statement above is kept as written).**
>
> - **Method.** The transcripts in `docs/transcripts/` were parsed line by line as
>   JSON and searched for real compaction events: system messages with
>   `subtype: compact_boundary`, `isCompactSummary` messages, and `/compact`
>   commands. Sessions **01-09 contain none** (0 of each).
> - **A plain text search is misleading.** Searching the raw files for the words
>   `compact_boundary` finds 3 hits in session 07. Those are the assistant's own
>   search commands, written while it audited for compactions, not compactions.
> - **Context use.** `notes/usage-ledger.csv` (10 sessions, rows through
>   2026-10-13T18:03Z) peaks at 23% context in sessions 01-09 and 45% in session 10,
>   all below the 50% mark where the course rule starts asking for `/compact`.
> - **Not covered.** Session 10 (`17a751d5`, the T06, T07, and T09 work on
>   2026-10-13) has no saved transcript yet, so its absence of compaction is not
>   confirmed from a transcript. The `PreCompact` hook has logged no rows in the
>   table below.

| UTC time | Session | Trigger | Focus note |
|---|---|---|---|
