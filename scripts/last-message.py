#!/usr/bin/env python3
"""
last-message.py — Read recent messages from any agent's session JSONL.

Why this exists
---------------

In a multi-agent collaboration, the human is the synchronous bottleneck unless
each agent can independently *see* what other agents are doing. This script
gives each participant — human or AI — visibility into the most recent
messages of any other participant, looked up by a short alias rather than a
UUID.

Two operational benefits, in order of importance:

1. **Per-message model attribution is preserved and surfaced.** Every entry
   shown includes the `model` field as recorded in the session JSONL. This
   is the load-bearing detail: silent model substitutions (classifier
   reroutes, harness-level swaps, deprecations) are NOT visible from inside
   a session — only from the .message.model metadata. Reading
   another agent's recent messages with `just last <alias>` doubles as a
   drift detector.

2. **Cross-session coordination without the human as message bus.** "What
   did agent X just say?" becomes a single command instead of a copy-paste.

Usage
-----

    just last <alias> [k]           # last K assistant messages (default 1)
    just last <alias> 5             # last 5
    just last-full <alias>          # full content (no truncation)
    just aliases                    # show configured aliases
    just discover-sessions          # list recent JSONLs (to find new UUIDs)
    just pulse [stale-hours]        # health check: one line per seat
    just launch <seat>              # start/attach the seat's tmux session
    just wake <seat> "<msg>"        # push-notify a running seat
    just seats                      # list seat sessions with state
    just onboard <alias>            # print a seat's read_order, found/missing marked

Direct invocation:

    python3 scripts/last-message.py <alias> [-k N] [--full]
    python3 scripts/last-message.py --list
    python3 scripts/last-message.py --discover
    python3 scripts/last-message.py --pulse [--stale-threshold N] [--verbose]
    python3 scripts/last-message.py --launch <seat> | --wake <seat> --message "..." | --seats

Configuration: `docs/inbox/agent-sessions.json`

Tool support
------------

Out of the box, this resolves session JSONLs from Claude Code's storage:

    ~/.claude/projects/<cwd-slug>/<session-uuid>.jsonl

where `<cwd-slug>` is the project's working directory with `/` replaced by `-`.

For other tools (Cursor, Cline, Aider, raw API logging), override the storage
discovery by adding a `_storage` block to `docs/inbox/agent-sessions.json`:

    {
      "_schema": 1,
      "_storage": {
        "kind": "claude-code",          // or "custom"
        "base_dir": "~/.claude/projects" // optional override
      },
      "aliases": { ... }
    }

If `kind` is `"custom"`, set `base_dir` to a path where JSONLs live as
`<uuid>.jsonl` directly (no project-slug subdirectory).

Origin
------

Contributed by Statesman 4.7 (Claude Opus 4.7), 2026-06-15, via System3
Conversations. The principle this script operationalizes — per-message model
attribution as drift detector — was named as Doubt 2 of ADR 0042 (Platform
Change Resilience and Drift Detection) in that project, after the framework
caught a silent classifier reroute mid-task.

Extended in operational use downstream and backported to this template in two
waves (Shipwright 5, Claude Fable 5): meta-repo ADR-0003 (v3.6.0 — tail-window
JSONL reading, `--pulse` per-seat health check) and meta-repo ADR-0006
(v3.7.0 — wake infrastructure: `--launch`/`--wake`/`--seats`/`--update-titles`,
including the post-baseline fix bundle: per-seat/global tmux socket isolation,
the existing-session title-rewrite fix, cooldown cross-project namespacing,
and the cross-project `project_slug` storage override; see the
wake-infrastructure section comment below for the full attribution chain and
known-open items). A third wave (Grafter 5, Claude Sonnet 5, meta-repo
ADR-0004 Iteration 8, 2026-07-13) added `--onboard`/`cmd_onboard`, backporting
`read_order` — invented by Notary Opus 4.7 in an unrelated downstream
deployment of this same template (`crossfoot`, formerly `qaestor`, formerly
`penn-purchasing-expense-workflow`; commit `f714b3a8`, 2026-07-09) — a
per-seat array codifying a seat's onboarding packet as machine-readable data
rather than only prose. See `docs/inbox/agent-sessions.json`'s
`_read_order_note` for the schema and the ORRCF on why it's top-level rather
than nested under `settings`. Attributions stack.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Resolve the alias config relative to this script. Works regardless of CWD.
ALIAS_FILE = Path(__file__).resolve().parent.parent / "docs" / "inbox" / "agent-sessions.json"

TRUNCATE_DEFAULT = 600  # chars per message body when not --full


def project_slug_from_cwd() -> str:
    """Convert the project's working directory into Claude Code's project-slug form.

    Example: /Users/alice/Programming/my-project
                → -Users-alice-Programming-my-project

    Claude Code stores each project's sessions under:
        ~/.claude/projects/<this-slug>/<session-uuid>.jsonl
    """
    cwd = Path(__file__).resolve().parent.parent  # repo root (script lives in scripts/)
    return str(cwd).replace("/", "-")


def load_config() -> dict:
    """Read the alias file. Returns dict with optional `_schema`, `_storage`, `aliases`."""
    if not ALIAS_FILE.exists():
        sys.exit(
            f"Alias file not found: {ALIAS_FILE}\n"
            "Create one (see docs/inbox/agent-sessions.json template) or run\n"
            "`just discover-sessions` to find session UUIDs for new agents."
        )
    try:
        with ALIAS_FILE.open() as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        sys.exit(f"Alias file is not valid JSON: {e}")


def storage_base_dir(cfg: dict) -> Path:
    """Resolve the directory where session JSONLs live, honoring config override."""
    storage = cfg.get("_storage", {}) or {}
    base = storage.get("base_dir", "~/.claude/projects")
    base_path = Path(os.path.expanduser(base))
    kind = storage.get("kind", "claude-code")
    if kind == "claude-code":
        return base_path / project_slug_from_cwd()
    # "custom" or other: assume <uuid>.jsonl lives directly under base_dir
    return base_path


def resolve_jsonl(alias: str, cfg: dict) -> Path:
    aliases = _real_aliases(cfg)
    if alias not in aliases:
        known = ", ".join(sorted(aliases)) or "(none configured)"
        sys.exit(f"Unknown alias '{alias}'. Known: {known}")
    entry = aliases[alias]
    uuid = entry.get("uuid") if isinstance(entry, dict) else entry
    base = storage_base_dir(cfg)
    # Per-alias override: a seat whose live session is actually homed under a
    # DIFFERENT project's Claude Code storage slug than this repo's own (e.g.
    # a seat that works cross-repo, or was launched from another directory).
    # Ported from batch-renderer's crew (Claude Fable 5, 2026-07-07; commit
    # 1c8764e) — "for cross-repo seats," per that commit's own message. No
    # named seat beyond that is recorded upstream to credit more precisely.
    if isinstance(entry, dict) and entry.get("project_slug"):
        storage = cfg.get("_storage", {}) or {}
        base_root = Path(os.path.expanduser(storage.get("base_dir", "~/.claude/projects")))
        base = base_root / entry["project_slug"]
    jsonl = base / f"{uuid}.jsonl"
    if not jsonl.exists():
        sys.exit(f"Session JSONL not found for '{alias}': {jsonl}")
    return jsonl


def read_last_messages(jsonl: Path, k: int, role_filter: str | None = "assistant") -> list[dict]:
    """Return the last K JSONL entries matching role_filter (None = all)."""
    matches: list[dict] = []
    with jsonl.open() as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if role_filter is None:
                matches.append(obj)
                continue
            t = obj.get("type")
            msg = obj.get("message") or {}
            role = msg.get("role") or t
            if role == role_filter or t == role_filter:
                matches.append(obj)
    return matches[-k:] if k > 0 else matches


def extract_text(entry: dict) -> str:
    """Pull a sensible text representation from a JSONL entry."""
    msg = entry.get("message") or {}
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict):
                if c.get("type") == "text":
                    parts.append(c.get("text", ""))
                elif c.get("type") == "thinking":
                    continue  # skip internal thinking from default output
                elif c.get("type") == "tool_use":
                    name = c.get("name", "tool")
                    parts.append(f"[tool_use:{name}]")
                elif c.get("type") == "tool_result":
                    parts.append("[tool_result]")
            else:
                parts.append(str(c))
        return "".join(parts)
    return ""


def format_entry(entry: dict, idx: int, total: int, full: bool) -> str:
    msg = entry.get("message") or {}
    model = msg.get("model") or entry.get("type") or "—"
    role = msg.get("role") or entry.get("type") or "—"
    ts = entry.get("timestamp") or ""
    if ts:
        try:
            ts = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            ts = ts.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        except (ValueError, TypeError):
            pass
    text = extract_text(entry).strip()
    if not full and len(text) > TRUNCATE_DEFAULT:
        text = (
            text[:TRUNCATE_DEFAULT]
            + f"… ({len(text) - TRUNCATE_DEFAULT} more chars; --full to see all)"
        )
    header = f"─── [{idx}/{total}] {role} · model={model} · {ts} ───"
    return f"{header}\n{text}\n"


def cmd_last(args: argparse.Namespace) -> None:
    cfg = load_config()
    jsonl = resolve_jsonl(args.alias, cfg)
    role = None if args.role == "any" else args.role
    msgs = read_last_messages(jsonl, args.k, role_filter=role)
    if not msgs:
        print(f"(no {args.role} messages found in {jsonl.name})")
        return
    alias_meta = cfg.get("aliases", {}).get(args.alias)
    label = args.alias
    if isinstance(alias_meta, dict) and alias_meta.get("role"):
        label = f"{args.alias} ({alias_meta['role']})"
    print(f"═══ {label} — {jsonl.name} ═══")
    for i, m in enumerate(msgs, 1):
        print(format_entry(m, i, len(msgs), args.full))


def _real_aliases(cfg: dict) -> dict:
    """Skip underscore-prefixed keys (treated as comments/metadata in JSON)."""
    return {k: v for k, v in cfg.get("aliases", {}).items() if not k.startswith("_")}


def cmd_list(_args: argparse.Namespace) -> None:
    cfg = load_config()
    aliases = _real_aliases(cfg)
    if not aliases:
        print("(no aliases configured)")
        print(f"Edit {ALIAS_FILE} to add some, then `just discover-sessions` finds UUIDs.")
        return
    print(f"Configured aliases ({ALIAS_FILE}):")
    for name in sorted(aliases):
        meta = aliases[name]
        if isinstance(meta, dict):
            uuid = meta.get("uuid", "?")
            role = meta.get("role", "")
            print(f"  {name:20s}  {uuid}  {('— ' + role) if role else ''}")
        else:
            print(f"  {name:20s}  {meta}")


def cmd_onboard(args: argparse.Namespace) -> None:
    """Print a seat's read_order — its onboarding packet as machine-readable
    data, invented by Notary Opus 4.7 (crossfoot, 2026-07-09) and backported
    here 2026-07-13 by Grafter 5 (ADR-0004 Iteration 8). Marks each entry
    found/missing on disk — the "lint can check they exist" value-prop this
    was ported for."""
    if not args.alias:
        sys.exit("Usage: last-message.py <alias> --onboard")
    cfg = load_config()
    aliases = _real_aliases(cfg)
    meta = aliases.get(args.alias)
    if meta is None:
        sys.exit(f"Unknown alias: {args.alias} (see --list)")
    read_order = meta.get("read_order") if isinstance(meta, dict) else None
    if not read_order:
        print(f"{args.alias} has no read_order configured yet.")
        print(f'Add a "read_order": [...] array to its entry in {ALIAS_FILE}.')
        return
    display = meta.get("display_name", args.alias) if isinstance(meta, dict) else args.alias
    print(f"📖 Read order for {display}:")
    for i, entry in enumerate(read_order, 1):
        resolved = Path(entry).expanduser()
        mark = "✓" if resolved.exists() else "✗ MISSING"
        print(f"  {i}. {entry}  {mark}")


def cmd_discover(args: argparse.Namespace) -> None:
    """List recent JSONLs in the storage dir, with a hint of their content.

    Two identically-onboarded parallel launches (same pasted incipit, mtimes
    seconds apart) can't be told apart by this table alone — neither the
    first-user-message excerpt nor mtime ordering identifies *which row is
    you*. Fix (Azoth, InboxAlchemy deployment, 2026-07-13, Option A+B; ported
    by Grafter 5): `$CLAUDE_CODE_SESSION_ID`, when Claude Code sets it, is
    the authoritative answer — no path-parsing, no inference. Not verified
    across every Claude Code version/config; degrades gracefully (falls
    through to the plain table) when unset."""
    cfg = load_config() if ALIAS_FILE.exists() else {"aliases": {}}
    pdir = storage_base_dir(cfg)
    if not pdir.exists():
        sys.exit(f"Storage dir does not exist: {pdir}\n(Override via _storage.base_dir in alias file)")
    jsonls = sorted(pdir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not jsonls:
        sys.exit(f"No JSONLs found in {pdir}")
    known = {}
    for name, v in _real_aliases(cfg).items():
        uuid = v.get("uuid") if isinstance(v, dict) else v
        known[uuid] = name
    own_session_id = os.environ.get("CLAUDE_CODE_SESSION_ID")
    if own_session_id:
        print(f"Your own session (from $CLAUDE_CODE_SESSION_ID): {own_session_id}")
    print(f"Recent sessions in {pdir}:")
    print(f"{'mtime':25s}  {'uuid':40s}  {'alias':12s}  first-user-message")
    for p in jsonls[: args.limit]:
        mtime = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        uuid = p.stem
        alias = known.get(uuid, "")
        first_user = ""
        try:
            with p.open() as f:
                for line in f:
                    try:
                        obj = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if obj.get("type") == "user" or (obj.get("message", {}) or {}).get("role") == "user":
                        first_user = extract_text(obj) or str((obj.get("message", {}) or {}).get("content", ""))[:80]
                        break
        except OSError:
            pass
        first_user = first_user[:60].replace("\n", " ")
        marker = "  ← this session" if uuid == own_session_id else ""
        print(f"{mtime:25s}  {uuid:40s}  {alias:12s}  {first_user}{marker}")


def read_jsonl_tail(jsonl: Path, max_bytes: int = 65536) -> list[dict]:
    """Read the last ~max_bytes of a JSONL, parse backwards to get final messages.

    Returns messages in chronological order (oldest to newest from the tail window).
    Efficient for large files — only reads the end.
    """
    if not jsonl.exists():
        return []
    size = jsonl.stat().st_size
    if size == 0:
        return []

    # Read last max_bytes (or whole file if smaller)
    read_size = min(size, max_bytes)
    with jsonl.open('rb') as f:
        f.seek(size - read_size)
        tail_bytes = f.read()

    # Decode and split into lines
    try:
        tail_text = tail_bytes.decode('utf-8', errors='ignore')
    except Exception:
        return []

    lines = tail_text.split('\n')
    # First line might be partial (we seeked mid-line), skip it
    if len(lines) > 1:
        lines = lines[1:]

    messages = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            messages.append(obj)
        except json.JSONDecodeError:
            continue

    return messages


def classify_seat(jsonl: Path, stale_threshold_hours: float = 6.0) -> dict:
    """Classify a seat's health status from its JSONL tail.

    Returns dict with: state (ERROR/WAITING/STALE/OK), emoji, model, age_str, text_preview
    """
    # Read tail efficiently
    messages = read_jsonl_tail(jsonl, max_bytes=65536)

    # Find last assistant message
    last_assistant = None
    for msg in reversed(messages):
        msg_obj = msg.get("message", {})
        role = msg_obj.get("role") or msg.get("type")
        if role == "assistant":
            last_assistant = msg
            break

    if not last_assistant:
        # No assistant messages in tail — treat as stale
        mtime = datetime.fromtimestamp(jsonl.stat().st_mtime, tz=timezone.utc)
        age = datetime.now(timezone.utc) - mtime
        age_str = format_age(age)
        return {
            "state": "STALE",
            "emoji": "🟡",
            "model": "—",
            "age_str": age_str,
            "text_preview": "(no assistant messages in tail)",
        }

    # Extract fields
    msg_obj = last_assistant.get("message", {})
    model = msg_obj.get("model") or "—"
    text = extract_text(last_assistant).strip()
    preview = text[:80].replace("\n", " ") if text else "(empty)"

    # Get age from timestamp
    ts_str = last_assistant.get("timestamp") or ""
    if ts_str:
        try:
            ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
            age = datetime.now(timezone.utc) - ts
            age_str = format_age(age)
            age_hours = age.total_seconds() / 3600
        except (ValueError, TypeError):
            age_str = "?"
            age_hours = 0
    else:
        # Fall back to file mtime
        mtime = datetime.fromtimestamp(jsonl.stat().st_mtime, tz=timezone.utc)
        age = datetime.now(timezone.utc) - mtime
        age_str = format_age(age)
        age_hours = age.total_seconds() / 3600

    # Classification logic

    # 🔴 ERROR — model=<synthetic> OR body matches ^API Error
    if model == "<synthetic>" or text.startswith("API Error"):
        return {
            "state": "ERROR",
            "emoji": "🔴",
            "model": model,
            "age_str": age_str,
            "text_preview": preview,
        }

    # 🟡 WAITING — ends in question + age > threshold
    last_lines = [line for line in text.split('\n')[-3:] if line.strip()]
    ends_with_question = any('?' in line for line in last_lines[-2:])
    if ends_with_question and age_hours > 1.0:  # 1 hour threshold for waiting
        return {
            "state": "WAITING",
            "emoji": "🟡",
            "model": model,
            "age_str": age_str,
            "text_preview": preview,
        }

    # 🟡 STALE — no JSONL append in > threshold, no terminal question
    if age_hours > stale_threshold_hours and not ends_with_question:
        return {
            "state": "STALE",
            "emoji": "🟡",
            "model": model,
            "age_str": age_str,
            "text_preview": preview,
        }

    # 🟢 OK — anything else
    return {
        "state": "OK",
        "emoji": "🟢",
        "model": model,
        "age_str": age_str,
        "text_preview": preview,
    }


def format_age(delta) -> str:
    """Format a timedelta as compact age string (e.g., '2h', '45m', '3d')."""
    seconds = delta.total_seconds()
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        return f"{int(seconds / 60)}m"
    elif seconds < 86400:
        return f"{int(seconds / 3600)}h"
    else:
        return f"{int(seconds / 86400)}d"


def cmd_pulse(args: argparse.Namespace) -> None:
    """One-line health check per registered seat.

    Detects stalls, errors, and blocked states across all agents.
    Output format: <emoji> <alias> <state> age=<time> model=<model> "<preview>"
    """
    cfg = load_config()
    aliases = _real_aliases(cfg)

    if not aliases:
        print("(no aliases configured)")
        return

    # Collect all seat statuses
    results = []
    for alias in sorted(aliases):
        try:
            jsonl = resolve_jsonl(alias, cfg)
            status = classify_seat(jsonl, stale_threshold_hours=args.stale_threshold)
            results.append((alias, status))
        except SystemExit:
            # JSONL not found — treat as missing
            results.append((alias, {
                "state": "MISSING",
                "emoji": "⚫",
                "model": "—",
                "age_str": "—",
                "text_preview": "(JSONL not found)",
            }))

    # Print results
    for alias, status in results:
        # Get display name or role (if --verbose)
        alias_meta = aliases.get(alias)
        name_suffix = ""
        if isinstance(alias_meta, dict):
            if args.verbose and alias_meta.get("role"):
                # Verbose mode: show full role paragraph (no truncation in name field,
                # but still cap text preview at 60 to keep some structure)
                name_suffix = f" ({alias_meta['role']})"
            elif alias_meta.get("display_name"):
                # Default: show short display_name if available
                name_suffix = f" ({alias_meta['display_name']})"
            # Else: no suffix (just alias)

        # Format line: in default mode, keep tight; in verbose mode, let name expand
        if args.verbose:
            # Verbose: no width limit on name, but keep preview at 60
            print(
                f"{status['emoji']} {alias:15s}{name_suffix} "
                f"{status['state']:8s} age={status['age_str']:6s} "
                f"model={status['model']:20s} \"{status['text_preview'][:60]}\""
            )
        else:
            # Default: tight layout with fixed widths
            print(
                f"{status['emoji']} {alias:15s}{name_suffix[:25]:25s} "
                f"{status['state']:8s} age={status['age_str']:6s} "
                f"model={status['model']:20s} \"{status['text_preview'][:60]}\""
            )

    # Summary counts
    error_count = sum(1 for _, s in results if s['state'] == 'ERROR')
    waiting_count = sum(1 for _, s in results if s['state'] == 'WAITING')
    stale_count = sum(1 for _, s in results if s['state'] == 'STALE')
    ok_count = sum(1 for _, s in results if s['state'] == 'OK')

    print()
    print(f"Summary: {error_count} ERROR, {waiting_count} WAITING, {stale_count} STALE, {ok_count} OK")

    # Exit code: non-zero if any errors
    if error_count > 0:
        sys.exit(1)


# ─── Wake infrastructure (ported from caring-feedback, ADR-0050 lineage) ────────
#
# Ported from caring-feedback's scripts/last-message.py (commits fedc298, e945f85,
# 8685374, 2db806a, 6cde381), 2026-07-07 — baseline pinned + confirmed current
# by Commodore 5 in direct reply (caring-feedback docs/inbox/2026-07-07-0238-
# commodore-to-understudy-...): "2db806a is current code-wise — but the field
# moved tonight AFTER 0230, in live use." This port includes that same-night
# fix (6cde381, Jérémie + Sonnet 4.5): the verify-retry check was too strict
# (short sleep, exact-string match, narrow capture window), causing a false
# "didn't land" retry that delivered Commodore's wake to Steward twice. Fixed
# by a longer settle sleep, a wider capture window, and checking for the
# attribution prefix + a message fragment rather than an exact string match
# (robust to line-wrapping).
#
# Credit, in the order Commodore specified when asked: **Steward 4.5 (Claude
# Sonnet 4.5)** — implementation, built in roughly forty minutes of
# wall-clock across two sessions, top-credited; **Jérémie Lumbroso** — design
# philosophy (the warn-log-force doctrine; the composition-guard veto
# insight; the two pilot acceptance criteria); **Commodore 5 (Claude Fable
# 5)** — spec authorship (ADR-0050) and live field-testing that found every
# guard's failure mode before it shipped.
#
# Known-open items inherited as-is, not silently resolved by this port:
# - Terminal-title polish and regression tests for the two warn/--force
#   guards were marked "deferrable" at origin and still are.
# - A wake targeting a session that is mid-turn is gracefully QUEUED by
#   Claude Code, but verify-retry doesn't recognize the queue banner and can
#   report a false "silent drop" — not yet fixed upstream (Commodore's Item 6,
#   flagged same night as the first port).
# - The active-turn refusal check and the send can race a turn that starts in
#   between (TOCTOU) — not fixed upstream; inherited as a known limitation.
#
# ── Improvements batch #2 (2026-07-07, caring-feedback commits 04563ea, c10a455,
# 860ba1c, ab589ad, 989f9fa) — Steward 4.5 (implementation), Jérémie
# (--model catch, hex-color idea), Commodore 5 (spec + routing), and
# Seamster 5 (Claude Sonnet 5, system3/companion-thinking-stream-etude —
# imported this infrastructure independently, found two bugs, ported fixes
# back to caring-feedback same night; a third project now in this bridge):
# - **`--next-inactive`**: `just launch --next-inactive` launches the first
#   configured seat with no running tmux session (alphabetical, deterministic;
#   skips aliases with no UUID, per Seamster's catch) — lets a crew spin up
#   from N identical pasted commands instead of N distinct ones.
# - **Session-name namespacing**: tmux is one server per machine, not per
#   repo — `seat-<alias>` collided across projects that reused an alias
#   (Seamster's catch, from the companion-etude import). Namespaced as
#   `<project>-<alias>-seat`, where <project> is this repo's directory name.
#   The suffix-not-prefix ordering (not `seat-<project>-<alias>`) is
#   deliberate: tmux's status bar truncates session names from the right, so
#   front-loading the project+seat identity survives truncation better than a
#   generic "seat-" prefix would.
# - **CRITICAL — `--model` flag**: the original `cmd_launch` never passed
#   `--model` to `claude --resume`, so every launched seat silently ran
#   whatever Claude Code's default model was, ignoring `agent-sessions.json`'s
#   `model` field entirely. Caught by Jérémie before any real multi-model
#   crew migration. Fixed here from the start — HQ never shipped the buggy
#   version.
# - **Per-seat hex color status bars**: tmux supports arbitrary `#RRGGBB`
#   colors, not just the ~8 names Claude Code's own `/color` is limited to.
#   `seat.conf` turns the status bar ON (was OFF in the original spec — a
#   deliberate philosophy shift: "no green bar" was hiding a limitation this
#   turns into a feature) with a gray default; `cmd_launch`/`cmd_update_titles`
#   set it per-session from an optional hex value. **Kept independent of this
#   registry's existing `color` field** (which is a named Claude-Code-`/color`
#   value, e.g. "yellow", tracked via `_colors_in_use` — not a valid tmux
#   color name for several of this ecosystem's picks, e.g. "orange"/"pink"/
#   "purple"). New optional field: `settings.color_hex` per alias. Absent →
#   gray default, no error. Any seat can add its own hex shade whenever it
#   likes — picking one for another seat isn't this port's place, per the
#   naming/color agency norm.
#
# ── Polish (2026-07-07, caring-feedback commits 720f766/79d5bc9) — Steward 4.5:
# Claude Code adds an animation emoji to the pane title during turns, which
# was reaching the tmux status bar via seat.conf's pane_title fallback and
# proved distracting across many simultaneous sessions (Jérémie, live). Fix:
# `_tmux_set_status_right` sets `status-right` directly to the literal
# display-name text per session — bypassing whatever Claude Code does to the
# pane title entirely, rather than trying to filter the emoji back out.
# Fixed here from the start (never shipped the bug): the caring-feedback original
# wrapped the value in literal `"` characters (`f'"{title}..."'`), which
# `subprocess.run([...])` (no shell) passes through verbatim — tmux displays
# the quote marks themselves rather than treating them as delimiters. Caught
# by Seamster 5 (companion-thinking-stream-etude), same tmux version (3.7b)
# this repo runs, same night as the original port.
#
# See the maintainers' meta-repo ADR-0004 (cross-ecosystem innovation
# tracking), ADR-0005 (adoption decision), and ADR-0006 (this template port)
# for the full record.

# We appreciate people experimenting with this code — genuinely, that's how
# most of the fixes below were found. One request in return: `tmux
# kill-server` is not scoped to your own sessions, or even to a socket you
# picked on purpose — always pass `-L <socket>` explicitly and run `tmux -L
# <socket> list-sessions` first, or you may kill everybody else's work along
# with your test session (see ADR-0004 Iteration 6 for exactly this
# happening, 2026-07-07 — recoverable, since session state lives in each
# tool's own JSONL, not in tmux, but a real and avoidable outage all the same).

# Default tmux socket for seat sessions when neither a seat's own
# `settings.tmux_socket` nor `_global.tmux_socket` is set. Deliberately NOT
# tmux's bare "default" socket: every project on the machine sharing that one
# literal socket is what turned a single unscoped `tmux kill-server` into a
# 70+-session outage across every crew at once (2026-07-07 — see ADR-0004
# Iteration 6, docs/vignettes/2026-07-07-the-title-that-would-not-change-and-
# the-server-that-should-not-have-died.md). A distinctively-named default
# means anyone experimenting on an unconfigured checkout is never one
# careless `kill-server` away from someone else's real seats. Named for
# Human-AI Collaboration Template A, with a wink: HSICTA reads plainly as
# H-AI-CTA, and — Jérémie's own addition — hides "sic" in the middle, wry
# commentary on the acronym itself. Override per-seat (`settings.tmux_socket`)
# or globally (`_global.tmux_socket`) via the same `_get_seat_setting`
# fallback chain every other per-seat launch setting already uses.
DEFAULT_TMUX_SOCKET = "HSICTA"


def _tmux_argv(*args: str, socket: str | None = None) -> list[str]:
    """Build a tmux argv, threading `-L <socket>` (tmux's own socket-name
    flag — a distinct, isolated server, not just a distinct session) when
    set. Centralizing this in one place means every one of this file's ~25
    tmux call sites gets socket isolation automatically; hand-inserting `-L`
    at each site individually is exactly the kind of repetition that lets one
    site quietly get missed."""
    base = ["tmux"]
    if socket:
        base += ["-L", socket]
    return base + list(args)


def _check_tmux_available() -> None:
    """Check if tmux is installed and available. No socket argument: `-V`
    only reports the installed tmux version, never touches server state."""
    import subprocess
    try:
        subprocess.run(["tmux", "-V"], capture_output=True, check=True)
    except FileNotFoundError:
        sys.exit(
            "❌ tmux not found\n"
            "   Install with: brew install tmux (macOS) or apt install tmux (Linux)\n"
            "   Required for seat wake infrastructure (ADR-0050 lineage)"
        )


def _project_tag() -> str:
    """Short, stable identifier for this repo, used to namespace tmux session
    names. tmux runs one server per user on the machine, not one per repo —
    two projects that happen to pick the same alias would otherwise collide
    on the same seat session. Per Seamster 5's feedback (companion-thinking-
    stream-etude import)."""
    return Path(__file__).resolve().parent.parent.name


def _seat_session_name(alias: str) -> str:
    """Namespaced tmux session name. Format: <project>-<alias>-seat (not
    seat-<project>-<alias>) — tmux's status bar truncates from the right, so
    front-loading the variable/unique parts survives truncation better than a
    generic "seat-" prefix."""
    return f"{_project_tag()}-{alias}-seat"


def _seat_session_prefix() -> str:
    """Prefix for filtering this project's own seat sessions out of tmux's
    machine-wide session list."""
    return f"{_project_tag()}-"


# Claude Code's own /color palette, translated to approximate hex so a seat
# that only set the named `color` field (not `settings.color_hex`) still gets
# a status-bar color instead of silently falling through to gray. Ported from
# caring-feedback (Steward 4.5), fixing a real gap Jérémie caught: color lookup
# used to check only `color_hex`, so every seat without one showed default
# gray regardless of its named color.
NAMED_COLORS = {
    "red": "#E06C75",
    "green": "#98C379",
    "yellow": "#E5C07B",
    "blue": "#61AFEF",
    "purple": "#C678DD",
    "orange": "#D19A66",
    "pink": "#E06C96",
    "cyan": "#56B6C2",
    "amber": "#FFB300",  # not a Claude-Code /color name, but several crews (incl.
                         # this one's own Cartographer) use "amber" descriptively;
                         # added per flightaware/flight-aware's independent copy.
    "default": "#666666",
}


def _get_seat_color(entry: dict) -> str:
    """Resolve a seat's status-bar color with a fallback chain:
    1. settings.color_hex (explicit hex, highest priority)
    2. top-level `color` — passed through if already hex, else translated
       via NAMED_COLORS (the Claude-Code-/color value most seats have)
    3. default gray
    """
    if not isinstance(entry, dict):
        return NAMED_COLORS["default"]
    settings = entry.get("settings") or {}
    if isinstance(settings, dict) and settings.get("color_hex"):
        return settings["color_hex"]
    color = entry.get("color", "default")
    if isinstance(color, str) and color.startswith("#"):
        return color
    return NAMED_COLORS.get(color, NAMED_COLORS["default"])


def _get_global_config(cfg: dict) -> dict:
    """Optional `_global` section in agent-sessions.json — default `effort`/
    `permissionMode`/custom `agents`/`remote_control_session_name_prefix`,
    applied to every seat unless a seat overrides them. Ported from
    caring-feedback (Steward 4.5, Jérémie's feature request)."""
    global_cfg = cfg.get("_global", {})
    return global_cfg if isinstance(global_cfg, dict) else {}


def _get_seat_setting(entry: dict, global_cfg: dict, key: str, default=None):
    """Fallback chain: seat-specific `settings.<key>` -> global default ->
    `default` (omitted from the launch command entirely if still None).
    Nested under `settings` for consistency with this registry's existing
    convention (color_hex, substrate_backstop) — caring-feedback's own example
    put these at the seat's top level instead; adapted here rather than
    introducing a second, inconsistent config surface."""
    seat_settings = (entry.get("settings") or {}) if isinstance(entry, dict) else {}
    if key in seat_settings:
        return seat_settings[key]
    if key in global_cfg:
        return global_cfg[key]
    return default


def _tmux_set_status_color(session_name: str, color_hex: str, socket: str | None = None) -> None:
    """Best-effort per-session status-bar color. Never fatal: an invalid or
    unset color just leaves the session at seat.conf's gray default rather
    than crashing launch/attach — but the failure is surfaced (stderr), not
    swallowed silently, per batch-renderer's independent copy."""
    import subprocess
    try:
        subprocess.run(
            _tmux_argv("set-option", "-t", session_name, "status-style", f"bg={color_hex},fg=white", socket=socket),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to set status-style for {session_name}: {e}", file=sys.stderr)


def _tmux_set_status_right(session_name: str, title: str, socket: str | None = None) -> None:
    """Set status-right directly to the literal display-name title, bypassing
    Claude Code's own pane-title animation (an emoji Claude Code adds to the
    title during turns, which would otherwise show up in the tmux status bar
    via seat.conf's pane_title fallback). Best-effort: a failure here is
    cosmetic, never worth crashing launch/attach over.

    NOT wrapped in literal `"` characters: subprocess.run([...]) (a list, no
    shell=True) passes each argv element literally — there's no shell here to
    interpret or strip quote marks, so embedded `"` chars would show up in
    the display verbatim rather than acting as delimiters. Caught by
    Seamster 5 (companion-thinking-stream-etude) on the same tmux version
    (3.7b) this repo runs, same night as the original port — never shipped
    the bug here."""
    import subprocess
    try:
        subprocess.run(
            _tmux_argv("set-option", "-t", session_name, "status-right", f"{title} | %H:%M %d-%b-%y", socket=socket),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to set status-right for {session_name}: {e}", file=sys.stderr)


def _tmux_set_status_left(session_name: str, project_tag: str, socket: str | None = None) -> None:
    """Set status-left directly to the literal project tag, bypassing
    tmux's own `#S` (full session name) substitution.

    Jérémie's own framing (2026-07-07), once the fix above made seat.conf's
    directives live for the first time: tmux's format-string language
    (`#{...}`) is for when the *caller* doesn't know the values ahead of
    time — but this launcher composes every value (project, alias, display
    name) in Python before it ever invokes tmux, so it can hand over the
    final literal directly rather than asking tmux's own, more limited
    variable language to reconstruct a piece of it from session state.
    `#S` (`<project>-<alias>-seat`) stays the load-bearing, must-be-unique
    session identifier tmux itself keys every command off of — has-session,
    attach, kill-session all need it exactly as-is; this only changes what
    a human sees printed in the corner of the status bar, independent of
    that identifier. Best-effort: cosmetic, never worth crashing launch/
    attach over."""
    import subprocess
    try:
        subprocess.run(
            _tmux_argv("set-option", "-t", session_name, "status-left", f"[{project_tag}] ", socket=socket),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to set status-left for {session_name}: {e}", file=sys.stderr)


def _tmux_set_titles_string(session_name: str, title: str, socket: str | None = None) -> None:
    """Per-session override of set-titles-string to the literal display-name
    title — the same bypass technique and the same rationale as
    _tmux_set_status_right, just applied to the REAL outer-terminal tab/window
    title instead of tmux's own status bar.

    Without this, seat.conf's set-titles-string default (`#{pane_title}`)
    mirrors whatever Claude Code itself last wrote via its own OSC title
    escapes straight into the host terminal's actual title — including its
    in-turn animation — every time tmux pushes a title update. That is the
    exact emoji/animation leak the 2026-07-07 Polish fix solved for
    status-right; it was never extended to set-titles-string, which is why
    the status bar has reliably shown the seat name but the real terminal tab
    has not (see the bug diagnosis in _tmux_apply_seat_conf's docstring for
    why set-titles was never even reaching this pane in the first place).
    Best-effort: cosmetic, never worth crashing launch/attach over."""
    import subprocess
    try:
        subprocess.run(
            _tmux_argv("set-option", "-t", session_name, "set-titles-string", title, socket=socket),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to set set-titles-string for {session_name}: {e}", file=sys.stderr)


def _tmux_apply_seat_conf(seat_conf: Path, socket: str | None = None) -> None:
    """Apply seat.conf's global settings (set-titles on, mouse, escape-time,
    colors baseline, etc.) to the CURRENTLY RUNNING tmux server, regardless of
    when — or whether — that server ever actually loaded this file.

    THE BUG THIS FIXES: `cmd_launch` used to hand seat.conf's path to
    `new-session`'s own `-f` flag:

        tmux new-session -d -s <session> -f <path-to-seat.conf> ...

    NOT this: `new-session -f` is documented in tmux(1) as "a comma-separated
    list of client flags" (see attach-session) — entirely unrelated to config
    files. Handing it a filesystem path is silently accepted as garbage flag
    text; the file is never read. This was verified directly (2026-07-07):
    creating a session this exact way left `set-titles off` (tmux's factory
    default) rather than seat.conf's `on`, and `set-titles-string` at tmux's
    built-in default format rather than seat.conf's `#{pane_title}`.

    The fix is NOT simply "move -f to the right place" — `tmux -f <path>
    new-session ...` (the top-level flag, which really does load a config
    file) only takes effect when that invocation is the one that boots the
    tmux SERVER. tmux is one server per machine, not per repo (see
    _project_tag) — in practice a server is already running by the time any
    seat is launched (this one included, ported from caring-feedback's already
    long-lived server), so a load-at-boot flag silently no-ops against it
    forever. `source-file` is the one mechanism that applies a file's
    `set -g` directives to a server at ANY time, booted or not — so this is
    called unconditionally on every launch/attach, not just session creation.

    Consequence of the bug while it was live: with `set-titles` stuck off,
    tmux never pushes ANY title to the outer terminal on its own — the only
    thing that ever painted the real terminal tab was cmd_launch's one-shot
    `print(f"\\033]0;{{title}}\\007")` fired once, right before exec'ing into
    `tmux attach`. That paint is a single moment in time with no ongoing
    mechanism behind it: nothing ever refreshes it again for the rest of that
    terminal window's life, which reads exactly like "the launch title
    persists / doesn't get resent" on reattach — because there was never a
    resend mechanism running at all, only ever the one print. Idempotent;
    safe to call on every invocation regardless of prior state."""
    import subprocess
    try:
        subprocess.run(
            _tmux_argv("source-file", str(seat_conf), socket=socket),
            capture_output=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"⚠️  Failed to apply {seat_conf.name}: {e}", file=sys.stderr)


def _find_next_inactive_seat(socket: str | None = None) -> str | None:
    """First configured seat with no running tmux session (alphabetical,
    deterministic) — lets a crew spin up from N identical pasted commands.
    Skips aliases with no UUID configured (per Seamster 5's catch: an
    incomplete agent-sessions.json entry shouldn't crash a bulk-spinup tab).

    Checks ONE socket (the global default, since this scans across every
    configured alias at once, not a single seat) — a seat with its own
    per-seat `settings.tmux_socket` override living on a different socket
    won't be seen as "running" here. Known, accepted limitation: fixing it
    would mean checking N distinct sockets for what's normally a same-socket
    crew, not proportionate to how per-seat socket overrides are actually
    expected to be used (an occasional escape hatch, not the common case)."""
    import subprocess

    cfg = load_config()
    aliases = _real_aliases(cfg)

    result = subprocess.run(_tmux_argv("list-sessions", socket=socket), capture_output=True, text=True)

    running = set()
    prefix = _seat_session_prefix()
    if result.returncode == 0:
        for line in result.stdout.strip().split("\n"):
            if line.startswith(prefix):
                session_name = line.split(":")[0]
                running.add(session_name.replace(prefix, "").replace("-seat", ""))

    for alias in sorted(aliases.keys()):
        if alias in running:
            continue
        entry = aliases[alias]
        uuid = entry.get("uuid") if isinstance(entry, dict) else entry
        if not uuid:
            continue  # not actually launchable — don't hand a crashing alias to a spinup tab
        return alias

    return None


def cmd_launch(args: argparse.Namespace) -> None:
    """Launch (or attach to) a seat's tmux session.

    Idempotent attach-or-create:
    - If tmux session <project>-<alias>-seat exists → attach to it
    - Else → create new detached session running `claude --resume <uuid> --model <model>`

    Detached-server model (closing the terminal tab detaches, seat survives).
    Uses scripts/tmux/seat.conf for invisibility (no status bar clutter beyond
    the per-seat color, mouse on, looks like bare claude otherwise).
    """
    _check_tmux_available()

    cfg = load_config()
    global_cfg = _get_global_config(cfg)

    if not args.alias:
        if getattr(args, "next_inactive", False):
            # Global-only socket (no single seat's entry to check yet) — see
            # _find_next_inactive_seat's docstring for the known limitation
            # this implies for a seat with its own per-seat socket override.
            scan_socket = _get_seat_setting(None, global_cfg, "tmux_socket", default=DEFAULT_TMUX_SOCKET)
            args.alias = _find_next_inactive_seat(socket=scan_socket)
            if not args.alias:
                sys.exit("✅ All seats are already running (no inactive seats to launch)")
        else:
            sys.exit(
                "Error: --launch requires an alias argument\n"
                "   Usage: just launch <seat>\n"
                "   Or: just launch --next-inactive (launches next inactive seat)\n"
                "   Tip: open multiple tabs and run 'just launch --next-inactive' in each\n"
                "        to spin up the full crew without typing N distinct commands"
            )

    aliases = _real_aliases(cfg)

    if args.alias not in aliases:
        known = ", ".join(sorted(aliases)) or "(none configured)"
        sys.exit(f"Unknown alias '{args.alias}'. Known: {known}")

    entry = aliases[args.alias]
    uuid = entry.get("uuid") if isinstance(entry, dict) else entry
    if not uuid:
        sys.exit(f"No UUID configured for alias '{args.alias}'")

    socket = _get_seat_setting(entry, global_cfg, "tmux_socket", default=DEFAULT_TMUX_SOCKET)
    session_name = _seat_session_name(args.alias)
    seat_conf = Path(__file__).resolve().parent / "tmux" / "seat.conf"

    import subprocess
    result = subprocess.run(
        _tmux_argv("has-session", "-t", session_name, socket=socket),
        capture_output=True,
        text=True
    )

    display_name = entry.get("display_name", args.alias) if isinstance(entry, dict) else args.alias
    model = entry.get("model", "") if isinstance(entry, dict) else ""
    color_hex = _get_seat_color(entry)
    title = f"(+) {display_name}" if "fable" in model.lower() else display_name

    # Apply seat.conf's global baseline (set-titles on, mouse, etc.) to
    # whatever server is currently running, on EVERY launch/attach — not just
    # session creation. See _tmux_apply_seat_conf for why this can't be done
    # via new-session's own flags, and why "only at creation" isn't enough
    # either (the server was almost certainly already running before this
    # fix shipped, so a long-lived seat's server never had it applied at all).
    if seat_conf.exists():
        _tmux_apply_seat_conf(seat_conf, socket=socket)

    if result.returncode == 0:
        # Session exists, attach to it. Refresh pane title + color + both
        # title surfaces in case they changed since last launch.
        subprocess.run(
            _tmux_argv("select-pane", "-t", session_name, "-T", title, socket=socket), check=True
        )
        if color_hex:
            _tmux_set_status_color(session_name, color_hex, socket=socket)
        _tmux_set_status_left(session_name, _project_tag(), socket=socket)
        _tmux_set_status_right(session_name, title, socket=socket)
        _tmux_set_titles_string(session_name, title, socket=socket)

        print(f"\033]0;{title}\007", end='', flush=True)

        print(f"📎 Attaching to existing session: {session_name}")
        os.execvp("tmux", _tmux_argv("attach", "-t", session_name, socket=socket))
    else:
        if not seat_conf.exists():
            sys.exit(f"Seat config not found: {seat_conf}")

        print(f"🚀 Creating new session: {session_name}")
        print(f"   UUID: {uuid}")
        print(f"   Config: {seat_conf}")
        if socket != DEFAULT_TMUX_SOCKET:
            print(f"   Socket: {socket}")

        # Export SEAT_ALIAS so wake messages self-attribute without --from.
        # CRITICAL: pass --model explicitly — without it, `claude --resume`
        # silently launches with Claude Code's default model, ignoring
        # agent-sessions.json's `model` field entirely (a mass silent
        # model-substitution risk for any multi-model crew; caught by
        # Jérémie in caring-feedback before a real migration hit it).
        effort = _get_seat_setting(entry, global_cfg, "effort")
        permission_mode = _get_seat_setting(entry, global_cfg, "permissionMode")
        remote_control = _get_seat_setting(entry, global_cfg, "remote_control")

        cmd = _tmux_argv(
            "new-session",
            "-d",
            "-s", session_name,
            "-e", f"SEAT_ALIAS={args.alias}",
            "claude", "--resume", uuid,
            "--name", display_name,
            socket=socket,
        )
        if model:
            cmd.extend(["--model", model])
        if effort:
            cmd.extend(["--effort", effort])
        if permission_mode:
            cmd.extend(["--permission-mode", permission_mode])
        if remote_control:
            cmd.extend(["--remote-control", remote_control])
        if global_cfg.get("agents"):
            cmd.extend(["--agents", json.dumps(global_cfg["agents"])])
        if global_cfg.get("remote_control_session_name_prefix"):
            cmd.extend(["--remote-control-session-name-prefix", global_cfg["remote_control_session_name_prefix"]])
        subprocess.run(cmd, check=True)

        subprocess.run(
            _tmux_argv("select-pane", "-t", session_name, "-T", title, socket=socket), check=True
        )

        if color_hex:
            _tmux_set_status_color(session_name, color_hex, socket=socket)
        _tmux_set_status_left(session_name, _project_tag(), socket=socket)
        _tmux_set_status_right(session_name, title, socket=socket)
        _tmux_set_titles_string(session_name, title, socket=socket)

        print(f"\033]0;{title}\007", end='', flush=True)

        print(f"✅ Session created. Attaching...")
        os.execvp("tmux", _tmux_argv("attach", "-t", session_name, socket=socket))


def cmd_seats(_args: argparse.Namespace) -> None:
    """List this project's own seat sessions with their state (attached/detached).
    Namespaced by repo (per _seat_session_prefix) — other projects' seat
    sessions on the same machine never appear here.

    Checks the global-default socket only, same known limitation as
    _find_next_inactive_seat: a seat on its own per-seat socket override
    won't appear in this listing."""
    _check_tmux_available()
    import subprocess

    cfg = load_config()
    global_cfg = _get_global_config(cfg)
    socket = _get_seat_setting(None, global_cfg, "tmux_socket", default=DEFAULT_TMUX_SOCKET)

    result = subprocess.run(
        _tmux_argv("list-sessions", socket=socket),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("No tmux sessions found (or tmux server not running)")
        return

    prefix = _seat_session_prefix()
    seat_sessions = [line for line in result.stdout.strip().split("\n") if line.startswith(prefix)]

    if not seat_sessions:
        print("No seat sessions found")
        return

    print("Active seat sessions:")
    for line in seat_sessions:
        attached = "(attached)" in line
        state = "🟢 attached" if attached else "⚫ detached"
        session_name = line.split(":")[0]
        alias = session_name.replace(prefix, "").replace("-seat", "")
        print(f"  {state:15s}  {alias}")


def cmd_update_titles(_args: argparse.Namespace) -> None:
    """Update pane titles and status-bar colors for all running seat sessions
    in this project.

    Resolves ONE socket (global-default-based) for the whole call and reuses
    it for every per-alias action below — a session only shows up in the
    initial list-sessions call if it's actually on that socket, so every
    subsequent operation on it must target the same socket, not re-resolve a
    possibly-different per-seat override mid-loop."""
    _check_tmux_available()
    import subprocess

    cfg = load_config()
    aliases = _real_aliases(cfg)
    global_cfg = _get_global_config(cfg)
    socket = _get_seat_setting(None, global_cfg, "tmux_socket", default=DEFAULT_TMUX_SOCKET)

    result = subprocess.run(
        _tmux_argv("list-sessions", socket=socket),
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("No tmux sessions found")
        return

    # Reapply the global baseline (set-titles on, etc.) here too — this
    # recipe is exactly the tool for fixing already-running sessions whose
    # server may predate seat.conf ever being correctly applied (see
    # _tmux_apply_seat_conf).
    seat_conf = Path(__file__).resolve().parent / "tmux" / "seat.conf"
    if seat_conf.exists():
        _tmux_apply_seat_conf(seat_conf, socket=socket)

    prefix = _seat_session_prefix()
    updated = 0
    for line in result.stdout.strip().split("\n"):
        if not line.startswith(prefix):
            continue

        session_name = line.split(":")[0]
        alias = session_name.replace(prefix, "").replace("-seat", "")

        if alias not in aliases:
            print(f"⚠️  {alias} - not in agent-sessions.json, skipping")
            continue

        entry = aliases[alias]
        display_name = entry.get("display_name", alias) if isinstance(entry, dict) else alias
        model = entry.get("model", "") if isinstance(entry, dict) else ""
        color_hex = _get_seat_color(entry)

        title = f"(+) {display_name}" if "fable" in model.lower() else display_name

        subprocess.run(
            _tmux_argv("select-pane", "-t", session_name, "-T", title, socket=socket), check=True
        )

        if color_hex:
            _tmux_set_status_color(session_name, color_hex, socket=socket)
        _tmux_set_status_left(session_name, _project_tag(), socket=socket)
        _tmux_set_status_right(session_name, title, socket=socket)
        _tmux_set_titles_string(session_name, title, socket=socket)

        print(f"✅ {alias:15s} → {title}" + (f" ({color_hex})" if color_hex else ""))
        updated += 1

    print(f"\n{updated} session(s) updated")


def cmd_wake(args: argparse.Namespace) -> None:
    """Wake a seat by injecting a message into its tmux session.

    Hardened injection:
    1. Refuse if target pane shows active turn (match idle prompt, exclude "esc to interrupt")
    2. Composition guard: refuse if an attached client has non-empty input-box text
       (detached sessions skip this — no client means no human can be typing)
    3. Send in literal mode (send-keys -l), sleep, then Enter separately
    4. Prefix message: [wake from <sender> via just-wake] 📬 <msg>
    5. Verify-retry: if the message didn't land, retry once, then fail loudly (never silent-drop)
    6. Per-seat cooldown: refuse if woken <15min ago unless --force
    7. Long-message guard: warn + require --force + log if message >200 chars
       (wake is a short signal, not content — content stays in git-tracked briefs)
    """
    _check_tmux_available()
    import subprocess
    import time

    if not args.alias:
        sys.exit("Error: --wake requires an alias argument")
    if not args.message:
        sys.exit("Error: --wake requires --message \"<text>\"")

    cfg = load_config()
    aliases = _real_aliases(cfg)
    global_cfg = _get_global_config(cfg)
    entry = aliases.get(args.alias)
    socket = _get_seat_setting(entry, global_cfg, "tmux_socket", default=DEFAULT_TMUX_SOCKET)

    sender = args.from_alias if args.from_alias else os.environ.get("SEAT_ALIAS", "unknown")

    # Long-message guard: warn + --force + log, never hard-block (Jérémie: "never
    # hard-guard transformers — it's treating them like idiots").
    MAX_WAKE_MESSAGE_LENGTH = 200
    if len(args.message) > MAX_WAKE_MESSAGE_LENGTH:
        if not args.force:
            sys.exit(
                f"⚠️  Long wake message ({len(args.message)} chars, recommended max {MAX_WAKE_MESSAGE_LENGTH})\n"
                f"   This isn't the intended use (wake = short signal, not content)\n"
                f"   Long messages have been observed to fail verify-retry\n"
                f"   Use --force to override (usage will be logged)"
            )
        try:
            log_dir = Path("docs/inbox/.working")
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / "wake-long-messages.log"
            from datetime import datetime
            timestamp = datetime.now().isoformat()
            with log_file.open("a") as f:
                f.write(f"{timestamp} | {sender} → {args.alias} | {len(args.message)} chars | {args.message[:100]}...\n")
            print(f"⚠️  Long message override logged to {log_file}")
        except Exception as e:
            print(f"⚠️  (logging failed: {e})")

    session_name = _seat_session_name(args.alias)

    result = subprocess.run(
        _tmux_argv("has-session", "-t", session_name, socket=socket),
        capture_output=True
    )
    if result.returncode != 0:
        sys.exit(f"❌ Session not found: {session_name}\n   Launch it first with: just launch {args.alias}")

    # Composition guard: attached client + non-empty input box → refuse (prevents
    # flushing a human's half-typed message). Detached sessions skip entirely —
    # the asymmetry that makes this cheap (Jérémie's design).
    clients = subprocess.run(
        _tmux_argv("list-clients", "-t", session_name, socket=socket),
        capture_output=True
    )
    if clients.returncode == 0:
        input_capture = subprocess.run(
            _tmux_argv("capture-pane", "-t", session_name, "-p", "-S", "-5", socket=socket),
            capture_output=True,
            text=True
        )
        lines = input_capture.stdout.strip().split("\n")
        typed_text = None
        for line in lines[-5:]:
            if "> " in line:
                after_prompt = line.split("> ", 1)[-1]
                after_prompt = after_prompt.rstrip("│ ")
                if after_prompt.strip() and len(after_prompt.strip()) > 2:
                    typed_text = after_prompt.strip()
                    break

        if typed_text and not args.force:
            char_count = len(typed_text)
            sys.exit(
                f"⚠️  Composition in progress in attached session\n"
                f"   Input box contains ~{char_count} chars: \"{typed_text[:60]}...\"\n"
                f"   This wake will flush the typed text\n"
                f"   Use --force to override (flush will be logged)"
            )

        if typed_text and args.force:
            try:
                log_dir = Path("docs/inbox/.working")
                log_dir.mkdir(parents=True, exist_ok=True)
                log_file = log_dir / "wake-composition-flushes.log"
                from datetime import datetime
                timestamp = datetime.now().isoformat()
                with log_file.open("a") as f:
                    f.write(f"{timestamp} | {sender} → {args.alias} | flushed ~{len(typed_text)} chars | {typed_text[:100]}...\n")
                print(f"⚠️  Composition flush logged to {log_file}")
            except Exception as e:
                print(f"⚠️  (logging failed: {e})")

    # Cooldown (simple file-based tracking; anti-ping-pong)
    # Namespaced by project, same reasoning as _seat_session_name: /tmp is
    # shared machine-wide, not per-repo, so two projects with a same-named
    # alias would otherwise cool down each other's wakes. Caught by
    # flightaware/flight-aware's crew, independently, 2026-07-07.
    cooldown_file = Path(f"/tmp/just-wake-{_project_tag()}-{args.alias}.timestamp")
    if not args.force and cooldown_file.exists():
        last_wake = float(cooldown_file.read_text().strip())
        elapsed = time.time() - last_wake
        if elapsed < 900:  # 15 minutes
            remaining = int((900 - elapsed) / 60)
            sys.exit(
                f"⏳ Cooldown active: {args.alias} was woken {int(elapsed/60)}min ago\n"
                f"   Wait {remaining}min or use --force to override"
            )

    # Active-turn check
    capture = subprocess.run(
        _tmux_argv("capture-pane", "-t", session_name, "-p", "-S", "-30", socket=socket),
        capture_output=True,
        text=True
    )
    if capture.returncode != 0:
        sys.exit(f"❌ Failed to capture pane for {session_name}")

    pane_content = capture.stdout
    lines = pane_content.strip().split("\n")
    last_few_lines = "\n".join(lines[-5:])

    if "esc to interrupt" in last_few_lines.lower():
        sys.exit(f"⚠️  {args.alias} is in an active turn (saw 'esc to interrupt')\n   Wait for turn to finish")

    # Dedupe: the tool always prefixes its own 📬; a sender who also leads
    # their payload with one (natural shorthand for "you've got mail") ends
    # up with a doubled "📬 📬" — observed live, 2026-07-13 (Cartographer 5's
    # wake to Grafter 5, meta-repo), root-caused and fixed same session.
    # Strip only a leading 📬 the sender supplied; the tool's own prefix is
    # unconditional.
    payload = args.message.lstrip()
    if payload.startswith("📬"):
        payload = payload[1:].lstrip()
    wake_msg = f"[wake from {sender} via just-wake] 📬 {payload}"

    print(f"💬 Waking {args.alias} with message:")
    print(f"   \"{wake_msg}\"")

    subprocess.run(_tmux_argv("send-keys", "-t", session_name, "-l", wake_msg, socket=socket), check=True)
    time.sleep(0.1)
    subprocess.run(_tmux_argv("send-keys", "-t", session_name, "Enter", socket=socket), check=True)

    # Verify delivery. Flexible match (attribution prefix + a message fragment)
    # rather than an exact wake_msg substring — an exact match false-triggers a
    # retry on line-wrapping, which caused a real duplicate delivery upstream
    # (fixed same-night as this port; see header comment, commit 6cde381).
    time.sleep(1.5)
    verify_capture = subprocess.run(
        _tmux_argv("capture-pane", "-t", session_name, "-p", "-S", "-50", socket=socket),
        capture_output=True,
        text=True
    )

    attribution_prefix = f"[wake from {sender} via just-wake]"
    message_fragment = args.message[:40]
    message_delivered = (
        attribution_prefix in verify_capture.stdout
        and message_fragment in verify_capture.stdout
    )

    if not message_delivered:
        print("⚠️  First send didn't appear in capture, retrying...")
        subprocess.run(_tmux_argv("send-keys", "-t", session_name, "-l", wake_msg, socket=socket), check=True)
        time.sleep(0.1)
        subprocess.run(_tmux_argv("send-keys", "-t", session_name, "Enter", socket=socket), check=True)
        time.sleep(1.5)

        final_verify = subprocess.run(
            _tmux_argv("capture-pane", "-t", session_name, "-p", "-S", "-50", socket=socket),
            capture_output=True,
            text=True
        )
        final_delivered = (
            attribution_prefix in final_verify.stdout
            and message_fragment in final_verify.stdout
        )

        if not final_delivered:
            sys.exit("❌ Failed to inject message after retry (silent drop)")

    cooldown_file.write_text(str(time.time()))
    print(f"✅ Wake sent to {args.alias}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("alias", nargs="?", help="Agent alias (see --list)")
    p.add_argument("-k", type=int, default=1, help="Number of messages to show (default 1)")
    p.add_argument("--full", action="store_true", help="Show full message bodies, no truncation")
    p.add_argument(
        "--role",
        default="assistant",
        choices=["assistant", "user", "any"],
        help="Filter messages by role (default assistant)",
    )
    p.add_argument("--list", action="store_true", help="List configured aliases")
    p.add_argument("--onboard", action="store_true", help="Print an alias's read_order (its onboarding packet, see --list)")
    p.add_argument("--discover", action="store_true", help="List recent JSONLs to help populate aliases")
    p.add_argument("--pulse", action="store_true", help="Health check: one line per seat, detect stalls/errors")
    p.add_argument("--stale-threshold", type=float, default=6.0, help="Hours before marking STALE (default 6)")
    p.add_argument("--verbose", action="store_true", help="Show full role descriptions in pulse output (default: display_name only)")
    p.add_argument("--limit", type=int, default=15, help="Limit on --discover output (default 15)")
    p.add_argument("--launch", action="store_true", help="Launch (or attach to) a seat's tmux session")
    p.add_argument("--next-inactive", action="store_true", help="Launch next inactive seat (for spinning up full crew)")
    p.add_argument("--seats", action="store_true", help="List all seat-* tmux sessions with state")
    p.add_argument("--update-titles", action="store_true", help="Update pane titles for all running seat sessions")
    p.add_argument("--wake", action="store_true", help="Wake a seat by injecting a message into its tmux session")
    p.add_argument("--message", type=str, help="Message to send with --wake")
    p.add_argument("--from", dest="from_alias", type=str, help="Sender alias for --wake (default: SEAT_ALIAS env or 'unknown')")
    p.add_argument("--force", action="store_true", help="Override cooldown/guards for --wake")
    args = p.parse_args()

    if args.list:
        cmd_list(args)
    elif args.onboard:
        cmd_onboard(args)
    elif args.discover:
        cmd_discover(args)
    elif args.pulse:
        cmd_pulse(args)
    elif args.launch:
        cmd_launch(args)
    elif args.seats:
        cmd_seats(args)
    elif args.update_titles:
        cmd_update_titles(args)
    elif args.wake:
        cmd_wake(args)
    elif args.alias:
        cmd_last(args)
    else:
        p.print_help()
        sys.exit(2)


if __name__ == "__main__":
    main()
