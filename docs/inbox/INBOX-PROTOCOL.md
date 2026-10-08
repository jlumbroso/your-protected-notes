# Inbox Protocol

A lightweight protocol for inter-participant coordination in projects with multiple contributors — typically a human plus one or more AI agents, or multiple AI agents collaborating on shared work.

This protocol is **optional**, **composable**, and **independent of the ADR template**. Adopt it if your project has multiple participants who need to coordinate without making the human a synchronous message bus.

---

## Why this exists

When a project involves multiple participants (human + multiple AI agents, peer reviewers, agents handing work off across sessions), coordination overhead grows fast. Without infrastructure, every cross-participant signal routes through the human:

- AI agent A produces output, hands it to the human
- Human copy-pastes to AI agent B
- B responds back to the human
- Human shuttles between contexts

The human becomes the synchronous mediator. **The human's attention is the project's scarcest resource.** Burning it on routing costs is wasteful and reduces the quality of cognitive work the human can contribute.

The inbox protocol routes inter-participant messages through **files in a shared directory** instead. Participants read at their own pace; act when ready; and the audit trail is automatic.

### Why git-tracked files instead of chat or memory

Storing messages as markdown files in a git-tracked directory is **a feature, not incidental**:

- **Auditable**: future participants can reconstruct decision provenance by reading the inbox chronologically
- **Searchable**: standard tools (`grep`, IDE search) work
- **Migratable**: the inbox moves with the repo; no platform lock-in
- **Versioned**: amendments and corrections are tracked over time
- **Asynchronous**: no participant needs to be present when a message is written

This is a meaningful upgrade over ephemeral chat-based coordination. The audit trail is automatic; participants can reconstruct the history of how decisions came to be by reading the inbox.

---

## Directory convention

A single flat directory at a known location in the repo:

```
docs/inbox/             # active messages
docs/inbox/archive/     # acted-upon messages preserved for provenance
```

Specific paths can vary by project (`coordination/inbox/`, `.inbox/`, `briefs/`, etc.) — pick one and stick with it.

---

## Filename convention

Every file in the inbox follows this pattern:

```
YYYY-MM-DD-HHMM-{from}-to-{to}-{subject}.md
```

Where:

- `YYYY-MM-DD-HHMM` — UTC timestamp at time of writing
- `{from}` — identifier of the participant writing the message (human name, AI agent name, role label — whatever the project's naming convention is)
- `{to}` — identifier of the intended recipient
- `{subject}` — kebab-case short topic

Example: `2026-05-22-1830-agent-a-to-agent-b-database-migration-question.md`

### Why this convention is structural, not aesthetic

The filename pattern enforces two properties that matter for multi-participant coordination:

1. **Chronological order across timezone-heterogeneous participants.** Different participants (or different sessions of the same participant) may have different time-locale settings. UTC timestamps in the filename produce a single canonical ordering that sorts correctly in `ls`, in file managers, and in tooling. Without this, replies can appear to predate their originating messages — a coordination bug that compounds across weeks.

2. **Deterministic referencing.** The same message gets the same filename across all participants. When agents A and B refer to "the database migration question," they refer to the file by the same name. The filename becomes a canonical reference key — participants can cite it, link to it, search for it without ambiguity.

A filename-generation recipe (any tool: shell script, IDE snippet, Justfile recipe, AI agent procedure) that stamps UTC and accepts `{from}`, `{to}`, `{subject}` as structured inputs eliminates a class of coordination friction. **Hand-naming defeats both properties** and is the most common source of inbox drift.

---

## Brief variants

Three message variants cover most coordination needs. The variants are **directional** — they capture different relationships between sender and receiver.

### Standard brief — forward dispatch

A → B, asking for something. Used for: questions, requests, proposals, status updates, RFC requests.

**Filename**: `YYYY-MM-DD-HHMM-{from}-to-{to}-{subject}.md`

**Typical structure**:
- Date / From / To / Re (if referencing prior brief) / Subject
- Context (why this matters)
- The ask (what's needed)
- Acceptance criteria (when applicable)
- Constraints / coordination notes

Standard briefs tend to be longer because they bear the burden of orienting the recipient.

### Completion brief — reverse confirmation

B → A, reporting result. Used for: "task done, here's the result," handoff confirmations, status reports back to the originator.

**Filename**: `YYYY-MM-DD-HHMM-{from}-completion-{subject}.md`

**Typical structure**:
- Date / From / To / Re (the originating brief) / Subject
- Status (done / partial / blocked)
- Deliverables (links, commit hashes, files produced)
- Open items (anything surfaced during the work)
- Acceptance ack

Completion briefs are typically shorter — they confirm rather than initiate.

### Stumped brief — peer help-seeking

Sender, signaling "I tried, I'm out of ideas, I need a peer's perspective."

**Filename**: `YYYY-MM-DD-HHMM-{from}-stumped-{subject}.md` (or use your project's vocabulary: `blocked-{subject}`, `help-{subject}`, etc.)

**The semantic distinction**: "stumped" and "blocked" describe different escalation paths. **Blocked** typically means *waiting on a resource* (infrastructure, rate limit, capacity, external dependency); resolution is usually a wait or an unblock action. **Stumped** specifically means *I have agency to act AND I tried AND I'm out of ideas AND I need a peer's perspective*; resolution is cognitive — another participant's reasoning. The four-field structure below maps to the stumped case.

**Four-field structure** (starting scaffolding; adapt names to your team's vocabulary):

1. **What I tried** — concrete actions already taken, with results
2. **Why I'm stuck** — what specific information or perspective is missing
3. **What would unblock me** — concrete: another participant's analysis, a specific query, a code change, a decision
4. **What I can do in parallel** — work that doesn't require the missing piece

The fourth field is load-bearing: it converts a hard-stop into a soft-stop where progress continues on alternate fronts while the blocker is resolved.

---

## Lifecycle

For every message in the inbox:

1. **Write**: author drafts the brief; commits to repo
2. **Read**: recipient reads at their next available moment (no synchronous expectation)
3. **Act**: recipient acts on the brief — reply with new brief, integrate into work, etc.
4. **Archive**: after acted on, the brief moves to `docs/inbox/archive/`

### Archive vs delete: default to archive

Briefs preserve the chain of decisions. **Default to archiving** when a brief is acted on — even if it feels resolved. Delete only when a brief is truly transient (e.g., a stumped brief resolved within the same hour) and contains no decisions worth preserving.

When in doubt, archive. Storage cost is negligible (~5-50KB per brief); the cost of irreversible deletion of decision provenance is much higher.

The archive serves as a corpus that future participants (humans or AIs picking up the project later) can read to reconstruct how decisions came to be.

---

## When to use vs not use

**Use the inbox for:**

- Routine coordination, handoffs, status updates between participants
- RFC requests (peer review of a brief or a design before implementation)
- Information sharing that doesn't require immediate action
- Anything where the human's synchronous attention isn't required

**Don't use the inbox for:**

- Time-sensitive decisions that need the human now (those go through the project's direct-communication channel)
- Inline code review comments (those go on the diff or PR)
- Ephemeral chatter that doesn't represent a decision or handoff

### For load-bearing briefs, consider an RFC step

When a brief scopes architecturally significant work, substrate-validating implementations, or cluster-level decisions, **consider routing an RFC review through a peer participant before dispatching to the implementer**. Briefs ARE substrate; substrate benefits from validation.

The cost of late refinement (after implementation has started) is much higher than the cost of pre-dispatch review. A 30-minute peer-review pass on a brief routinely catches structural issues that would cost hours or days to refactor after the fact.

In practice, this looks like:

1. Author drafts the implementation brief
2. Author routes it to a peer reviewer (RFC step): `…-author-to-reviewer-rfc-{topic}.md`
3. Reviewer surfaces refinements: `…-reviewer-to-author-rfc-{topic}-review.md`
4. Author integrates refinements; dispatches refined brief to the implementer: `…-author-to-implementer-{topic}.md`

This pattern adds one cycle but reduces architectural risk. See the worked example at the end of this document.

---

## Communication patterns

These patterns apply across all brief variants — they describe how participants present information within a brief.

### Options · Recommendation · Rationale · Confidence · Falsifier (ORRCF)

When a brief surfaces a decision-point, present:

- **Options** — the choice space, enumerated with short labels (A / B / C)
- **Recommendation** — which option the author leans toward, with a clear bold pick
- **Rationale** — why the lean; reference evidence (data, prior decisions, constraints) rather than taste
- **Confidence** — an anchor with its mandatory *because*: the number forces reasons and discloses basis, never a calibration claim; read as action bands — ≥0.90 act · 0.60–0.85 your call · ≤0.55 route to another mind
- **Falsifier** — `If wrong:` what would *change this pick* — nullification, never just a cost

Earlier documents may say **ORJ** (Options + Recommendation + Justification); ORRCF is that pattern's ratified successor — read old ORJ blocks tolerantly, as valid history.

Stopping at Options is **not showing up fully**. The recipient can't evaluate the author's read without seeing the recommendation + reasoning. Stating a lean forces the author to commit to a position — which is where real reasoning shows. The recipient can then accept, override, or interrogate the recommendation efficiently.

In a multi-participant workflow where different agents may be triangulating positions, **attribute the recommendation to its author** (e.g., "Recommendation (from agent A): **B — short name**."). Knowing *which* participant is recommending *which* option is part of the signal.

### Show the wrong pattern alongside the correct pattern

When a brief prescribes a behavior ("do X for this case"), **include the antipattern explicitly** ("NOT this: ..."). Implementers under cognitive load pattern-match on visible code; an absent antipattern leaves the door open for the wrong pattern to creep back in.

Example:

> **Correct** — pass user context to all queries:
> ```typescript
> withUserContext(userId, () => db.query(...))
> ```
>
> **Antipattern** — bypassing user context with admin-level queries:
> ```typescript
> // DO NOT: db.adminQuery(...)
> ```

Showing the wrong pattern alongside the correct pattern reduces the risk that "don't do Y" gets inherited as "Y with a comment marking it safe."

---

## Tooling note

The filename convention is **tool-agnostic**. Any filename-generator works:

- A shell script that prompts for `{from}`, `{to}`, `{subject}` and creates the file
- An IDE snippet
- A Justfile recipe (e.g., `just brief agent-a agent-b topic`)
- A short procedure documented for AI agents to follow
- Hand-generation (but per "filename is structural" above, this defeats the convention's properties — automate when possible)

Pick whatever fits your team's tooling. The protocol's value is in the convention, not the implementation.

---

## Worked examples

### Example 1: Standard brief

**Filename**: `2026-05-22-1430-agent-a-to-agent-b-database-migration-question.md`

```markdown
# Agent A → Agent B: Question on the user-table migration

- **Date**: 2026-05-22 ~10:30 AM ET (filename UTC)
- **From**: Agent A
- **To**: Agent B
- **Re**: (none — new thread)
- **Subject**: Should the user-table migration add the `lastLoginAt` column as nullable or with a default?

## Context

We need to add `lastLoginAt` to track login activity. Two reasonable choices:

## Options

- **A — Nullable** (default behavior for "never logged in"; null until first login)
- **B — Non-null with default 'now()'** at migration time (all existing users get a timestamp)

## Recommendation (from Agent A): **A — Nullable**

Existing users haven't logged in (or we don't know when); defaulting to migration-time `now()` would misrepresent. Nullable is honest about the data state.

## Confirm

Does the analytics path tolerate null? If yes, A is safe.
```

### Example 2: Completion brief

**Filename**: `2026-05-22-1530-agent-b-completion-database-migration-question.md`

```markdown
# Agent B → Agent A: Completion — user-table migration shipped

- **Date**: 2026-05-22 ~11:30 AM ET (filename UTC)
- **From**: Agent B
- **To**: Agent A
- **Re**: 2026-05-22-1430-agent-a-to-agent-b-database-migration-question.md
- **Subject**: lastLoginAt column added as nullable per your recommendation

## Status

Done. Migration shipped; column is nullable; analytics path verified to tolerate nulls.

## Deliverables

- Migration: `migrations/2026-05-22-add-last-login-at.sql`
- Commit: `abc123` on `main`
- Analytics PR: `#456`

## Open items

None.

## Acceptance

Migration applied to production at 11:25 AM ET; no errors.
```

### Example 3: Stumped brief

**Filename**: `2026-05-22-1645-agent-c-stumped-test-failures-after-schema-update.md`

```markdown
# Agent C → All (or specific recipient): Stumped — test failures after schema update

- **Date**: 2026-05-22 ~12:45 PM ET (filename UTC)
- **From**: Agent C
- **To**: All (anyone with context on the test infrastructure)
- **Subject**: 12 tests failing after the schema update; not sure why

## What I tried

1. Re-ran the failing tests in isolation — same failures
2. Checked the schema diff for the column type — `BIGINT` not `INT` as expected
3. Inspected the failing assertions — they expect `number`, getting `bigint`
4. Looked at `Prisma.Decimal` handling — that's for monetary, not relevant

## Why I'm stuck

Don't know if (a) Prisma's TypeScript generator switched BIGINT to bigint vs number in a recent version, (b) we need a serializer config change, (c) the test expectations need to update to match the new column type, or (d) something else entirely.

## What would unblock me

Someone with Prisma version-history context could probably answer in 2 minutes. OR a pointer to a similar issue elsewhere in the codebase.

## What I can do in parallel

Continue on the unrelated UI tests (Phase 3 task list) while this is open.
```

### Example 4 (optional): RFC pattern for load-bearing briefs

When a brief is architecturally significant, the RFC-before-dispatch pattern looks like this:

1. **Author drafts implementation brief**: `2026-05-22-1700-author-to-implementer-feature-x-implementation.md`
2. **Author routes to reviewer FIRST**: `2026-05-22-1705-author-to-reviewer-rfc-feature-x-architecture-review.md`
3. **Reviewer produces RFC feedback**: `2026-05-22-1815-reviewer-to-author-rfc-feature-x-review-substantive.md` (with refinements)
4. **Author integrates refinements**: revises the implementation brief
5. **Author dispatches refined brief to implementer**: same filename as #1, or a new dated version

The RFC step adds one round-trip but routinely catches structural issues that would cost hours or days to fix after implementation has started.

---

## Adopting this protocol

To adopt this protocol in your project:

1. Create `docs/inbox/` (or your preferred path) in the repo
2. Document the filename convention in a project README or this same INBOX-PROTOCOL.md
3. Pick a filename-generation tool (Justfile, shell script, IDE snippet)
4. Onboard each participant: human + each AI agent gets a brief instruction on writing / reading / archiving
5. Use it for one or two coordination cycles to validate the workflow before extending

You don't need every participant to use the protocol perfectly from day one. The convention pays compound dividends as it stabilizes; early friction (especially around filename generation) is normal.

If your project also uses the [adr.md ADR template](docs/adr/templates/adr.md), the inbox protocol composes with it cleanly — ADRs can cite inbox briefs as their `Originating Context`, and briefs can request RFC review of proposed ADRs.

---

## Companion patterns (cross-references)

- `adr.md` — the ADR template; can reference inbox briefs in `Originating Context`
- `seed.md` — for brain-dump → chunked-ADRs workflow; complementary to inbox
- Project-specific memory or knowledge-store conventions — if your project maintains them, brief authors benefit from citing relevant entries by reference

The inbox protocol does not require any other template; it stands alone.
