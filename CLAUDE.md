# Autocoder - Autonomous Coding Agent

<!-- Last reviewed: 2026-02-04 -->

Autonomous coding agent using Claude Agent SDK. Two-agent pattern:
1. **Initializer Agent** - Reads app spec, creates features in SQLite
2. **Coding Agent** - Implements features one by one

---

## Quick Start

```bash
# Windows
start.bat          # CLI menu
start_ui.bat       # Web UI

# macOS/Linux
./start.sh
./start_ui.sh
```

---

## Key Directories

```
Python Backend:
├── start.py              # CLI launcher
├── autonomous_agent_demo.py  # Agent entry point
├── agent.py              # Session loop (Claude SDK)
├── client.py             # SDK config + security hooks
├── security.py           # Bash allowlist (ALLOWED_COMMANDS)
└── prompts.py            # Prompt loading with fallback

Server API (server/routers/):
├── projects.py           # Project CRUD
├── features.py           # Feature management
├── agent.py              # Start/stop/pause/resume
└── spec_creation.py      # WebSocket for spec creation

React UI (ui/src/):
├── App.tsx               # Main app + kanban
├── hooks/useWebSocket.ts # Real-time updates
└── components/           # FolderBrowser, NewProjectModal

MCP Server:
└── mcp_server/feature_mcp.py  # Feature management tools
```

---

## Project Registry

Projects stored anywhere, registered in `~/.autocoder/registry.db`:
- SQLite with SQLAlchemy ORM
- POSIX paths for cross-platform

Each project contains:
- `prompts/app_spec.txt` - Application spec (XML)
- `prompts/*.md` - Agent prompts
- `features.db` - Feature database
- `.agent.lock` - Prevents multiple instances

---

## Security Model

Defense-in-depth in `client.py`:
1. OS-level sandbox for bash
2. Filesystem restricted to project directory
3. Bash commands validated against `ALLOWED_COMMANDS`

---

## MCP Tools (for agent)

- `feature_get_stats` - Progress statistics
- `feature_get_next` - Next pending feature
- `feature_mark_passing` - Mark complete
- `feature_skip` - Move to end of queue

---

## YOLO Mode

Skip testing for rapid prototyping:
```bash
python autonomous_agent_demo.py --project-dir my-app --yolo
```
- No regression testing
- No Playwright
- Features pass after lint/type-check

---

## Quick Reference

| Need | Location |
|------|----------|
| Slash commands | `.claude/commands/` |
| Skills | `.claude/skills/` |
| Prompt templates | `.claude/templates/` |
| Protocols | `docs/protocols/` |

---

## Synced Protocols

Check `docs/protocols/` for: Claude Code Web vs Terminal, Git Conventions.
