# VS Code Optimization Guide
*Created: 2026-01-04*
*Purpose: Eliminate bloat and unnecessary processes in VS Code*

## The Problem

Each VS Code project spawns multiple processes:
- **Python projects**: 2 LSP servers (isort + black) per project
- **ChatGPT codex server**: 1 per window
- **Total overhead**: 30-50MB RAM per project + constant file watching

With 12 projects open, this means:
- 24+ Python LSP servers
- 10+ codex servers
- Hundreds of MB of RAM wasted
- Constant CPU usage from file watchers

---

## Template 1: Python Projects (Minimal)

**Use for**: Most Python projects where you don't need constant linting/formatting

```json
{
  "editor.formatOnSave": false,
  "editor.formatOnPaste": false,
  "editor.formatOnType": false,

  "isort.check": false,
  "black-formatter.importStrategy": "useBundled",

  "python.analysis.typeCheckingMode": "off",
  "python.analysis.autoImportCompletions": false,
  "python.analysis.indexing": false,

  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/.venv/**": true,
    "**/__pycache__/**": true,
    "**/.pytest_cache/**": true
  },

  "files.autoSave": "off",

  "github.copilot.enable": {
    "*": false
  }
}
```

**What this disables:**
- Automatic formatting (format on-demand instead: Cmd+Shift+P → Format Document)
- Import sorting on every keystroke
- Type checking (use mypy manually when needed)
- Auto-imports (type them yourself or use Claude)
- File watching for __pycache__ and .venv
- Copilot (you have Claude!)

---

## Template 2: Node.js/TypeScript (Minimal)

**Use for**: React, Next.js, Node.js projects

```json
{
  "editor.formatOnSave": false,
  "editor.formatOnPaste": false,

  "typescript.suggest.enabled": false,
  "typescript.validate.enable": false,
  "javascript.suggest.enabled": false,
  "javascript.validate.enable": false,

  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/node_modules/**": true,
    "**/dist/**": true,
    "**/.next/**": true,
    "**/.turbo/**": true
  },

  "files.autoSave": "off",

  "github.copilot.enable": {
    "*": false
  }
}
```

**What this disables:**
- TypeScript IntelliSense (use Claude instead)
- JavaScript validation
- Watching node_modules and build outputs
- Auto-save

---

## Template 3: MCP Projects (Ultra-Minimal)

**Use for**: MCP servers and projects where you primarily use Claude Code

```json
{
  "editor.formatOnSave": false,

  "python.languageServer": "None",

  "isort.check": false,
  "black-formatter.importStrategy": "fromEnvironment",

  "python.analysis.typeCheckingMode": "off",
  "python.analysis.autoImportCompletions": false,
  "python.analysis.indexing": false,

  "files.watcherExclude": {
    "**/.git/**": true,
    "**/node_modules/**": true,
    "**/.venv/**": true,
    "**/__pycache__/**": true,
    "**/.pytest_cache/**": true,
    "**/dist/**": true
  },

  "files.autoSave": "off",

  "github.copilot.enable": {
    "*": false
  },

  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter",
    "editor.formatOnSave": false
  }
}
```

**What this disables:**
- **Everything!** No language server at all
- No auto-complete, no linting, no type checking
- Minimal file watching
- Format manually when needed

**Philosophy**: Let Claude Code be your IDE. VS Code is just a text editor.

---

## How to Disable ChatGPT Codex Server

The codex server is from the **OpenAI ChatGPT extension**. You have two options:

### Option 1: Disable the Extension
1. Open VS Code
2. Click Extensions (Cmd+Shift+X)
3. Search for "ChatGPT"
4. Click "Disable" (or "Uninstall" if you never use it)

### Option 2: Prevent Auto-Start (Global)
Add to your **User Settings** (Cmd+,):
```json
{
  "chatgpt.gpt3.enable": false,
  "chatgpt.automaticStartup": false
}
```

### Verify It's Disabled
After disabling, check processes:
```bash
ps aux | grep codex | grep -v grep
```

Should return nothing.

---

## Recommended Extensions to Disable/Uninstall

Based on your workflow (using Claude Code primarily):

### Definitely Disable:
- **GitHub Copilot** - You have Claude!
- **ChatGPT/OpenAI** - codex server overhead
- **Pylance** - Redundant with Claude
- **IntelliCode** - AI suggestions you don't need

### Maybe Disable (Per Project):
- **isort** - Format imports manually
- **Black** - Format manually when needed
- **ESLint/Prettier** - Lint/format on-demand

### Keep:
- **Claude Code** - Your main tool!
- **Python** (base extension) - Needed for .py file support
- **Git** - Essential

---

## Global Settings (User-Level)

Add these to your **global settings.json** (Cmd+, → Open Settings JSON):

```json
{
  // Disable features globally
  "editor.formatOnSave": false,
  "editor.formatOnPaste": false,
  "editor.formatOnType": false,

  // Reduce file watching
  "files.watcherExclude": {
    "**/.git/objects/**": true,
    "**/.git/subtree-cache/**": true,
    "**/node_modules/**": true,
    "**/.venv/**": true,
    "**/__pycache__/**": true,
    "**/dist/**": true
  },

  // Disable telemetry
  "telemetry.telemetryLevel": "off",

  // Reduce auto-save overhead
  "files.autoSave": "off",

  // Disable minimap (saves CPU)
  "editor.minimap.enabled": false,

  // Reduce animations
  "workbench.reduceMotion": "on",

  // Disable breadcrumbs (saves rendering)
  "breadcrumbs.enabled": false
}
```

---

## How to Apply Settings

### Per-Project:
1. `cd ~/Programming/your-project`
2. Create/edit `.vscode/settings.json`
3. Paste appropriate template
4. Reload VS Code window (Cmd+Shift+P → "Reload Window")

### Verify Changes:
```bash
# Check for LSP servers (should be minimal)
ps aux | grep -E "isort|black|pylance" | grep -v grep

# Check for codex (should be empty)
ps aux | grep codex | grep -v grep
```

---

## Expected Results

**Before optimization:**
- 40+ processes per project (LSP servers, codex, etc.)
- 3-4GB RAM for VS Code
- Constant CPU usage from file watchers

**After optimization:**
- 5-10 processes per project (core only)
- 1-2GB RAM for VS Code
- Minimal CPU usage
- Faster window switching
- Less beachballing!

---

## Troubleshooting

### "I need formatting sometimes!"
Use on-demand:
- **Format Document**: Cmd+Shift+P → "Format Document"
- **Format Selection**: Cmd+K Cmd+F

### "I miss auto-complete!"
Ask Claude Code instead! It's better at understanding context.

### "My settings aren't taking effect!"
1. Reload window: Cmd+Shift+P → "Reload Window"
2. Check if user settings override project settings
3. Disable extension entirely if needed

---

## Maintenance

**Weekly**: Check running processes
```bash
ps aux | grep -E "python|node|codex" | wc -l
```

Should be <50 processes total.

**Monthly**: Restart VS Code to clear accumulated cruft

**When adding new project**: Copy appropriate template first!

---

## Summary

The key insight: **You don't need an IDE when you have Claude Code.**

VS Code should be a lightweight text editor with syntax highlighting. Let Claude handle:
- Code completion
- Refactoring
- Bug fixes
- Documentation

This saves RAM, CPU, and prevents the freezing/beachballing you experienced.
