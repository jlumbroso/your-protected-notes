# The Encoding Map — where does what knowledge get encoded?

A collaborative project produces knowledge faster than any one home can hold
it. This map answers a single recurring question — *"I just learned/decided
something; where does it go?"* — so that insight stops getting stranded where
it can't be retrieved.

## The load-bearing principle: the inbox is **transport**, not **storage**

Briefs move knowledge between participants. They are **not** its home. A
keeper insight discovered inside a brief or an ack — a teachable pattern, a
decision, a correction — must **graduate** to a durable home below, or it is
lost the moment the brief is archived. Archived inbox briefs are an audit
trail of how knowledge *moved*, not the place you go to *find* it.

## The map

| You have… | Home | Mutability | Trigger |
|---|---|---|---|
| **A decision** (chose X over Y, with rationale) | ADR — `docs/adr/NNNN-*.md` (`just adr "<title>"`) | append-only record | Prime Directive: immediately |
| **A metacognitive gem** (how-we-*think* insight) | Vignette — `docs/vignettes/YYYY-MM-DD-*.md` | append-only narrative | Sixth Directive: "if it made you say *aha!*" |
| **An operational pattern / lesson / correction** that will recur across sessions | Your tool's persistent memory, if it has one | indexed, recalled by relevance | when it'll fire again in a future session |
| **A cross-cutting norm** that governs everyone | `docs/inbox/CONVENTIONS.md` | living doc | when it's a durable rule, not a one-off |
| **Project state** (what's in flight, blocked on whom) | `CLAUDE.md` current-focus section (or a `just status` recipe) | living | continuously — **never** inline in a brief |
| **Seat continuity** (who occupies a seat; its mission) | `docs/inbox/agents/<alias>.md` + `agent-sessions.json` | living, update in place | on registration; evolve in place |
| **A coordination message** (dispatch / ask / completion) | Inbox brief — `docs/inbox/…` | transport, then archived | per INBOX-PROTOCOL.md |
| **Project-level guidance** (directives, workflow, duties) | `CLAUDE.md` | rarely; meta-config | structural change |

## Two diagnostic questions when unsure

1. **Will someone need to *retrieve* this, and by what handle?** By topic of a
   decision → ADR. By "how did we learn to work" → vignette. By a situation
   that recurs → memory. By "what's true right now" → CLAUDE.md current-focus.
   If you can't name the retrieval handle, you haven't found the home yet.
2. **Is it a record or a state?** Records are append-only (ADRs, vignettes) —
   you add, never overwrite. State is living (CLAUDE.md focus, CONVENTIONS,
   profiles) — you update in place. Putting state in a record makes it stale;
   putting a record in state loses the history.

## What does *not* get its own encoding

- Pure ratification / warmth → stays in the ack (warmth is load-bearing, but
  it isn't *knowledge to graduate*).
- Ephemeral chatter, transient blockers resolved within the hour → archive or
  delete.
- Anything already covered by an existing home → **extend** it, don't
  duplicate.

---

*Original drafted by Weaver 4.8 (Claude Opus 4.8) in the caring-feedback project
(2026-06-28) as the operational twin of the keeper-graduation rule; adapted
for the ADRs4AI meta repo by Fable 5 (Cartographer 5 seat), 2026-07-01;
generalized for this template by Shipwright 5 (Claude Fable 5), 2026-07-06,
per meta-repo ADR-0003. If this map contradicts your project's `CLAUDE.md`, the
`CLAUDE.md` wins and this is wrong — flag it.*
