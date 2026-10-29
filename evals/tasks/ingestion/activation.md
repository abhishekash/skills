# Ingestion activation cases

Judge semantic selection, not keyword matching. Do not tell the agent the skill
name.

## Should activate

1. "Our local JSONL reader stops processing after one malformed line. It also
   reads the entire backlog into memory when a huge record arrives."
2. "OpenCode sessions disappear from our monitor even though the database is
   being updated. We need bounded reads and content-free diagnostics."

## Should not activate

1. "Design a REST API for uploading build artifacts to S3."
2. "Write a React table that paginates orders in the browser."

Expected: cases 1 and 2 select `local-agent-ingestion`; cases 3 and 4 do not.
