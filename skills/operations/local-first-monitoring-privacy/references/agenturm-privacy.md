# Agenturm privacy case study

These are Agenturm's concrete privacy choices. They are **case study**, not a
universal policy or compliance claim. The portability rules are in `SKILL.md`.

## Network

- Receiver bound to `127.0.0.1` by default.
- `OBSERVATORY_TOKEN` was an optional shared secret for non-loopback/TLS-proxied
  use. It was not a login system, role model, or encryption.
- Local discovery was not enabled on a non-loopback receiver.

## Storage and deletion

- SQLite database created with `0600` before SQLite opened it.
- Config directory `0700`; preference files `0600`.
- Exports created with `O_EXCL | 0600`; existing files were not overwritten.
- Retention was logical deletion, not secure erasure. Free pages, journals,
  snapshots, and backups could retain content. Native source logs were separate.

## Capture

- Recognizable credentials and selected sensitive structured fields were redacted
  before storage, best-effort.
- Private/encrypted reasoning, binary payloads, process environments, and
  credential files were excluded.
- Content caps: 8,000 characters per activity record, 2,000 per nested field, at
  most 60 entries.
- `--metadata-only` omitted native message text, commands, and results from future
  ingestion; it did not erase stored content.
- MCP inventory retained server/client/scope names only, not commands, URLs,
  headers, or environment values.

## Preferences

Persisted allowlist: theme, active view, Reviews/Prompts/Errors flags, and
bounded dismissed-attention fingerprints. No searches, session IDs, selections,
endpoints, or credentials. `AGENTURM_UI_PREFERENCES=0` disabled reads and writes.
The file was capped at 16 KiB, parsed defensively, and written atomically.

## Diagnostics and exports

- Diagnostics showed source paths, read counters, backlog, skipped oversized
  records, and schema errors. No raw events, credentials, or exception text.
- Export showed a frozen exact JSON preview and required explicit confirmation.
  It included only the selected record and loaded evidence, with a coverage
  disclaimer, and stated that it was not a redaction pass.

## What was not claimed

- Redaction was best-effort, not complete.
- Retention was not secure erasure.
- A loopback receiver was not "hardened for the internet."
- Token auth was not multi-user authorization.
- The local database was treated as sensitive because normal agent activity can
  contain private project information.
