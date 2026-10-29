---
name: local-first-monitoring-privacy
description: Design the privacy boundary for a local monitor that captures agent prompts, tool output, paths, and telemetry — loopback defaults, owner-only files, redaction, metadata-only capture, allowlisted preferences, content-free diagnostics, previewed exports, and honest retention. Use before shipping or reviewing a local observability tool.
---

# Local-first monitoring privacy

A local agent monitor sees the most sensitive part of a developer's work:
prompts, source code, shell commands, tool arguments/results, file paths, and
sometimes credentials. "It stays on your machine" is a deployment statement, not
a privacy design.

The goal is not zero collection. It is **explicit, bounded, inspectable
collection** with honest labels and safe defaults.

## When to use

- Capturing native agent sessions or OTLP telemetry.
- Adding diagnostics, preferences, exports, or retention.
- A screenshot/log/error might contain prompts, paths, tokens, or endpoints.
- Deciding whether a receiver token is needed.
- Writing privacy claims for a README or release.
- Reviewing a local monitor before public release.

## Threat model

Assume:

- The SQLite database is sensitive even without credentials; normal agent
  activity contains private project information.
- Producers can emit arbitrary attributes, including secrets.
- Prompts/tool outputs can contain credentials, customer data, and proprietary
  code.
- Local files can be read by other users/processes if permissions are wrong.
- Screenshots, diagnostics, exports, and logs can be shared accidentally.
- Backups/snapshots/free pages can outlive logical deletion.
- A loopback receiver is still reachable by any local process/user that can
  connect, unless the OS isolates them.

## Network boundary

- Bind to `127.0.0.1` by default.
- `OBSERVATORY_TOKEN` (or equivalent) is an optional **shared secret** for
  non-loopback/TLS-proxied use. It is not a login system, roles, per-user
  authorization, or encryption.
- If bound to a non-loopback address, require a token, TLS/reverse proxy, and an
  explicit warning. Do not call the receiver "hardened for the internet".
- Do not enable local session discovery on a non-loopback receiver; local files
  should only be read by a local receiver.
- Static status pages can stay open; data/API routes should require the token
  when configured.
- Reject URL credentials and malformed endpoints in the client.

## File permissions

- Create the SQLite database with `0600` **before** SQLite opens it. If it
  already exists, verify/tighten permissions.
- Create the config directory `0700`; write preferences with `0600`.
- Exports: `O_EXCL | 0600`; refuse overwrite; remove a partial file on failure;
  do not follow symlinks blindly.
- Do not put secrets in filenames, logs, or diagnostic text.
- Treat backups and database copies as sensitive.

## Capture and redaction

- Redact recognizable credentials and selected sensitive structured fields
  **before storage**, best-effort.
- Exclude private/encrypted reasoning, binary payloads, process environments,
  and credential files.
- Cap content: 8,000 characters per activity record, 2,000 per nested field, at
  most 60 entries (Agenturm defaults).
- Provider SDK capture should omit prompts/responses by default; content capture
  is opt-in.
- MCP inventory should retain only server/client/scope names. Drop commands,
  URLs, headers, and environment values.
- Process health should use matching PIDs, start identity, and CPU/I/O counters;
  not arguments, environment, or file contents.
- Never claim redaction is complete. Upstream schemas and truncation leave gaps.

## Metadata-only and deletion

- `--metadata-only` omits native message text, commands, and results from
  **future** ingestion. It does not erase stored content. Say that.
- `--no-local-agents` stops native discovery; it does not erase history.
- Metadata-only for native capture is separate from SDK content-capture options.
- Retention is **logical deletion**, not secure erasure. Deleted content may
  remain in SQLite free pages, journals, filesystem snapshots, and backups.
  Native source logs are separate and are not deleted by pruning telemetry.
- A retention setting is not a substitute for disk encryption or a disposal
  policy.

## Preferences

Persist only a small allowlist:

- theme
- active view
- non-sensitive filter flags (Reviews/Prompts/Errors)
- bounded failure fingerprints for dismissals

Never persist:

- search queries
- session IDs or scopes
- selected evidence
- endpoints, tokens, credentials
- raw prompts/paths

Additional rules:

- `AGENTURM_UI_PREFERENCES=0` (or equivalent) disables reads and writes.
- Headless tests never read/write the developer's config unless given an
  explicit test path.
- Cap file size (16 KiB in Agenturm).
- Parse defensively; a malformed/oversized file returns empty, not a crash.
- Write atomically via a temp file in the same directory + replace.
- A read-only config directory must not break monitoring.
- Fingerprints are bounded hashes (64 hex, list cap 100), not raw IDs.

## Diagnostics

Diagnostics are for support, not a data dump.

Allowed:

- source path (local; can identify a project/user)
- last successful read
- source mtime/size
- bytes/records/spans/events last poll and totals
- backlog, skipped oversized, schema errors
- OpenCode session counts/latest update/payload bytes
- retention guidance and first-run help

Not allowed:

- raw events/prompts/outputs
- receiver credentials/tokens
- endpoint secrets
- exception text that may include payloads
- arbitrary producer attributes

Strip terminal control sequences before rendering paths. State in the screen
that paths may identify projects/users.

## Exports

- `x` opens a **frozen privacy preview** of the exact JSON; no file is created
  before explicit confirmation.
- Export only the selected record and currently loaded evidence; say it is not a
  complete history.
- Include a coverage/completeness disclaimer.
- State clearly: "This exact JSON may contain prompts, outputs, paths, session/
  trace IDs, or secrets recorded by your agent. It is NOT redacted."
- Never include receiver credentials or background configuration.
- Create owner-only files, refuse overwrite, and do not leave truncated output.
- Review again before sharing.

## AI summaries and optional providers

- Optional AI summaries should run only when explicitly requested.
- Explain what evidence is sent and to which provider.
- Do not send prompts by default if the feature can work on recorded metadata.
- Propagate completeness flags; unknown totals stay unknown in the prompt.
- Cache by session snapshot; label an earlier-snapshot summary.
- A local recorded-progress summary should work without a provider/API key.

## UI copy rules

- "Local by default" is not "private by default" unless you explain capture.
- "Not captured" ≠ "does not exist".
- "Not reported" ≠ zero.
- "Not redacted" on exports.
- "Logical deletion, not secure erasure" on retention.
- "Loopback by default" on network.
- "Best-effort redaction" on capture.
- "May contain prompts, outputs, paths, or secrets" on exports/diagnostics.

## Test matrix

| Test | Expected |
|---|---|
| DB creation | mode `0600` before/after open |
| Prefs save/load | only allowlisted keys; mode `0600`; no search/session/endpoint |
| Pref opt-out | no `stat`/`mkdir`/write calls |
| Malformed/oversized prefs | empty result, no crash |
| Diagnostics with secret fields | secrets absent; expected counters present |
| Export allowlist | endpoint/token absent; selected detail present |
| Export write | `0600`; refuse overwrite; no partial on failure |
| Metadata-only | future content omitted; existing content untouched |
| Retention + refresh race | deleted cache not resurrected |
| Fingerprint | stable for same failure; changes for new trace/time |
| Dismissal list | bounded, hashed, no raw session IDs |

## Failure modes

| Anti-pattern | Consequence |
|---|---|
| Default umask DB creation | Brief world-readable telemetry |
| Token presented as auth/encryption | False security for non-loopback use |
| Diagnostics dump raw events | Secrets in screenshots/issues |
| Preferences store searches/IDs/endpoints | Sensitive behavior leaked |
| Export overwrites a file | Data loss; may follow symlink |
| "Retention" implies secure erase | Data remains in free pages/backups |
| Metadata-only claimed to erase old data | False privacy promise |
| Raw exception text in UI | Payload/secrets leak |
| AI summary silently sends prompts | Unexpected data egress |
| Local discovery on a network-bound receiver | Remote exposure of local files |
| Logging credentials in errors | Secret sprawl |

## Case study

Agenturm's privacy page is unusually explicit for an alpha: loopback by default,
best-effort redaction, metadata-only for future ingestion, allowlisted UI
preferences, content-free diagnostics, previewed exports, and a retention section
that says logical deletion is not secure erasure. These were not afterthoughts;
they came from review findings: a database created under a permissive umask, a
diagnostics screen that could leak, preferences that could have stored searches,
and an export that could overwrite a file. Each became a regression test.

The UI copy follows the same rule: never imply more certainty or safety than the
implementation provides.

## Checklist

- [ ] Loopback default; token/TLS guidance for non-loopback.
- [ ] Owner-only DB/config/export creation.
- [ ] Redaction before storage; excluded content classes documented.
- [ ] Content caps and metadata-only behavior stated.
- [ ] Prefs allowlist; opt-out; atomic/private write.
- [ ] Diagnostics content-free; control chars stripped.
- [ ] Export preview + confirmation + no overwrite + coverage disclaimer.
- [ ] Retention documented as logical deletion; backups/free pages called out.
- [ ] AI summaries explicit, scoped, and completeness-aware.
- [ ] Tests prove secrets do not appear in prefs/diagnostics/exports.
- [ ] Privacy copy matches actual behavior; no stronger claim.
