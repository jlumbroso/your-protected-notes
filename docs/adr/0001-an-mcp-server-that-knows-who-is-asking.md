# ADR-0001: An MCP server that knows who is asking

- **Date**: 2026-10-08  |  **Iteration**: 1  |  **Status**: Accepted  |  **Deciders**: Jérémie Lumbroso (course direction), Lapidary 5 (Claude Fable 5, build)

**TL;DR**: This prototype adds *identity* to the simplest possible MCP server — a notes list — using Neon Auth, so that one `Authorization` header separates a shared guest commons from a private per-user shelf; this ADR is the self-contained account of the technologies, the four design decisions with their roads not taken, and the two decisions deliberately left open.

## Context — what this is, assuming you arrive knowing nothing

**The course this serves.** CAM ("Computationally Assisted Metacognition," CIS 7000, Penn, Fall 2026) teaches students to build *instruments*: small servers that extend an AI model's reach into things the student actually cares about. By session 5 every student had deployed an MCP server backed by a real database. Those servers had a gap this prototype closes: **they answered anyone**. A personal memory that any caller can read is not yet personal.

**The technologies, one paragraph each:**

- **MCP (Model Context Protocol)** is the open standard by which an AI client (here: Claude) discovers and calls *tools* that a server exposes. A tool is a typed function with a docstring; the model reads the docstrings and decides when to call. This server exposes four: `user_status`, `add_note`, `list_notes`, `clear_notes`. Transport here is MCP's streamable-HTTP: the client POSTs to `/mcp`, and — crucially for this prototype — every call arrives as an HTTP request that can carry **headers**.
- **FastMCP** (the `mcp` Python SDK's server class) turns decorated Python functions into MCP tools. One detail matters here: a tool that declares a `ctx: Context` parameter receives the request context, through which the server reads the caller's HTTP headers. That is the entire mechanism by which identity arrives.
- **Neon** is serverless Postgres; the course already uses it (session 5's `your-first-memory`) because its free tier gives every student a real database whose contents **outlive the server** — Render's free compute has an ephemeral disk, so state kept next to the code dies on every redeploy.
- **Neon Auth** is Neon's user-authentication offering: enabling it on a project provisions a **Stack Auth** project (Stack is the identity provider under the hood) wired to the same database. Two artifacts matter: a **JWKS URL** (the provider's published public keys) and the **`neon_auth.users_sync` table** — a read-only mirror of the user list *inside your own database*, with columns `id` (opaque text UUID), `name`, `email`, `raw_json`, timestamps.
- **JWT verification** is how the server trusts a caller without talking to the provider on every request: the client presents a signed token (`Authorization: Bearer …`); the server checks the signature against the JWKS keys and reads the `sub` claim — the user id. Stateless, offline, one function (`current_identity()` in `server.py`).
- **Crockford Base32** is Douglas Crockford's 32-character alphabet (0–9, A–Z minus **I, L, O, U**) designed to be unambiguous when read aloud or retyped. Note petnames are four of these characters: `A7K2`.

**Why these and not others** is the subject of the decisions below. The one inherited constraint worth naming: everything must run on free tiers with no credit card, because the downstream users are students.

## The four decisions (each with the road not taken)

**D1 — Identity is the `sub` claim (the opaque user id), never the email.** Notes key on the JWT's `sub`, which equals `neon_auth.users_sync.id`. Email is fetched only for display in `user_status`. *Road not taken*: keying on email, which is human-readable in the table but mutable and reassignable — at a university, routinely (students graduate; addresses are recycled). A user who changed email would be silently severed from their shelf. The sync table itself encodes the asymmetry: `id` is the key, `email` an attribute. → QST-IDENTITY-KEY below.

**D2 — Guests share a commons; they are not refused.** No token is a *mode*, not an error: guest notes carry `user_id IS NULL` and every guest sees them. *Roads not taken*: refusing guests (auth as a wall — demonstrates only an error message) and read-only guests (half the contrast). The commons makes auth's value *visible in one minute*: add a note as guest, watch your neighbor see it; sign in, add another, watch it become invisible to them. What auth buys is **ownership**, and the demo is the lesson. Cost: NULL-equality subtlety in SQL (`IS NOT DISTINCT FROM` — plain `=` silently fails on NULL), which is itself worth teaching. → QST-GUEST-MODE below.

**D3 — Petnames are Crockford-4, unique per shelf, database-arbitrated.** 32⁴ ≈ 1.05M ids per shelf; generate-and-insert with 5 retries against a unique index (`(petname, COALESCE(user_id,''))`) — the database, not the application, arbitrates uniqueness. Per-shelf, not global: two users can both hold `A7K2`, because shelves are separate namespaces. *Roads not taken*: sequential ids (leak how much you write), UUIDs (unreadable aloud, useless across a classroom).

**D4 — An invalid token is not an absent one.** Three-way boundary: absent → guest; valid → user; **invalid → loud error**. *Road not taken*: the forgiving degrade (invalid → guest), tempting for demo smoothness, rejected because it converts every auth misconfiguration — expired token, wrong JWKS URL, clock skew — into a *silent privacy bug*: the caller believes they are filing privately while writing to the public commons. The worst outcome in this design is not denial; it is misfiled ownership.

All four are proven live: `scripts/2026-10-08-three-mode-probe.py` ran the full HTTP path against a real Stack sign-up (see its OUTCOME footer).

## Questions

*A note on their status, part of this repo's pedagogy: both were posed and answered-by-recommendation BEFORE the code was generated, and the code was built to match. They remain `unanswered` because the ANS slot belongs to a human, not to the model that wrote the Recommendation — a recommendation, however confident, is not an answer. (The first draft of this repo got that wrong and marked them closed itself; the correction is part of what this project transfers.)*

### QST-IDENTITY-KEY: Which Neon Auth identifier keys the data?
- Status: unanswered — pre-answered at design time; code built on the Recommendation; override welcome
- Why asking: the `user_id` column every note hangs on is forever; `users_sync` offers two candidates.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — the `id` / `sub` claim**: opaque, stable for the account's lifetime, present in every verified token with no database lookup.
- **B — the email**: human-readable in raw rows, but mutable, reassignable, and absent from some providers' tokens.

**Recommendation**: (by Claude Fable 5 / Lapidary 5)
**A — the `id`.** *Rationale*: D1 above; the deciding evidence is the sync table's own shape (`id` is the sync key) and the token's own shape (`sub` is free on the hot path). *Confidence*: 0.95 — because both failure modes of B are routine events at a university. *If wrong*: only a requirement for human-readable rows could flip this — and the fix would be a display JOIN (which `user_status` already does), never a re-key.

**ANS:** (by <name>, <date optional>)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->

### QST-GUEST-MODE: What does the server do for a caller with no token?
- Status: unanswered — pre-answered at design time; code built on the Recommendation; override welcome
- Why asking: the guest path defines what auth *buys*; wall, pen, and commons each teach a different lesson.
- Need: pick a letter (or override — any shape answers)

Options:
- **A — refuse**: every tool errors until signed in.
- **B — read-only guest**: guests may list, never write.
- **C — guest commons**: guests share one public shelf; users get private ones.

**Recommendation**: (by Claude Fable 5 / Lapidary 5)
**C — guest commons.** *Rationale*: D2 above — the one-minute visible contrast is the pedagogical payload, and C keeps the server usable before auth is configured, which `docs/RETROFIT-NEON-AUTH.md` depends on. *Confidence*: 0.8 — because C's NULL-semantics cost is real and deliberate. *If wrong*: a deployment whose commons could collect abuse (URL shared beyond a classroom) — then B, one guard clause in `add_note`.

**ANS:** (by <name>, <date optional>)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->
