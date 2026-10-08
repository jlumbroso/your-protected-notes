# your-protected-notes

**An MCP server that knows who is asking.** Minimal Neon Auth prototype:
one `notes` table, four tools, three modes —

| mode | trigger | what you see |
|---|---|---|
| **guest** | no `Authorization` header | the shared guest commons |
| **user** | valid Neon Auth (Stack) JWT | your private shelf |
| **error** | invalid/expired token | a loud failure — never silent guest-ing (ADR-0001 D4) |

Tools: `user_status` (always answers) · `add_note` · `list_notes` ·
`clear_notes`. Notes get 4-char **Crockford Base32** petnames (`A7K2` —
no I/L/O/U, readable aloud), unique per shelf.

- **Setup**: Neon project → enable Neon Auth (Stack) → fill `.env` from
  `.env.example` (`DATABASE_URL`, `NEON_AUTH_JWKS_URL`, `STACK_PROJECT_ID`).
- **Start here if you're new**: [docs/adr/0001](docs/adr/0001-an-mcp-server-that-knows-who-is-asking.md)
  is the self-contained account — what this is, every technology it stands
  on, all four decisions with roads not taken, and two QSTs posed (and
  recommended, but deliberately NOT closed) before the code existed.
- **Already have a server storing in Neon?**
  [docs/RETROFIT-NEON-AUTH.md](docs/RETROFIT-NEON-AUTH.md) is written to be
  handed to your Claude.
- **Open**: how the token reaches the server from claude.ai ([ADR-0002](docs/adr/0002-how-does-the-token-reach-the-server.md) — spike pending).

*Founded 2026-10-08 from
[human-ai-collaboration-template-A](https://github.com/ADRs4AI/human-ai-collaboration-template-A),
fixtures stripped. CAM (CIS 7000, Penn, Fall 2026) · private prototype.*
