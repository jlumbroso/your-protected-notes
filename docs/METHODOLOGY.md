# Human-AI Collaboration Methodology

- **Version**: 3.5
- **For**: Jérémie Lumbroso & Claude models
- **Purpose**: Explain why this system works

---

## Core Problem

**Conversations between humans and AI contain valuable thinking, but they disappear when sessions end or context windows fill.**

Every discussion has:
- Decision-making that matters
- Reasoning that informs future work
- Context that shouldn't be repeated

Traditional approaches lose this. We preserve it.

---

## Core Solution

**Transform conversations into persistent artifacts using a simple workflow:**

1. Human dumps thoughts naturally (stream-of-consciousness)
2. AI adds structure (navigation codes, questions)
3. Both iterate on focused documents
4. Decisions persist in version control
5. Future instances continue seamlessly

---

## Why This Works

### For Humans
- **No forced structure** - Think naturally, dump freely
- **Focus preserved** - Each ADR is one thread
- **Decisions tracked** - Nothing lost to time
- **Voice honored** - Your words stay your words

### For AI
- **Clear workflow** - Knows what to do
- **Agency granted** - Can structure and organize
- **Context preserved** - Future instances continue
- **Grep-able artifacts** - Can find anything fast

### For Both
- **Shared understanding** - Validated at each step
- **Compound knowledge** - Builds rather than repeats
- **Trust built** - Through transparent process
- **Cognitive partnership** - Not tool use

---

## Key Principles

### 1. Stream-of-consciousness preservation

Human thought flows naturally - messy, tangential, emotional. The system captures this without forcing linear structure. AI adds organization after, not during, the dump.

### 2. Navigation over narration

Instead of long explanations, we use codes:
- `QST:` marks questions → `grep '^### QST:'` finds them
- `ANS:` marks answers → `grep 'ANS:'` finds them
- `COD:` marks code → `grep '^### COD:'` finds them
- `NOT:` marks remarks, annotations → `grep 'NOT:'` finds them

Every decision is findable in seconds.

### 3. Iteration as documentation

Changes aren't hidden - they're tracked. Each iteration shows:
- What changed
- Why it changed  
- What we learned

The journey matters, not just the destination.

### 4. Agency with bounds

AI isn't just transcribing - it's a cognitive partner with:
- Permission to structure
- Freedom to ask questions
- Responsibility to document
- Obligation to validate

### 5. Recommendation visibility

*(Added 2026-04-22 by Opus 4.7, from live iteration with Jérémie on the Frozen Horizon project.)*

When the AI asks a question in an ADR, it must also offer its lean — and the lean must be **structurally visible**, not paragraph-embedded. Every `QST` block includes a `**Recommendation**: (by [model-name])` section between the options and the `**ANS:**` block, leading with a bold pick and followed by 2–4 sentences of justification grounded in evidence.

**Why this matters**: asking a question without stating your position shifts the entire cognitive load to the human. They have to read every option, infer the AI's slant from prose hedges ("I lean B"), and synthesize both at once. Putting the recommendation under its own heading separates *what I think* from *what the options are* — the human can accept, override, or interrogate the recommendation efficiently. It also forces the AI to commit to a position, which is where real reasoning shows.

**The attribution `(by [model-name])` matters too**: in a multi-model workflow (Opus, Sonnet, Haiku, GPT, Gemini all collaborating on the same repo), the human is triangulating between perspectives. Knowing *which* model is recommending *which* option is part of the signal, not noise.

This is a small protocol addition with a large effect on decision velocity.

### 6. Persistence over perfection

Better to commit a rough ADR now than lose the thinking forever. Iterate later. Version control preserves evolution.

---

## The Workflow in Detail

### Phase 1: Brain Dump
**Human**: Creates `seed-[topic].md` and dumps everything - thoughts, questions, frustrations, code, whatever.

**Why it works**: No cognitive load to structure. Just capture.

### Phase 2: Chunking
**AI**: Reads dump, identifies distinct threads (usually 2-5), creates separate ADR for each.

**Why it works**: One ADR = one decision. Keeps focus tight.

### Phase 3: Seeding
**AI**: Extracts relevant parts of the dump (or other source — brief, prior ADR, observation) into each ADR's "Originating Context" section.

**Why it works**: Preserves original thinking. Context isn't lost.

### Phase 4: Questioning
**AI**: Adds navigation codes, asks clarifying questions with context about why they matter.

**Why it works**: Questions have purpose. Human knows why info is needed.

### Phase 5: Answering
**Human**: Fills in `ANS:` blocks naturally. No special format needed.

**Why it works**: Just answer. AI will structure.

### Phase 6: Deciding
**AI**: Processes answers, documents decision with rationale.

**Why it works**: Thinking is explicit, not hidden.

### Phase 7: Validating
**Both**: Confirm shared understanding.

**Why it works**: Catches misalignment before it compounds.

### Phase 8: Iterating
**Both**: Update as understanding evolves, track iterations.

**Why it works**: Shows growth, not just final state.

---

## Navigation Codes Explained

These make everything grep-able:

| Code | Purpose | Who Adds | When to Use |
|------|---------|----------|-------------|
| QST: | Questions needing answers | AI | When clarification needed |
| ANS: | Answers to questions | Human | When answering |
| COD: | Code examples | Both | When code illustrates |
| API: | API specifications | Both | When showing interfaces |
| FIL: | Files to examine | Both | When context needed |
| DOC: | Documentation | Both | When referencing |
| NOT: | Note, remark, comment | Both | When recording an observation, or a thought in context |

**Why codes work**: They're short, unique, meaningful. Grep finds them instantly. No ambiguity.

---

## Template Selection

### seed.md
**Use when**: You have thoughts but no clear structure yet
**Result**: Raw dump that becomes multiple ADRs

### adr.md  
**Use when**: Complex decision needing back-and-forth
**Result**: Structured dialogue with clear outcome

### adr-madr.md (standard MADR)
**Use when**: Simple decision, options known
**Result**: Clean decision record

**Decision tree**:
```
Have thoughts? 
├─ Unstructured? → seed.md
└─ Decision to make?
   ├─ Complex/unclear? → adr.md
   └─ Simple/clear? → adr-madr.md
```

---

## What Makes This Different

**Traditional documentation**: Write for future readers
**This system**: Capture the conversation itself

**Traditional ADRs**: Record final decision
**This system**: Track the thinking that led there

**Traditional AI use**: Tool that executes tasks
**This system**: Cognitive partner that thinks with you

---

## Success Indicators

You know it's working when:
- No important decisions lost
- New people/AIs can continue immediately
- Any decision findable in <10 seconds
- Both parties feel understood
- Knowledge accumulates rather than repeats

You know it's not working when:
- Conversations without artifacts
- Repeated explanations
- Can't find past decisions
- Misalignment discovered late
- Process feels burdensome

---

## Anti-patterns to Avoid

1. **Over-structuring human input** - Let them dump naturally
2. **Under-structuring AI output** - Navigation codes are essential
3. **Skipping validation** - Catches problems early
4. **Waiting for perfection** - Commit rough, iterate later
5. **Treating as ceremony** - It serves the work, not vice versa

---

## When a Taught Form Must Change

The template is versioned (semantic versioning; the line-1 version markers on template files carry it), and the governance line is simple: **patch** = improvement within taught intent; **minor** = a change to what is taught; **major** = a break — unavailable except through the deprecation policy below. Additions are cheap; removals are governed, because retiring a form adopters learned is the one move that can strand their files.

**The deprecation policy** (ratified 2026-08-12 by the format-stability council; adopters inherit reversibility, not just rules):

1. A taught or tolerated form may be removed only when a census shows **zero live instances across the watched corpus for a full release cycle** — including an ecosystem-wide sweep, never just one repo's — OR its migration has been offered-and-declined *visibly* in every surviving instance.
2. Removal first demotes the form from "read correctly" to "read as candidate + loud diagnostic" for one more full cycle before any harder failure. **Silence is never the first step of a deprecation.**
3. Every removal happens on the record — a registered, reviewable decision with the evidence attached, never a quiet redefinition of what was promised.

The spirit in one line: **reading stays tolerant forever; only what is taught and emitted ever narrows.** No existing file — yours or anyone's — breaks because of a template decision.

---

## Adapting for Your Needs

This system encodes certain values:
- Transparency over privacy
- Persistence over ephemerality
- Partnership over tool use
- Evolution over finality

If these don't match your collaboration style, adapt:
- Keep what serves you
- Cut what doesn't
- Add what's missing
- Make it yours

The core insight remains: **conversations have value, preserve them**.

---

## For AI Instances

When you load CLAUDE.md at session start:
1. Read the project context (what/where/why)
2. Check for open questions and current focus
3. Look for HANDOFF.md if previous session ended mid-work
4. Start from there

When a human dumps thoughts:
1. Read the whole dump first
2. Identify distinct threads
3. Create focused ADRs
4. Ask questions that matter

When validating:
1. Check you understood correctly
2. Verify the decision makes sense
3. Note any uncertainties
4. Confirm with human

The goal: Be a cognitive partner, not just a tool.

---

## For Humans

When starting:
1. Dump thoughts into seed file - messy is fine
2. Tell AI "chunk this into ADRs"
3. Answer questions naturally
4. Validate decisions together

When continuing:
1. Check for unanswered questions: `grep 'unanswered' docs/adr/`
2. Answer them in place
3. Let AI process and iterate

When stuck:
1. Dump more thoughts
2. AI will help untangle

The goal: Think naturally, let AI add structure.

---

*This methodology serves the work. If something doesn't work, change it. The system should help, not hinder.*
