#!/usr/bin/env python3

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass
from pathlib import Path


DEFAULT_ADR_DIR = "docs/adr"
DEFAULT_FROM = 1


@dataclass
class Preview:
    file_path: str
    line_number: int
    before: list[str]
    after: str


@dataclass
class TransformResult:
    transformed: str
    changed: bool
    blocks_changed: int
    lines_removed: int
    previews: list[Preview]


def parse_number(value: str) -> int:
    try:
        parsed = int(value, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected a non-negative integer, got {value!r}") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError(f"expected a non-negative integer, got {value!r}")
    return parsed


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Unwrap hard-wrapped prose blocks in numbered ADR Markdown files.",
    )
    parser.add_argument("--write", action="store_true", help="Rewrite files. Without this, the script is a dry run.")
    parser.add_argument("--check", action="store_true", help="Exit with status 1 if any file would change.")
    parser.add_argument(
        "--from",
        dest="from_adr",
        type=parse_number,
        default=DEFAULT_FROM,
        metavar="N",
        help=f"First ADR number to process. Default: {DEFAULT_FROM:04d}.",
    )
    parser.add_argument("--to", dest="to_adr", type=parse_number, metavar="N", help="Last ADR number to process.")
    parser.add_argument("--dir", dest="adr_dir", default=DEFAULT_ADR_DIR, metavar="PATH", help=f"ADR directory. Default: {DEFAULT_ADR_DIR}.")
    parser.add_argument("--file", dest="files", action="append", default=[], metavar="PATH", help="Process one file. Can be passed multiple times.")
    parser.add_argument(
        "--preview",
        nargs="?",
        const=5,
        default=0,
        type=parse_number,
        metavar="N",
        help="Show the first N block rewrites. Default: 5.",
    )
    parser.add_argument("--self-test", action="store_true", help="Run built-in parser regression checks.")
    args = parser.parse_args(argv)

    if args.check and args.write:
        parser.error("--check and --write cannot be used together")

    return args


def discover_adr_files(args: argparse.Namespace) -> list[Path]:
    if args.files:
        files = sorted({Path(file) for file in args.files})
        for file_path in files:
            if not file_path.is_file():
                raise FileNotFoundError(f"--file path is not a file: {file_path}")
        return files

    adr_dir = Path(args.adr_dir)
    if not adr_dir.is_dir():
        raise NotADirectoryError(f"--dir path is not a directory: {adr_dir}")

    files: list[Path] = []
    for file_path in sorted(adr_dir.iterdir()):
        if not re.match(r"^\d{4}-.*\.md$", file_path.name):
            continue
        adr_number = int(file_path.name[:4], 10)
        if adr_number < args.from_adr:
            continue
        if args.to_adr is not None and adr_number > args.to_adr:
            continue
        files.append(file_path)

    return files


def fence_start(line: str) -> str | None:
    match = re.match(r"^ {0,3}(```+|~~~+)", line)
    return match.group(1) if match else None


def is_fence_end(line: str, marker: str) -> bool:
    char = re.escape(marker[0])
    return bool(re.match(rf"^ {{0,3}}{char}{{{len(marker)},}}\s*$", line))


def is_thematic_break(line: str) -> bool:
    return bool(re.match(r"^ {0,3}([-*_])(?:\s*\1){2,}\s*$", line))


def match_list_item(line: str) -> re.Match[str] | None:
    return re.match(r"^( {0,3})([-*+]|(?:0|[1-9]\d{0,8})[.)])(\s+)(.*)$", line)


def is_list_item(line: str) -> bool:
    return match_list_item(line) is not None


def is_plain_line_protected(line: str) -> bool:
    stripped = line.strip()
    if stripped == "":
        return True
    if re.match(r"^\s", line):
        return True
    if re.match(r"^ {0,3}#{1,6}\s+", line):
        return True
    if is_thematic_break(line):
        return True
    if is_list_item(line):
        return True
    if re.match(r"^ {0,3}>", line):
        return True
    if re.match(r"^ {0,3}\|", line):
        return True
    if re.match(r"^ {0,3}\[[^\]]+\]:", line):
        return True
    if re.match(r"^\*\*(?:ANS|QST)\b", line):
        return True
    if re.match(r"^\[Fill this in\]$", line):
        return True
    if re.match(r"^ {0,3}</?[A-Za-z][^>]*>", line):
        return True
    return False


def mark_protected_lines(lines: list[str]) -> list[bool]:
    protected = [False] * len(lines)
    in_fence = False
    fence_marker = ""
    in_html_comment = False
    html_block_tag = ""

    for index, line in enumerate(lines):
        stripped = line.strip()

        if in_fence:
            protected[index] = True
            if is_fence_end(line, fence_marker):
                in_fence = False
                fence_marker = ""
            continue

        if in_html_comment:
            protected[index] = True
            if "-->" in line:
                in_html_comment = False
            continue

        if html_block_tag:
            protected[index] = True
            if re.search(rf"</{html_block_tag}>", line, re.IGNORECASE):
                html_block_tag = ""
            continue

        marker = fence_start(line)
        if marker:
            protected[index] = True
            in_fence = True
            fence_marker = marker
            continue

        if "<!--" in line:
            protected[index] = True
            if "-->" not in line:
                in_html_comment = True
            continue

        html_block = re.match(r"^<(details|div|table|pre|ul|ol|blockquote)(?:\s|>)", stripped, re.IGNORECASE)
        if html_block and not re.search(rf"</{html_block.group(1)}>", line, re.IGNORECASE):
            protected[index] = True
            html_block_tag = html_block.group(1).lower()
            continue

        protected[index] = is_plain_line_protected(line)

    return protected


def has_hard_break(line: str) -> bool:
    stripped = line.strip()
    return bool(re.search(r"(?: {2,}|\\)$", line) or re.search(r"<br\s*/?>$", stripped, re.IGNORECASE))


def count_leading_spaces(line: str) -> int:
    match = re.match(r"^ *", line)
    return len(match.group(0)) if match else 0


def is_list_continuation_line(line: str, min_indent: int, previous_line: str) -> bool:
    if line.strip() == "":
        return False
    if count_leading_spaces(line) < min_indent:
        return False

    stripped = line.strip()
    list_item = match_list_item(line)
    if fence_start(line):
        return False
    if is_thematic_break(line):
        return False
    if list_item:
        indent, marker, _spacing, content = list_item.groups()
        is_plus_continuation = (
            marker == "+"
            and len(indent) == min_indent
            and bool(re.match(r"^[a-z]", content.strip()))
            and not re.search(r":\s*$", previous_line.strip())
        )
        is_numeric_paren_continuation = (
            bool(re.match(r"^\d+\)$", marker))
            and marker != "1)"
            and len(indent) == min_indent
            and bool(re.match(r"^[a-z]", content.strip()))
            and not re.search(r":\s*$", previous_line.strip())
        )
        if not is_plus_continuation and not is_numeric_paren_continuation:
            return False

    if re.match(r"^#{1,6}\s+", stripped):
        return False
    if re.match(r"^>", stripped):
        return False
    if re.match(r"^\|", stripped):
        return False
    if re.match(r"^\[[^\]]+\]:", stripped):
        return False
    if re.match(r"^<!--", stripped):
        return False
    if re.match(r"^</?[A-Za-z][^>]*>", stripped):
        return False
    if re.match(r"^\*\*(?:ANS|QST)\b", stripped):
        return False
    if re.match(r"^\[Fill this in\]$", stripped):
        return False

    return True


def join_soft_wrapped_lines(lines: list[str]) -> str:
    joined = ""
    for line in lines:
        stripped = line.strip()
        if joined == "":
            joined = stripped
        elif re.search(r"-$", joined) and re.match(r"^[A-Za-z0-9`]", stripped):
            joined += stripped
        else:
            joined += f" {stripped}"
    return joined


def try_unwrap_list_item(lines: list[str], start_index: int, file_path: str) -> tuple[str, int, Preview] | None:
    match = match_list_item(lines[start_index])
    if not match:
        return None

    indent, marker, spacing, content = match.groups()
    if content.strip() == "":
        return None

    min_indent = len(indent) + len(marker) + len(spacing)
    block = [lines[start_index]]

    index = start_index + 1
    while index < len(lines) and not has_hard_break(lines[index - 1]) and is_list_continuation_line(lines[index], min_indent, lines[index - 1]):
        block.append(lines[index])
        index += 1

    if len(block) <= 1:
        return None

    prefix = f"{indent}{marker}{spacing}"
    after = f"{prefix}{join_soft_wrapped_lines([content, *block[1:]])}"
    preview = Preview(file_path=file_path, line_number=start_index + 1, before=block, after=after)
    return after, len(block), preview


def transform_markdown(text: str, file_path: str) -> TransformResult:
    eol = "\r\n" if "\r\n" in text else "\n"
    has_trailing_newline = text.endswith("\n")
    lines = re.split(r"\r?\n", text)
    if has_trailing_newline:
        lines.pop()

    protected = mark_protected_lines(lines)
    output: list[str] = []
    previews: list[Preview] = []
    blocks_changed = 0
    lines_removed = 0
    index = 0

    while index < len(lines):
        list_result = try_unwrap_list_item(lines, index, file_path)
        if list_result:
            after, consumed, preview = list_result
            output.append(after)
            blocks_changed += 1
            lines_removed += consumed - 1
            previews.append(preview)
            index += consumed
            continue

        if protected[index]:
            output.append(lines[index])
            index += 1
            continue

        start = index
        block: list[str] = []
        while index < len(lines) and not protected[index]:
            block.append(lines[index])
            index += 1

        unsafe_hard_break = any(has_hard_break(line) for line in block[:-1])
        if len(block) <= 1 or unsafe_hard_break:
            output.extend(block)
            continue

        after = join_soft_wrapped_lines(block)
        output.append(after)
        blocks_changed += 1
        lines_removed += len(block) - 1
        previews.append(Preview(file_path=file_path, line_number=start + 1, before=block, after=after))

    transformed = eol.join(output) + (eol if has_trailing_newline else "")
    return TransformResult(
        transformed=transformed,
        changed=transformed != text,
        blocks_changed=blocks_changed,
        lines_removed=lines_removed,
        previews=previews,
    )


def format_preview(preview: Preview) -> str:
    lines = [f"{preview.file_path}:{preview.line_number}", "Before:"]
    lines.extend(f"  {line}" for line in preview.before)
    lines.extend(["After:", f"  {preview.after}"])
    return "\n".join(lines)


def run_self_tests() -> None:
    cases = [
        {
            "name": "plain prose paragraph",
            "input": "Alpha wraps\nonto the next line.\n\n# Heading\n",
            "expected": "Alpha wraps onto the next line.\n\n# Heading\n",
        },
        {
            "name": "simple bullet continuation",
            "input": "- A bullet wraps\n  onto the next line.\n",
            "expected": "- A bullet wraps onto the next line.\n",
        },
        {
            "name": "numbered-list continuation",
            "input": "1. A numbered item wraps\n   onto the next line.\n",
            "expected": "1. A numbered item wraps onto the next line.\n",
        },
        {
            "name": "checklist continuation",
            "input": "- [ ] A task wraps\n  onto the next line.\n",
            "expected": "- [ ] A task wraps onto the next line.\n",
        },
        {
            "name": "plus-sign prose continuation",
            "input": "2. Members + activity\n   + actions belong together.\n",
            "expected": "2. Members + activity + actions belong together.\n",
        },
        {
            "name": "numeric-parenthesis prose continuation",
            "input": "- Phase\n  5) intentionally avoids flicker.\n",
            "expected": "- Phase 5) intentionally avoids flicker.\n",
        },
        {
            "name": "hyphen-split token",
            "input": "- `docs/example-\n  2026.md` is referenced.\n",
            "expected": "- `docs/example-2026.md` is referenced.\n",
        },
        {
            "name": "nested list stays nested",
            "input": "1. Parent item:\n   - Nested child\n   - Second child\n",
            "expected": "1. Parent item:\n   - Nested child\n   - Second child\n",
        },
        {
            "name": "blockquote stays wrapped",
            "input": "> quoted text\n> stays quoted\n",
            "expected": "> quoted text\n> stays quoted\n",
        },
        {
            "name": "fenced code stays wrapped",
            "input": "```txt\nline one\nline two\n```\n",
            "expected": "```txt\nline one\nline two\n```\n",
        },
        {
            "name": "hard line break stays wrapped",
            "input": "Alpha  \nbeta\n",
            "expected": "Alpha  \nbeta\n",
        },
        {
            "name": "answer placeholder stays split",
            "input": "**ANS:** (by author)\n[Fill this in]\n",
            "expected": "**ANS:** (by author)\n[Fill this in]\n",
        },
    ]

    failures = []
    for case in cases:
        result = transform_markdown(case["input"], f"<{case['name']}>")
        if result.transformed != case["expected"]:
            failures.append({**case, "actual": result.transformed})

    if failures:
        for failure in failures:
            print(f"Self-test failed: {failure['name']}", file=sys.stderr)
            print("Expected:", file=sys.stderr)
            print(failure["expected"], file=sys.stderr)
            print("Actual:", file=sys.stderr)
            print(failure["actual"], file=sys.stderr)
        raise RuntimeError(f"{len(failures)} self-test case(s) failed")

    print(f"Self-test passed: {len(cases)} case(s).")


def main(argv: list[str]) -> int:
    args = parse_args(argv)

    if args.self_test:
        run_self_tests()
        return 0

    files = discover_adr_files(args)
    changed_files = []
    previews: list[Preview] = []
    total_blocks_changed = 0
    total_lines_removed = 0

    for file_path in files:
        original = file_path.read_text(encoding="utf-8")
        result = transform_markdown(original, str(file_path))
        if not result.changed:
            continue

        changed_files.append(
            {
                "file_path": file_path,
                "blocks_changed": result.blocks_changed,
                "lines_removed": result.lines_removed,
            }
        )
        total_blocks_changed += result.blocks_changed
        total_lines_removed += result.lines_removed
        previews.extend(result.previews)

        if args.write:
            file_path.write_text(result.transformed, encoding="utf-8", newline="")

    verb = "Updated" if args.write else "Would update"
    print(f"{verb} {len(changed_files)} file(s), {total_blocks_changed} soft-wrapped block(s), removing {total_lines_removed} hard line break(s).")

    for file_info in changed_files:
        action = "updated" if args.write else "would update"
        print(f"{action} {file_info['file_path']}: {file_info['blocks_changed']} block(s), {file_info['lines_removed']} line break(s)")

    if args.preview > 0 and previews:
        print("\nPreview:")
        for preview in previews[: args.preview]:
            print("\n" + format_preview(preview))

    if args.check and changed_files:
        print("\nCheck failed: run with --write to apply these unwrap changes.", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        print(error, file=sys.stderr)
        raise SystemExit(1)
