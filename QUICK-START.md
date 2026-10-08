# Quick Start Card

**Streamlined Human-AI Collaboration System A v3.2**

---

## 30-Second Overview

This system preserves valuable conversations by turning them into persistent artifacts.

**You**: Dump thoughts naturally → **Claude**: Adds structure → **Together**: Make decisions that persist

---

## Essential Files (3)

1. **CLAUDE.md** (87 lines) - Claude reads this at session start
2. **seed.md** (12 lines) - For brain dumps
3. **adr.md** (~120 lines) - For decisions

---

## The Workflow (5 steps)

```
1. Dump → Create seed-[topic].md with all your thoughts
2. Tell → "Claude, chunk this into ADRs"
3. Answer → Fill in ANS: blocks naturally
4. Decide → Claude documents with rationale
5. Persist → Decisions in version control
```

---

## Navigation Codes (6 codes)

Find anything instantly:
```bash
QST:  # Questions     → grep '^### QST:' docs/adr/
ANS:  # Answers       → grep 'ANS:' docs/adr/
COD:  # Code examples → grep '^### COD:' docs/adr/
API:  # API calls     → grep '^### API:' docs/adr/
FIL:  # Files         → grep '^### FIL:' docs/adr/
DOC:  # Documentation → grep '^### DOC:' docs/adr/
NOT:  # Notes, remarks, comments, observations → grep 'NOT:' docs/adr/
```

---

## File Structure

```
project/
├── CLAUDE.md              # Customize this per project
├── docs/adr/
│   ├── seed-*.md          # Brain dumps
│   ├── 0001-*.md          # ADRs (numbered)
│   └── templates/         # Templates
└── [your code]
```

---

## When to Use What

| Have... | Use... |
|---------|--------|
| Messy thoughts | seed.md |
| Complex decision | adr.md |
| Simple decision | adr-madr.md (MADR) |
| Quick question | Just ask (escalate if needed) |

---

## Customize CLAUDE.md

Replace these sections:
```markdown
### What we're building:
[Your project description]

### Current focus:
[What you're working on now]

### Key decisions made:
- [Decision 1] - See docs/adr/0001-*.md
```

---

## Success Check

✅ Important decisions don't disappear
✅ New AI instances continue seamlessly  
✅ Find past decisions in <10 seconds
✅ Process feels helpful, not burdensome

---

## First Session

1. Tell Claude: "I've dumped thoughts in seed-[topic].md"
2. Claude creates ADRs
3. You answer questions
4. Decisions documented
5. Done

---

## Core Principle

**Conversations have value. Preserve them without ceremony.**

---

## Learn More

- **README.md** - Full documentation
- **METHODOLOGY.md** - The "why"

---

## Version

v3.0 - Streamlined by Claude Sonnet 4.5 (Nov 2025)

---

**Ready? Start with Claude Code.** 🚀

---

*Print this card. Keep it handy. Start preserving conversations.*
