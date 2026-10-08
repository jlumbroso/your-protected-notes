<!-- adr template version: "failure-classes 3.8.0" -->

# Failure Class Taxonomy

**Purpose**: Categorize structural failure patterns to recognize them across incidents and establish preventive contracts.

**Version**: 1.0 (Initial taxonomy, will grow with each debrief)

---

## How to Use This Document

### When writing a debrief:
1. Review the classes below to see if your incident matches an existing pattern
2. If it matches, cite the class name in the **Failure Class** field
3. If it's new, add it to this document as part of the debrief process

### When adding a new class:
- Include pattern description (what makes it this class)
- Provide at least one concrete example (link to DEBRIEF-NNN)
- Specify what kind of contract typically prevents this class
- Reference Architecture of Complexity concepts if relevant

---

## Process Failures

Process failures occur when the **methodology** for making changes fails, independent of technical correctness.

### Untested Hypothesis / Premature Fix

**Pattern:** Fix deployed based on correlation without validating causation

**Characteristics:**
- Hypothesis formed from observing symptoms
- Fix deployed without testing if hypothesis is correct
- Often occurs under time pressure or when "it seems obvious"
- The fix may actually work, but for wrong reasons (or make things worse)

**Examples:**
- DEBRIEF-001: Blocked messages with calendar attributes, assuming they crashed NSUnarchiver - but never tested if they actually crashed

**Contract to establish:**
- Validation gate: reproduce the bug, verify the fix resolves it, understand mechanism
- Test both positive case (does crash) and negative case (doesn't always have marker)
- No preemptive blocking based on heuristics without concrete evidence

**Key question:** Can you make the bug happen on demand? If not, question your diagnosis.

---

### Missing Validation Gate

**Pattern:** Changes deployed without verifying they achieve intended effect

**Characteristics:**
- Assumption that code change = problem solved
- No end-to-end testing of the fix
- Tests verify partial behavior but not complete user experience
- Particularly dangerous with crash fixes or error handling

**Examples:**
- (To be added as encountered)

**Contract to establish:**
- Verification requirement: every fix must demonstrate before/after behavior
- End-to-end validation, not just unit test coverage
- "Does this fix actually solve the user's problem?" test

---

## Architectural Failures

Architectural failures occur when the **structure** of the system makes certain bugs possible or likely.

### Dual Ownership

**Pattern:** Two subsystems both believe they own the same state or behavior

**Characteristics:**
- Both subsystems are correct within their local context
- Failure emerges at the interface between them
- Neither is violating a contract, because the contract doesn't specify ownership
- Often an off-by-one, race condition, or inconsistent state issue

**Examples:**
- Off-by-one bug where both `questions` array and refresh logic managed `idx` independently

**Contract to establish:**
- Single source of truth designation: "[Subsystem A] owns [state X]"
- Other components read but never modify
- Clear interface contract for ownership

**Architecture of Complexity reference:**
- This is a near-decomposability failure (Simon)
- Two subsystems that should be nearly independent aren't
- Interface between them is underspecified

---

### Contract Unspecified

**Pattern:** Interface between components exists but its promises/requirements aren't documented

**Characteristics:**
- Components work correctly in isolation
- Integration fails because assumptions don't align
- "It worked before" until conditions changed
- No single source of truth for what the interface guarantees

**Examples:**
- (To be added as encountered)

**Contract to establish:**
- Explicit interface specification
- What does this component promise to its callers?
- What does it require from its dependencies?
- Under what conditions might it fail?

**Architecture of Complexity reference:**
- Interfaces define the decomposition of a complex system
- Unclear interfaces prevent near-decomposability

---

### Near-Decomposability Failure

**Pattern:** Subsystems that should be independent aren't, because coupling is hidden or implicit

**Characteristics:**
- Changes in one component unexpectedly break another
- "I didn't think that would affect this"
- Coupling exists through shared state, assumptions, or timing
- Refactoring reveals unexpected dependencies

**Examples:**
- (To be added as encountered)

**Contract to establish:**
- Make dependencies explicit
- Minimize coupling at interfaces
- Document what each subsystem assumes about the world

**Architecture of Complexity reference:**
- Herbert Simon's "Architecture of Complexity" (1962)
- Systems decompose into nearly independent subsystems
- The "nearly" is critical - interfaces specify the limited coupling
- When subsystems are more coupled than they should be, complexity explodes

**If Architecture of Complexity skill is available**, consult for deeper analysis of:
- Hierarchical decomposition
- Stable intermediate forms
- Interface specifications as coupling minimizers

---

### Race Condition / Timing Dependency

**Pattern:** Behavior depends on the order/timing of events that isn't guaranteed

**Characteristics:**
- "It works most of the time"
- Fails under specific timing conditions (slow network, fast CPU, etc.)
- Often involves async operations, promises, event handlers
- Hard to reproduce consistently

**Examples:**
- (To be added as encountered)

**Contract to establish:**
- Explicit ordering guarantees
- Synchronization mechanisms (locks, queues, etc.)
- "This operation completes before that operation begins"

---

## Data Failures

Data failures occur when **assumptions about data** turn out to be wrong.

### Null/Undefined Handling

**Pattern:** Code doesn't handle absence of expected data

**Characteristics:**
- "Cannot read property X of undefined"
- Assumptions about what's always present
- Often revealed by edge cases or unusual user behavior

**Examples:**
- (To be added as encountered)

**Contract to establish:**
- Null/undefined handling policy
- What's guaranteed to exist? What's optional?
- How to handle missing data (default, error, skip?)

---

### Type Mismatch / Schema Drift

**Pattern:** Data structure in one system doesn't match expectations in another

**Characteristics:**
- Database schema vs. TypeScript types diverge
- API returns different shape than expected
- Migration didn't update all consumers
- "It works in dev but not production"

**Examples:**
- (To be added as encountered)

**Contract to establish:**
- Single source of truth for data shape
- Schema validation at boundaries
- Migration checklist (update DB, types, tests, docs)

---

## Testing Failures

Testing failures occur when **tests don't catch what they should**, or create false confidence.

### Test Validates Wrong Thing

**Pattern:** Test passes but doesn't verify actual correctness

**Characteristics:**
- Mock returns what you told it to return (circular test)
- Test verifies implementation detail, not behavior
- Test passes even when real user would see bug
- High coverage but low confidence

**Examples:**
- (To be added as encountered)

**Contract to establish:**
- "Would this test catch a real bug that affects users?"
- Test real behavior, not implementation
- End-to-end tests for critical paths

**See:** Fourth Directive in CLAUDE.md

---

## Adding New Classes

When you encounter a failure that doesn't fit existing classes:

1. **Name it clearly**: Pattern name should describe the structural issue, not the symptom
2. **Describe the pattern**: What makes it this class vs. something else?
3. **Give concrete example**: Link to DEBRIEF-NNN where you first saw it
4. **Specify contract type**: What kind of rule prevents this class going forward?
5. **Reference theory if relevant**: Simon's Architecture of Complexity, etc.

**Template for new class:**
```markdown
### [Class Name]

**Pattern:** [One sentence describing the failure type]

**Characteristics:**
- [Bullet point]
- [Bullet point]

**Examples:**
- [DEBRIEF-NNN: Brief description]

**Contract to establish:**
- [What kind of rule prevents this]

**Architecture of Complexity reference:** (if applicable)
- [How Simon's framework illuminates this]
```

---

## Meta-Observation

This taxonomy itself is a **stable intermediate form** (Simon's term) - it:
- Captures patterns that emerge from specific incidents
- Provides vocabulary for recognizing similar failures
- Enables preventive contracts rather than reactive fixes
- Grows over time as you encounter new failure modes

The goal isn't comprehensive classification, it's **pattern recognition that leads to systemic improvement**.

---

**Version History:**
- v1.0 (2026-03-15): Initial taxonomy with Process, Architectural, Data, and Testing failures
