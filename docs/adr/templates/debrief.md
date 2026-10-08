<!-- adr template version: "debrief 3.9.0" -->

# DEBRIEF-NNN: [Brief Label]

- **Date**: YYYY-MM-DD
- **Failure Class**: [See docs/adr/templates/failure-classes.md for taxonomy]
- **Incident**: [One sentence: what happened]
- **Discovered by**: [Human / AI / test / user]
- **Fixed in**: [commit hash or PR link]

---

## Guidance for Root Cause Analysis

This debrief captures **what was learned**, not just what was fixed.

**Key questions** (work through these even without deep frameworks):
1. What architectural gap made this bug possible?
2. Which subsystems were involved, and what did each assume?
3. What contract was missing or underspecified?
4. What rule prevents this failure class going forward?

**If available**: Consult the Architecture of Complexity skill 
(`/mnt/skills/user/architecture-of-complexity/SKILL.md`) for 
deeper analysis of near-decomposability, interface contracts, 
and stable intermediate forms.

---

## Symptom

What was experienced or would have been experienced by a user.

[Describe the observable behavior - error message, wrong output, crash, etc.]

---

## Reproduction

Can you trigger this bug on demand?

- [ ] Can reproduce the original bug consistently
- [ ] Can verify the fix resolves it
- [ ] Understand why the fix works (mechanism, not just correlation)

**Steps to reproduce:**
[How to trigger the bug - specific commands, inputs, conditions]

**Reproduction notes:**
[Document what happened when you tried to reproduce]

**If you CANNOT reproduce:**
- Was this a transient error? (database lock, network timeout, race condition)
- Is the diagnosis based on correlation, not causation?
- Might the "fix" be blocking things unnecessarily?

**Key insight:** If you can't make the bug happen again, question whether 
your understanding of the root cause is correct.

---

## Root Cause (structural)

NOT "the code at line N was wrong." Instead, answer:
- What architectural gap made this possible?
- Which subsystems touched this, and what did each assume?
- Was there missing ownership? Underspecified contract?
- Is this a near-decomposability failure? (Two subsystems that should be independent but weren't, because the interface was underspecified)

**If Architecture of Complexity skill available**: Consider whether this is a failure of:
- Near-decomposability (subsystems more coupled than they should be)
- Interface specification (contract between modules unclear)
- Stable intermediate forms (no clear ownership of state)

[Your structural analysis here]

---

## Contract Established

The permanent rule that now exists. This is the **deliverable** of the debrief.

Ask:
- What invariant should hold?
- Who owns this state/behavior?
- What does the interface promise?
- How do we make this failure class structurally impossible?

**Write as a positive rule** (examples from real debriefs):

**Ownership contract:**
> "The `questions` refresh subsystem is the single source of truth for `idx`. 
> Other components read it but never modify it."

**Validation contract:**
> "Before deploying a fix that blocks messages based on content markers:
> 1. Extract actual blob, test with target API (NSUnarchiver)
> 2. Test both positive case (does crash) and negative case (doesn't always have marker)
> 3. End-to-end validation with actual client"

**Interface contract:**
> "The `textFromAttributedBody()` function guarantees: if NSUnarchiver succeeds, 
> message has text. If it returns nil or throws, message shows as [attachment].
> No preemptive blocking based on heuristics."

**API contract:**
> "The `/search` endpoint promises to return results in <500ms. If processing
> exceeds 400ms, return partial results with `incomplete: true` flag."

---

[Your contract specification here]

---

## Regression Test

- **Link**: `path/to/test.ts`
- **Test description**: [The describe/it text from the test]
- **What it catches**: [This specific bug instance]

**Code reference** (optional):
```typescript
// Example of the regression test
describe('Regression tests', () => {
  it('should handle dual ownership correctly (DEBRIEF-001)', () => {
    // Bug: two subsystems both modified idx
    // Fixed in commit abc123
    // ...
  });
});
```

---

## Navigation (optional)

Use only when needed for clarification or additional context.

### QST: [Question for human if AI needs clarification]
- Status: unanswered
- Why asking: [Context]

**ANS:** (by [name])
[Fill this in]

---

### NOT: [Any observations, patterns, or insights worth recording]

[Notes here]

---

## Related Debriefs

Links to other debriefs in the same failure class (helps identify patterns over time):

- [DEBRIEF-NNN: Related incident] - [Brief connection]

---

## Related ADRs

Links to architectural decisions that emerged from this analysis:

- [ADR-NNN: Title] - [How it relates]

---

## Validation

When the debrief is complete:
- [ ] Root cause is structural, not local
- [ ] Contract is stated as a positive rule
- [ ] Regression test exists and is linked
- [ ] Failure class is identified

**Notes**: [Any follow-up needed or open questions]

---

## Iterations

### Iteration 1 ([date])
- [Who contributed what]
- [What analysis emerged]
- [What changed]
