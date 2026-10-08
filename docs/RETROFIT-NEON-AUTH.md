# Retrofit guide: add Neon Auth to a project that already stores data in Neon

*This document is written to be handed to a Claude model. Student: paste it
(or its URL) into your conversation and say "help me add auth to my server
following this guide." Model: the steps below are ordered; the schema
migration in step 3 is the only irreversible one — show the human the SQL
and get their go before running it.*

## What you start with
A working MCP server (e.g. `your-first-memory`) with tables in a Neon
project, keyed by nothing — every caller sees the same rows.

## What you end with
The same server, three-mode (`guest` / `user` / loud error), with existing
rows preserved on a shared commons and new signed-in rows private per user.

## Steps

**1. Provision Neon Auth on the SAME project that holds your data.**
Neon console → your project → *Auth* → enable (provider: Stack), or via the
Neon MCP: `provision_neon_auth(project_id, branch_id, auth_provider="stack")`.
You receive: a Stack project id, a publishable client key, and a **JWKS URL**.
A `neon_auth.users_sync` table appears in your database — users will sync
into it; you never write it.

**2. Set two new environment variables on your deployment** (Render →
Environment): `NEON_AUTH_JWKS_URL` and `STACK_PROJECT_ID`. Like
`DATABASE_URL`, they are configuration, not code (your ADR on secrets
already covers why).

**3. Migrate your schema: add the ownership column.**
```sql
ALTER TABLE <your_table> ADD COLUMN user_id TEXT;   -- NULL = pre-auth rows
```
Existing rows keep `NULL` — they become the guest commons, so **nothing you
stored before auth is lost**; it is simply public-to-guests, which it
already was in fact. (Decide with your human whether that is acceptable or
whether old rows should be claimed by their owner / archived.)

**4. Add identity resolution to the server** — copy `current_identity()`
from this repo's `server.py`. The contract (ADR-0004): absent token →
`(None, None)` = guest; valid token → `(sub, email)`; invalid token →
raise. Key on `sub`, never email (ADR-0001).

**5. Thread `user_id` through every query.**
Reads: `WHERE user_id IS NOT DISTINCT FROM %s` (NULL-safe equality — plain
`=` silently fails on NULL). Writes: insert the resolved `user_id`.
Deletes: same `IS NOT DISTINCT FROM` guard, so a guest can never clear a
user's shelf.

**6. Add `user_status`** (copy the tool) — it is your probe for every step
after this one.

**7. Test the three modes** before telling anyone it works:
no header → guest; a real token (see this repo's `scripts/mint-test-token`
pattern) → your email; a garbled token → an error, NOT guest. If the third
check comes back "guest," stop: you have the silent-misfiling bug ADR-0004
exists to prevent.

**8. Write YOUR ADR.** You just made real decisions (commons vs. claim for
old rows; refuse-guests or not). Record them with the roads not taken —
template in `docs/adr/templates/`.
