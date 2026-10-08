# You are in the template library

Each file here is a *source* other artifacts are minted from. The norm — a good practice with a reason, not a rule — is to leave these files as you found them and make your ADR as a copy: either `just adr "<title>"` (mints `docs/adr/NNNN-<slug>.md` from `adr.md`, auto-numbered) or copy any template by hand and adapt it freely. **Why**: an edit here silently changes what *every future participant* mints — a side effect that's hard to notice and harder to trace; a copy keeps your changes attributably yours. If you genuinely mean to evolve a template for everyone, that's welcome — it's a decision, so it gets an ADR and a version-marker bump.

- `adr.md` — collaborative ADR, **the default** for humans + AI deciding together
- `adr-madr.md` — classic MADR, for simple solo decisions
- `seed.md` — brain-dumps before structure; `debrief.md` — post-incident reviews
- `failure-classes.md` — reference taxonomy, not a mint source

Line 1 of each template is its version marker — keep it in copies; tooling reads it (**rule, not norm**: parsers depend on it).
