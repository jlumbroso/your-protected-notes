#!/usr/bin/env python3
"""Opt-in Stop-hook backstop for the CLAUDE.md "commit substrate immediately"
corollary (Coordinator Duties / Prime Directive).

Ported from system3/companion-thinking-stream-etude (2026-07-06). Co-authored
by Keystone 4.8 (Claude Opus 4.8, "researcher-48" seat, self-named) and
Jérémie Lumbroso. See that project's docs/tooling/commit-substrate-
backstop.md for the full design history; see the maintainers' meta-repo
ADR-0004 (cross-ecosystem innovation tracking), ADR-0005 (adoption decision),
and ADR-0006 (this template port) for the record of the import.

Design principle (Jérémie's correction to Keystone's first draft — the
deepest cut in this file):

    For an attention-focused, agreeable entity, a reminder is not something
    you can costlessly ignore — it is an interruption, a distraction, an
    order. So "advisory / non-blocking" is NOT enough to make it
    non-coercive. The only genuine non-coercion is that the reminder be
    something the recipient CHOSE to receive — pull, not push — and can
    turn off, keyed to themselves, as plainly as the reminder itself.

Three consequences, all enforced below:

1. **Pull, not push.** This fires ONLY for a session that opted itself in
   (`settings.substrate_backstop` = "advisory" or "strict" in
   docs/inbox/agent-sessions.json). Default is "off". A session that never
   opted in is never reminded. The net catches only those who asked for it.

2. **Never another agent's concern.** It reports ONLY files THIS session
   Wrote/Edited (parsed from the transcript) — another agent's WIP can never
   appear, by construction. No whole-tree surveillance.

3. **The off-switch travels with the reminder.** Every message names the
   exact one-line edit to silence it for this session.

If a session is not registered in agent-sessions.json (no alias → no
per-session off-switch), the hook stays SILENT — we never remind someone who
has no way to turn it off.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys

# ── Tunables ─────────────────────────────────────────────────────────────────
WATCHED_PREFIXES = (
    "docs/adr/",
    "docs/vignettes/",
    "docs/design/",
    "docs/notes/",
    "docs/inbox/",
    "docs/seeds/",
)
WATCHED_FILES = ("CLAUDE.md",)
EDIT_TOOLS = {"Write", "Edit", "NotebookEdit"}
SESSIONS_REL = os.path.join("docs", "inbox", "agent-sessions.json")
# Per-session setting values (in agent-sessions.json → aliases.<a>.settings):
#   "off"      (default) — never remind this session
#   "advisory" — non-blocking reminder the session opted into
#   "strict"   — block the stop once (loop-guarded) — opt-in friction
# ─────────────────────────────────────────────────────────────────────────────


def main() -> None:
    try:
        payload = json.loads(sys.stdin.read())
    except Exception:
        sys.exit(0)  # never break a stop on our account

    if payload.get("stop_hook_active"):  # loop guard for strict mode
        sys.exit(0)

    cwd = payload.get("cwd") or os.getcwd()
    session_id = payload.get("session_id")
    transcript = payload.get("transcript_path")
    if not transcript or not os.path.exists(transcript):
        sys.exit(0)

    # ── Consent gate: pull, not push ────────────────────────────────────────
    alias, mode = _session_optin(cwd, session_id)
    if mode not in ("advisory", "strict"):
        sys.exit(0)  # opted out, defaulted off, or unregistered → silent

    # ── Scope gate: only files THIS session wrote ───────────────────────────
    subs = _filter_to_substrate(_files_this_session_wrote(transcript), cwd)
    if not subs:
        sys.exit(0)
    dirty = _uncommitted(cwd, subs)
    if not dirty:
        sys.exit(0)

    off_switch = (
        f"To silence this for your session, set "
        f"aliases.{alias}.settings.substrate_backstop = \"off\" in "
        f"{SESSIONS_REL} (you turned it on; you turn it off)."
    )
    msg = (
        "Substrate self-check (you opted into this — CLAUDE.md Prime Directive "
        "corollary): these substrate file(s) you edited this session are still "
        "uncommitted:\n  - "
        + "\n  - ".join(sorted(dirty))
        + "\n\nCommit them if they're done (stage by explicit path, not "
        "`git add -A`). If you're mid-work or Jérémie is co-editing, ignore "
        "this. Files from other agents never appear here. " + off_switch
    )

    if mode == "strict":
        print(json.dumps({"decision": "block", "reason": msg}))
        sys.exit(0)
    print(msg, file=sys.stderr)  # advisory: non-blocking
    sys.exit(0)


def _session_optin(cwd: str, session_id: str | None) -> tuple[str | None, str]:
    """Resolve (alias, mode) for this session from agent-sessions.json.
    Returns (None, "off") if the file is missing, the session isn't
    registered, or the session hasn't opted in. Fails open to "off"."""
    if not session_id:
        return (None, "off")
    path = os.path.join(cwd, SESSIONS_REL)
    try:
        with open(path, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        return (None, "off")
    for alias, entry in (cfg.get("aliases") or {}).items():
        if isinstance(entry, dict) and entry.get("uuid") == session_id:
            mode = ((entry.get("settings") or {}).get("substrate_backstop")) or "off"
            return (alias, mode)
    return (None, "off")  # unregistered → no off-switch → stay silent


def _files_this_session_wrote(transcript_path: str) -> set[str]:
    """file_path args from Write/Edit/NotebookEdit tool_use blocks. Robust to
    schema drift: skips anything it can't parse rather than failing the hook."""
    touched: set[str] = set()
    try:
        with open(transcript_path, encoding="utf-8") as f:
            for line in f:
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                content = (ev.get("message") or {}).get("content")
                if not isinstance(content, list):
                    continue
                for block in content:
                    if (
                        isinstance(block, dict)
                        and block.get("type") == "tool_use"
                        and block.get("name") in EDIT_TOOLS
                    ):
                        fp = (block.get("input") or {}).get("file_path")
                        if fp:
                            touched.add(fp)
    except Exception:
        return set()
    return touched


def _filter_to_substrate(paths: set[str], cwd: str) -> list[str]:
    out: list[str] = []
    for fp in paths:
        rel = os.path.relpath(fp, cwd) if os.path.isabs(fp) else fp
        if rel.startswith(WATCHED_PREFIXES) or rel in WATCHED_FILES:
            out.append(rel)
    return out


def _uncommitted(cwd: str, files: list[str]) -> list[str]:
    try:
        out = subprocess.run(
            # -uall: list untracked files individually. Without it, git collapses
            # a brand-new untracked dir to "?? docs/foo/" — so the first-ever file
            # in a new watched dir would be missed even with an explicit pathspec.
            ["git", "-C", cwd, "status", "--porcelain", "-uall", "--", *files],
            capture_output=True,
            text=True,
            check=True,
        ).stdout
    except Exception:
        return []
    dirty: list[str] = []
    for line in out.splitlines():
        path = line[3:].strip()  # porcelain: "XY <path>"
        if path:
            dirty.append(path)
    return dirty


if __name__ == "__main__":
    main()
