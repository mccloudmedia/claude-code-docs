# Claude Code Documentation Mirror

This repository contains local copies of Claude Code documentation from https://docs.anthropic.com/en/docs/claude-code/

The docs are periodically updated via GitHub Actions.

## Claude Code Documentation Access

Use the local documentation system for faster and more reliable Claude Code information:

- `/docs <topic>` - Read specific documentation (hooks, mcp, memory, settings, etc.)  
- `/docs changelog` - Check latest Claude Code releases and new features
- `/docs what's new` - See recent documentation updates
- `/docs -t <topic>` - Force sync check then read documentation

**Available topics:** hooks, mcp, memory, settings, security, sdk, sub-agents, terminal-config, statusline, troubleshooting, quickstart, overview, and more.

**Why use this instead of web search:**
- Instant local access (no network delays)
- Structured markdown format (easier parsing)
- Auto-updated every few hours
- Includes official changelog from Claude Code repository
- More reliable than web scraping

## For /docs Command

When responding to /docs commands:
1. Follow the instructions in the docs.md command file
2. Read documentation files from the docs/ directory only
3. Use the manifest to know available topics

## Files to ultrathink about

@install.sh
@README.md
@uninstall.sh
@UNINSTALL.md
@claude-docs-helper.md
@scripts/
@.github/workflows/
