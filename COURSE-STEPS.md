# your-protected-notes — the steps, in class order

*Level 3 of the instrument series. **Level 1**,
[`your-first-instrument`](https://github.com/jlumbroso/test-time-mcp-exercise),
gave your model a sense of time. **Level 2**,
[`your-first-memory`](https://github.com/jlumbroso/your-first-memory), gave it
a record that outlives the conversation. This level gives the record an
**owner**: the server learns who is asking. Each level is the previous one
plus exactly one idea — if level 2 felt comfortable, you have everything you
need here.*

## 0. Read the account (new at this level)

[docs/adr/0001](docs/adr/0001-an-mcp-server-that-knows-who-is-asking.md) is
the self-contained story — every technology, every decision, every road not
taken, and two questions that were posed *before the code existed*. You don't
have to agree with the decisions; you have to be able to find them.

## 1. Read the server (still 3 minutes, really)

`server.py`. Compare against level 2's: the diff is one column
(`user_id`), one function (`current_identity`), and one new tool
(`user_status`). That diff is the whole level.

## 2. Get your database + enable Neon Auth

1. neon.tech → your project (reuse level 2's!) → **Auth** → enable
   (provider: Stack). You receive a **JWKS URL** and a project id.
2. Notice the new `neon_auth.users_sync` table in your database: the user
   list, synced *into* your own Postgres. You never write it; you may JOIN it.
3. Copy, as in level 2, the **connection string**.

## 3. Deploy (render.com — same moves as level 2)

Use this template (the button — it keeps the lineage), Render → New →
Blueprint → your fork; paste `DATABASE_URL`, `NEON_AUTH_JWKS_URL`, and
`STACK_PROJECT_ID` when asked. Your MCP URL is
`https://<your-service>.onrender.com/mcp`.

## 4. Feel the difference

1. Connect your Claude (no sign-in yet) and ask: *"what's my user status?"*
   — **guest**. Add a note. Your neighbor, also a guest, can see it:
   you're on the shared commons.
2. Sign in (your instructor will show the token step for your setup —
   see [docs/adr/0002](docs/adr/0002-how-does-the-token-reach-the-server.md)
   for why this step is still ours to smooth). Ask again: **user**, with
   your email. Add a note. Your neighbor *cannot* see this one.
3. That one-minute contrast — commons vs. shelf — is what authentication
   *is*. Everything else is machinery in its service.

## 5. Retrofit your real instrument

The level isn't the notes server — it's the move. Your level-2 memory (or
whatever it became: moods, catches, gems) stores data worth owning.
[docs/RETROFIT-NEON-AUTH.md](docs/RETROFIT-NEON-AUTH.md) is written to be
handed to your Claude: *"help me add auth to my server following this
guide."* One column, one function, three modes — and then your memory is
**yours**.
