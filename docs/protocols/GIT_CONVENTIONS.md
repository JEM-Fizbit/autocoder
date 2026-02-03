# Git Conventions Protocol

> Universal git workflow, commit conventions, and branching strategies for AI-assisted development.

**Applies to:** All projects using Git
**Last Updated:** 2026-02-03
**Version:** 1.0

---

## Table of Contents

- [Commit Messages](#commit-messages)
- [Branching Strategy](#branching-strategy)
- [Pull Request Workflow](#pull-request-workflow)
- [Git Configuration](#git-configuration)
- [Common Operations](#common-operations)
- [MCP Integration](#mcp-integration)
- [Security Rules](#security-rules)

---

## Commit Messages

### Format

```
type(scope): description

[optional body]

[optional footer]
Co-Authored-By: Claude <noreply@anthropic.com>
```

### Types

| Type | Use For |
|------|---------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code restructuring |
| `test` | Adding/updating tests |
| `chore` | Build, dependencies, tooling |
| `perf` | Performance improvements |

### Scope Examples

| Scope | Meaning |
|-------|---------|
| `api` | API routes/endpoints |
| `db` | Database changes |
| `ui` | User interface |
| `auth` | Authentication |
| `edge` | Edge Functions |
| `lambda` | AWS Lambda |

### Examples

```bash
# Feature
feat(api): add user preferences endpoint

# Bug fix
fix(auth): resolve session expiration race condition

# Documentation
docs(readme): update installation instructions

# Database
feat(db): add analytics table with RLS policies

# Edge Function
feat(edge): add TTS generation function
```

### Commit Message Rules

1. **Imperative mood**: "add feature" not "added feature"
2. **No period** at end of subject line
3. **Max 72 characters** for subject line
4. **Blank line** between subject and body
5. **Body explains "why"**, not "what" (code shows what)

---

## Branching Strategy

### Main Branches

| Branch | Purpose | Deploys To |
|--------|---------|------------|
| `main` | Production code | Production |
| `develop` | Integration branch (optional) | Staging |

### Feature Branches

```bash
# Create feature branch
git checkout -b feat/user-preferences

# Create fix branch
git checkout -b fix/login-redirect

# Create refactor branch
git checkout -b refactor/api-structure
```

### Branch Naming

```
type/description-in-kebab-case

# Examples
feat/add-dark-mode
fix/memory-leak-in-player
refactor/extract-auth-service
docs/update-api-reference
```

---

## Pull Request Workflow

### Creating a PR

```bash
# 1. Ensure branch is up to date
git fetch origin
git rebase origin/main

# 2. Push branch
git push -u origin feat/my-feature

# 3. Create PR via GitHub CLI
gh pr create --title "feat: add my feature" --body "## Summary
- Added X
- Fixed Y

## Test Plan
- [ ] Test A
- [ ] Test B"
```

### PR Title Format

Same as commit message format:
```
type(scope): description
```

### PR Body Template

```markdown
## Summary
Brief description of changes

## Changes
- Change 1
- Change 2

## Test Plan
- [ ] Manual testing step 1
- [ ] Manual testing step 2

## Screenshots (if UI changes)
[Add screenshots here]
```

### Review Process

1. **Self-review**: Check diff before requesting review
2. **CI passes**: All checks must pass
3. **Reviewer approval**: At least one approval required
4. **Squash merge**: Keep history clean

---

## Git Configuration

### Required Setup

```bash
# Set identity (use for all projects)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"

# Per-project override (if needed)
git config user.name "Project Name"
git config user.email "project@example.com"
```

### Recommended Settings

```bash
# Default branch name
git config --global init.defaultBranch main

# Rebase on pull (cleaner history)
git config --global pull.rebase true

# Auto-prune on fetch
git config --global fetch.prune true

# Better diff algorithm
git config --global diff.algorithm histogram
```

---

## Common Operations

### Daily Workflow

```bash
# Start of day: update main
git checkout main
git pull origin main

# Create feature branch
git checkout -b feat/my-feature

# Work on feature...
git add specific-file.ts
git commit -m "feat: add initial implementation"

# Push and create PR
git push -u origin feat/my-feature
gh pr create
```

### Updating Feature Branch

```bash
# Fetch latest main
git fetch origin main

# Rebase onto main (preferred)
git rebase origin/main

# Or merge main into feature branch
git merge origin/main
```

### Fixing Commits

```bash
# Amend last commit (before push)
git commit --amend -m "corrected message"

# Interactive rebase (before push, use carefully)
git rebase -i HEAD~3

# Add forgotten file to last commit
git add forgotten-file.ts
git commit --amend --no-edit
```

### Undoing Changes

```bash
# Discard uncommitted changes to a file
git checkout -- path/to/file

# Unstage a file
git reset HEAD path/to/file

# Undo last commit (keep changes)
git reset --soft HEAD~1

# Undo last commit (discard changes) - DANGEROUS
git reset --hard HEAD~1
```

---

## MCP Integration

### GitHub MCP Server

When using Claude Code with the GitHub MCP server, these operations are handled by MCP tools:

| Operation | MCP Tool | Local Git |
|-----------|----------|-----------|
| Create PR | `mcp__github__create_pull_request` | `gh pr create` |
| List PRs | `mcp__github__list_pull_requests` | `gh pr list` |
| Get PR diff | `mcp__github__pull_request_read` | `gh pr diff` |
| Create branch | `mcp__github__create_branch` | `git checkout -b` |
| Push files | `mcp__github__push_files` | `git push` |

### When to Use Which

| Use MCP | Use Local Git |
|---------|---------------|
| Creating PRs | Local commits |
| Reviewing PRs | Branch switching |
| GitHub API operations | Rebasing |
| Cross-repo operations | Amending commits |

### Local Operations Still Required

MCP handles GitHub remote operations, but local git commands are still needed for:

- `git add` - Staging files
- `git commit` - Creating commits
- `git checkout` - Switching branches locally
- `git rebase` - Rewriting history
- `git stash` - Temporary storage

---

## Security Rules

### Never Commit

- `.env` files with real secrets
- API keys or tokens
- Database credentials
- Private keys
- `node_modules/` (use .gitignore)

### Safe Practices

```bash
# Use specific file adds, not blanket add
git add specific-file.ts  # ✅ Good
git add .                 # ❌ Risky
git add -A                # ❌ Risky

# Check what you're committing
git diff --staged         # Review before commit

# Use .gitignore
echo ".env" >> .gitignore
echo "*.pem" >> .gitignore
```

### If Secrets Are Committed

1. **Immediately rotate the secret** (most important)
2. Remove from history (optional, complex):
   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch path/to/secret" \
     --prune-empty --tag-name-filter cat -- --all
   ```
3. Force push (coordinate with team)
4. Contact GitHub to clear caches

---

## Deployment Integration

### Auto-Deploy Triggers

| Platform | Trigger | Branch |
|----------|---------|--------|
| Vercel | Push to main | `main` |
| Render | Push to main | `main` |
| Replit | Auto-sync | `main` |
| Supabase | GitHub integration | `main` |

### Pre-Push Checklist

- [ ] All tests pass locally
- [ ] No console.logs or debug code
- [ ] No hardcoded secrets
- [ ] Commit message follows convention
- [ ] PR description is complete

---

## Quick Reference

```bash
# Status
git status
git log --oneline -10

# Branching
git checkout -b feat/name    # Create branch
git checkout main            # Switch to main
git branch -d feat/name      # Delete local branch

# Committing
git add file.ts              # Stage file
git commit -m "type: msg"    # Commit
git commit --amend           # Fix last commit

# Syncing
git fetch origin             # Get remote changes
git pull --rebase            # Update with rebase
git push origin branch       # Push branch

# PRs (GitHub CLI)
gh pr create                 # Create PR
gh pr list                   # List PRs
gh pr merge                  # Merge PR
```

---

**Protocol Version**: 1.0
**Last Updated**: 2026-02-03
**Sources**: Fizbit-orchestration, statarb-platform, TeachMeIn5-FullApp
