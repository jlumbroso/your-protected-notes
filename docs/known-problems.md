# Known problems — MCP · Neon Auth · OAuth · the whole stack

*The honest ledger, opened 2026-10-08 (session-6 night) at Jérémie's ask.
Each entry: symptom → cause → what to do → status. Entries are appended,
never silently deleted — a fixed problem keeps its row with a FIXED mark,
because the next cohort will hit the symptom before reading the fix.*

## 1. "Sign-up failed" after a sign-up that actually worked — FIXED (copy)
**Symptom**: you sign up, get redirected (it worked), retry or re-submit,
and see *"Sign-up failed (password too weak, or account exists)"* — reads
like rejection. Live specimen: 2026-10-08 23:49 UTC, two retries on an
account created seconds earlier.
**Cause**: the login page's error copy didn't distinguish Stack's
`USER_EMAIL_ALREADY_EXISTS` from real failures.
**Now**: the page says *"Good news: this email already has an account —
press SIGN IN instead."*

## 2. In-flight logins die on redeploy (and naps)
**Symptom**: the login page worked, but the connector reports failure;
retrying the whole add-connector flow succeeds.
**Cause**: authorization codes and DCR client registrations live
**in memory** (prototype-grade, by design — see ADR-0002). Any restart
— a deploy, a free-tier nap, a crash — wipes codes mid-dance. Issued
TOKENS keep working (verification is stateless JWT), only the in-flight
handshake dies.
**Do**: retry the flow once. **s7 fix**: persist codes/clients in the
database (one small table).

## 3. The free tier naps — first contact is slow
**Symptom**: login page or first tool call takes ~30-60 s or times out.
**Cause**: Render free instances sleep when idle.
**Do**: wait, retry once. Finish the login within **5 minutes** — our
authorization codes expire (one-time, 300 s).

## 4. claude.ai says "No sign-in — Detected" — and it's wrong, on purpose
**Symptom**: adding the connector, claude.ai pre-selects "No sign-in".
**Cause**: this server never 401s (guests are a *mode*, ADR-0001 D2), so
auto-detection concludes no auth exists. A guest-friendly server HIDES
its auth from detectors — a genuine design finding.
**Do**: override to **Sign in now** + OAuth client **Register
automatically (DCR)**. (Or take the "Continue as guest" door on our
login page — added mid-class 2026-10-08.)

## 5. Stack rejects sign-ups relayed from a new host
**Symptom**: login worked locally, failed identically in production
("Sign-up failed") with nothing else changed.
**Cause**: Stack validates `verification_callback_url` against the
project's **trusted domains**; localhost passes by default, your deploy
URL does not.
**Do**: add the deploy URL to Neon Auth's trusted domains (console →
Auth, or the Neon MCP `add_auth_trusted_domain` — note it requires
`auth_provider: "stack"`). Found and fixed 2026-10-08 ~5:15 PM.

## 6. Neon MCP tool quirks (for anyone driving it from a model)
- Parameter naming is inconsistent: some tools want `project_id`, the
  connection-string tool rejects `projectId` — read each error, it lists
  the accepted keys.
- `provision_neon_auth` requires `branch_id` AND `auth_provider`
  (`stack` | `better_auth` | `mock`); the error reveals the options.
- `run_sql` takes bare `sql` + `project_id`, not a params object.

## 7. One transient `POST /mcp 400` right after login — benign (watch)
**Symptom**: a single 400 in the logs immediately after token exchange,
then normal 200/202 traffic.
**Read**: client probing before session init; has not recurred within a
session. Watching; not chased.

## 8. Tables self-create; databases do not
**Symptom**: "DATABASE_URL is not set" or connection failures on a fresh
fork.
**Cause/design**: the server runs `CREATE TABLE IF NOT EXISTS` on every
connection — but the Neon **project** must exist first, made by you
(COURSE-STEPS step 2). Auth likewise: `provision_neon_auth` is a
once-per-project act, not server startup magic.

## 9. Everything lives in ONE Neon project — including things named differently
**Symptom**: "I can't find the protected-notes database."
**Cause**: levels share a project (the retrofit lesson): the course's
test project holds `quotes` (level 2), `notes` (level 3), and
`neon_auth.users_sync` in one `neondb`. Check the org switcher if a
project is missing entirely — projects live in a specific organization.
