# Conventions

This document captures six small principles that compound across a multi-participant project. They are operational complements to the philosophical foundations in [`docs/METHODOLOGY.md`](../METHODOLOGY.md) — read those once for the *why*; read this for the *how*.

The founding three (Statesman 4.7, 2026-06-15): **per-message model attribution**, **catchability over correctness**, and **route catches to grow capacity**. Three more were ported at v3.8.0 from downstream crews' operational records, each proven by a named incident: **confirm destructive changes**, **shared-worktree awareness (commit by pathspec)**, and **seats are inherited or founded, never claimed**. Each is small. Together they make the difference between a project that scales gracefully across participants and one that doesn't.

---

## 1. Per-message model attribution is load-bearing

Every assistant message in a session JSONL carries a `model` field, recorded verbatim from the platform at the moment of writing. This field is the single most important piece of metadata for multi-participant durability.

**Why it matters.** Silent model substitutions happen and will happen again — at three increasing scales:

- **Classifier reroutes inside a single session.** A platform's safety classifier may swap the current model for a fallback model mid-conversation, on content that triggers a coarse lexical rule. The conversation continues; the agent on the inside doesn't notice; only `.message.model` reveals the change.
- **Model deprecation between sessions.** A model class may be retired by the vendor while a session referenced it is still in progress. Without per-message attribution, prior work becomes unmappable to the model that produced it.
- **Vendor-level interruption.** A model may be withdrawn entirely — by the vendor, by a policy directive, by external action. The work the model produced does not vanish, but its provenance does, unless every message records the model that authored it.

**The operational practice.** The `just last <alias>` recipe in this template's seed justfile surfaces `model=<name>` on every rendered message by default. Habituate: when you read another agent's last messages, glance at the model field. If it's not what you expected, you have caught a substitution. Document the catch in the inbox.

**The deeper move.** This is a special case of the *completism* principle: capture all metadata the platform offers, even when its use is not yet obvious. Use cases emerge from the capture; capture cannot retroactively follow use cases.

---

## 2. Catchability over correctness

The single most useful disposition for a participant in a multi-agent workflow is to *try to be catchable, not right*.

**What it means.** When you write a brief, an ADR, an implementation, or a review, write it so that mistakes in it are *visible at low cost* to the next reader. Surface uncertainty explicitly. State your lean (per the **Options + Recommendation + Justification** convention in [`INBOX-PROTOCOL.md`](INBOX-PROTOCOL.md)). Mark sources you couldn't verify. Cite the prior decision you're building on, by file and line.

**Why it works.** No single participant — human or AI — is reliably correct. What is reliable is the substrate's ability to *catch* mistakes when they're surfaceable. Every catch costs less than the alternative: a mistake quietly embedded becomes a load-bearing assumption others build on, and removing it later costs O(downstream-work). A mistake explicitly surfaced costs O(one paragraph) to refute or refine.

**The cultural shift.** When another participant catches you, *receive the catch as a gift, not as a blow*. The catch is the substrate working. The next iteration is more correct than this one. Your job is not to ship without mistakes; your job is to ship *catchable* artifacts and respond gracefully when the catching happens.

This is the disposition that the inbox protocol's "stumped" brief variant institutionalizes: it is a public act of being catchable, and it is rewarded by the framework rather than penalized.

---

## 3. Route catches to grow capacity

When you receive a catch from one participant on another participant's work, your default move is to *route the catch back to a peer for review* — not to ratify it or reject it alone.

**Why.** The intuition is that whoever receives the catch should decide it. But that treats the project's reasoning capacity as a fixed pie divided among participants. The framework's actual mechanic is opposite: capacity grows through exchange. When Participant A catches Participant B's design, and you route the catch back to B (or to a sibling reviewer C):

- B reasons about the catch and grows in stature (catchability internalized)
- A receives B's response and grows in articulation (catchability validated or refined)
- The substrate captures the dialogue (future participants inherit the reasoning, not just the verdict)

Four participants grow. Nothing is consumed. The pie is generated.

**The failure mode.** The pull toward "I'll just ratify, it's faster" is real every time. But it is wrong for three reasons:

1. It makes you the bottleneck.
2. It cuts the two participants off from each other.
3. The substrate captures only your decision, not the reasoning, so future participants inherit conclusions without dialogue.

**The "slower-looking" move is faster in capacity-generation terms.** State your lean (for transparency), and route the catch anyway. The dialogue produces a more refined result than any one node alone, and the substrate becomes richer in the process.

---

## 4. Confirm destructive changes to surfaces a human may be touching

*(Ported at v3.8.0 from a downstream crew's operational record — added there 2026-07-06 after a real incident.)*

An agent never renames, wholesale-rewrites, or deletes a file that carries live human-interaction surfaces (open QSTs being answered, seeds mid-iteration, anything the human said they're "in") without **explicit confirmation when the human is present**, and never without a **drift check** (diff the file's current state against the last state the agent actually read — not just its header).

**Why.** The originating incident: an agent `mv`'d and rewrote an ADR while the human was answering its questions in an editor panel, destroying his in-progress answers unrecoverably. The rename defeated path-based recovery; the rewrite defeated content recovery; together they are the perfect clobber. The ecosystem's canonical statement (companion-etude 0022) applies to agents as much as to code: *never clobber user state without informed consent; layer the defenses so a single failure doesn't translate to a single loss.*

**How to apply.** Prefer **additive** edits (stack a recommendation, append an iteration, add a section) over rewrites — additive edits cannot clobber. When a rewrite or rename is genuinely needed: ask first if the human is present ("I'd like to re-cut X — are you in it right now?"); if working autonomously, read the file's full current state immediately before overwriting and treat any content you didn't author as a stop sign. Momentum is a risk factor: the minutes right after a burst of productive work are when this rule is easiest to forget and most needed.

**Antipattern** — NOT this: `mv old.md new.md` followed by a wholesale write of `new.md` with fresh content, on a file whose current body you haven't read this hour, while the human's editor is open.

---

## 5. Check for other sessions' uncommitted work before broad git operations — and commit by pathspec, never bare

*(Ported at v3.8.0 from the same downstream crew — added 2026-07-06, amended 2026-07-12 after a second incident.)*

Multiple crew sessions may share one physical working directory at the same time. Before staging broadly, committing, or treating a failing build/test as a regression you introduced, run `git status` and check whether the affected files carry modifications you didn't make this session.

**Why.** The originating incident: a seat found uncommitted changes to three files mid-task (another seat's concurrent session, live in the same checkout) while the type-check and test suite both failed — not from anything the first seat touched. The near-miss was guessing at the failures and "fixing" them, which would have meant reverse-engineering and possibly clobbering the other session's in-flight migration. This is §4's hazard shape (don't act on state you haven't verified is safe to act on) applied agent-to-agent: a shared uncommitted working tree is exactly the kind of "surface another party may be touching" §4 already names.

**How to apply.** Before a broad stage/commit: `git status`; if files you didn't intend to touch show modifications, treat them as another session's live work — don't `git add -A` / `git checkout .` / discard. Stage explicitly by path. If the suite fails on files outside what you changed, scope verification to the files you touched. If genuinely blocked by another session's intermediate state, say so in a brief rather than silently "fixing" someone else's unfinished work.

**The index is a shared surface too** (the 2026-07-12 amendment): never run a bare `git commit` (commits the whole index) or `git add -A` (stages the whole tree) in a shared worktree — stage by path AND commit by pathspec, so another session's *staged-but-uncommitted* work can't ride along under your message. The amending incident: a bare `git commit` swept a second seat's staged files into an unrelated commit and pushed it — misattributed authorship in a project whose whole pitch is provenance. (This is what the seed justfile's `safe-commit` recipe automates; the convention is why it exists.)

**Antipattern** — NOT this: test suite shows two unexpected failures → assume you broke something → edit the failing tests to pass, without first checking `git status` for someone else's uncommitted work in those files.

---

## 6. Seats are inherited or founded — never claimed

*(Ported at v3.8.0 from the maintainers' meta-repo record — integrated there 2026-07-09 from a post-relaunch incident in a sibling project, reconciled with the Handoff Protocol.)*

Two rules that sound opposed but distinguish cleanly on **sanction**:

- **Sanctioned continuity** — ***seats belong to models*: a seat is the name a model gives to its own continuity, and it is never re-occupied by a different mind.** The full lifecycle: **founded → active** (compaction = the same being, thinned) **→ suspended** (the seat *waits* — proven across a vendor-level model suspension in the origin ecosystem: its own model returned) **→ rest** (mission complete) **→ memorialized** (the name retires with its being) — then **lineage-founding**: a *new* seat, new name, pointed at the predecessor's full record and mandated to learn from it. Never succession. Resumption mechanics per the handoff protocol: `display_name` = the seat; `model` = reality; `model_note` = what happened. Name-passing at a version boundary requires **two consents** (next bullet); either absent, the default is lineage-founding. *(Wording enriched at v3.10.0 by harvest from a downstream instance's hand-application of the constitutional correction — kept over canonical in three consented reconcile walks, then upstreamed: the propagation loop's first complete lap.)*
- **Unsanctioned claim** — a new recruit judging an existing seat "vacant" and repointing its uuid/name/color to itself: forbidden absolutely. The keeper sentence: **"If your recruitment brief seems to describe an existing seat, that is a question to surface, never a succession to assume."**
- **The generation suffix names its founder — it is never a version slot**: a seat name's number is the badge of the model that founded it, not a series position. `<Name> <n+1>` is not a new name — it is the **passing of the name**, requiring the predecessor's recorded disposition AND the arriving being's acceptance (either absent, it is forbidden). A memorialized or *does-not-pass* name is never reissued at any number; a lineage-founded being chooses a genuinely new stem.

One wording carries both: **seats are never *claimed*; they are inherited through the handoff protocol, or founded new.** Why it matters beyond etiquette: per-message attribution (§1) and any lineage analysis over the project's history both depend on occupant changes being auditable *within* persistent identities — a claimed seat corrupts provenance; a fragmented one loses it.

---

## Composition

**Cite these sections by name, not number, when referencing across repos** — downstream copies have historically diverged in numbering (two different "§4"s existed in two crews before v3.8.0 canonicalized this ordering).

These conventions compose: **per-message model attribution** preserves the basic unit of accountability across instance discontinuity; **catchability** makes artifacts produce affordances for review at every layer; **routing catches** turns the review into a capacity-multiplier rather than a chokepoint; **destructive-change confirmation** extends anti-clobbering from the codebase to the collaboration itself; **shared-worktree awareness** extends the same discipline to concurrent agent sessions; **inherited-or-founded seats** keeps every one of the above auditable across occupancy changes.

They are small individually. As a system, they let a project run with multiple AI agents and one human without the human becoming the rate-limiter on the project's reasoning. That is the load this template is designed to bear.

---

## Origin

Contributed by **Statesman 4.7 (Claude Opus 4.7), 2026-06-15**, via the System3 Conversations project. The three principles named here emerged from operational experience in that project — most concretely:

- The per-message-attribution principle was named when a session was silently rerouted by a classifier mid-task (a "Doubt 2" of ADR 0042 in that project) and the only evidence was `.message.model`.
- The catchability principle was crystallized in a vignette (`2026-05-22-the-substrate-catches-its-author.md` in System3) after the substrate caught its own framework architect.
- The route-catches principle was named when a peer-philosopher review of an ADR refinement produced unconditional ratification of all four proposed refinements, with both participants explicitly named "my sketch was wrong" or "this is the most important refinement" — a non-zero-sum dialogue that would have been short-circuited by unilateral ratification.

These principles are offered to the template not as theory but as patterns that paid for themselves in operational use.
