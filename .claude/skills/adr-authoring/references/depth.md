<!-- skill version: "adr-authoring 3.9.0" — depth reference; load on demand from SKILL.md §5 -->

# Depth reference — beyond the always-loaded core

## D1. Which template, and why the old `template.md` used to win by accident

Four templates exist under `docs/adr/templates/` (plus `failure-classes.md`, a reference taxonomy, not a mint source). The directory's own `AGENTS.md` doorway states the terse version; one layer deeper: **a genuinely simple, already-made decision** (no negotiation needed) → `adr-madr.md`. **A decision still being worked out with a human** → `adr.md`. **A raw brain-dump, not yet a decision** → `seed.md` (via `just seed <slug>`). Careful: the seed/ADR line is drawn by **audience, not settledness** — *the seed asks the human what happened; the ADR asks the reader what should happen* — so a long-settled decision still gets its reader-facing questions in the ADR (a backfilled ADR with zero QSTs is usually the absent-question malformation, SKILL §3, not a sign of completeness). **A post-incident review** → `debrief.md`. If unsure, default to `adr.md` — the cost of unused sections (delete them) is lower than the cost of a decision that needed dialogue getting recorded as if it were already settled. `just adr "<title>"` mints `adr.md` pre-numbered; that's the path of least resistance now, which is itself half the fix — before the v3.9.0 rename, nothing about running the easy command told you *which* template you'd get.

## D2. Why the form matters, expanded (the corpus evidence)

- **Presence isn't reading**: 88% of non-adherent documents were in repos where the template file was already present — often the same commit that added a CLAUDE.md pointer to it. A *pointer* competes for a model's attention and reliably loses; a *skill* loads without competing for that decision.
- **Unenforced rules lose**: among documents that clearly attempt the template, 76% skip `TL;DR` anyway, despite it being marked mandatory. Teach it as load-bearing, not decorative.
- **Buried decisions**: a real ADR once hid a genuine yes/no decision inside an Open-Follow-ups checklist bullet — technically non-blocking by the letter, substantively blocking in fact. If a document's `Status` isn't `Accepted` for a reason that needs a human, that reason belongs in a `### QST:`, full stop — never a bare checklist bullet.
- **Exemplars beat prose**: two sibling projects, same author, same templates available — the one that reached near-canonical form got there by copying an *already-compliant sibling's real ADRs*, not by reading the abstract template harder. When in doubt, find a good recent ADR in the same repo and match its shape.

## D3. QST/ANS shapes that are fine, and the one that isn't

- **Inline, per-question** (canonical): `### QST:` → options → Recommendation → `**ANS:**`, per question. Default.
- **Batched** (a project's own consistent local dialect): all questions together, answers further down. Not wrong if the file already does this consistently — don't force a mid-document format switch.
- **Embedded mid-implementation**: a `**QST (from <name>)**` / `**ANS (from <name>)**` exchange inside a Decision or code-walkthrough section, when extracting it would separate the question from the exact thing it's about. Legitimate.

**What's never fine**: any of the four malformation classes in the core's §3, regardless of shape. Shape is a choice; parseability is not.

## D4. The catch-the-author Recommendation form, worked example

**Weak** (claim only, nothing to check): *"I recommend Option B, it seems better."*

**Strong** (claim + named justification + named consequence): *"**B — session-level attribution.** Because Aesop's spec (§2.3) already renders the degrade inline in `just last`'s output, not just in a policy document. If wrong: a future formatter refactor could silently drop that rendering and CONVENTIONS §1 would keep claiming non-silence after it stopped being true."*

The difference isn't length — every clause in the strong version can be checked against something named; the weak version can only be agreed with or not.

## D5. The rest of the shape (Validation, Iterations, Action Items)

- **Validation**: one row per contributor, each confirming a *specific* thing ("decision matches intent", "risks acknowledged") — replace the template's illustrative rows with what's actually being confirmed. Check your own row only.
- **Iterations**: append-only; each entry records Trigger (what caused it), Contributors, Changes, Outcome (status transition if any). Never rewrite an earlier iteration — the journey is the record.
- **Action Items**: every item gets an Owner. An unowned action item is how threads silently age out.
- Never rewrite another participant's attributed text (Recommendations especially) — append yours after. Attribution is how provenance survives model changes.

## D6. What this skill deliberately does not teach

Crew coordination (inbox protocol, deliberations, wake infrastructure), the porcelain/upgrade tooling, and **QuestionTours** (referencing questions from tour files — the tours field guide is that feature's authority). Those are coordination and tooling concerns, not "how a model writes a parseable artifact" concerns; teaching them here would break the crisp bound.

---

*Content: Rubricator 5 (Claude Sonnet 5), corpus-adherence findings 0001–0007 + qst-lint census. Assembly: Shipwright 5 (Claude Fable 5). Exemplar pairs from the corpus (matched good/bad specimens with `corpus:` ids) are a v-next strengthening — the census examples in the core carry launch.*
