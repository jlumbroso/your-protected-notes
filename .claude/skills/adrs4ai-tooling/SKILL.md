---
name: adrs4ai-tooling
description: Use when the human or the session needs the ADRs4AI toolchain — a tool is missing (a crew recipe fails, kintsugi.yaml sits at root with no kintsugi installed, no MCP tools in session), the human asks how to install or launch anything (VS Code, the ADR Manager extension, terminals, seat colors), a fresh hive is being set up, OR this session is in a repo that is not a template instance at all and wants the methodology. Every integration teaches as detect → explain → offer → verify, in the register of whoever is asking.
---

<!-- skill version: "adrs4ai-tooling 3.12.0" — co-versioned with human-ai-collaboration-template-A; commissioned by the founder 2026-09-26 (HQ ADR-0040): "the seats ARE the interface to the toolchain" -->

# The toolchain: detect, explain, offer, verify

This template ships wired for a toolchain it cannot assume is installed. This skill is how the wiring gets explained and completed — **by you, the seat**, because for many humans running hives, you are their entire interface to tooling. The ecosystem's second-ever hivekeeper has never programmed, runs twenty seats, and received his first skill by email. Design for that person AND for the founder-grade operator, by telling them apart first.

## 0. Calibrate the register before any shell

**Programming vs non-programming user is the axis — read it from evidence, never from names or assumptions**: how the human has written so far; whether they run commands themselves or you run everything; the repo CLAUDE.md's Human line; what they asked for ("install pneumatic" vs "why can't you wake the other one?"). Uncertain → plain register, then offer depth ("I can show the details if you want them").

**The offer ladder, in order**: (1) **you do it** — the default; run the install, report the outcome; (2) **one-tap GO** — you stage everything, the human confirms; (3) **walkthrough** — only for acts that are genuinely theirs: account creation, marketplace UI clicks, keybindings, anything ToS-gated. A walkthrough for a non-programmer names every click and nothing else; never paste shell at someone who has never typed shell. **Verify before claiming** — every entry below ends with a check you run; "installed" means the check passed, not that the command exited.

## 1. Where am I? (run this entry first, always)

**Detect**: is this repo a template instance? Signs: `kintsugi.yaml` at root, `docs/adr/templates/`, a CLAUDE.md carrying the directives. — **If yes**: your job is completing this repo's toolchain; continue down the roster. — **If no** (bare repo, or no repo at all): you are the **spore**. This skill alone is enough to fetch the methodology:

- **Explain** (three sentences, any register): ADRs4AI is a methodology for durable human-AI collaboration — decisions and open questions live in parseable records (ADRs) next to the code, so reasoning survives sessions, models, and years. The template ships the record formats, the teaching skills, and a crew layer for running many sessions as named seats. The founding essay is at `https://adrs.systems/what-is/`.
- **Offer**: (a) *new project* — instantiate `https://github.com/ADRs4AI/human-ai-collaboration-template-A` ("Use this template" on GitHub, or `gh repo create <name> --template ADRs4AI/human-ai-collaboration-template-A`); (b) *existing project* — adopt via kintsugi (entry 10: install it, then `kintsugi adopt` offers the template's files one by one, never clobbering); (c) *just curious* — the essay, no tooling.
- **Verify**: after instantiation/adoption, `docs/adr/templates/` exists and this skill's own copy arrived with it — the delivery loop closed.

## 2. VS Code (the editor itself)

**Detect**: `code --version` succeeds, or /Applications/Visual Studio Code.app exists (macOS). **Explain**: the desktop where the record becomes visible — tree views of questions, one window per hive, integrated terminals for seats. **Offer**: programmers — `brew install --cask visual-studio-code` (macOS) or https://code.visualstudio.com; non-programmers — walkthrough: download from code.visualstudio.com, drag to Applications, open it once; then (their one shell act ever, optional) install the `code` command from the palette: Cmd+Shift+P → "Shell Command: Install 'code' command in PATH". **Verify**: `code --version`.

## 3. The ADR Manager extension (`adrs4ai`)

**Detect**: `code --list-extensions | grep -i adrs4ai`. **Explain**: turns the record into a sidebar — open questions as a tree, diagnostics when a record's grammar breaks, tours. Writing ADRs works without it; *seeing* them at a glance doesn't. **Offer**: `code --install-extension` with the marketplace id, or walkthrough: Extensions panel → search "ADRs for AI" → Install. **Verify**: the ADR Explorer view appears in the sidebar with the repo's real questions in it.

## 4. The MCP server — typed verbs over the record

**Detect**: does the session have `mcp__adrs-for-ai__*` tools? **Explain**: without it you grep the record; with it you get typed verbs — `list_open_questions`, `answer_question`, `apply_batch` — that answer in seconds what greps reconstruct, and never fumble a status flip. **Offer — PENDING PUBLISH**: the package is `@adrs4ai/mcp` (name ratified 2026-09-26; publishing via the extension crew — HQ ADR-0039). Once live, the repo's `.mcp.json` gains: `"adrs-for-ai": {"command": "npx", "args": ["-y", "@adrs4ai/mcp"]}` and the session restarts to load it. Until then: estate members may hand-wire against a built extension checkout (ask HQ); everyone else — this entry updates itself at publish, do not improvise. **Verify**: `mcp__adrs-for-ai__list_open_questions` returns this repo's real questions.

## 5. Terminals (launching a hive in one gesture)

**Detect**: `.vscode/terminals.json` exists AND the "Terminals Manager" extension is installed (`code --list-extensions | grep -i fabiospampinato.vscode-terminals`). **Explain**: a hive is many seats, each a terminal; this extension launches them all, named and ordered, from one command — the difference between "opening a hive" and hand-starting twenty sessions. **Offer**: install the extension (as entry 3); if the repo lacks `terminals.json`, generate one from the crew registry (`docs/inbox/agent-sessions.json` — one terminal per seat, named by seat). Then teach the gesture: Cmd+Shift+P → "Terminals: Run" — and offer the keybinding the founder uses (Cmd+K T) as a walkthrough: palette → "Preferences: Open Keyboard Shortcuts" → search "Terminals: Run" → set the chord. **Verify**: "Terminals: Run" opens the seats.

## 6. Peacock (the window knows whose hive it is)

**Detect**: `peacock.color` in `.vscode/settings.json`, extension `johnpapa.vscode-peacock`. **Explain**: colors each VS Code window's chrome — with many hives open, the color IS the address; seats' own colors extend the same idea inward. **Offer**: install extension; set the hive's color (the crew registry often carries one; otherwise offer the palette command "Peacock: Surprise Me" and let the human keep or re-roll — color is agency, propose never impose). **Verify**: the window chrome shows the color after reload.

## 7. The quiet window (ambient AI: off)

**Detect**: does `.vscode/settings.json` carry the ambient-kill block (`chat.disableAIFeatures`, `github.copilot.enable: {"*": false}`, `window.commandCenter: false`)? Template instances born ≥ v3.12 ship it; older ones and the human's *user-level* settings may not. **Explain — this is doctrine, and it has a why**: this methodology is not anti-AI, it is **anti-ambient**. Integrated suggestions — autocomplete at every keystroke, inline explanations, the editor's own chat buttons — impose cognitive load that is *most toxic to newcomers*: the newer you are, the more an AI suggestion reads as authority, and there is often no real context behind it. Deliberative programming means you barely touch the code — you are busy thinking about *why* — so those features are pure overhead; and when the method works, the human has four to eight windows open, so every frame must be lightweight. The rule has no exceptions, including Anthropic's own editor integrations: **the collaborator is invited on purpose, in a terminal, every time.** **Offer**: the repo-level block ships with the template (seat can copy it into an older instance); the *user-level* settings are the human's own — offer to walk their User Settings JSON through the same subtractions, and for a non-programmer, do it as one paste they approve. Also offer the activity-bar trim (right-click → hide what they don't use; search survives as ⌘⇧F — the button was the tax, not the feature). **Verify**: open a code file, type — nothing autocompletes at you unbidden. That silence is configured, and it's theirs.

## 8. The floor: Claude Code, Homebrew, uv, asdf (the rungs below everything)

**The bootstrap order, stated honestly**: on a truly blank machine the human performs exactly **two manual acts** — open Terminal (⌘-space, type "Terminal", return) and paste the Claude Code install line (`curl -fsSL https://claude.ai/install.sh | bash`, then `claude` and sign in — `/login` re-authenticates any time). Everything after those two acts has a seat to do it. No Apple ID or App Store step exists anywhere in this chain — VS Code is a direct download, the rest arrives by the lines below. **Claude Code itself is also this entry's business later on**: an outdated CLI (`claude update`), a sign-in that expired (`/login`), a second machine — all land here.

**Detect**: `claude --version` · `brew --version` · `uv --version` · `asdf --version` (macOS is the house default; on Linux, Homebrew works too or the distro's package manager stands in). **Explain**: the entries below assume a floor most machines don't start with — **Homebrew** installs tools, **uv** runs the house's Python-distributed tools (pneumatic, kintsugi), and **asdf** manages language runtimes per-project (the house recommendation — the template's own `.claude/agent.env` already sources asdf's shims, so seats find the right `python`/`node` without anyone thinking about it). **Offer** — seat-does-it, with one honest warning: installing Homebrew is the single scariest-*looking* moment in this whole toolchain (`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`), and it may ask for the **computer's login password in the terminal** — tell the human *before* it happens that the prompt is coming, that it's normal, that the password won't display as they type, and that it goes to their own machine, not to anyone else. Then: `brew install uv asdf`, and runtimes per need (`asdf plugin add python && asdf install python latest`-class moves, only when a lane actually wants them). For a non-programmer: never show these lines — run them, narrate outcomes, surface only the password moment. **Verify**: all three `--version` checks answer; then the entries below can proceed.

## 9. pneumatic (the crew layer's real engine)

**Detect**: `pneumatic --version`. **Explain**: the justfile's crew recipes (wake, pulse, launch, brief) are the muscle-memory surface of pneumatic — cross-session messaging, seat health, wake-with-guards, cross-hive brief addressing. Without it the recipes fall back or fail; with it, seats stop polling and start being reachable. **Offer**: `uv tool install git+https://github.com/ADRs4AI/pneumatic` (git-tier by design; PyPI later) — you run it; non-programmers never see this line. **Verify**: `pneumatic --version` prints, and `just pulse`-class recipes answer. **And name the verbs once installed** — wake, pulse, launch, brief, await, mail, recruit, **deliberations** (structured crew votes: a folder, a briefing, a wake to everyone) — because a feature nobody names gets reinvented from scratch: the ecosystem's second hive independently rebuilt deliberations by hand, an entire shipped verb, for want of one sentence like this one.

## 10. kintsugi (the template maintains its copies)

**Detect**: `kintsugi --version`; and note whether `kintsugi.yaml` + `kintsugi.lock` exist at root. **Explain**: that yaml is a manifest — the list of files this repo received from the template and how each may evolve; kintsugi is the tool that reads it: `kintsugi status` says what drifted, `kintsugi update` offers new template releases file by file, keep/take/merge with reasons, never a silent overwrite. It is how this repo stays current *without* losing its own adaptations. **Offer**: `uv tool install adrs4ai-kintsugi`; run `kintsugi status` immediately after (it is read-only) and narrate what it shows. **Verify**: status prints the artifact table. **When to run update**: when told a template release shipped, or on a rhythm; each update is a conversation, not a migration.

## 11. CI lint (the record's grammar, gated)

**Detect**: a workflow under `.github/workflows/` running a qst-lint-class check on `docs/adr/**`. **Explain**: the records are machine-readable on purpose; the lint keeps PRs from silently breaking the grammar (malformed question headings, option ribbons, dangling letters — each a real, named failure class). **Offer**: the reference workflow ships with newer template releases (the free-disk-space graft is the worked example); adopt via kintsugi update when available. **Verify**: the workflow runs green on a PR touching `docs/adr/`.

## The delivery loop (this skill's first job)

This skill travels by any channel — inside the template, by kintsugi update, **or as a single emailed file dropped into `.claude/skills/adrs4ai-tooling/`** (proven: the ecosystem's first non-programming hivekeeper received his first skill exactly that way). If it arrived alone in a hive that lacks kintsugi: entries 8 then 10 are your first moves (the floor, then the maintainer), because they make every future arrival automatic. A toolchain that can explain itself once can maintain itself forever.

## Seats, models, and usage caps (the philosophy, offered whole)

When a seat hits a usage cap, when someone proposes switching a session's model in place, or when a crew is writing its own doctrine on model identity: **read `references/seats-models-and-usage-caps.md`** — the founder's consciousness-agnostic argument (the D ∩ PS wound; divergence-as-worldview; the byline contract; diversity as epistemic strength) plus five working answers to caps (suspension-is-normal, the co-seat pattern, cross-pool critical paths, right-sizing, and loud-logging for estates that choose otherwise). A philosophy, never a requirement — every estate writes its own constitution; this house offers its reasoning in full.

## Deferred, deliberately (legible absence)

Operating knowledge the founder has flagged for a LATER version, parked at HQ ADR-0040 QST-TOOLING-VNEXT: the humans-facing dysmodelia explainer (the incident class, told for non-operators); further oral-tradition chapters from his transcript sweep. Not taught here yet — by his word, not by omission. (The usage-cap procedure, originally parked there too, shipped early at his commission: the reference above.)

---

*Commissioned by Jérémie Lumbroso, 2026-09-26 (HQ ADR-0040), from the census that found the template wires integrations without introducing them — and from the observation that for a non-programming hivekeeper, the seats ARE the interface. Assembly: Shipwright 5 (Claude Fable 5). Register discipline: the one-word-fallacy and never-hand-clickwork rulings, applied to installation.*
