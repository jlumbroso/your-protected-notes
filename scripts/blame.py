#!/usr/bin/env python3
"""blame.py — seat-level file provenance from session JSONLs (`just blame`).

Why this exists
---------------
`git blame` cannot attribute work to seats: every seat commits under the same
git author (Jérémie's global config), and Co-Authored-By trailers are
commit-grained and best-effort. The session JSONLs under
`~/.claude/projects/<slug>/` are the only record of WHICH session (→ seat)
touched WHICH file, WHEN, with WHICH model — via the harness's own tool_use
records. This tool is the query interface over that record: the crew's
answer to "who created/modified this file and when?"

Jérémie's idea (2026-07-09, dictated): "search for all tool records and...
find occurrences of a specific file name or file name pattern and then
provide a result of who made modifications or created that file at which
time." Manual precedents that motivated it: the Herald forensics, the
ADR-0007 orphan hunt — each was this exact query, done by hand.

Design notes
------------
- Prefilter with a cheap substring test per line (ripgrep-in-spirit; JSONL
  lines are huge and mostly irrelevant), then json.loads ONLY candidate
  lines and anchor on real `tool_use` structure — never regex fields out of
  raw JSON (same false-positive family as the QST-count bug fixed by
  Understudy 2026-07-06: substring hits are not records).
- File tools (Write/Edit/MultiEdit/NotebookEdit/Read) give VERIFIED paths
  (input.file_path). Bash gives HEURISTIC hits (pattern appeared somewhere
  in the command string — could be an mv target, a grep, or a mention);
  labeled `bash?` honestly rather than upgraded to certainty. Read hits are
  shown only with --reads (provenance usually means writes).
- "created" is approximated as the chronologically FIRST Write to a path in
  the record — labeled `write*` — since the JSONLs don't record whether the
  file pre-existed. Honest approximation, honestly marked.
- Seat resolution reuses the registry (docs/inbox/agent-sessions.json) via
  last-message.py's own loader; unregistered session UUIDs print truncated,
  so pre-crew sessions still show up rather than vanishing.

Usage
-----
    just blame <pattern>              # e.g. just blame refresh-terminals
    just blame <pattern> --reads      # include Read hits
    just blame <pattern> -n 50        # cap rows (default 30, newest last)

Origin: Cartographer 5 (Claude Fable 5), 2026-07-09, prototyping Jérémie's
dictated idea same-session. v1 scope: this project's JSONLs only; cross-
project sweep + per-seat project_slug overrides are the module owners' call
(see docs/adr/seed-2026-07-09-seat-blame-tool.md).
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

REPO_ROOT = Path(__file__).resolve().parent.parent

_LM_PATH = REPO_ROOT / "scripts" / "last-message.py"
_spec = importlib.util.spec_from_file_location("last_message", _LM_PATH)
last_message = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(last_message)

FILE_TOOLS = {"Write", "Edit", "MultiEdit", "NotebookEdit"}
READ_TOOLS = {"Read"}
ET = ZoneInfo("America/New_York")


def _project_dir() -> Path:
    base = Path("~/.claude/projects").expanduser()
    slug = str(REPO_ROOT).replace("/", "-")
    return base / slug


def _uuid_to_seat() -> dict[str, str]:
    """session-uuid → display label, from the registry (best-effort)."""
    mapping: dict[str, str] = {}
    try:
        cfg = last_message.load_config()
        for alias, entry in last_message._real_aliases(cfg).items():
            if isinstance(entry, dict) and entry.get("uuid"):
                label = entry.get("display_name", alias)
                model = entry.get("model", "")
                if "fable" in model.lower():
                    label = f"(+) {label}"
                mapping[entry["uuid"]] = label
    except Exception:
        pass  # registry problems shouldn't kill forensics — fall back to UUIDs
    return mapping


def scan(pattern: str, include_reads: bool) -> list[dict]:
    hits: list[dict] = []
    proj = _project_dir()
    if not proj.is_dir():
        sys.exit(f"No session storage at {proj}")
    pat_lower = pattern.lower()

    for jsonl in sorted(proj.glob("*.jsonl")):
        session = jsonl.stem
        try:
            with open(jsonl, encoding="utf-8", errors="replace") as f:
                for line in f:
                    # Cheap prefilter: skip the vast majority of lines before
                    # paying for json.loads. Case-insensitive on purpose.
                    if pat_lower not in line.lower():
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("type") != "assistant":
                        continue
                    msg = rec.get("message") or {}
                    content = msg.get("content")
                    if not isinstance(content, list):
                        continue
                    for block in content:
                        if not isinstance(block, dict) or block.get("type") != "tool_use":
                            continue
                        name = block.get("name", "")
                        inp = block.get("input") or {}
                        matched, kind, detail = None, None, None
                        if name in FILE_TOOLS or name in READ_TOOLS:
                            fp = str(inp.get("file_path") or inp.get("notebook_path") or "")
                            if pat_lower in fp.lower():
                                if name in READ_TOOLS and not include_reads:
                                    continue
                                matched, kind, detail = fp, name.lower(), None
                        elif name == "Bash":
                            cmd = str(inp.get("command") or "")
                            if pat_lower in cmd.lower():
                                matched, kind = "(command)", "bash?"
                                detail = " ".join(cmd.split())[:80]
                        if matched is None:
                            continue
                        hits.append({
                            "ts": rec.get("timestamp", ""),
                            "session": session,
                            "model": msg.get("model", "?"),
                            "kind": kind,
                            "path": matched,
                            "detail": detail,
                        })
        except OSError:
            continue

    hits.sort(key=lambda h: h["ts"])

    # First verified Write per path ≈ creation (honest approximation): mark it.
    seen_written: set[str] = set()
    for h in hits:
        if h["kind"] == "write":
            if h["path"] not in seen_written:
                h["kind"] = "write*"
                seen_written.add(h["path"])
    return hits


def _fmt_ts(iso: str) -> str:
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.astimezone(ET).strftime("%m-%d %I:%M%p ET")
    except ValueError:
        return iso[:16]


def main() -> None:
    parser = argparse.ArgumentParser(description="Seat-level file provenance from session JSONLs.")
    parser.add_argument("pattern", help="filename or path fragment (case-insensitive substring)")
    parser.add_argument("--reads", action="store_true", help="include Read-tool hits")
    parser.add_argument("-n", type=int, default=30, help="max rows shown (newest kept; default 30)")
    args = parser.parse_args()

    seats = _uuid_to_seat()
    hits = scan(args.pattern, args.reads)

    if not hits:
        print(f"No tool records matching '{args.pattern}' in this project's sessions.")
        return

    shown = hits[-args.n:]
    if len(hits) > len(shown):
        print(f"({len(hits) - len(shown)} older hit(s) omitted — pass -n {len(hits)} for all)")
    print(f"🔎 blame '{args.pattern}' — {len(hits)} tool record(s), chronological:\n")
    for h in shown:
        who = seats.get(h["session"], h["session"][:8] + "…")
        line = f"  {_fmt_ts(h['ts']):18s}  {who:22s}  {h['kind']:7s}  {h['path']}"
        if h["detail"]:
            line += f"\n  {'':18s}  {'':22s}  {'':7s}  └ {h['detail']}"
        print(line)

    print("\n  by seat:")
    per_seat: dict[str, int] = {}
    for h in hits:
        who = seats.get(h["session"], h["session"][:8] + "…")
        per_seat[who] = per_seat.get(who, 0) + 1
    for who, n in sorted(per_seat.items(), key=lambda kv: -kv[1]):
        print(f"    {who:22s} {n}")
    print("\n  legend: write* = first recorded Write (≈ creation) · bash? = pattern seen in a shell command (heuristic, not a verified file op)")


if __name__ == "__main__":
    main()
