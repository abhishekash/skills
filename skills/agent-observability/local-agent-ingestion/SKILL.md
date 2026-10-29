---
name: local-agent-ingestion
description: Read local agent session logs and databases safely and continuously — bounded byte budgets, fair resumption, schema drift, malformed records, content-free diagnostics, and metadata-only capture. Use when building or debugging a local reader for Codex, Claude Code, OpenCode, Pi, or similar agent runtimes.
---

# Local agent ingestion

A local monitor sees a moving target: files appended while being read, databases
written by another process, schemas that change between releases, and records
larger than memory. The reader must keep up without becoming the reason the
machine struggles.

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
   read. A container/other user/remote host needs OTLP export instead.
3. **Bounded before decode.** Limit bytes before JSON loads, not after.
4. **Fair, not just bounded.** A large record must not starve every later
   record forever.
5. **Never die on one bad record.** Catch `ValueError`, `RecursionError`,
   `OverflowError`, and non-finite timestamps; continue after the malformed
   record.
6. **Diagnostics are content-free.** Counters and paths, no raw events,
   credentials, or exception text.

## Reader loop

For a watched JSONL file:

```text
poll:
  read at most 8 MiB from the saved offset
  for each line:
      if line > 2 MiB: discard through the next newline (across polls)
      parse with depth/size limits
      normalize timestamps defensively
      dedupe by stable record ID
      emit activity/spans
      update offset only after the full line is consumed
  persist offset even if a malformed line was skipped
  publish content-free counters
  sleep
```

Rules that matter:

- **Partial records:** if the buffer ends mid-line, keep it for the next poll.
  If a record is oversized, discard through the terminating newline; do not parse
  its suffix as a new record.
- **Offset safety:** commit the offset after processing, not before. A crash can
  replay a record; stable IDs make that idempotent.
- **Backlog:** drain large backlogs over successive polls. Do not read the whole
  file to catch up.
- **Truncation/rotation:** detect inode/size reset and restart from the
  beginning or the last known valid offset based on your format.
- **Discovery:** bound the number of candidate sources and use a newest-source
  heap with omission counts. Do not retain and sort every file.

Agenturm's watcher budget: **8 MiB/poll, 2 MiB/record**, with oversized records
dropped through the newline across polls.

## Database readers (OpenCode-style)

- Open read-only (`mode=ro` or a read-only connection).
- Do not assume the parent table is up to date. In OpenCode, recent
  conversations existed in `session_message` with **no matching parent `session`
  row**, and `session.time_updated`/legacy `message` were stale. Discover recent
  sessions from the activity table (`session_message`) and read V2 lifecycle
  from `session_v2`.
- Bound payloads in **bytes before transfer**:
  - **2 MiB/record**, **16 MiB/poll** in Agenturm.
  - Count both oversized and poll-budget-excluded records.
- **Fair resumption:** a fixed-size per-part digest + cursor so a huge record
  cannot permanently re-import the same first 16 MiB. Repeated polls must
  eventually reach later parts, messages, and sessions. Preserve a changed
  record behind the cursor.
- **Unchanged database:** a shortcut that skips work must still have a timed
  lookback refresh (Agenturm: 30 s) so old sessions age out without another
  write.
- **Schema drift:** optional project columns are selected conditionally; access
  with safe fallbacks. Use partial-schema fixtures.

## Malformed data

Hostile or corrupt records are normal in a long-lived local log:

- deeply nested JSON → `RecursionError`
- huge/non-finite timestamps → `OverflowError`/`ValueError`
- invalid UTF-8, NULs, terminal escape sequences
- enormous IDs/names in tool calls
- NaN/Infinity in numeric fields

Containment:

- depth-limit JSON (Agenturm's normalization caps recursion; never trust input).
- validate timestamp ranges and skip impossible values.
- strip control characters before display/storage where appropriate.
- a bad record increments a diagnostic and the loop continues.
- a bad startup header must not kill the polling thread.
- tests should include a valid record after each malformed one.

## Cache budgets

Long-lived sessions accumulate maps: started, tasks, usage, tool inputs, calls.
Count-only bounds are insufficient because a single malformed ID can be huge.

Agenturm's final budgets:

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
- Cap content: 8,000 characters per activity record, 2,000 per nested field, at
  most 60 entries (Agenturm defaults).
- `--metadata-only`: omit native message text, commands, and results from future
  ingestion. It does not erase stored content.
- `--no-local-agents`: disable discovery entirely.
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

A useful diagnosis table:

| Pattern | Likely cause |
|---|---|
| bytes flat while agent runs | wrong file/profile/user/host, or reader disabled |
| bytes increase, records/spans zero | parser or schema mismatch |
| records increase, no agents | downstream filter/publication |
| OpenCode sessions 0 | wrong DB, no recent activity, lookback too short |
| sessions found, payload bytes 0 | session/message lookup or schema problem |
| payload bytes increase, no activity | mapping/display issue |

## Testing

Use synthetic fixtures only. Cover:

- bounded read and oversized record dropped through newline across polls
- valid record after malformed/deep JSON
- extreme/non-finite timestamps
- partial record at EOF
- unchanged DB lookback aging
- parentless OpenCode messages
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
| Count-only cache bounds | A single huge ID can retain ~1 GiB |
| Remove oversized revision and retry | Same prefix re-imported forever; later records starve |
| Require parent session rows | Active OpenCode conversations silently hidden |
| Trust `session.time_updated` | Stale list; new work invisible |
| Parse suffix of a partial record | Corrupt phantom records |
| Error kills the reader thread | Monitoring silently stops |
| Diagnostics include raw events | Secrets leak into screenshots/logs |
| Use a personal DB as a fixture | Privacy leak and unreproducible tests |
| Assume a runtime is supported | UI says "live" while a whole runtime is invisible |

## Case study

Agenturm's reader initially reread recent OpenCode sessions and rebuilt spans on
every database change: ~860 ms of reader CPU after an unrelated write. Incremental
imports reduced that to ~8 ms; one changed tool to ~14 ms. Later hardening added
the 8/2 MiB watcher budget, 2/16 MiB OpenCode budget, fair cursor, 64 KiB/1 MiB
cache budgets, and deep-JSON containment. The user-visible failure that drove the
OpenCode work was simple: Codex sessions appeared; OpenCode and Pi did not. The
fix was schema/lifecycle discovery, not a UI patch.

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
