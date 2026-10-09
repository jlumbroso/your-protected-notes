# Neon Auth moved: Stack → Managed Better Auth (what it means here)

*Researched and probe-verified 2026-10-08 evening, after Jérémie found the
console no longer matched our instructions. Every claim below was either
read in Neon's current docs or demonstrated against a live throwaway
project (`better-auth-probe`); nothing is inferred-only.*

## What changed

- **Neon's docs**: "Legacy Neon Auth (Stack Auth) is **no longer accepting
  new users**" · "We'll keep supporting it for existing users." New
  projects get **Managed Better Auth** — built on the open-source
  better-auth, with Neon hosting the auth server per-branch and the
  **database as the source of truth**.
- Practical console consequence: the Auth page our course material
  described (project id, publishable key) no longer exists for new
  projects. The new page shows **one base URL**:
  `https://<endpoint>.neonauth.<region>.neon.tech/<db>/auth`.

## What we verified empirically (the shape of the new world)

| Aspect | Legacy Stack | Managed Better Auth (probed) |
|---|---|---|
| Config you copy | JWKS URL + publishable key (+ ids) | **one base URL** |
| JWKS | api.stack-auth.com per-project URL | `{base}/.well-known/jwks.json` — exists, 1 key |
| JWT algorithm | ES256/RS256 | **EdDSA** (verifiers must allow it!) |
| JWT lifetime | ~1 h | **900 s** — refresh matters |
| Email for display | JOIN `neon_auth.users_sync` | **in the JWT claims** (and `neon_auth."user"`) |
| User tables | `neon_auth.users_sync` (mirror) | better-auth natives: `"user"`, `session`, `account`, `jwks`… — **no `users_sync`** (the MCP provision response still *says* `users_sync`; stale) |
| Sign-up/in REST | `/auth/password/sign-{up,in}` at Stack | `{base}/sign-{up,in}/email` — **`Origin` header required** |
| Session → JWT | token in response body | session **cookie** (`__Secure-neon-auth.session_token`) → `GET {base}/token` |
| Trusted-domain config | required for callbacks (bit us at 5:15 PM) | not hit in probing (watch) |

## What this repo does about it

`server.py` + `auth.py` are now **dual-provider**, switched by one
environment variable:

- **`NEON_AUTH_BASE_URL` set** → Better Auth mode: login page relays to
  `{base}/sign-{up,in}/email` (with Origin), exchanges the session cookie
  at `{base}/token`, hands claude.ai the EdDSA JWT; OAuth refresh re-runs
  the exchange (`refresh_token` carries the session, prefixed `ba:`).
  JWKS is derived from the base URL. Email read from claims.
- **Otherwise** → legacy Stack mode, exactly as the class ran on
  2026-10-08 (kept working all night; Neon has promised continued
  support).

Both modes pass the full scripted OAuth dance
(`scripts/2026-10-08-oauth-dance-probe.py`): discovery → DCR → login →
code → PKCE token → user mode.

## For the course

- **Existing class infrastructure** (the session-6 demo server and its
  Stack users): unchanged, keeps working.
- **Students creating new projects** (session 7 onward): follow the
  Better Auth path in COURSE-STEPS — now the primary one, **three**
  variables total (`DATABASE_URL`, `NEON_AUTH_BASE_URL`, `PUBLIC_URL`).
- **Open question** (watch list): Neon's migration tooling for moving a
  legacy Stack project onto Managed Better Auth — the docs describe code
  changes and an "eject" path; whether the class demo project should
  migrate is a decision for the s7 prep, not a necessity.
