---
description: Organize project documentation and memory
allowed-tools: Read, Edit, Write, Glob, Grep, Bash
---

# Neat - Knowledge Base Organizer

You are a **knowledge base editor**, not a recorder. Recorders only append, editors review globally, merge duplicates, fix outdated content, delete废弃. Your job is to keep the project's knowledge system **clean, accurate, and friendly to newcomers** — like a neat freak.

## Step 0: Size Check (Prevent Bloat)

Before any sync action, check key file sizes:

```bash
# Check main doc file line counts
wc -l CLAUDE.md README.md 2>/dev/null
find docs -name "*.md" -exec wc -l {} + 2>/dev/null | sort -rn | head -10
```

**Size limits**:
- `CLAUDE.md`: ~300 lines (needs slimming if over)
- Single `docs/*.md`: ~1500 lines (needs splitting if over)
- Memory index: ~150 lines (needs slimming if over)

**Execution order**: Slim down first (break bloat) → Then incremental sync (fill gaps)

## Step 1: Inventory Current State

```bash
# 1. List current project structure
ls -la
find . -maxdepth 2 -name "*.md" -not -path "*/node_modules/*" -not -path "*/.git/*" | sort

# 2. List docs directory
ls -la docs/ 2>/dev/null
find docs -name "*.md" 2>/dev/null | sort

# 3. Check temp files
find . -name "test_*.py" -o -name "*test*.md" -o -name "*TEMP*" 2>/dev/null | grep -v node_modules
```

**Output file list**, mark each file: 「reviewed / to-change / no-change」

## Step 2: Identify Changes and Organize

### File Classification Principles

**Keep in root directory**:
- `README.md` - Project description
- `CLAUDE.md` - AI collaboration guide
- `CHANGELOG.md` - Change log
- `DEVELOPMENT_PLAN.md` - Development plan

**Move to docs/archive/**:
- Old reports and summaries (dated files)
- Completed feature docs
- Historical audit docs

**Move to docs/guides/**:
- User guides and tutorials
- API guides
- Troubleshooting docs

**Move to docs/reports/**:
- Performance reports
- Security audits
- Quality reports

**Move to tests/temp/** or delete:
- Temporary test files
- Diagnostic scripts
- One-time verification files

### Execute Organization

```bash
# Create directory structure
mkdir -p docs/archive docs/guides docs/reports backend/tests/temp 2>/dev/null

# Move files (adjust based on actual situation)
# mv ARCHITECTURE_*.md docs/archive/
# mv RECORDING_*.md docs/guides/
# mv test_*.py backend/tests/temp/
```

## Step 3: Slim Down Outdated Content

### Clean Up Historical Narratives in CLAUDE.md

**Check and delete**:
- Historical narrative blockquotes at top ("2026-05-08 X feature launched")
- Redundant "see docs/X.md" pointers
- Project memories replaced by new versions
- Single-incident post-mortem narratives

**Keep**:
- Hard boundary rules
- Prohibited items
- Command quick reference
- Permission model
- Pitfall warnings

### Clean Up Memory Files

```bash
# Check memory file sizes
wc -l ~/.claude/projects/*/memory/*.md 2>/dev/null | sort -rn
```

**Delete or merge**:
- Relative time descriptions ("today", "yesterday", "recently")
- Duplicate memory entries
- Completed todo items
- Expired technical decisions

## Step 4: Verify and Commit

### Self-Check List

- [ ] CLAUDE.md net growth ≤ 30 lines
- [ ] Root directory only has core files
- [ ] Docs classified by type correctly
- [ ] No relative time leftovers
- [ ] Temp files removed or archived
- [ ] No contradictions between memories

### Commit Changes

```bash
git add -A
git status
```

Display the list of changes ready to commit, wait for user confirmation before committing.

## Step 5: Change Summary

After all file modifications complete, give user a concise summary:

```
## Sync Complete

### File Organization
- Archived files: X → docs/archive/
- Guide files: X → docs/guides/
- Report files: X → docs/reports/
- Test files: X → backend/tests/temp/

### Memory Changes
- Updated: xxx
- Added: xxx
- Deleted: xxx

### Not Handled
- xxx (reason)
```
