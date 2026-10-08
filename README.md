# your-protected-notes

**An MCP server that knows who is asking.** Minimal Neon Auth prototype:
one `notes` table, four tools, three modes —

| mode | trigger | what you see |
|---|---|---|
| **guest** | no `Authorization` header | the shared guest commons |
| **user** | valid Neon Auth (Stack) JWT | your private shelf |
| **error** | invalid/expired token | a loud failure — never silent guest-ing (ADR-0004) |

Tools: `user_status` (always answers) · `add_note` · `list_notes` ·
`clear_notes`. Notes get 4-char **Crockford Base32** petnames (`A7K2` —
no I/L/O/U, readable aloud), unique per shelf.

- **Setup**: Neon project → enable Neon Auth (Stack) → fill `.env` from
  `.env.example` (`DATABASE_URL`, `NEON_AUTH_JWKS_URL`, `STACK_PROJECT_ID`).
- **Decisions, with roads not taken**: [docs/adr/](docs/adr/) — two were
  answered *before the code existed* (0001 identity, 0002 guest mode): the
  QST-before-generation pattern this prototype also demonstrates.
- **Already have a server storing in Neon?**
  [docs/RETROFIT-NEON-AUTH.md](docs/RETROFIT-NEON-AUTH.md) is written to be
  handed to your Claude.
- **Open**: how the token reaches the server from claude.ai (ADR-0005 —
  spike pending).

*Founded 2026-10-08 from
[human-ai-collaboration-template-A](https://github.com/ADRs4AI/human-ai-collaboration-template-A),
fixtures stripped. CAM (CIS 7000, Penn, Fall 2026) · private prototype.*
