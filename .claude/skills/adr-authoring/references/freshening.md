<!-- adr template version: "questions-reference 3.10.0" — sibling reference; stem re-keys with the family at the next minor -->

# The freshening pass — combing ADRs so the record catches up with reality

The founding instruction, verbatim (Jérémie Lumbroso, 2026-08-30 — this protocol is
its professionalization; improvements flow back as specimens via brief to the
template lane, so the protocol calibrates instead of being re-explained):

> go through each ADR: evaluate whether status has changed, add iterations, etc.,
> and what's left to build · evaluate whether we forgot anything, make a list of
> things to do to close off the ADRs · update recommendations of open questions
> if open · add new questions to resolve problems unbuilt in ADRs

**What a freshening pass is**: a periodic, evidence-driven sweep that makes the
record true again — statuses reflecting reality, iterations recording what
happened, open questions carrying current recommendations, and gaps surfaced as
real questions instead of silent debt. It is *gardening, not rewriting*: every
edit is additive, attributed, and evidenced.

---

## Phase 0 — scope, order, and the two laws that govern the whole pass

Enumerate with the handle-aware grep (`grep -E '^### QST(-[A-Za-z0-9-]{1,24})?:'`)
and the project's open-question sweep — never a bare-`QST:` grep, which silently
misses every handled question. Triage order: **Accepted and Partially
Implemented first** (most likely stale against a moving world), then **Proposed**
(decisions aging toward their gate), then **Implemented** (rarely stale), **Draft
last** (an owner's active surface — coordinate, don't garden). Archives are
never swept.

Two laws apply to every step below:

1. **The freshness corollary**: anything you are about to report as *open* gets
   its Status line and ANS slot re-read **at touch time** — never trusted from
   notes, boards, or memory. A stale board presenting a decided thing as a
   pending ask spends the human's attention on a fiction.
2. **Status authority is declared, and transitions carry annotations**: the tool
   and the sweeper never *guess* a status. You **propose** flips with evidence;
   the document's owner (or the human, for gates) ratifies — except where
   standing authority already covers you (your own crew's ADRs, with the
   transition annotation written: whoever flips a status owes the one-line why).

## Phase 1 — per-ADR: the five checks

**Check 1 — Status vs. reality.** Compare the declared document Status against
the world, and *name the evidence* (a commit, a tag, a shipped file, a brief):

- Built since last touched → propose `Accepted → Implemented` (all) or
  `→ Partially Implemented` (some), citing what shipped.
- The world moved past it → propose `Superseded — by <what>` or record
  **overtaken by events** (the OBE class): the decision no longer needs making
  because reality answered it. Say *what* answered it.
- Still true → touch nothing; absence of change is a finding too.

**Check 2 — Iterations debt.** If things happened that the Iterations section
does not record (commits or briefs citing this ADR are the detector), draft the
missing entry — trigger, contributors, changes, outcome — **dated today and
honest about being retrospective** ("recorded at freshening"): never write an
entry as if it were contemporaneous. The record's authority rests on never
backdating.

**Check 3 — The remainder inventory.** From the Decision, Action Items, and Open
Follow-ups versus reality, produce the close-off list. Every remainder item gets
a disposition, not just a mention: **build** (it's still owed — by whom) ·
**route** (another lane's, dispatch it) · **OBE** (dead, with the evidence) ·
**promote** (it turned out to be a decision — becomes a QST, Check 5).

**Check 4 — Open-question freshening.** For every open-family question
(`unanswered` | `unresolved` | `deferred` — the ball grid):

- *Verify the status line is true first.* The two known failure shapes: an
  answered question whose token was never flipped (flip it, annotate, credit the
  answer's date), and a decision point that isn't QST-shaped at all — invisible
  to every sweep (re-stake it canonically; a question that wants to be found
  must be a QST heading with a Status line).
- *Refresh the recommendation by stacking, never editing.* The prior
  recommendation is another moment's attributed record — add
  `**Recommendation (updated)**: (by <you>, <date>)` in the house's current form
  (ORRCF at this writing), and say explicitly whether your lean **stands**
  ("X stands, strengthened by Y"), **moves** (name what changed it — walking
  back a lean silently is the one dishonesty this convention exists to prevent),
  or **defers** (the question aged into someone else's lane).
- *If the world closed it*, propose the closing token with its annotation —
  `moot` (the world acted), `superseded — by <successor>` (a successor acts),
  `withdrawn` (the asker acts). Reality catching up is a *closure*, not a
  deletion: the question and its history stay.

**Check 5 — New questions for unbuilt problems.** Gaps discovered by Checks 1–4
become **canonical QST blocks** — heading, Status line, why-asking, options, an
attributed recommendation — never prose TODOs (a TODO is a question hiding from
the answering machinery). If the gap is a genuinely *new* decision rather than
this ADR's remainder, it becomes a seed or new ADR instead, cross-cited both
ways with fully qualified references.

## Phase 2 — the sweep's output contract

1. **Granular commits, one per ADR touched**, attributed, message naming which
   checks fired.
2. **A freshening report** (brief or report-message): per ADR — what changed,
   what closed, what's proposed-pending-ratification. Cite everything with its
   whole address (same-doc bare handles; same-project `adr:NNNN#handle`;
   cross-project the canonical `adr://v1/...` URI).
3. **The human's section last, and shaped honestly**: every item that needs the
   human ships its full context and a reasoned recommendation, and closes with
   *answer in any shape — a word if the reasoning carries you, a paragraph where
   it doesn't; the sweeper parses it into the record.* Shrinking the answer slot
   never shrinks the ask; shortness is the answerer's choice.

## The don'ts (each purchased with a real incident)

- Never edit another author's attributed recommendation or answer — stack.
- Never re-stamp a version marker; a marker changes only when its file is
  genuinely re-templated.
- Never close a question you merely *believe* is dead — the closing token needs
  its evidence in the annotation, and closing on someone's behalf needs their
  authority or the human's.
- Never mass-edit archives, and never sweep another seat's Draft.
- Never invent citation or status dialects mid-sweep; the sweep repairs
  dialect, it must not mint it.

## Seeds, briefly

Seeds freshen on their own two axes — lifecycle (the Thread's dates and the
Model Response Request checkboxes are the declared sensors) and derivation (the
Derived Into section against the linked ADRs' own statuses). A seed sweep
verifies the sensors are truthful and the placeholder line matches reality;
chunking remains the owner's call, never the sweeper's.

## Calibration

This protocol is versioned with the skill. Tunables — triage order, aging
thresholds, batch size per pass — are conventions, not laws: when a pass teaches
something (a check that misfired, a missing disposition, a new failure shape),
send the specimen to the template lane by brief; it lands here as text the next
release, and the pass improves instead of being re-explained.

---

*Professionalized from the founder's instruction by Shipwright 5 (Claude Fable 5,
HQ template lane), 2026-08-30. Every rule above has a named incident behind it
in the ecosystem's record; none is speculative.*
