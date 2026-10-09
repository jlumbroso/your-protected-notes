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

1. neon.tech → your project (**reuse level 2's** — auth attaches to the
   database you already have). In the sidebar: **Auth** → enable, with
   provider **Stack** (Stack Auth is the identity service Neon wires in:
   it stores your users, checks their passwords, signs their tokens).
2. Notice the new `neon_auth.users_sync` table in your database: your
   user list, synced *into* your own Postgres. You never write it; you
   may JOIN it (that's how `user_status` shows an email).
3. The Auth page now shows everything you'll copy in step 3. In plain
   words:

| Variable | What it actually is | Where to copy it |
|---|---|---|
| `DATABASE_URL` | the address+password of your Postgres (same as level 2) | project → **Connect** → connection string (`postgresql://…`) |
| `NEON_AUTH_JWKS_URL` | the public keys your server uses to CHECK token signatures | project → **Auth** → JWKS URL |
| `STACK_PROJECT_ID` | which user-base to trust — the id of YOUR Stack project | project → **Auth** → project id |
| `STACK_PUB_CLIENT_KEY` | the publishable key the login page uses to talk to Stack (`pck_…`, not secret) | project → **Auth** → publishable key |
| `PUBLIC_URL` | your own server's address, so the login/OAuth pages advertise the right home | you know it after step 3: `https://<your-service>.onrender.com` |

## 3. Deploy (render.com — same moves as level 2)

Use this template (the button — it keeps the lineage), Render → New →
Blueprint → your fork; paste the **five variables** from the step-2
table when asked (for `PUBLIC_URL`, Render shows your service URL on
the dashboard the moment the service exists — paste it and redeploy if
you filled it last). Your MCP URL is
`https://<your-service>.onrender.com/mcp`.

## 4. Feel the difference

1. Connect your Claude (no sign-in yet) and ask: *"what's my user status?"*
   — **guest**. Add a note. Your neighbor, also a guest, can see it:
   you're on the shared commons.
2. Sign in — the server runs its own OAuth now. When ADDING the
   connector, two overrides matter:
   - Authentication: claude.ai will say "No sign-in — **Detected**".
     Override to **Sign in now** (this server is polite to guests, so it
     must be told to ask).
   - OAuth client: **Register automatically (DCR)**.
   The server's own login page opens (sign in, or "New here — sign up").
   **Timeouts**: the free-tier server naps — the first load can take
   ~1 minute (retry once); finish the login within 5 minutes (codes
   expire); afterwards renewal is automatic. Then ask again: **user**,
   with your email. Add a note. Your neighbor *cannot* see this one.
3. That one-minute contrast — commons vs. shelf — is what authentication
   *is*. Everything else is machinery in its service.

## 5. Retrofit your real instrument

The level isn't the notes server — it's the move. Your level-2 memory (or
whatever it became: moods, catches, gems) stores data worth owning.
[docs/RETROFIT-NEON-AUTH.md](docs/RETROFIT-NEON-AUTH.md) is written to be
handed to your Claude: *"help me add auth to my server following this
guide."* One column, one function, three modes — and then your memory is
**yours**.
