<!-- adr template version: "questions-reference 3.11.5" -->

# Questions reference — status vocabulary, identity, and answer forms

The ratified grammar for QST/ANS blocks, in one place. Source of authority:
the format-stability register (vscode-adrs-for-ai ADR-0032, Accepted 2026-08-12,
14/14 founder-ratified) paired to this template at v3.10.0. **This is a described
grammar, not a proposed one** — every form below was in daily use before it was
frozen; the freeze encodes what adopters actually see.

---

## 1. Question status: the vocabulary

One line, one job — `- Status:` carries the question's lifecycle, and nothing else does.

**The open family** (work remains; the token says whose ball it is):

| Token | Meaning | Whose ball |
|---|---|---|
| `unanswered` | awaiting the human's answer | the human's |
| `unresolved` | answered once, passed back for model work | the model's |
| `deferred` | parked on purpose; neither party owes a move now | nobody's — still open |

**The closed family** (no further answer is coming):

| Token | Meaning |
|---|---|
| `answered` | the question got its answer — the normal close |
| `withdrawn` | the asker retired it |
| `superseded` | a successor question replaced it |
| `moot` | the world changed; the question no longer applies |

The teaching sentence, ratified as such: **`withdrawn` = the asker acts;
`moot` = the world acts; `superseded` = a successor acts — three agents, three words.**

There is no `duplicate` token: a duplicate IS `superseded — by QST-X` naming the
survivor. One semantic, one spelling.

**Transition obligation**: whoever flips a status owes the one-line annotation
saying why (see §2) — a bare flip strands the next reader. Tooling that sweeps
for `unanswered` only is *correct*: the other tokens are deliberately outside
"awaiting the human" — don't "fix" such a sweep to match them.

**Reopening** is edit-to-reopen: change the token back and say why in the
annotation. Status authority is declared, not derived — the tool never guesses.

## 2. The annotation grammar (question level only)

```
- Status: <token> [— <free annotation>]
```

The annotation is never parsed, only preserved — it is the pressure valve that
keeps the token set small. Worked examples:

```
- Status: unanswered — routing to Jérémie
- Status: unresolved — back to the model to fold the review
- Status: deferred — awaiting user data, revisit after launch
- Status: superseded — by QST-SCOPE (successor covers both cases)
```

The `superseded — by QST-X` pointer is **taught, never parsed as load-bearing**;
tools may harvest it opportunistically (read-wide/write-canonical, applied to
annotations).

**Document level is different, on purpose**: the document `Status:` field is
workflow state consumed by tooling — it stays a **strict five-value enum**
(`Draft | Accepted | Partially Implemented | Implemented | Superseded`;
case-insensitive read, canonical-case write) with **no annotation grammar
taught**. When a document needs to say more, use structured fields
(`**Awaiting**:`, `**Scope Remaining**:`) instead of decorating the enum. The
asymmetry is a feature: two levels, two kinds of consumer, two tools matched
to them.

## 3. Question identity: handles and anchors — one story

Two mechanisms, one hierarchy:

- **Handle** (everyday): `### QST-<ID>: <title>` — the id is 1–24 letters/digits
  with interior hyphens (`QST-STATUS-VOCAB:` is legal; `QST--X:` is not).
  Canonical-**optional**: a bare `### QST:` is always legal; add the handle when
  the question will be referenced. The ethos, ratified: *a question that is
  referenced must have a handle.*
- **Anchor comment** (advanced): `<!-- @adr-anchor: <slug> -->` placed as the
  **first non-blank content AFTER the heading** — before the heading it silently
  binds to the previous section (two experienced writers made exactly this
  mistake the same night; placement is the whole rule). Use it when the heading
  must stay pure prose, or when the id must survive retitling. Where both exist,
  the comment wins resolution.

## 4. Answer forms

**Attribution** (the byline):

```
**ANS:** (by <name>, <date optional>)
```

The `by`/`from` keyword is what makes it a byline; a bare parenthetical stays
part of your answer. (`**ANS:** (Jérémie)` is answer *content*, preserved
verbatim — "parses on world-knowledge" is the failure mode this rule prevents.)

**The empty answer**: `[Fill this in]` is the sole placeholder that tools emit
and the template teaches. Other forms (`TBD`, `[pending]`, bare `[]`) are read
tolerantly, written never.

**Where the block ends — the `---` is load-bearing**: a QST block runs to the
next `###` heading or a bare thematic break (`---`), and inside it the answer
layer collects *everything* after the ANS marker until the next attributed
marker. So trailing commentary — a `NOT:` filing note, a routing remark, any
prose meant as *about* the question rather than *the answer to it* — must sit
**after a `---`**, never bare below the ANS slot, or the parser reads it as
answer content. (The rule has lived in the extension's parser since the
founder's 2026-07 parse-accuracy reports; taught here since 3.11.5.)

**Pending state** — the answer isn't ready and you want to say where things
stand. Two taught outlets:

- *Headline (lifecycle state)*: put it on the Status line, whose job this is —
  `- Status: unanswered — routing to Jérémie`
- *Overflow (answer-production state)*: a bracketed placeholder-with-note —
  `**ANS:** [Pending: Loftsman's benchmark results due Friday]`

**✗ Never this**:

```
**ANS:** _pending — routing to Jérémie_
```

Bare or italic prose in the ANS slot breaks the slot's contract — **the ANS
text IS the answer**; every tool that layers, prefills, or writes leans on that
contract, and each overload is a question that silently vanishes or prefills
junk into the human's box.

## 5. The reserved invisible channel

HTML comments carry machine-facing markers, in one frozen shape:

```
<!-- @adr-<action>: <value> -->
```

Current family: `@adr-anchor: <slug>` (identity, §3) and
`@adr-dismissed: <reason-slug>` (on a QST heading line: this candidate is not
actually a question; initial reason vocabulary is `not-a-question` only — the
shape is closed, the reason list grows on evidence). The channel is invisible
on GitHub by design — that is its degrade-gracefully property.

**The one grandfathered exception**, named by exact string so no tidiness
crusade misreads it: the template version marker
`<!-- adr template version: "<stem> X.Y.Z" -->` (line 1 of template files and
documents minted from them) predates the family shape and is blessed as-is.
Fossil markers on existing documents are historical truth — never re-stamp them.

## 6. When a taught form must die

Demotion follows the ratified deprecation policy (three rules: zero live
census instances ecosystem-wide or visible offered-and-declined migration;
one full cycle of loud diagnostics before any harder failure — silence is
never the first step; every removal on the record, never by quiet
redefinition). Retiring a tolerance is a register-visible event, not a
bug-fix impulse. See `docs/METHODOLOGY.md` § deprecation.

---

*Landed at template v3.10.0 (the ADR-0032 pairing) by Shipwright 5
(Claude Fable 5, ADRs4AI HQ). The freeze note carries two honest riders from
the council: the `superseded` pointer is intended syntax-invariant across
question/seed/document levels, but the document level is not yet built to
match; and envelope-tag examples in any teaching material appear escaped or
fenced — teaching files are substrate too.*
