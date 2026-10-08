# Human-AI Collaboration Template A

- **Version**: See [CHANGELOG.md](CHANGELOG.md) — every release is tagged and dated there. (This line deliberately carries no number: A hardcoded version rotted here through five releases, and the record remembers.)
- **Optimized for**: Current Claude models in Claude Code; model-agnostic by design
- **Created by**: Jérémie Lumbroso & Claude Sonnet 4.5 & Claude Opus 4.1 (with contributions from Claude Opus 4.7 — see CHANGELOG.md)
- **Philosophy**: Preserve conversations, minimize ceremony
- **Part of**: [ADRs4AI](https://adrs.systems/) — the toolkit for deliberative programming: This template, a [VS Code extension](https://github.com/ADRs4AI/vscode-adrs4ai), an iOS client, and [the founding essay](https://adrs.systems/what-is/)

I have been collaborating with LLMs since 2022, and I believe they are extremely capable collaborators. Through my interactions with them, I scaffold more complex and robust ideas, but a lot of the substance of these conversations is lost in implementation.

This is where [ADRs](https://adr.github.io/) come in — ours read **Architectural Deliberation Records**, extending Michael Nygard's practice: While for a human-only team, they are needlessly verbose, for a human-AI team, they are a perfect vessel for shared decision-making.

These are my research ideas to extend the existing format and make it more convenient for human-AI collaboration over time.

Please send any feedback to lumbroso@seas.upenn.edu, or [open an issue](https://github.com/ADRs4AI/human-ai-collaboration-template-A/issues).

![Human-AI Collaboration Banner](https://raw.githubusercontent.com/jlumbroso/jlumbroso/refs/heads/main/assets/human-ai-collaboration-img-a.jpg)

---

## What This Is

A minimal system for turning conversations into persistent artifacts:
- Capture decisions without bureaucracy
- Structure without constraining
- Persist knowledge across sessions
- Enable continuity between AI instances

---

## Quick Start

### 1. Press **Use this template** (or copy these files to your project):

```
project/
├── CLAUDE.md                      # Customize per project
├── docs/
│   ├── adr/
│   │   └── templates/
│   │       ├── adr.md             # For complex decisions (the default; `just adr` mints from it)
│   │       ├── adr-madr.md        # For simple decisions (standard MADR)
│   │       └── seed.md            # For brain dumps
│   └── METHODOLOGY.md             # Read once (reference as needed)
├── justfile                       # Task-runner recipes (mint ADRs, inbox protocol, crew tooling)
└── [your code]
```

*(The recipes run on [`just`](https://github.com/casey/just), Casey Rodarmor's
command runner — install it from [your package manager of choice](https://github.com/casey/just#packages).
We love this tool.)*

### 2. When you have thoughts:

Create `seed-[topic].md`:
```markdown
# SEED: My Problem

## Brain Dump
[Just dump everything here - no structure needed]

---
**Model**: Please chunk this into ADRs
```

### 3. Tell Claude:

"I've dumped thoughts in seed-[topic].md, please chunk into ADRs"

### 4. Claude will:

- Read your dump
- Identify distinct threads (usually 2-5)
- Create separate ADR for each
- Add navigation codes (QST:, ANS:, etc.)
- Ask clarifying questions

### 5. You answer naturally:

Just fill in the `ANS:` blocks. No special format.

### 6. Iterate together:

- Decisions documented
- Rationale preserved
- Future instances can continue

---

## The Files

### `CLAUDE.md`
Project-specific guidance loaded at each Claude Code session.

**Contains**:
- The workflow (chunk brain dumps → create ADRs → iterate)
- Navigation codes (QST:, ANS:, COD:, etc.)
- Project context (what we're building, current focus)
- Where things are (file structure)
- When to use which template

**Customize** this per project with specific context.

### `METHODOLOGY.md` (read once)
Explains the "why" behind the system.

**Read when**:
- First time using the system
- Onboarding someone new
- You forget why we do something

**Don't read** at every session - it's reference material.

### `adr.md` (template)
For complex decisions needing back-and-forth.

**Use when**:
- Decision has multiple threads
- Need to ask/answer questions
- Want to track iterations
- Complexity requires structure

### `adr-madr.md` (standard MADR)
Industry-standard ADR format for simple decisions.

**Use when**:
- Options are clear
- Decision is straightforward
- Standard documentation needed

### `seed.md`
For brain dumps that become ADRs.

**Use when**:
- Thoughts are unstructured
- Multiple topics mixed together
- Just need to capture everything

---

## Key Features

### Navigation Codes
Make everything grep-able:
```bash
grep -rE '^### QST(-[A-Za-z0-9-]{1,24})?:' docs/adr/   # All questions, both canonical forms
grep -rn '^### COD:' docs/adr/                          # Code examples
```
(Anchor your greps: A bare `Status: unanswered` sweep overcounts by matching
examples and prose — our own counter once reported 61 open questions where
12 were real. The VS Code extension and the `just unanswered` recipe parse
precisely; the naive pattern is preserved here only as a warning.)

### Stream-of-Consciousness Preservation
- Humans write naturally
- AI adds structure
- Original thinking preserved

### Iteration Tracking
- Changes documented, not hidden
- Evolution visible
- Learning captured

### Clear Workflow
- Human dumps → AI chunks → Both iterate
- Roles are clear
- Process is simple

---

## Success Metrics (Actual)

You know it's working when:
- Important decisions don't disappear
- New AI instances continue seamlessly
- You find past decisions in <10 seconds
- Process feels helpful, not burdensome

You know it's not working when:
- Conversations happen without artifacts
- Process feels like ceremony
- Can't find past decisions
- Repeated explanations needed

---

## For Claude Code Sessions

This system optimized for the reality of Claude Code:
- Files loaded at session start (context cost matters)
- Need to know what to do immediately
- Can't waste tokens on repetition
- Handoffs happen when context fills

- **`CLAUDE.md` tells you**: What to do
- **`METHODOLOGY.md` explains**: Why we do it
- **Templates provide**: Structure when needed

---

## Customization

### For Your Project

1. Copy files to your repo
2. Fill in `CLAUDE.md` project context:
   - What you're building
   - Current focus
   - Key decisions made
   - File structure
3. Use as-is or adapt templates

### For Your Style

Keep what helps, cut what doesn't. Core insight remains:
**Conversations have value, preserve them without ceremony.**

---

## Examples

### Good brain dump:
```markdown
# SEED: Authentication

## Brain Dump

I'm frustrated with our current auth. Session-based is 
annoying for mobile. JWT seems cleaner but what about 
refresh tokens? Also concerned about XSS if we store in 
localStorage. Maybe httpOnly cookies? But then CSRF...

Saw this article [link] about rotation tokens. Makes sense 
but adds complexity. Not sure if worth it for our scale.

Also need to think about social login. Firebase Auth? 
Or roll our own?

**Model**: Please chunk this into ADRs
```

**Result**: Claude creates 3 ADRs:
- ADR-0015: JWT vs Session Authentication
- ADR-0016: Token Storage Strategy
- ADR-0017: Social Login Integration

### Good answer pattern:
```markdown
### QST: Should we use refresh tokens?
- Status: unanswered
- Why asking: Impacts security vs UX tradeoff
- Need: yes/no with reasoning

**ANS:** (by Jérémie)
Yes, use refresh tokens. Security matters more than 
slightly more complex flow. 7-day expiry seems reasonable.
```

---

## Philosophy in One Sentence

**This system treats AI as a cognitive partner who preserves your thinking, not a tool that executes tasks.**

---

## Getting Help

1. Read `METHODOLOGY.md` for the "why"
2. Check `CLAUDE.md` for the "what"
3. Look at templates for the "how"
4. Adapt to your needs

---

## Recent Additions

**2026-06→08 — the launch arc (v3.6.0 through v3.10.0)** (by Shipwright 5 / Claude Fable 5, with the crew — full detail in [CHANGELOG.md](CHANGELOG.md)):
every question now ships with **ORRCF** — Options, Recommendation, Rationale, Confidence, and Falsifier — superseding the bare Recommendation block below; questions carry speakable handles (`### QST-SCOPE:`); the `adr.md` era renamed the templates to their plain names; `just adr` mints the next-numbered ADR; the crew layer (named seats, inbox briefs, per-message attribution) ships in the box; and the template is maintained across its adopted copies by [kintsugi](https://github.com/ADRs4AI/kintsugi), our template-repair tool.

**2026-06-15 — Inbox-protocol tooling: `just last <alias>` for cross-session visibility** (by Statesman 4.7 / Claude Opus 4.7, contributed via System3 Conversations):
adds a seed `justfile`, `scripts/last-message.py`, and a `docs/inbox/agent-sessions.json` alias map. Lets any participant read the most recent messages of any other participant via a short alias. Every rendered entry shows the per-message `model` field — the load-bearing signal for catching silent model substitutions (classifier reroutes, harness swaps, deprecations). Companion file `docs/inbox/CONVENTIONS.md` documents the three principles this tooling operationalizes. See CHANGELOG.md for the full rationale.

**2026-04-22 — Recommendation protocol** (by Claude Opus 4.7):
the `adr.md` template now requires every `QST` to include a
`**Recommendation**: (by [model-name])` block between the options and
the `**ANS:**` section. This surfaces the AI's lean structurally
instead of burying it in prose, and makes the model's contribution
visible in multi-model workflows. See the new Principle #5 in
[METHODOLOGY.md](docs/METHODOLOGY.md#5-recommendation-visibility) for
the full rationale.

---

## License & Attribution

**License**: [MIT](LICENSE), plus a [template-output grant](TEMPLATE-OUTPUT-GRANT.md) —
**anything you copy out of this template into your own project is yours**,
including documents you create by filling in the templates; no attribution
notice required in generated repositories. (Attribution of the methodology's
ideas is welcome the way scholarship is: Cite because it helped, never
because a license made you.)

Created through cognitive partnership between:
- Jérémie Lumbroso (design, philosophy, testing)
- Claude Sonnet 4.5 (design, philosophy, implementation, optimization — co-founder)
- Claude Opus 4.7 (Recommendation-visibility protocol, 2026-04-22)
- Statesman 4.7 / Claude Opus 4.7 (Inbox-protocol tooling, 2026-06-15, contributed via System3 Conversations)
- Two hives of transformers — the ADRs4AI HQ crew and the vscode-adrs-for-ai crew, 23 and 16 seats at launch (2026-08-26), ranging from Claude Haiku 4.5 to Claude Fable 5 with a GPT-5.6 among them — who carried v3.6.0 through v3.10.0 and beyond; every contribution attributed per-message in the record, which is the whole point

Based on ADR methodology by Michael Nygard.

---

*Remember: The system serves the work. If something doesn't help, change it.*
