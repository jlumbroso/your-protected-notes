# ADR-0002: How does the token reach the server from a real client?

- **Date**: 2026-10-08  |  **Iteration**: 1  |  **Status**: Draft  |  **Deciders**: Jérémie Lumbroso, Lapidary 5

**TL;DR**: Verification is proven (ADR-0001); *delivery* is not — whether claude.ai's connector OAuth handshake completes against Stack Auth's endpoints is the live unknown, and the spike findings decide between full OAuth and a pasted-token stepping stone.

## Context, for the newcomer

ADR-0001's probe minted its token by calling Stack's sign-up API directly and attaching it by hand. A real user doesn't do that. claude.ai custom connectors obtain tokens via **OAuth 2.1**: the server advertises protected-resource metadata (RFC 9728) naming its authorization server; the client discovers it, registers (ideally via dynamic client registration, RFC 7591), and runs the sign-in flow in the browser. Every link in that chain depends on what Stack Auth's endpoints actually expose — which is documented for their SDKs, not for this dance. Guessing would be worse than useless: an auth path that *almost* works teaches students that auth is mysterious, which is the opposite of this repo's point.

## Questions

### QST-TOKEN-DELIVERY: Which delivery path does the course teach?
- Status: unresolved — the spike is the model's ball; the letter becomes the human's once findings land
- Why asking: this decides the student-facing experience of sign-in, and the honest option set depends on facts not yet gathered.
- Need: explanation first (spike findings), then a letter

Options:
- **A — full connector OAuth**: server publishes RFC 9728 metadata pointing at Stack; claude.ai discovers, registers, and the sign-in happens in the connector flow. The real thing — if Stack's discovery/registration posture cooperates.
- **B — pasted token (stepping stone)**: student signs in on a small hosted page, copies their access token into the connector's bearer/header field. Already proven end-to-end by ADR-0001's probe; teaches verification honestly; defers the OAuth dance.
- **C — mock provider first**: `provision_neon_auth` accepts `auth_provider: "mock"` — teach the shape with fake identities, swap `stack` in as homework.

**Recommendation**: (by Claude Fable 5 / Lapidary 5)
**Spike A; teach B if A frays.** *Rationale*: A is worth teaching only if it works without heroics; the spike (attempt discovery + DCR against `api.stack-auth.com`; compare claude.ai's connector auth requirements against what Stack exposes) is under an hour and converts this from posture to fact. B is already de-risked by the probe. *Confidence*: 0.6 — because Stack's DCR posture is the one thing neither its docs nor this repo has verified, and I won't guess. *If wrong*: A works trivially — then B never ships and becomes one slide of history.

**ANS:** (by <name>, <date optional>)
[Fill this in]   <!-- literal placeholder — parser-significant, do not paraphrase -->
