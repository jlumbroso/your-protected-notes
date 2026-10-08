# ADR Unwrap Scripts

These scripts remove hard word-wrapping from numbered ADR Markdown files while preserving Markdown structures where joining lines would be risky.

They are optional hygiene tools for ADR-heavy repositories. They are not general-purpose Markdown formatters, and they should not be wired into a template-derived project automatically unless that project explicitly wants the policy.

## Implementations

Two dependency-free implementations are provided:

- `unwrap-adrs.mjs` for projects that already have Node.js available.
- `unwrap-adrs.py` for projects that already have Python available.

The two implementations are intended to be behaviorally equivalent. They expose the same flags and carry matching built-in self-tests.

## Default Target

By default, each script scans numbered ADR files under `docs/adr`:

```sh
node scripts/unwrap-adrs/unwrap-adrs.mjs
python3 scripts/unwrap-adrs/unwrap-adrs.py
```

The default lower bound is ADR `0001`. The file matcher is:

```text
docs/adr/[0-9][0-9][0-9][0-9]-*.md
```

Use `--from`, `--to`, or `--file` to narrow the target:

```sh
node scripts/unwrap-adrs/unwrap-adrs.mjs --from 0031 --to 0035
python3 scripts/unwrap-adrs/unwrap-adrs.py --file docs/adr/0035-architecture-of-complexity-applied.md
```

## Safe Workflow

Run the built-in parser checks first:

```sh
node scripts/unwrap-adrs/unwrap-adrs.mjs --self-test
python3 scripts/unwrap-adrs/unwrap-adrs.py --self-test
```

Preview the proposed changes:

```sh
node scripts/unwrap-adrs/unwrap-adrs.mjs --from 0001 --preview 20
python3 scripts/unwrap-adrs/unwrap-adrs.py --from 0001 --preview 20
```

Apply the changes with one implementation:

```sh
node scripts/unwrap-adrs/unwrap-adrs.mjs --from 0001 --write
```

Verify the result is idempotent:

```sh
node scripts/unwrap-adrs/unwrap-adrs.mjs --from 0001 --check
python3 scripts/unwrap-adrs/unwrap-adrs.py --from 0001 --check
```

Check for whitespace errors:

```sh
git diff --check -- scripts/unwrap-adrs docs/adr/[0-9][0-9][0-9][0-9]-*.md
```

## What They Unwrap

The scripts unwrap:

- Plain prose paragraphs.
- Simple bullet continuations.
- Numbered-list continuations.
- Checklist continuations.
- Literal `+` prose continuations, such as `activity` followed by `+ actions`.
- Numeric-parenthesis prose continuations, such as `Phase` followed by `5) ...`.
- Hyphen-split tokens, such as a filename split as `example-` followed by `2026.md`.

## What They Protect

The scripts deliberately leave these structures alone:

- Headings.
- Blank lines and thematic breaks.
- Code fences.
- Indented code or diagram blocks.
- Blockquotes.
- Markdown tables.
- Link reference definitions.
- HTML comments and common HTML block tags.
- QST/ANS markers and `[Fill this in]` placeholders.
- Explicit Markdown hard line breaks, including two trailing spaces, a trailing backslash, or trailing `<br>`.
- Nested list items, unless the nested-looking line matches one of the narrow prose-continuation exceptions above.

## Check Mode

`--check` performs the same analysis as a dry run but exits with status `1` if any file would change:

```sh
node scripts/unwrap-adrs/unwrap-adrs.mjs --from 0001 --check
python3 scripts/unwrap-adrs/unwrap-adrs.py --from 0001 --check
```

This is useful for a pre-commit hook or CI check if a project chooses to require unwrapped ADR prose.

## Limitations

These are repository-oriented Markdown cleanup scripts, not full Markdown parsers. They prefer false negatives over false positives: if a wrapped structure looks like a table, blockquote, code block, HTML block, or nested list, it is left alone.

Always review the diff after `--write`. The scripts are designed so rerunning them after a successful cleanup reports zero changes.
