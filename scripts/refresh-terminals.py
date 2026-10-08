#!/usr/bin/env python3
"""
refresh-terminals.py — Generate .vscode/terminals.json from the crew registry.

Why this exists
---------------

`temp/vscode-terminals` (fabiospampinato/vscode-terminals, "Terminals Manager")
opens N configured terminals from one VS Code command ("Terminals: Run"). This
script generates its config from the single source of truth this ecosystem
already has — `docs/inbox/agent-sessions.json` — so the crew manifest never
drifts out of sync with the registry, and a full-crew relaunch (e.g. after a
tmux-kill-class event) is one generated file plus one VS Code command instead
of remembering every alias by hand.

See docs/adr/0008-rapid-relaunch-via-vscode-terminals-manager.md for the full
design record, including why this deliberately does NOT use the extension's
own `persistent`/`multiplexer: "tmux"` fields (bare `tmux new -s`, no `-L`
socket, no seat.conf — the exact unhardened pattern ADR-0004 Iteration 6 just
fixed). Every generated terminal's command is `just launch <alias>` instead —
reusing the already-hardened launcher rather than duplicating a weaker one.

Two modes, two ideas of "safe" (ADR-0008 Iterations 5–6)
---------------------------------------------------------

Jérémie's spec has two distinct mechanics, and they are MODES of one
command, not alternatives:

  (B) `just refresh-terminals`        — DEFAULT: top-up. Open only seats
      with no pane currently open. Everyday use; running it twice in a row
      is a no-op the second time. "Idempotent" in the sense users mean it:
      no duplicates.
  (A) `just refresh-terminals --all`  — recovery: open EVERY launchable
      seat, unconditionally. For after a wipe (e.g. a tmux-kill-class
      event) or a fresh machine. Running it against live seats opens
      harmless second clients on the same tmux sessions — duplicates by
      design, announced in the output.

Two independent safety layers, which earlier iterations conflated:

1. INJECTION-proofing (Iteration 5, kept in both modes): the extension's
   own `getTerminalByName` cache lookup (`src/runner.ts`) could `sendText`
   a launch command straight into an already-open pane — a running Claude
   Code session reads that as a chat turn. Fixed at the root: every entry's
   `target` is a per-run nonce that can never match a real pane's name, so
   the extension always creates a fresh terminal. `dynamicTitle: true`
   leaves the visible label to tmux's title-setting (ADR-0004 Iter 6).
2. DUPLICATE-avoidance (Iteration 6, the default mode): detection via
   `has_conflicting_open_pane` (attached-client + fuzzy-title, read-only)
   filters out seats that are already open. Iteration 5's root-cause fix
   made this unnecessary *as an injection guard* and it was briefly deleted
   on that reasoning — but it was never only a guard: it is the user-facing
   top-up semantics. Restored as the default mode's filter.

Usage
-----

    just refresh-terminals            # (B) top-up: only seats not already open
    just refresh-terminals --all      # (A) everyone: full-crew relaunch
    python3 scripts/refresh-terminals.py [--all]

Ordering
--------

`.vscode/terminals.txt` gives a partial order: one alias per line (bullets,
`#`-comments, and surrounding whitespace all tolerated), top to bottom.
Aliases not listed there come after, alphabetically. Auto-created (in
alphabetical order) on first run if it doesn't exist yet — a real,
persistent, hand-editable file, not just a fallback default: rearrange it
freely and the order sticks across every future regeneration, unlike
terminals.json itself, which is fully regenerated every run.

Origin
------

Herald 5 (Claude Sonnet 5), 2026-07-07, per Jérémie's spec (docs/adr/0008).
"""

from __future__ import annotations

import argparse
import colorsys
import importlib.util
import json
import math
import re
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TERMINALS_TXT = REPO_ROOT / ".vscode" / "terminals.txt"
TERMINALS_JSON = REPO_ROOT / ".vscode" / "terminals.json"

# ─── Reuse last-message.py's own registry/color logic rather than
# re-deriving it — a dash in the filename makes it an invalid module name for
# a normal `import`, so it's loaded by path instead. Keeps color resolution
# (settings.color_hex → named color → gray) identical to what the tmux
# status bar already shows for the same seat. ────────────────────────────────
_LM_PATH = REPO_ROOT / "scripts" / "last-message.py"
_spec = importlib.util.spec_from_file_location("last_message", _LM_PATH)
last_message = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(last_message)

ICON = "robot"  # Confirmed present in VS Code's bundled @vscode/codicons set.
MAX_DESCRIPTION_LENGTH = 100

# VS Code's default Dark+ terminal ANSI colors — the canonical reference this
# script quantizes every seat's hex color against. `color` (both the
# extension's field and VS Code's own TerminalOptions.color) only accepts one
# of these theme-color IDs, not an arbitrary hex string, unlike tmux's
# status-bar color. A user on a different color theme will see a technically
# different (but still reasonably close) rendered color than the hex being
# matched — a known, documented simplification (ADR-0008), not something
# solvable without introspecting the live theme at generation time.
VSCODE_DARK_ANSI = {
    "Black": "#000000",
    "Red": "#cd3131",
    "Green": "#0dbc79",
    "Yellow": "#e5e510",
    "Blue": "#2472c8",
    "Magenta": "#bc3fbc",
    "Cyan": "#11a8cd",
    "White": "#e5e5e5",
    "BrightBlack": "#666666",
    "BrightRed": "#f14c4c",
    "BrightGreen": "#23d18b",
    "BrightYellow": "#f5f543",
    "BrightBlue": "#3b8eea",
    "BrightMagenta": "#d670d6",
    "BrightCyan": "#29b8db",
    "BrightWhite": "#e5e5e5",
}


# The 6 chromatic ANSI hues, as hue angles in degrees — each has a "regular"
# and "Bright" variant in VSCODE_DARK_ANSI. Grayscale (Black/BrightBlack/
# White/BrightWhite) is matched separately, by value only, below.
_HUE_ANCHORS_DEG = {
    "Red": 0.0,
    "Yellow": 60.0,
    "Green": 120.0,
    "Cyan": 180.0,
    "Blue": 240.0,
    "Magenta": 300.0,
}

# (name, reference value) pairs for the grayscale match. VS Code's own
# default palette has White == BrightWhite (both #e5e5e5) — not a bug here,
# just how that reference palette is defined.
_GRAYSCALE_BY_VALUE = [
    ("Black", 0.0),
    ("BrightBlack", 0.4),
    ("White", 0.90),
    ("BrightWhite", 0.90),
]

SATURATION_GRAYSCALE_THRESHOLD = 0.15


def _hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return (int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16))


def _hue_distance(h1: float, h2: float) -> float:
    d = abs(h1 - h2) % 360
    return min(d, 360 - d)


def quantize_to_ansi_theme_color(hex_color: str) -> str:
    """Nearest `terminal.ansi*` theme-color ID to an arbitrary hex color.

    Hue-first, not raw RGB/redmean distance. A first version of this function
    used redmean (a well-known, cheap RGB-distance approximation) and it was
    wrong in an embarrassing, very visible way: a plain distance metric lets
    darkness swamp hue, which is exactly backwards for a seat-identity color.
    Herald's own color (#66023C, Tyrian purple — hue ≈325°, but only V=0.40,
    fairly dark) came back as "terminal.ansiBlack"; Naturalist's viridian
    (#40826D, hue ≈161°, V=0.51) came back as "terminal.ansiBrightBlack" —
    both numerically defensible under raw distance, both unmistakably wrong
    to a human eye, caught by actually reading this file's own first
    generated output rather than trusting the math blind. Fixed before
    either shipped anywhere.

    Grayscale colors (low saturation) are matched by value only, against
    Black/BrightBlack/White/BrightWhite. Everything else is matched by hue to
    the nearest of the 6 chromatic anchors, then the Bright/regular variant is
    picked by whichever's own value is closer to the target's — preserving
    hue exactly, brightness approximately.
    """
    r, g, b = _hex_to_rgb(hex_color)
    hue, sat, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
    hue_deg = hue * 360

    if sat < SATURATION_GRAYSCALE_THRESHOLD:
        best_name, best_dist = None, math.inf
        for name, ref_val in _GRAYSCALE_BY_VALUE:
            dist = abs(val - ref_val)
            if dist < best_dist:
                best_dist, best_name = dist, name
        return f"terminal.ansi{best_name}"

    best_hue_name, best_hue_dist = None, math.inf
    for name, anchor in _HUE_ANCHORS_DEG.items():
        dist = _hue_distance(hue_deg, anchor)
        if dist < best_hue_dist:
            best_hue_dist, best_hue_name = dist, name

    def _value_of(hex_ref: str) -> float:
        rr, gg, bb = _hex_to_rgb(hex_ref)
        return colorsys.rgb_to_hsv(rr / 255, gg / 255, bb / 255)[2]

    regular_val = _value_of(VSCODE_DARK_ANSI[best_hue_name])
    bright_val = _value_of(VSCODE_DARK_ANSI[f"Bright{best_hue_name}"])
    variant = best_hue_name if abs(val - regular_val) <= abs(val - bright_val) else f"Bright{best_hue_name}"

    return f"terminal.ansi{variant}"


def truncate_description(role: str) -> str:
    """Strip the "<DisplayName> — <Model>. " prefix every role in this
    registry starts with (redundant with the terminal's own `name` field),
    then hard-cap to MAX_DESCRIPTION_LENGTH. Falls through gracefully to a
    plain truncation if a role doesn't match the expected prefix shape."""
    stripped = re.sub(r"^.+? — .+?\.\s+", "", role, count=1)
    text = stripped if stripped != role or " — " not in role else role
    if len(text) > MAX_DESCRIPTION_LENGTH:
        text = text[: MAX_DESCRIPTION_LENGTH - 1].rstrip() + "…"
    return text


def parse_ordering_file(path: Path) -> list[str]:
    """Parse `.vscode/terminals.txt`: one alias per line, bullets/whitespace
    tolerant. Returns aliases in file order (lowercased); blank lines,
    `#`-comments, and common bullet markers (-, *, +, "1.", "1)") are
    stripped."""
    if not path.exists():
        return []
    order = []
    bullet_re = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s*")
    for raw_line in path.read_text().splitlines():
        line = bullet_re.sub("", raw_line).strip()
        if not line or line.startswith("#"):
            continue
        order.append(line.lower())
    return order


def ensure_ordering_file(path: Path, all_aliases: list[str]) -> None:
    """Create `.vscode/terminals.txt` (alphabetical order of every
    launchable seat) if it doesn't exist yet — a real, persistent,
    hand-editable file Jérémie can freely rearrange, not just an implied
    fallback that only ever exists in code. Represents the FULL crew's
    preferred order regardless of any single run's `--only-closed` filter —
    "in what order do my seats appear," independent of who's up right now.
    Never overwrites an existing file — once created, it's yours to edit;
    regeneration only ever touches terminals.json, never this."""
    if path.exists():
        return
    header = (
        "# Seat launch order for `just refresh-terminals` — one alias per line.\n"
        "# Rearrange freely; lines are read top to bottom. Aliases not listed\n"
        "# here (e.g. a newly-registered seat) are appended after, alphabetically.\n"
        "# This file is yours — regeneration only ever touches terminals.json.\n"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(header + "\n".join(sorted(all_aliases)) + "\n")
    print(f"✅ Created {path.relative_to(REPO_ROOT)} (alphabetical) — rearrange it freely, it's never auto-overwritten.")


def resolve_order(aliases: dict, ordering_file: Path, registered_aliases: set[str] | None = None) -> list[str]:
    """Full launch order: `terminals.txt`'s partial order first (genuinely
    unknown aliases warned about and skipped, never fatal), then every
    remaining alias in `aliases`, alphabetically.

    `registered_aliases` (defaults to `aliases.keys()` for backward compat)
    is the FULL set of real, registered aliases — used only to decide
    whether to warn. Without it, calling this with a `--only-closed`-
    filtered `aliases` dict misfires "unknown alias" for every seat that's
    simply excluded THIS run (already has a pane open), not actually
    unregistered — a real bug caught the first time `--only-closed` ran
    against terminals.txt (2026-07-07): every seat was live, so `aliases`
    was empty, and all six real, registered names got flagged as
    "unknown.\""""
    listed = parse_ordering_file(ordering_file)
    included = set(aliases.keys())
    known = registered_aliases if registered_aliases is not None else included

    ordered: list[str] = []
    seen: set[str] = set()
    for alias in listed:
        if alias not in known:
            print(f"⚠️  {ordering_file.name}: unknown alias '{alias}', skipping", file=sys.stderr)
            continue
        if alias not in included or alias in seen:
            continue
        ordered.append(alias)
        seen.add(alias)

    remainder = sorted(a for a in included if a not in seen)
    ordered.extend(remainder)

    return ordered


def titles_fuzzy_match(candidate: str, display_name: str) -> bool:
    """Whether `candidate` (an actual, possibly-decorated pane title) refers
    to the same seat as `display_name` — tolerant of decoration
    (`cmd_launch`'s own `"(+) "` Fable-model prefix, an emoji, stray
    punctuation) but not of a genuinely different name.

    Jérémie's own heuristic (2026-07-07 correction): the candidate must
    contain the display name in full; whatever's left after removing it must
    contain no more than one run of alphabetic characters — i.e. only
    decoration survives the subtraction, not another real word."""
    if display_name not in candidate:
        return False
    remainder = candidate.replace(display_name, "", 1)
    alphabetic_runs = re.findall(r"[A-Za-z]+", remainder)
    return len(alphabetic_runs) <= 1


def has_conflicting_open_pane(alias: str, entry: dict, global_cfg: dict, display_name: str) -> bool:
    """Whether a pane matching this seat is CURRENTLY OPEN somewhere right
    now — not merely "does this seat's tmux session exist."

    (Authored by Herald 5 for Iterations 3–4; deleted in the Iteration-5
    root-cause fix on the reasoning that injection-proofing made it
    unnecessary; RESTORED in Iteration 6 because it was never only an
    injection guard — it is the detection that makes the default top-up
    mode possible. History preserved below verbatim.)

    THE INCIDENT THIS EXISTS TO PREVENT (2026-07-07): the extension's own
    `Runner.run` looks up an existing VS Code terminal by exact name match
    before creating a new one (`getTerminalByName`, unconditionally). For
    any seat whose generated `name` happened to match its real, live pane's
    name exactly, "Terminals: Run" found that live pane and called
    `sendText` directly into it — which a running Claude Code process reads
    as a new chat turn, bypassing every guard `cmd_wake` was built with.

    THE FIRST FIX WAS WRONG (caught by Jérémie the same night): checking
    `has-session` is the wrong signal, because a tmux session persists
    after the pane viewing it is closed — that's the entire point of tmux
    detachment, and exactly the "rapid relaunch" case this feature exists
    for. Excluding on session-existence alone would permanently refuse to
    re-offer a seat whose terminal was simply closed.

    The corrected signal, in two steps:
    1. `list-clients` — non-empty output means something is actually
       viewing this session right now (exit 0 with empty output = exists
       but detached; exit != 0 = no session — both safe to open).
    2. If attached, the pane's current title must fuzzy-match this seat's
       display name (`titles_fuzzy_match`), tolerant of launch decoration.

    Both checks are read-only (`list-clients`, `display-message`).

    Known, accepted residual risk: a TOCTOU gap between this check (at
    generation time) and when "Terminals: Run" is actually clicked — same
    class as `cmd_wake`'s own active-turn check. Regenerate promptly before
    running, not hours ahead."""
    socket = last_message._get_seat_setting(
        entry if isinstance(entry, dict) else {}, global_cfg, "tmux_socket",
        default=last_message.DEFAULT_TMUX_SOCKET,
    )
    session_name = last_message._seat_session_name(alias)

    clients = subprocess.run(
        last_message._tmux_argv("list-clients", "-t", session_name, socket=socket),
        capture_output=True, text=True,
    )
    if clients.returncode != 0 or not clients.stdout.strip():
        return False  # no session, or session exists but nothing attached — safe either way

    title = subprocess.run(
        last_message._tmux_argv("display-message", "-p", "-t", session_name, "#{pane_title}", socket=socket),
        capture_output=True, text=True,
    )
    if title.returncode != 0:
        return False

    return titles_fuzzy_match(title.stdout.strip(), display_name)


def build_terminal_entry(alias: str, entry: dict, run_nonce: str, *, is_first: bool) -> dict:
    """`target` is set to a value unique to this run (never colliding with
    any real terminal's name), so the extension's `getTerminalByName` cache
    lookup (`cacheKey = target || name`) can never match an already-open
    pane — it always creates a fresh terminal (ADR-0008 Iteration 5). This
    is what makes running "Terminals: Run" against an already-open seat
    idempotent (a harmless second client on the same tmux session) instead
    of the extension injecting the launch command into the live pane.

    `dynamicTitle: True` means the fresh terminal's displayed name isn't
    pinned to that nonce — it's left to whatever the running process (tmux,
    via the title-setting fixed in ADR-0004 Iteration 6) sets dynamically,
    so the visible label still ends up as the correct, clean display name."""
    display_name = entry.get("display_name", alias) if isinstance(entry, dict) else alias
    # Same "(+) " Fable-usage marker cmd_launch applies to tmux titles
    # (last-message.py) — so the manifest/printed list match the live tabs
    # (dynamicTitle hands naming to tmux post-launch anyway; this covers the
    # pre-launch moment and the CLI printout). Lookup safety unaffected:
    # cacheKey = target (nonce), never name.
    model = entry.get("model", "") if isinstance(entry, dict) else ""
    if "fable" in model.lower():
        display_name = f"(+) {display_name}"
    role = entry.get("role", "") if isinstance(entry, dict) else ""
    color_hex = last_message._get_seat_color(entry)

    terminal = {
        "name": display_name,
        "description": truncate_description(role) if role else f"Seat: {alias}",
        "icon": ICON,
        "color": quantize_to_ansi_theme_color(color_hex),
        "cwd": "${workspaceFolder}",
        "command": f"source .claude/agent.env >/dev/null 2>&1; just launch {alias}",
        "target": f"{alias}--{run_nonce}",
        "dynamicTitle": True,
        "execute": True,
        # recycle MUST be False (Iteration 6b): runner.ts line 26 is
        # `recycle && ID_TO_INSTANCE.get(cacheKey) || getTerminalByName(cacheKey)`.
        # The nonce defeats getTerminalByName (name lookup) across regenerations,
        # but with recycle:true the extension's own in-memory map still returns
        # the instance it created for THIS nonce — so running "Terminals: Run"
        # twice on the SAME generated file would sendText into the live pane
        # created by the first run. recycle:false dead-ends both cache paths:
        # every run of every file always creates a fresh terminal.
        "recycle": False,
    }
    if is_first:
        terminal["open"] = True  # Reveal the terminal panel after "Run" — don't steal focus.

    return terminal


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate .vscode/terminals.json from the crew registry.")
    parser.add_argument(
        "--all",
        action="store_true",
        help=(
            "Mode A (recovery): include EVERY launchable seat unconditionally, "
            "even ones with a pane already open (those get a harmless second "
            "client — duplicates by design). Default is mode B (top-up): only "
            "seats with no pane currently open."
        ),
    )
    args = parser.parse_args()

    cfg = last_message.load_config()
    aliases = last_message._real_aliases(cfg)
    global_cfg = cfg.get("_global", {}) if isinstance(cfg, dict) else {}

    # Only launchable seats — same discipline as _find_next_inactive_seat:
    # don't hand a crashing alias to a bulk-run command.
    launchable = {
        alias: entry
        for alias, entry in aliases.items()
        if (entry.get("uuid") if isinstance(entry, dict) else entry)
    }

    if not launchable:
        sys.exit("No launchable seats found in agent-sessions.json — nothing to generate.")

    ensure_ordering_file(TERMINALS_TXT, list(launchable.keys()))

    # Mode B (default): drop seats whose pane is open right now. Detection is
    # read-only; the per-run nonce below keeps even mistakes injection-proof.
    skipped_open: list[str] = []
    included = launchable
    if not args.all:
        included = {}
        for alias, entry in launchable.items():
            display_name = entry.get("display_name", alias) if isinstance(entry, dict) else alias
            if has_conflicting_open_pane(alias, entry, global_cfg, display_name):
                skipped_open.append(alias)
            else:
                included[alias] = entry

    mode_label = "A/--all: every seat, unconditionally" if args.all else "B/default: top-up (only seats not already open)"

    if not included:
        # Write an EMPTY manifest rather than returning early: leaving the
        # previous run's file in place (possibly an --all manifest) means a
        # later "Terminals: Run" would execute stale entries — the exact
        # double-run-on-same-file hazard recycle:False guards, plus opening
        # seats that are open NOW but weren't at the stale generation time.
        TERMINALS_JSON.parent.mkdir(parents=True, exist_ok=True)
        empty_header = (
            "// GENERATED by scripts/refresh-terminals.py — do not hand-edit.\n"
            f"// Mode at generation: {mode_label}.\n"
            "// Every seat had an open pane at generation time — deliberately EMPTY\n"
            "// so \"Terminals: Run\" is a no-op instead of executing a stale manifest.\n"
        )
        TERMINALS_JSON.write_text(empty_header + json.dumps({"autorun": False, "terminals": []}, indent=2) + "\n")
        print(f"✅ Mode {mode_label}")
        print(f"   Every launchable seat already has an open pane ({', '.join(sorted(skipped_open))}).")
        print(f"   Wrote an EMPTY {TERMINALS_JSON.relative_to(REPO_ROOT)} (\"Terminals: Run\" is now a no-op).")
        print("   Run with --all if you want second clients on purpose.")
        return

    order = resolve_order(included, TERMINALS_TXT, registered_aliases=set(launchable.keys()))

    run_nonce = uuid.uuid4().hex[:12]
    terminals = [
        build_terminal_entry(alias, included[alias], run_nonce, is_first=(i == 0))
        for i, alias in enumerate(order)
    ]

    config = {
        "autorun": False,  # Explicit, on-demand relaunch via "Terminals: Run" — not on every window open.
        "terminals": terminals,
    }

    TERMINALS_JSON.parent.mkdir(parents=True, exist_ok=True)
    header = (
        "// GENERATED by scripts/refresh-terminals.py — do not hand-edit.\n"
        "// Regenerate: `just refresh-terminals [--all]` (reads docs/inbox/agent-sessions.json\n"
        "// + .vscode/terminals.txt for ordering). See docs/adr/0008.\n"
        f"// Mode at generation: {mode_label}.\n"
        "// Injection-proof in both modes: each entry's `target` is a per-run nonce,\n"
        "// so the extension always creates a fresh terminal, never sendText into a\n"
        "// live one. Snapshot semantics: reflects open panes AT GENERATION TIME —\n"
        "// regenerate promptly before \"Terminals: Run\", don't reuse hours later.\n"
    )
    TERMINALS_JSON.write_text(header + json.dumps(config, indent=2, ensure_ascii=False) + "\n")

    print(f"✅ Mode {mode_label}")
    print(f"   Wrote {TERMINALS_JSON.relative_to(REPO_ROOT)} ({len(terminals)} seat(s)):")
    for alias in order:
        entry = included[alias]
        display_name = entry.get("display_name", alias) if isinstance(entry, dict) else alias
        model = entry.get("model", "") if isinstance(entry, dict) else ""
        if "fable" in model.lower():
            display_name = f"(+) {display_name}"
        print(f"   {alias:15s} → {display_name}")
    if skipped_open:
        print(f"   Skipped (pane already open): {', '.join(sorted(skipped_open))}")
    print()
    print("👉 In VS Code: Cmd+Shift+P → \"Terminals: Run\" — opens the seats listed above.")
    print("   (No first-party way to trigger that from this CLI — see ADR-0008.)")


if __name__ == "__main__":
    main()
