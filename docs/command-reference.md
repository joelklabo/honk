# Honk CLI Command Reference

**Repository:** ~/code/honk  
**Last Updated:** 2025-11-19

## Overview

Honk is an agent-first CLI for developer workflows, providing system diagnostics, PTY monitoring, and AI-assisted note-taking.

---

## Installation

```bash
cd ~/code/honk
pip install -e .
```

---

## Command Structure

```
honk [OPTIONS] COMMAND [ARGS]...
```

**Global Options:**
- `--no-color` - Disable colored output
- `--version` - Show version and exit
- `--help` - Show help message

---

## Commands

### 1. `honk watchdog` - System Health Monitoring

Monitor PTY usage and system health.

#### `honk watchdog pty show`

Display current PTY usage and detect potential leaks.

```bash
honk watchdog pty show
honk watchdog pty show --json
```

**Output:**
- Total PTYs in use
- Processes holding PTYs
- Heavy PTY users (>4 PTYs)
- Suspected leaks

---

#### `honk watchdog pty clean`

Kill processes with orphaned PTY sessions.

```bash
# Dry-run mode (show what would be killed)
honk watchdog pty clean --plan

# Interactive mode (confirm each kill)
honk watchdog pty clean --interactive

# Adjust threshold
honk watchdog pty clean --threshold 10

# JSON output
honk watchdog pty clean --json
```

**Options:**
- `--plan` - Dry-run mode (no actual kills)
- `--interactive` - Prompt for confirmation
- `--threshold INT` - Minimum PTYs to trigger cleanup (default: 4)
- `--json` - Output as JSON

**Safety:** With recent fixes (Task 98), this command:
- ✅ Never kills processes with active controlling TTY
- ✅ Uses high threshold for copilot processes (20 PTYs)
- ✅ Protects interactive sessions (Copilot CLI, tmux, screen)

---

#### `honk watchdog pty daemon`

Background PTY monitoring service with caching.

```bash
# Start daemon
honk watchdog pty daemon --start

# Stop daemon
honk watchdog pty daemon --stop

# Check status
honk watchdog pty daemon --status

# Start with custom scan interval
honk watchdog pty daemon --start --scan-interval 60

# Enable auto-kill above threshold
honk watchdog pty daemon --start --auto-kill-threshold 50
```

**Options:**
- `--start` - Start daemon in background
- `--stop` - Stop running daemon
- `--status` - Check daemon status
- `--scan-interval INT` - Seconds between scans (default: 30)
- `--auto-kill-threshold INT` - Auto-kill processes above this PTY count (default: 0, disabled)
- `--json` - Output as JSON

**Output Files:**
- `tmp/pty-cache.json` - Cached PTY data
- `tmp/pty-daemon.log` - Daemon log file

---

#### `honk watchdog pty observer`

TUI dashboard displaying cached PTY data.

```bash
# Live mode (auto-refresh every 5s)
honk watchdog pty observer

# Single snapshot
honk watchdog pty observer --no-live

# Custom cache file
honk watchdog pty observer --cache-file /path/to/cache.json
```

**Options:**
- `--live/--no-live` - Auto-refresh every 5s (default: live)
- `--cache-file PATH` - Path to cache file (default: tmp/pty-cache.json)

**Prerequisites:** Requires `textual` library and running daemon.

**Fix Applied (Task 60):** Async event loop errors resolved.

---

#### `honk watchdog pty watch`

Monitor PTY usage and auto-clean when thresholds exceeded.

```bash
# Basic watch
honk watchdog pty watch

# Custom interval and threshold
honk watchdog pty watch --interval 10 --max-ptys 100

# JSON output stream
honk watchdog pty watch --json

# With system notifications
honk watchdog pty watch --notify
```

**Options:**
- `--interval INT` - Check interval in seconds (default: 5)
- `--max-ptys INT` - Auto-clean threshold (default: 200)
- `--json` - Stream JSON events
- `--notify` - Send system notification on cleanup

---

#### `honk watchdog pty history`

Show history of cleanup events from log file.

```bash
honk watchdog pty history
honk watchdog pty history --limit 50
```

**Options:**
- `--limit INT` - Number of entries to show (default: 20)

---

### 2. `honk system` - System Diagnostics Suite

#### `honk system summary`

High-level dashboard of system health.

```bash
honk system summary
```

---

#### `honk system processes`

Show running processes, sorted by CPU or memory.

```bash
honk system processes
```

**Known Issue (Task 100):** Internal error with PID 0 (kernel_task). Fix pending.

---

#### `honk system network`

Show network connections.

```bash
honk system network
```

**Known Issue (Task 101):** Internal error. Fix pending.

---

#### `honk system pty`

Detailed report of all processes currently holding PTYs.

```bash
honk system pty
```

---

#### `honk system fds`

Report on file descriptor usage.

```bash
honk system fds
```

---

### 3. `honk agent` - AI Agent Management

#### `honk agent list`

List available agents in project or globally.

```bash
honk agent list
```

---

#### `honk agent invoke`

Invoke agents programmatically from CLI or scripts.

```bash
honk agent invoke AGENT_NAME
```

---

#### `honk agent scaffold`

Create new agents from templates.

```bash
honk agent scaffold
```

---

#### `honk agent template`

Manage agent templates (list, show, add).

```bash
honk agent template list
honk agent template show TEMPLATE_NAME
```

---

#### `honk agent validate`

Validate agent YAML frontmatter against schema.

```bash
honk agent validate AGENT_FILE
```

---

### 4. `honk notes` - AI-Assisted Note-Taking

#### `honk notes edit`

Open AI-assisted notes editor.

```bash
honk notes edit
```

---

#### `honk notes organize`

Organize notes file with AI (non-interactive).

```bash
honk notes organize
```

---

#### `honk notes agent-get`

Agent-friendly: Get information without opening editor.

```bash
honk notes agent-get
```

---

#### `honk notes agent-set`

Agent-friendly: Set content without opening editor.

```bash
honk notes agent-set
```

---

#### `honk notes agent-organize`

Agent-friendly: Organize file without opening editor.

```bash
honk notes agent-organize
```

---

#### `honk notes config`

Manage notes configuration.

```bash
honk notes config
```

---

### 5. `honk release` - Release Automation Tools

```bash
honk release --help
```

---

### 6. `honk demo` - Demo Commands

#### `honk demo hello`

Demo command demonstrating full CLI contract.

```bash
honk demo hello
```

---

### 7. `honk doctor` - Prerequisite Checks

Run doctor packs to check prerequisites.

```bash
# Plan mode (no mutations)
honk doctor --plan

# JSON output
honk doctor --json
```

---

### 8. `honk auth` - Authentication Management

```bash
honk auth --help
```

---

### 9. `honk completion` - Shell Completion Management

```bash
honk completion --help
```

---

### 10. Utility Commands

#### `honk info`

Show CLI information.

```bash
honk info
```

---

#### `honk version`

Show version information.

```bash
honk version
```

---

#### `honk help-json`

Get machine-readable help for a specific command.

```bash
honk help-json COMMAND
```

---

#### `honk introspect`

Emit command catalog with metadata for all commands.

```bash
honk introspect
```

---

## Recent Fixes (2025-11-19)

### Task 98: PTY Cleanup Safety
**Fixed:** `honk watchdog pty clean` no longer kills active Copilot CLI sessions.
- Added controlling TTY check (protects interactive sessions)
- Raised threshold from 4 → 20 PTYs for copilot processes
- Graceful fallback without psutil dependency

### Task 60: Observer Async Errors
**Fixed:** `honk watchdog pty observer` async/event loop warnings resolved.
- Replaced `set_interval` with recursive `call_later` pattern
- Proper async scheduling in Textual app context

---

## Future Improvements

See planloop tasks:
- Task 99: Add `--dry-run` flag as alias for `--plan`
- Task 100: Fix `honk system processes` PID 0 error
- Task 101: Fix `honk system network` internal error
- Task 103: Add comprehensive tests for PTY commands
- Task 104: Add safelist configuration for PTY cleanup

---

## Support

**Repository:** https://github.com/user/honk (if public)  
**Issues:** File bugs and feature requests in the issue tracker  
**Documentation:** See `docs/` folder in repository
