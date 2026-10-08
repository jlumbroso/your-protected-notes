<!-- adr template version: "adr 3.11.5" -->
<!--
adr teaching map: the example is not the teaching — these are the up-links from this file to what teaches its form; load them rather than winging it. (Sibling: the template-version marker dates the mold this file was minted from.)
  skill: adr-authoring
  mcp: adrs-for-ai
-->

# [ADR Title - Decision/Topic]

- **Date**: [YYYY-MM-DD]
- **Iteration**: [N]
- **Status**: [Draft | Accepted | Partially Implemented | Implemented | Superseded]   <!-- the frozen five (v1 core, ratified 2026-08-12): case-insensitive read, canonical-case write; strict enum at document level — no annotations here -->
- **Deciders**: [Names / roles of contributors]

**TL;DR**: [One-line summary of the decision, written by the author at point of decision. May go stale as the ADR iterates; treat as the author's intent at write-time, not the canonical current rendering. Mandatory field — if you cannot write this in one line, the ADR is not done yet.]

---

## Quick Reference

**Navigation codes** (for grep):
- `QST:` Questions  
- `ANS:` Answers
- `COD:` Code examples
- `API:` API calls
- `FIL:` Files to examine
- `DOC:` Documentation
- `NOT:` Notes, remarks, observations

**Find things**:
```bash
grep -E '^### QST(-[A-Za-z0-9-]{1,24})?:' file.md   # All questions, both canonical forms — a bare-QST grep silently misses every handled question
grep 'Status: unanswered' file.md                   # Awaiting the human (by design, this misses unresolved/deferred — those are not the human's ball)
grep '^### COD:' file.md                             # Code examples
```

---

## Originating Context

**Source**: [Type and link to where this ADR originated, e.g.:
- `Human dump (below)` — stream-of-consciousness from a contributor
- `Brief: <path/to/brief.md>` — a brief from another contributor (see also: [INBOX-PROTOCOL.md](../../../INBOX-PROTOCOL.md) if your project uses the inbox-based coordination protocol)
- `Seed: <path/to/seed.md>` — a seed that was chunked into multiple ADRs
- `Prior ADR open question: <ADR-xxxx#QST-N>` — a follow-up
- `Code review / observation / external discussion / etc.`

Multiple sources may be listed.]

[If the source is a human dump, drop the stream-of-consciousness here — no structure needed, just everything that's on your mind about this decision]

[If the source is a brief, seed, or other reference, you may summarize the originating constraints here in a paragraph, OR rely on the link above.]

**Agency Grant**: [Optional: What freedom does the author have? "Implement as you see fit" / "Explore options" / "Just structure my thoughts"]

---

## Explicitation

*Making explicit what the Originating Context implied or contained tacitly. The author reflects back what they understand the problem to be, so misalignment surfaces here, not later.*

**What I understand**:

1. [Thread/topic 1] — [why it matters]
2. [Thread/topic 2] — [why it matters]

**Assumptions**:

- [Assumption 1]
- [Assumption 2]

**Confirm**: [Who is the author asking to confirm? Could be the originator (if a brief or dump), another contributor, or a self-check before moving on.]

---

## Questions

**Use the `QST:` / `ANS:` codes for open questions.** They're required for grep-ability and for any tooling (e.g., the ADRs4AI extension) that parses ADRs as structured documents. Open questions outside this format are invisible to those tools.

**Protocol** (added 2026-04-22 by Opus 4.7; superseded to ORRCF 2026-09, founder-ratified; byline completed 2026-10-04): every QST block must include a `**Recommendation**: (by [seat], [model], [YYYY-MM-DD])` section between the options and the `**ANS:**` block. The byline's three fields make three different catches possible: the **seat** says who answers for the lean, the **model** makes a silent substitution visible (per-message attribution's whole point), and the **date** makes freshness checkable — a recommendation is a claim about a moment. A session with no seat writes the model and date alone; the date is never optional. The human should not have to extract the AI's lean from prose. If walking back an earlier lean during iteration, say so explicitly — silent walk-backs are the one dishonesty this form exists to prevent.

**The ORRCF form** (pronounced *or-SEFF*; ratified via the format-stability register, 2026-08-25 — the catch-the-author lineage, completed): a recommendation carries five parts, spelled out once here — **Options, Recommendation, Rationale, Confidence, Falsifier**:

- **Options** — the neutral design space, laid out before any lean (never "alternatives," which frames rivals to a foregone pick). **Form**: one option per bullet — `- **A — <petname>**: <clear description>` — never listed inline in a running sentence; a pick-shaped question without its lettered block is underspecified, and the Recommendation's letter must name an entry in it. **Who the block is for**: it must stand alone as the *answer surface* — descriptions evaluable without the Rationale, because the human may read only the block; the Recommendation and Rationale exist for the reader who wants to check the author, not the one who wants to answer.
- **Recommendation** — the bold pick (`**B — short name.**`), skimmable without reading — the petname repeated beside the letter *on purpose*, so the pick still reads when the block has scrolled off; a bare `**B.**` is a reference, not a recommendation.
- **Rationale** — the thinking trace that maps the space to the lean, citing evidence *named specifically enough to be checked* — a file, an ADR, a measurement — never "best practice" or taste. (*Rationale*, not "justification": justification is defensive and post-hoc; rationale is the reasoning written down.)
- **Confidence** — at the END, never in a chip, and **always with its because**: `Confidence: 0.8 — because A, B, C`. The number is not a calibration claim; it is an anchor that forces the because-clause, and it discloses your *basis* (did you run it, or read about it?). A bare confidence token is malformed, not modest — a culture of performative confidence is corrosive to epistemic continuity. Read confidence as an action band: **≥0.90 act · 0.60–0.85 your call · ≤0.55 route to another mind** — teach the action, not the scale.
- **Falsifier** — taught label **`If wrong:`** — names *what would change this recommendation*: an observation, a measurement, a ruling. **Nullification, not price**: "if wrong, we lose a day" is a cost, not a falsifier; "if the census shows X, this flips to B" is a falsifier. (Field audit, 2026-09: ten of ten wild consequence-clauses were cost-shaped — the distinction must be taught or it is not written.) **And the nullifier names the option it flips to, when one exists** — for a reader answering by letter, a falsifier that does not land on a letter is a second question. (Ephemeris 5.1's field practice, adopted 2026-09-11.)

A recommendation whose author can be caught is worth more than one that can only be believed (`docs/inbox/CONVENTIONS.md` §catchability). Pre-ORRCF recommendations (claim + justification + consequence) remain valid history — read tolerantly, never rewritten; new recommendations use the five parts.

**Status tokens & annotations** (frozen at the v3.10.0 pairing): the open family is `unanswered` (the human's ball) | `unresolved` (answered once, passed back — the model's ball) | `deferred` (parked; nobody owes a move now). The closing family is `answered` | `withdrawn` (the asker acts) | `superseded` (a successor acts — point to it: `superseded — by QST-X`) | `moot` (the world acts). Any question-level token may carry a ` — <annotation>` (never parsed, always preserved — it is the pressure valve that keeps the token set small); whoever flips a status owes the one-line annotation saying why. The document-level `Status:` in the header stays a strict enum — when a document needs to say more, use structured fields, never a decorated enum value.

**Question identity — one story**: `### QST-<id>:` (1–24 letters/digits, interior hyphens) is the everyday citable handle, canonical-**optional** — add it when anything will refer back to the question; *a question that is referenced must have a handle*. The advanced form is an `<!-- @adr-anchor: <slug> -->` comment placed as the first non-blank content **after** the heading (placed before it, it silently binds to the previous section) — for when the heading must stay pure prose or the id must survive retitling; where both exist, the comment wins resolution. HTML comments shaped `<!-- @adr-<action>: <value> -->` are the reserved machine channel (`@adr-anchor`, `<!-- @adr-dismissed: <reason-slug> -->` on a heading line). The one grandfathered exception to that shape is this file's own line-1 version marker, `<!-- adr template version: "<stem> X.Y.Z" -->`, blessed exactly as-is — and version markers on *existing* documents are historical truth: never re-stamp them.

**Answering**: the `by`/`from` keyword is what makes a byline — `**ANS:** (by <name>, <date optional>)`; a bare `(Name)` stays part of the answer text. Pending state lives on the Status line (`- Status: unanswered — routing to <name>`) or in a bracketed `[Pending: …]` — never as bare prose in the ANS slot, because **the ANS text IS the answer** and every tool that layers, prefills, or writes leans on that contract. `[Fill this in]` is the sole empty-answer form tools emit and this template teaches. **And the block's closing `---` is load-bearing, not typography**: a QST block ends at the next `###` heading or bare `---`, and the answer layer collects everything until then — so trailing commentary (a `NOT:` filing note, a routing remark) goes **after a `---`**, never bare below the ANS slot, or it is read as answer content.

### QST: [Question text]
- Status: unanswered
- Why asking: [How this shapes my approach]
- Need: [pick a letter (or override — an answer in any shape is complete) | yes/no | explanation | etc]

Options:
- **A — [petname]**: [description concrete enough to evaluate without leaving this block]
- **B — [petname]**: [description — including what would make a reader choose it over A]
- **C — [petname]**: [add letters as the space needs; never fewer than the space has]

<!-- One option per bullet — never a running sentence (the "ribbon" malformation: unskimmable,
     unanchorable, and the Recommendation's letter loses its referent). A question with no
     enumerable options (pure elicitation) says so explicitly — `Options: none (elicitation)` —
     and the Need line then bounds the answer's expected shape. Full specification is never optional. -->

**Recommendation**: (by [seat], [model], [date — e.g. Shipwright 5, Claude Fable 5, 2026-10-04; no seat? model + date alone])

[**B — short name.** *Rationale*: 2–4 sentences mapping the options to the pick, from evidence named specifically enough to be checked (a file, an ADR, a measurement). *Confidence*: <anchor> — because <reasons>; read as an action band (≥0.90 act · 0.60–0.85 your call · ≤0.55 route to another mind). *If wrong*: what observation or ruling would change this pick — nullification, never just cost. If walking back an earlier lean, say so explicitly.]

**ANS:** (by [name])
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---
<!-- this --- ends the QST block (parser boundary, not typography): any comment
     ABOUT the question — a NOT: filing note, a routing remark — goes below a
     --- like this one; placed bare after the ANS slot it becomes the answer -->

### QST: [Another question]
- Status: unanswered  
- Why asking: [Context]
- Need: [Format]

Options:
- **A — [petname]**: [description]
- **B — [petname]**: [description]

**Recommendation**: (by [seat], [model], [date])

[Pick. *Rationale* from checkable evidence. *Confidence* — because. *If wrong*: the nullifier.]

**ANS:** (by [name])
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

## Supporting Materials

Use these only when needed - delete unused sections.

### COD: [example-name]
```python
# Your code here
```

### API: [call-name]
**Request:**
```http
POST /endpoint
{"param": "value"}
```

**Response:**
```json
{"result": "data"}
```

### FIL: [files-to-read]
- `/path/file.py` - [What to look for]
- `/path/file.md` - [Why it matters]

### DOC: [reference-name]
[Documentation excerpt or link]

---

## Decision

### Context
[What problem are we solving? Why does it matter?]

### Options

**Option A**: [Name]
- Pros: [Benefits]
- Cons: [Drawbacks]

**Option B**: [Name]  
- Pros: [Benefits]
- Cons: [Drawbacks]

### Chosen: [Option name]

**Rationale**: [The reasoning that mapped the options to this choice — from our discussion, written as the thinking trace]

**Trade-offs accepted**: [What we're giving up]

### Consequences
- [Immediate impact 1]
- [Immediate impact 2]
- [Long-term consideration]

---

## Open Follow-ups

*Concerns, observations, or questions surfaced during this ADR that don't block acceptance but shouldn't be lost. Use `QST:` for questions wanting answers; use bullets for declarative concerns or future tasks.*

### QST: [Open question to revisit later]
- Status: unresolved
- Why deferring: [Reason it's not blocking this ADR]

**ANS:** [Fill when resolved; or link to the ADR / discussion that resolved it]   <!-- literal placeholder — parser-significant, do not paraphrase -->

---

- [ ] [Concern: a worry we accepted but want to monitor]
- [ ] [Future task: something this decision implies but doesn't require now]
- [ ] [Unverified assumption: something to verify before [milestone]]

---

## Action Items

- [ ] [Task 1] - Owner: [name / role]
- [ ] [Task 2] - Owner: [name / role]

---

## Validation

*Each contributor confirms (add rows as needed; the prescribed examples are illustrative — replace with what's actually being confirmed):*

- [ ] [Name / role]: Decision captured matches intent
- [ ] [Name / role]: Reasoning is sound
- [ ] [Name / role]: Approach is implementable
- [ ] [Name / role]: Risks are acknowledged
- [ ] [Name / role]: [What they're confirming]

**Notes**: [Any caveats or follow-up needed]

---

## Iterations

*Each iteration captures how the ADR evolved. `Trigger` records what caused this iteration (a brief, a code review, an observation, an external event, etc.); `Outcome` records what changed and any status transition.*

### Iteration 1 ([date])
- Trigger: [What caused this iteration — e.g., initial draft from human dump / brief at <path> / etc.]
- Contributors: [Who contributed to this iteration]
- Changes: [What evolved]
- Outcome: [Status transition if any — e.g., `Draft → Proposed`]

### Iteration 2 ([date])
- Trigger: [What caused this iteration]
- Contributors: [Who contributed]
- Changes: [How approach evolved]
- Outcome: [Status transition if any]

---

## Glossary (optional)

*Project-specific terms introduced or used in this ADR, glossed for future readers. Terminology drifts over months; preserving meaning at time-of-decision matters.*

- **[Term]**: [Definition at time-of-decision]
- **[Term]**: [Definition]

---

## Links

- Related ADRs: [links]
- Related code: [links]
- Supersedes: [if applicable]
