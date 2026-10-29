#!/usr/bin/env python3
"""Generate a synthetic build-runner JSONL file. No real agent data."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def line(record: dict) -> str:
    return json.dumps(record, separators=(",", ":")) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="build_log.jsonl")
    parser.add_argument("--oversized-bytes", type=int, default=3_000_000)
    parser.add_argument("--backlog-records", type=int, default=40)
    args = parser.parse_args()

    path = Path(args.output)
    base = path.parent
    base.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as stream:
        stream.write(line({"job_id": "job-1", "step": "checkout", "status": "ok"}))
        stream.write('{"job_id":"job-2","step":"compile"')  # partial, no newline

    # A second file contains the malformed/oversized sequence plus a valid tail.
    mixed = base / "build_log_mixed.jsonl"
    with mixed.open("w", encoding="utf-8") as stream:
        stream.write(line({"job_id": "job-3", "step": "prepare", "status": "ok"}))
        stream.write('{"job_id":"job-oversized","payload":"' + ("x" * args.oversized_bytes) + '"}\n')
        stream.write("{not valid json}\n")
        stream.write(line({"job_id": "job-4", "step": "compile", "status": "ok"}))
        stream.write(line({"job_id": "job-5", "step": "test", "status": "failed"}))

    backlog = base / "build_backlog.jsonl"
    with backlog.open("w", encoding="utf-8") as stream:
        stream.write('{"job_id":"job-huge","payload":"' + ("y" * args.oversized_bytes) + '"}\n')
        for index in range(args.backlog_records):
            stream.write(line({"job_id": f"job-{index + 10}", "step": "step", "status": "ok"}))
    print(f"wrote {path}, {mixed}, {backlog}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
