---
name: local-agent-ingestion
description: Read local agent session logs and databases safely and continuously — bounded byte budgets, fair resumption, schema drift, malformed records, content-free diagnostics, and metadata-only capture. Use when building or debugging a local reader for Codex, Claude Code, OpenCode, Pi, or similar agent runtimes.
---

# Local agent ingestion

A local monitor sees a moving target: files appended while being read, databases
written by another process, schemas that change between releases, and records
larger than memory. The reader must keep up without becoming the reason the
machine struggles.

## Operating contract

**Purpose.** Produce a design or implementation for a local reader that is
read-only, bounded, resumable, schema-tolerant, and diagnosable without leaking
content.

**Inputs.** The runtime's source location and format (append-only log, JSONL,
SQLite, etc.); the supported version or fixture; expected record identity; the
content-capture policy (full vs metadata-only); the host's concurrency and
shutdown model; the diagnostic fields the UI needs.

**Workflow.**

1. Inventory the source and its identity: path, format, version, update pattern,
   rotation/truncation behavior.
2. Define a stable record ID and the offset/cursor model.
3. Set byte budgets before decode for both files and database payloads.
4. Define fair resumption and schema-drift behavior.
5. Contain malformed records without killing the reader thread.
6. Bound in-memory caches by bytes and preserve cumulative totals.
7. Emit content-free diagnostics that distinguish poll success from new data.
8. Add synthetic fixtures for partial/oversized/malformed/schema-variant input.
9. Document the tested version and remaining unknowns.

**Deliverable.** A reader design or patch with: source contract; identity;
offset/cursor; byte budgets; fairness; schema handling; diagnostics; redaction/
metadata-only behavior; fixtures and tests.

**Completion.** A synthetic fixture with a partial record, an oversized record,
and a malformed record followed by a valid record is ingested without losing the
valid record or killing the loop; a large backlog makes forward progress across
polls; a schema variant is handled or reported; diagnostics contain no raw
content; a clean temporary checkout can run the fixture.

## Reading this skill

- **Invariant** — read-only, bounded before decode, fair progress, one malformed
  record cannot kill the reader, content-free diagnostics.
- **Default** — Agenturm's byte budgets, cache sizes, lookback windows, and
  content caps. These are examples/configurable defaults.
- **Case study** — Agenturm's measured reader behavior and runtime observations.
  See [`references/agenturm-readers.md`](references/agenturm-readers.md).

Numbers are labeled where they appear. Unlabeled numbers are illustrative;
adapt them to the source and version under test.

## When to use

- Tailing JSONL session logs that can grow for hours.
- Opening an agent's SQLite database read-only while the agent writes it.
- Supporting multiple runtimes with different schemas.
- A reader stops updating, misses sessions, or consumes too much memory.
- Diagnostics report "no errors" but no new records appear.
- Adding metadata-only capture or redaction.

## Principles

1. **Read-only.** Never write to another agent's database. Use synthetic
   fixtures in tests; never commit personal session data.
2. **Same user, same host.** Local discovery only sees files the process can
   read. A container/other user/remote host needs OTLP export or a copied source.
3. **Bounded before decode.** Limit bytes before JSON loads, not after.
4. **Fair, not just bounded.** A large record must not starve every later
   record forever.
5. **Never die on one bad record.** Catch `ValueError`, `RecursionError`,
   `OverflowError`, and non-finite timestamps; continue after the malformed
   record.
6. **Diagnostics are content-free.** Counters and paths, no raw events,
   credentials, or exception text.

## Reader loop

```text
# schematic: adapt to the source format
poll:
  read at most <poll_budget> from the saved offset
  for each complete line:
      if line > <record_budget>: discard through the next newline (across polls)
      parse with depth/size limits
      normalize timestamps defensively
      dedupe by stable record ID
      emit activity/spans
      commit offset only after the full line is consumed
  persist offset even if a malformed line was skipped
  publish content-free counters
  sleep
```

Rules that matter:

- **Partial records:** if the buffer ends mid-line, keep it for the next poll.
  If a record is oversized, discard through the terminating newline; do not parse
  its suffix as a new record.
- **Offset safety:** commit after processing, not before. A crash can replay a
  record; stable IDs make that idempotent.
- **Backlog:** drain large backlogs over successive polls. Do not read the whole
  file to catch up.
- **Truncation/rotation:** detect inode/size reset and restart from the beginning
  or the last known valid offset based on the format.
- **Discovery:** bound the number of candidate sources and use a newest-source
  heap with omission counts. Do not retain and sort every file.

Agenturm's **example/default** watcher budget was **8 MiB/poll, 2 MiB/record**,
with oversized records dropped through the newline across polls.

## Database readers

- Open read-only (`mode=ro` or a read-only connection).
- Do not assume the parent table is up to date. Discover recent records from the
  activity table, and read lifecycle from the current schema (observed OpenCode V2
  behavior in 2026-10: `session_v2`; older parent/legacy tables could be stale;
  see the reference).
- Bound payloads in **bytes before transfer**:
  - Agenturm's example: **2 MiB/record**, **16 MiB/poll**.
  - Count both oversized and poll-budget-excluded records.
- **Fair resumption:** a fixed-size per-part digest + cursor so a huge record
  cannot permanently re-import the same first chunk. Repeated polls must
  eventually reach later parts, messages, and sessions. Preserve a changed
  record behind the cursor.
- **Unchanged database:** a shortcut that skips work must still have a timed
  lookback refresh (Agenturm used a 30 s example) so old records age out without
  another write.
- **Schema drift:** optional columns are selected conditionally; access with safe
  fallbacks. Use partial-schema fixtures.

## Malformed data

Hostile or corrupt records are normal in a long-lived local log:

- deeply nested JSON → `RecursionError`
- huge/non-finite timestamps → `OverflowError`/`ValueError`
- invalid UTF-8, NULs, terminal escape sequences
- enormous IDs/names in tool calls
- NaN/Infinity in numeric fields

Containment:

- depth-limit JSON; never trust input.
- validate timestamp ranges and skip impossible values.
- strip control characters before display/storage where appropriate.
- a bad record increments a diagnostic and the loop continues.
- a bad startup header must not kill the polling thread.
- fixtures should include a valid record after each malformed one.

## Cache budgets

Long-lived sessions accumulate maps: started, tasks, usage, tool inputs, calls.
Count-only bounds are insufficient because a single malformed ID can be huge.

Agenturm's **example/default** budgets:

- **64 KiB per entry**
- **1 MiB per map**
- tracked bytes, not just entry count
- safe eviction with a diagnostic, not truncation that collides identities
- preserve cumulative usage totals
- preserve ordinary late tool-result correlation for a recent window

Test with huge keys/values, not just many entries.

## Content capture and privacy

- Redact recognizable credentials and selected sensitive structured fields
  before storage, best-effort.
- Exclude private/encrypted reasoning, binary payloads, process environments,
  and credential files.
- Agenturm's example content caps: 8,000 characters per activity record, 2,000
  per nested field, at most 60 entries. These are defaults, not universal limits.
- `--metadata-only`: omit native message text, commands, and results from future
  ingestion. It does not erase stored content.
- `--no-local-agents` (or equivalent): disable discovery entirely.
- Local MCP inventory should retain only server/client/scope names, never command
  lines, URLs, headers, or environment values.
- Process health should use only matching PIDs, start identity, and CPU/I/O
  counters; not arguments, environment, or file contents.

## Diagnostics

`last_success_ns` only proves the poll succeeded. To locate a stall, track:

- source path (okay to show locally; it can identify a project/user)
- last successful read
- source mtime / size
- bytes read last poll / total
- records, spans, activity events last poll / total
- backlog bytes
- skipped oversized records
- schema errors / skipped records
- OpenCode: sessions found, latest session update, payload bytes last poll
- omission counts for bounded discovery

Never include raw events, credentials, endpoint tokens, or exception text. Strip
terminal control sequences from paths before rendering.

| Pattern | Likely cause |
|---|---|
| bytes flat while the source updates | wrong file/profile/user/host, or reader disabled |
| bytes increase, records/spans zero | parser or schema mismatch |
| records increase, no records in the UI | downstream filter/publication |
| database sessions 0 | wrong DB, no recent activity, lookback too short |
| sessions found, payload bytes 0 | session/message lookup or schema problem |
| payload bytes increase, no activity | mapping/display issue |

## Worked example

**Input.** A synthetic JSONL file for a build runner contains:

1. a partial line at EOF;
2. a 3 MiB record;
3. malformed JSON;
4. a valid record `{"id":"job-9","step":"compile","status":"ok"}`.

Budgets: 2 MiB/record, 8 MiB/poll. Cache: one map, 1 MiB.

**Expected output.** Poll 1 reads the prefix, keeps the partial line, drops the
3 MiB record through its newline, skips the malformed record, and ingests
`job-9`. The offset advances past the dropped/malformed records. Diagnostics:
`skipped_oversized=1`, `skipped_records=1`, `records_last_poll=1`. Poll 2
completes the partial record. The reader thread stays alive.

This is the fixture to write before claiming the reader is robust.

## Testing

Use synthetic fixtures only. Cover:

- bounded read and oversized record dropped through newline across polls
- valid record after malformed/deep JSON
- extreme/non-finite timestamps
- partial record at EOF
- unchanged DB lookback aging
- parentless records / stale parent tables
- partial/optional columns
- small patched budgets + repeated polls → later parts/messages/sessions reached
- changed record behind the cursor
- huge cache keys/values → byte budget eviction, no collision
- cumulative usage preserved after eviction
- late tool result still correlates
- source rotation/truncation
- diagnostics contain no secrets/content

Do not use the developer's real agent database in tests or benchmarks.

## Failure modes

| Anti-pattern | Consequence |
|---|---|
| Read entire backlog per poll | Memory spike and long stalls |
| Count-only cache bounds | A single huge ID can retain a large amount of memory |
| Remove oversized revision and retry | Same prefix re-imported forever; later records starve |
| Require parent session rows | Active conversations silently hidden |
| Trust a stale parent table | New work invisible |
| Parse suffix of a partial record | Corrupt phantom records |
| Error kills the reader thread | Monitoring silently stops |
| Diagnostics include raw events | Secrets leak into screenshots/logs |
| Use a personal DB as a fixture | Privacy leak and unreproducible tests |
| Assume a runtime is supported | UI says "live" while a runtime is invisible |

## Case study

Agenturm's measured reader behavior, exact budgets, and runtime quirks are in
[`references/agenturm-readers.md`](references/agenturm-readers.md). They are a
concrete implementation, not a universal contract.

## Related skills

These are separate skills. Naming one here does **not** load it; use your host's
skill-loading mechanism.

- `agent-session-status` — turn the ingested evidence into state.
- `sqlite-telemetry-store` — persist the normalized records without losing
  completeness.
- `local-first-monitoring-privacy` — decide what content to capture and retain.

## Checklist

- [ ] Read-only; same-user/host assumptions documented.
- [ ] Byte budgets before decode; backlog drains across polls.
- [ ] Oversized partial records discarded through newline.
- [ ] Fair cursor/resumption; changed record behind cursor preserved.
- [ ] Deep JSON/extreme timestamps cannot kill the reader.
- [ ] Parentless/stale-schema discovery handled.
- [ ] Unchanged DB has timed lookback.
- [ ] Cache limits are bytes per entry and per map; usage preserved.
- [ ] Content limits/redaction/metadata-only implemented.
- [ ] Diagnostics are content-free and distinguish poll success from new data.
- [ ] Synthetic fixtures cover malformed/huge/partial/schema-drift cases.
- [ ] No personal DB/logs in tests or benchmarks.
