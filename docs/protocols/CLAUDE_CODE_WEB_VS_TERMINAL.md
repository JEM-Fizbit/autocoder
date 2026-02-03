# Claude Code: Web vs Terminal Differences

> **Last Updated:** 2025-11-25
> **Last Reviewed:** 2026-01-29 (still accurate)
> **Purpose:** Document operational differences between Claude Code Web (cloud) and Claude Code Terminal (local) environments

## Overview

Claude Code operates differently depending on the environment:
- **Terminal (Local):** Direct access to your system with your credentials
- **Web (Cloud):** Sandboxed environment with proxy-mediated access

This document captures key differences discovered during development sessions.

---

## Git Access & Branch Restrictions

### Terminal (Local)
- Uses your local git credentials (SSH keys, GitHub tokens, credential manager)
- **Full branch access** - can push to any branch including `main`
- Direct connection to GitHub

### Web (Cloud)
- Git operations route through a **security proxy**
- **Restricted to `claude/*` branches** matching the session ID pattern
- Cannot push directly to `main` or other protected branches

#### Branch Naming Pattern
```
claude/<description>-<session-id>
```
Example: `claude/choose-model-01YMbQpDKaYno8RejxNzDcAG`

#### How It Works
1. All git traffic routes through the proxy at `HTTP_PROXY` / `HTTPS_PROXY`
2. Proxy validates push targets against session ID
3. Pushes to non-matching branches return **HTTP 403**

#### Environment Variables (Web)
```bash
CCR_TEST_GITPROXY=1                    # Git proxy enabled
CLAUDE_CODE_SESSION_ID=session_xxx     # Session ID for branch validation
HTTPS_PROXY=http://...@21.0.0.31:15002 # Proxy endpoint
```

### Workaround for Main Branch Pushes
Since web Claude cannot push to `main`:

1. **Web Claude:** Develop on `claude/*` branch, commit and push
2. **Terminal Claude or User:** Merge to `main` and push
   ```bash
   git fetch origin claude/<branch-name>
   git checkout main
   git merge origin/claude/<branch-name>
   git push origin main
   ```

---

## Environment Variables

### Terminal
- Loaded from shell environment, `.env` files, or exported manually
- Persists across sessions (based on your shell config)

### Web
- Configured in **client environment settings** before session starts
- Injected into container at session initialization
- **Does not persist between sessions** unless configured in client
- Changes to client config require **new session** to take effect

### Accessing Environment Variables
Both environments can access variables the same way:
```bash
echo $VARIABLE_NAME
curl -H "Authorization: token $GITHUB_TOKEN" <url>
```

---

## File System Persistence

### Terminal
- Full access to local file system
- All changes persist

### Web
- Runs in ephemeral container
- Project directory (`/home/user/<project>`) persists during session
- Files outside project may not persist between sessions
- Prefer storing configs in project directory or client environment

---

## Authentication Differences

| Credential Type | Terminal | Web |
|-----------------|----------|-----|
| Git SSH keys | Your local keys | Not available |
| Git HTTPS tokens | Your credential manager | Proxy-managed |
| GitHub PAT | Direct use | Must add to client env |
| API keys | Local `.env` or export | Client environment config |

---

## Recommended Workflow

### For Development (Web Claude)
1. Work on designated `claude/*` branch
2. Commit and push changes regularly
3. Use GitHub API for repo status checks (requires `GITHUB_TOKEN`)

### For Production Merges
1. Create PR from `claude/*` branch to `main`
2. Merge via GitHub UI, or
3. Have terminal Claude or user merge locally

### Environment Setup
Add all required tokens to **client environment configuration**:
```
GITHUB_TOKEN=ghp_xxx          # For GitHub API access
ANTHROPIC_API_KEY=sk-xxx      # Already set for Claude
# ... other project-specific vars
```

---

## Key Reference Sources

### Official Documentation
- [Claude Code Settings](https://docs.claude.com/en/docs/claude-code/settings)
- [Claude Code GitHub Actions](https://docs.claude.com/en/docs/claude-code/github-actions)
- [Using the GitHub Integration](https://support.claude.com/en/articles/10167454-using-the-github-integration)

### Architecture & Security
- [Making Claude Code more secure with sandboxing](https://www.anthropic.com/engineering/claude-code-sandboxing)
- [Claude Code Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### GitHub Issues (Known Limitations)
- [#11153: Claude Code cannot push to GitHub - 403 errors](https://github.com/anthropics/claude-code/issues/11153)
  - Confirms session ID validation for branch pushes
  - Documents workaround of creating new branch with current session ID
- [#11070: Claude Code branches disappear from GitHub](https://github.com/anthropics/claude-code/issues/11070)
  - Documents branch visibility issues

### Community Resources
- [Complete Guide to Git Flow in Claude Code](https://medium.com/@dan.avila7/complete-guide-to-setting-up-git-flow-in-claude-code-616477941f78)
- [Claude Code Developer Cheatsheet](https://awesomeclaude.ai/code-cheatsheet)

---

## Quick Reference

### Check Your Environment
```bash
# See if you're in web or terminal
echo $CLAUDE_CODE_REMOTE  # "true" = web, empty = terminal

# Check git proxy status
echo $CCR_TEST_GITPROXY   # "1" = proxy enabled

# See your session ID (for branch naming)
echo $CLAUDE_CODE_SESSION_ID
```

### Test GitHub API Access
```bash
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  "https://api.github.com/repos/OWNER/REPO" | jq '.full_name'
```

---

## Summary Table

| Capability | Terminal | Web |
|------------|----------|-----|
| Push to `main` | Yes | No (403) |
| Push to `claude/*` | Yes | Yes |
| Direct GitHub auth | Yes | No (proxy) |
| Persistent env vars | Yes | Per-session |
| File persistence | Full | Project dir only |
| SSH keys | Available | Not available |
