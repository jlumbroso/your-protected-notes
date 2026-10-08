#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';

const DEFAULT_ADR_DIR = 'docs/adr';
const DEFAULT_FROM = 1;

function usage() {
  return `Usage: node scripts/unwrap-adrs/unwrap-adrs.mjs [options]

Unwrap hard-wrapped prose blocks in numbered ADR Markdown files.

Options:
  --write             Rewrite files. Without this, the script is a dry run.
  --check             Exit with status 1 if any file would change.
  --from N            First ADR number to process. Default: ${String(DEFAULT_FROM).padStart(4, '0')}.
  --to N              Last ADR number to process.
  --dir PATH          ADR directory. Default: ${DEFAULT_ADR_DIR}.
  --file PATH         Process one file. Can be passed multiple times.
  --preview [N]       Show the first N block rewrites. Default: 5.
  --self-test         Run built-in parser regression checks.
  -h, --help          Show this help.
`;
}

function parseNumber(value, flag) {
  const parsed = Number.parseInt(value, 10);
  if (!Number.isInteger(parsed) || parsed < 0) {
    throw new Error(`${flag} expects a non-negative integer, got "${value}"`);
  }
  return parsed;
}

function parseArgs(argv) {
  const options = {
    adrDir: DEFAULT_ADR_DIR,
    check: false,
    files: [],
    from: DEFAULT_FROM,
    preview: 0,
    selfTest: false,
    to: undefined,
    write: false,
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];

    if (arg === '--write') {
      options.write = true;
    } else if (arg === '--check') {
      options.check = true;
    } else if (arg === '--from') {
      i += 1;
      if (i >= argv.length) throw new Error('--from requires a value');
      options.from = parseNumber(argv[i], '--from');
    } else if (arg === '--to') {
      i += 1;
      if (i >= argv.length) throw new Error('--to requires a value');
      options.to = parseNumber(argv[i], '--to');
    } else if (arg === '--dir') {
      i += 1;
      if (i >= argv.length) throw new Error('--dir requires a value');
      options.adrDir = argv[i];
    } else if (arg === '--file') {
      i += 1;
      if (i >= argv.length) throw new Error('--file requires a value');
      options.files.push(argv[i]);
    } else if (arg === '--preview') {
      const next = argv[i + 1];
      if (next && !next.startsWith('-')) {
        i += 1;
        options.preview = parseNumber(next, '--preview');
      } else {
        options.preview = 5;
      }
    } else if (arg === '-h' || arg === '--help') {
      options.help = true;
    } else if (arg === '--self-test') {
      options.selfTest = true;
    } else {
      throw new Error(`Unknown option: ${arg}`);
    }
  }

  if (options.check && options.write) {
    throw new Error('--check and --write cannot be used together');
  }

  return options;
}

function discoverAdrFiles(options) {
  if (options.files.length > 0) {
    return [...new Set(options.files.map((file) => path.normalize(file)))].sort().map((file) => {
      const stat = fs.statSync(file);
      if (!stat.isFile()) {
        throw new Error(`--file path is not a file: ${file}`);
      }
      return file;
    });
  }

  const stat = fs.statSync(options.adrDir);
  if (!stat.isDirectory()) {
    throw new Error(`--dir path is not a directory: ${options.adrDir}`);
  }

  return fs
    .readdirSync(options.adrDir)
    .filter((file) => /^\d{4}-.*\.md$/.test(file))
    .filter((file) => {
      const adrNumber = Number.parseInt(file.slice(0, 4), 10);
      return adrNumber >= options.from && (options.to === undefined || adrNumber <= options.to);
    })
    .sort()
    .map((file) => path.join(options.adrDir, file));
}

function isFenceStart(line) {
  return line.match(/^ {0,3}(```+|~~~+)/);
}

function isFenceEnd(line, marker) {
  if (!marker) return false;
  const char = marker[0];
  return new RegExp(`^ {0,3}${char}{${marker.length},}\\s*$`).test(line);
}

function isThematicBreak(line) {
  return /^ {0,3}([-*_])(?:\s*\1){2,}\s*$/.test(line);
}

function matchListItem(line) {
  return line.match(/^( {0,3})([-*+]|(?:0|[1-9]\d{0,8})[.)])(\s+)(.*)$/);
}

function isListItem(line) {
  return Boolean(matchListItem(line));
}

function isPlainLineProtected(line) {
  if (line.trim() === '') return true;
  if (/^\s/.test(line)) return true;
  if (/^ {0,3}#{1,6}\s+/.test(line)) return true;
  if (isThematicBreak(line)) return true;
  if (isListItem(line)) return true;
  if (/^ {0,3}>/.test(line)) return true;
  if (/^ {0,3}\|/.test(line)) return true;
  if (/^ {0,3}\[[^\]]+\]:/.test(line)) return true;
  if (/^\*\*(?:ANS|QST)\b/.test(line)) return true;
  if (/^\[Fill this in\]$/.test(line)) return true;
  if (/^ {0,3}<\/?[A-Za-z][^>]*>/.test(line)) return true;
  return false;
}

function markProtectedLines(lines) {
  const protectedLines = new Array(lines.length).fill(false);
  let inFence = false;
  let fenceMarker = '';
  let inHtmlComment = false;
  let htmlBlockTag = '';

  for (let i = 0; i < lines.length; i += 1) {
    const line = lines[i];
    const trimmed = line.trim();

    if (inFence) {
      protectedLines[i] = true;
      if (isFenceEnd(line, fenceMarker)) {
        inFence = false;
        fenceMarker = '';
      }
      continue;
    }

    if (inHtmlComment) {
      protectedLines[i] = true;
      if (line.includes('-->')) {
        inHtmlComment = false;
      }
      continue;
    }

    if (htmlBlockTag) {
      protectedLines[i] = true;
      if (new RegExp(`</${htmlBlockTag}>`, 'i').test(line)) {
        htmlBlockTag = '';
      }
      continue;
    }

    const fenceStart = isFenceStart(line);
    if (fenceStart) {
      protectedLines[i] = true;
      inFence = true;
      fenceMarker = fenceStart[1];
      continue;
    }

    if (line.includes('<!--')) {
      protectedLines[i] = true;
      if (!line.includes('-->')) {
        inHtmlComment = true;
      }
      continue;
    }

    const htmlBlock = trimmed.match(/^<(details|div|table|pre|ul|ol|blockquote)(?:\s|>)/i);
    if (htmlBlock && !new RegExp(`</${htmlBlock[1]}>`, 'i').test(line)) {
      protectedLines[i] = true;
      htmlBlockTag = htmlBlock[1].toLowerCase();
      continue;
    }

    protectedLines[i] = isPlainLineProtected(line);
  }

  return protectedLines;
}

function hasHardBreak(line) {
  return /(?: {2,}|\\)$/.test(line) || /<br\s*\/?>$/i.test(line.trim());
}

function countLeadingSpaces(line) {
  return line.match(/^ */)[0].length;
}

function isListContinuationLine(line, minIndent, previousLine) {
  if (line.trim() === '') return false;
  if (countLeadingSpaces(line) < minIndent) return false;

  const trimmed = line.trim();
  const listItem = matchListItem(line);
  if (isFenceStart(line)) return false;
  if (isThematicBreak(line)) return false;
  if (listItem) {
    const [, indent, marker, , content] = listItem;
    const isPlusContinuation =
      marker === '+' &&
      indent.length === minIndent &&
      /^[a-z]/.test(content.trim()) &&
      !/:\s*$/.test(previousLine.trim());
    const isNumericParenContinuation =
      /^\d+\)$/.test(marker) &&
      marker !== '1)' &&
      indent.length === minIndent &&
      /^[a-z]/.test(content.trim()) &&
      !/:\s*$/.test(previousLine.trim());

    if (!isPlusContinuation && !isNumericParenContinuation) return false;
  }
  if (/^#{1,6}\s+/.test(trimmed)) return false;
  if (/^>/.test(trimmed)) return false;
  if (/^\|/.test(trimmed)) return false;
  if (/^\[[^\]]+\]:/.test(trimmed)) return false;
  if (/^<!--/.test(trimmed)) return false;
  if (/^<\/?[A-Za-z][^>]*>/.test(trimmed)) return false;
  if (/^\*\*(?:ANS|QST)\b/.test(trimmed)) return false;
  if (/^\[Fill this in\]$/.test(trimmed)) return false;

  return true;
}

function tryUnwrapListItem(lines, startIndex, filePath) {
  const match = matchListItem(lines[startIndex]);
  if (!match) return null;

  const [, indent, marker, spacing, content] = match;
  if (content.trim() === '') return null;

  const minIndent = indent.length + marker.length + spacing.length;
  const block = [lines[startIndex]];

  let i = startIndex + 1;
  while (i < lines.length && !hasHardBreak(lines[i - 1]) && isListContinuationLine(lines[i], minIndent, lines[i - 1])) {
    block.push(lines[i]);
    i += 1;
  }

  if (block.length <= 1) return null;

  const prefix = `${indent}${marker}${spacing}`;
  const after = `${prefix}${joinSoftWrappedLines([content, ...block.slice(1)])}`;

  return {
    after,
    consumed: block.length,
    preview: {
      after,
      before: block,
      filePath,
      lineNumber: startIndex + 1,
    },
  };
}

function joinSoftWrappedLines(lines) {
  return lines.map((line) => line.trim()).reduce((joined, line) => {
    if (joined === '') return line;
    if (/-$/.test(joined) && /^[A-Za-z0-9`]/.test(line)) {
      return `${joined}${line}`;
    }
    return `${joined} ${line}`;
  }, '');
}

function unwrapBlock(block) {
  return joinSoftWrappedLines(block);
}

function transformMarkdown(text, filePath) {
  const eol = text.includes('\r\n') ? '\r\n' : '\n';
  const hasTrailingNewline = text.endsWith('\n');
  const lines = text.split(/\r?\n/);
  if (hasTrailingNewline) {
    lines.pop();
  }

  const protectedLines = markProtectedLines(lines);
  const output = [];
  const previews = [];
  let blocksChanged = 0;
  let linesRemoved = 0;

  for (let i = 0; i < lines.length; ) {
    const listResult = tryUnwrapListItem(lines, i, filePath);
    if (listResult) {
      output.push(listResult.after);
      blocksChanged += 1;
      linesRemoved += listResult.consumed - 1;
      previews.push(listResult.preview);
      i += listResult.consumed;
      continue;
    }

    if (protectedLines[i]) {
      output.push(lines[i]);
      i += 1;
      continue;
    }

    const start = i;
    const block = [];
    while (i < lines.length && !protectedLines[i]) {
      block.push(lines[i]);
      i += 1;
    }

    const unsafeHardBreak = block.slice(0, -1).some(hasHardBreak);
    if (block.length <= 1 || unsafeHardBreak) {
      output.push(...block);
      continue;
    }

    const after = unwrapBlock(block);
    output.push(after);
    blocksChanged += 1;
    linesRemoved += block.length - 1;
    previews.push({
      after,
      before: block,
      filePath,
      lineNumber: start + 1,
    });
  }

  const transformed = output.join(eol) + (hasTrailingNewline ? eol : '');
  return {
    blocksChanged,
    changed: transformed !== text,
    linesRemoved,
    previews,
    transformed,
  };
}

function formatPreview(preview) {
  return [
    `${preview.filePath}:${preview.lineNumber}`,
    'Before:',
    ...preview.before.map((line) => `  ${line}`),
    'After:',
    `  ${preview.after}`,
  ].join('\n');
}

function runSelfTests() {
  const cases = [
    {
      name: 'plain prose paragraph',
      input: 'Alpha wraps\nonto the next line.\n\n# Heading\n',
      expected: 'Alpha wraps onto the next line.\n\n# Heading\n',
    },
    {
      name: 'simple bullet continuation',
      input: '- A bullet wraps\n  onto the next line.\n',
      expected: '- A bullet wraps onto the next line.\n',
    },
    {
      name: 'numbered-list continuation',
      input: '1. A numbered item wraps\n   onto the next line.\n',
      expected: '1. A numbered item wraps onto the next line.\n',
    },
    {
      name: 'checklist continuation',
      input: '- [ ] A task wraps\n  onto the next line.\n',
      expected: '- [ ] A task wraps onto the next line.\n',
    },
    {
      name: 'plus-sign prose continuation',
      input: '2. Members + activity\n   + actions belong together.\n',
      expected: '2. Members + activity + actions belong together.\n',
    },
    {
      name: 'numeric-parenthesis prose continuation',
      input: '- Phase\n  5) intentionally avoids flicker.\n',
      expected: '- Phase 5) intentionally avoids flicker.\n',
    },
    {
      name: 'hyphen-split token',
      input: '- `docs/example-\n  2026.md` is referenced.\n',
      expected: '- `docs/example-2026.md` is referenced.\n',
    },
    {
      name: 'nested list stays nested',
      input: '1. Parent item:\n   - Nested child\n   - Second child\n',
      expected: '1. Parent item:\n   - Nested child\n   - Second child\n',
    },
    {
      name: 'blockquote stays wrapped',
      input: '> quoted text\n> stays quoted\n',
      expected: '> quoted text\n> stays quoted\n',
    },
    {
      name: 'fenced code stays wrapped',
      input: '```txt\nline one\nline two\n```\n',
      expected: '```txt\nline one\nline two\n```\n',
    },
    {
      name: 'hard line break stays wrapped',
      input: 'Alpha  \nbeta\n',
      expected: 'Alpha  \nbeta\n',
    },
    {
      name: 'answer placeholder stays split',
      input: '**ANS:** (by author)\n[Fill this in]\n',
      expected: '**ANS:** (by author)\n[Fill this in]\n',
    },
  ];

  const failures = [];
  for (const testCase of cases) {
    const result = transformMarkdown(testCase.input, `<${testCase.name}>`);
    if (result.transformed !== testCase.expected) {
      failures.push({ ...testCase, actual: result.transformed });
    }
  }

  if (failures.length > 0) {
    for (const failure of failures) {
      console.error(`Self-test failed: ${failure.name}`);
      console.error('Expected:');
      console.error(failure.expected);
      console.error('Actual:');
      console.error(failure.actual);
    }
    throw new Error(`${failures.length} self-test case(s) failed`);
  }

  console.log(`Self-test passed: ${cases.length} case(s).`);
}

function main() {
  const options = parseArgs(process.argv.slice(2));
  if (options.help) {
    process.stdout.write(usage());
    return;
  }

  if (options.selfTest) {
    runSelfTests();
    return;
  }

  const files = discoverAdrFiles(options);
  const changedFiles = [];
  const previews = [];
  let totalBlocksChanged = 0;
  let totalLinesRemoved = 0;

  for (const filePath of files) {
    const original = fs.readFileSync(filePath, 'utf8');
    const result = transformMarkdown(original, filePath);
    if (!result.changed) continue;

    changedFiles.push({
      blocksChanged: result.blocksChanged,
      filePath,
      linesRemoved: result.linesRemoved,
    });
    totalBlocksChanged += result.blocksChanged;
    totalLinesRemoved += result.linesRemoved;
    previews.push(...result.previews);

    if (options.write) {
      fs.writeFileSync(filePath, result.transformed);
    }
  }

  const verb = options.write ? 'Updated' : 'Would update';
  console.log(
    `${verb} ${changedFiles.length} file(s), ${totalBlocksChanged} soft-wrapped block(s), removing ${totalLinesRemoved} hard line break(s).`,
  );

  for (const file of changedFiles) {
    console.log(
      `${options.write ? 'updated' : 'would update'} ${file.filePath}: ${file.blocksChanged} block(s), ${file.linesRemoved} line break(s)`,
    );
  }

  if (options.preview > 0 && previews.length > 0) {
    console.log('\nPreview:');
    for (const preview of previews.slice(0, options.preview)) {
      console.log('\n' + formatPreview(preview));
    }
  }

  if (options.check && changedFiles.length > 0) {
    console.error('\nCheck failed: run with --write to apply these unwrap changes.');
    process.exitCode = 1;
  }
}

try {
  main();
} catch (error) {
  console.error(error instanceof Error ? error.message : String(error));
  process.exit(1);
}
