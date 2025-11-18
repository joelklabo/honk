# AI Agent Configuration

> **⚠️ IMPORTANT:** This file (`docs/agents.md`) is the **SINGLE SOURCE OF TRUTH** for all AI agent instructions.
> 
> The following files are **SYMLINKS** to this file:
> - `AGENTS.md` → `docs/agents.md`
> - `CLAUDE.md` → `docs/agents.md`
> - `GEMINI.md` → `docs/agents.md`
> - `.github/instructions.md` → `docs/agents.md`
>
> **ONLY EDIT THIS FILE** (`docs/agents.md`) when updating AI agent context or instructions.
> Changes here automatically apply to all AI assistants (Agents, Claude, Gemini, GitHub Copilot).

## Project Structure

```
.
├── .github/
│   └── instructions.md -> ../docs/agents.md  (symlink)
├── .gitignore
├── AGENTS.md -> docs/agents.md               (symlink)
├── CLAUDE.md -> docs/agents.md               (symlink)
├── GEMINI.md -> docs/agents.md               (symlink)
├── docs/
│   ├── agents.md                 ← YOU ARE HERE (source of truth)
│   ├── plans/
│   │   └── main.md               ← Main work tracking document
│   ├── references/               # Documentation, research, notes
│   └── README.md
└── tmp/                          # Temporary files (gitignored)
```

## General Guidelines

- Follow project conventions and style
- Reference `docs/` for context
- **Use `docs/plans/main.md` for work tracking**
  - This is the primary document for tasks, progress, decisions, and next steps
  - Update this file as you complete tasks or make progress
  - Document important decisions and their rationale here
- **Use the project's `tmp/` directory** for all temporary files, scratch work, and outputs
  - ⚠️ **DO NOT use `/tmp/` or system temp directories**
  - All temporary files should go in `./tmp/` (relative to project root)
  - This directory is gitignored and safe for any temporary content
  - Examples: logs, cache files, build artifacts, test outputs, scratch files
- Check `docs/plans/` for project planning documents
- Check `docs/references/` for reference documentation

## Project Context

Add project-specific context here...

### Tech Stack

- Add technologies used in this project...

### Coding Standards

- Add standards here...

## Important Files & Directories

- **docs/plans/main.md** - Main work tracking document (tasks, progress, decisions)
- **docs/plans/** - Additional project plans, architecture decisions, roadmaps
- **docs/references/** - Reference documentation, research notes
- **docs/agents.md** - This file (AI configuration)
- **tmp/** - Temporary files and scratch work (gitignored)

## Custom Agents

Define custom GitHub Copilot agents below:

### Example Agent

```markdown
---
name: Example Agent
description: A sample custom agent
---

# Agent Instructions

Your instructions here...
```
