# Honk Watchdog PTY - Implementation Specification

**Version:** 1.0  
**Status:** Draft  
**Created:** 2025-11-18  
**Area:** `watchdog`  
**Tool:** `pty`

---

## Executive Summary

`honk watchdog pty` is a PTY session monitoring and cleanup tool that detects orphaned pseudo-terminal (PTY) devices and terminates leaking processes. It addresses the common problem of PTY exhaustion caused by long-running processes (especially Copilot/Node agents) that don't properly clean up terminal sessions.

The tool follows Honk's design principles:
- **Agent-first:** Machine-readable output via result envelopes and `--json`
- **Prereq-driven:** Uses doctor packs to verify system requirements
- **Typer-based:** Auto-generated help with Rich formatting
- **Safe by default:** Conservative cleanup rules and detailed reporting

---

## Command Structure

### Namespace

```
honk watchdog pty <action> [options]
```

**Area:** `watchdog` (system health monitoring)  
**Tool:** `pty` (PTY session management)  
**Actions:** `show`, `clean`, `watch`, `daemon`, `observer`

### Grammar Alignment

Following Honk's `<area> <tool> <action>` pattern:
- **Area:** `watchdog` - system health monitoring and cleanup tools
- **Tool:** `pty` - PTY-specific operations
- **Actions:** 
  - `show` - display current PTY usage
  - `clean` - kill leaking processes
  - `watch` - monitor and auto-clean
  - `daemon` - background PTY monitoring service
  - `observer` - TUI dashboard for cached PTY data

---

## Actions Specification

### 1. `honk watchdog pty show`

**Purpose:** Enumerate all PTY devices and processes using them.

**Signature:**
```bash
honk watchdog pty show [--json] [--no-color]
```

**Options:**
- `--json` (bool, default: false): Output result envelope
- `--no-color` (bool, default: false): Disable Rich formatting

**Behavior:**
1. Run `global` doctor pack (verify `lsof` availability)
2. Execute `lsof -FpnT` to enumerate PTY mappings
3. Parse output to build process → PTY mapping
4. Calculate statistics (total PTYs, heavy users, suspected leaks)
5. Return result envelope with facts

**Exit Codes:**
- `0` - Success
- `10` - Prerequisites failed (lsof not found)
- `50` - Internal error

**Result Envelope Structure:**
```json
{
  "version": "1.0",
  "command": ["honk", "watchdog", "pty", "show"],
  "status": "ok",
  "changed": false,
  "code": "watchdog.pty.show.ok",
  "summary": "Found 247 PTYs across 18 processes",
  "run_id": "uuid",
  "duration_ms": 142,
  "facts": {
    "total_ptys": 247,
    "process_count": 18,
    "heavy_users": [
      {
        "pid": 12345,
        "command": "node /usr/local/bin/copilot-agent",
        "pty_count": 87,
        "ptys": ["/dev/ttys001", "/dev/ttys002", "..."]
      }
    ],
    "suspected_leaks": [
      {
        "pid": 12345,
        "command": "node /usr/local/bin/copilot-agent",
        "pty_count": 87,
        "reason": "copilot-like process with >4 PTYs"
      }
    ],
    "processes": [
      {
        "pid": 12345,
        "command": "node /usr/local/bin/copilot-agent",
        "pty_count": 87,
        "ptys": ["/dev/ttys001", "..."]
      }
    ]
  },
  "links": [
    {
      "rel": "docs",
      "href": "https://github.com/honk/honk/blob/main/docs/references/watchdog-pty-spec.md"
    }
  ],
  "next": [
    {
      "run": ["honk", "watchdog", "pty", "clean"],
      "summary": "Clean up suspected leaks"
    }
  ]
}
```

**Human-Friendly Output (Rich):**
```
=== PTY Usage ===
Found 18 processes with PTYs.

PID 12345: node /usr/local/bin/copilot-agent
   - /dev/ttys001
   - /dev/ttys002
   [... 85 more ...]

=== Summary ===
Total PTYs in use: 247
Processes holding PTYs: 18

Heavy PTY users (>4 PTYs):
• PID 12345 (node /usr/local/bin/copilot-agent) — 87 PTYs
• PID 67890 (node /usr/bin/github-copilot) — 23 PTYs

Suspected Copilot/Node leaks:
• PID 12345 (node /usr/local/bin/copilot-agent) — 87 PTYs
• PID 67890 (node /usr/bin/github-copilot) — 23 PTYs
```

---

### 2. `honk watchdog pty clean`

**Purpose:** Kill processes with orphaned PTY sessions.

**Signature:**
```bash
honk watchdog pty clean [--json] [--no-color] [--plan] [--threshold INT]
```

**Options:**
- `--json` (bool, default: false): Output result envelope
- `--no-color` (bool, default: false): Disable Rich formatting
- `--plan` (bool, default: false): Dry-run mode, show what would be killed
- `--threshold` (int, default: 4): Minimum PTYs to trigger cleanup for copilot-like processes

**Behavior:**
1. Run `global` doctor pack
2. Enumerate PTYs via `show` logic
3. Identify leaking processes using heuristics:
   - Command contains "copilot" (case-insensitive)
   - Command contains "node" + "copilot"
   - Command contains "agent" + "copilot"
   - Process has > `--threshold` PTYs
4. If `--plan`, report what would be killed and exit
5. Send `SIGTERM` to identified processes
6. Re-scan PTYs and report changes
7. Return result envelope with killed PIDs

**Cleanup Heuristics (Safety Rules):**
- Only kill processes matching copilot-like patterns
- Never kill system processes (PID < 100, UID 0)
- Respect `--threshold` for non-copilot processes
- Use SIGTERM (graceful) not SIGKILL

**Exit Codes:**
- `0` - Success (killed processes or none found)
- `10` - Prerequisites failed
- `30` - Permission denied (can't kill process)
- `50` - Internal error

**Result Envelope Structure:**
```json
{
  "version": "1.0",
  "command": ["honk", "watchdog", "pty", "clean"],
  "status": "ok",
  "changed": true,
  "code": "watchdog.pty.clean.ok",
  "summary": "Killed 2 leaking processes, freed 110 PTYs",
  "run_id": "uuid",
  "duration_ms": 523,
  "facts": {
    "before": {
      "total_ptys": 247,
      "process_count": 18
    },
    "after": {
      "total_ptys": 137,
      "process_count": 16
    },
    "killed": [
      {
        "pid": 12345,
        "command": "node /usr/local/bin/copilot-agent",
        "pty_count": 87,
        "success": true
      },
      {
        "pid": 67890,
        "command": "node /usr/bin/github-copilot",
        "pty_count": 23,
        "success": true
      }
    ],
    "freed_ptys": 110
  },
  "next": [
    {
      "run": ["honk", "watchdog", "pty", "show"],
      "summary": "Verify cleanup results"
    }
  ]
}
```

**Human-Friendly Output (Rich):**
```
=== Cleaning PTY leaks ===
Killed PID 12345 (node /usr/local/bin/copilot-agent) — 87 PTYs
Killed PID 67890 (node /usr/bin/github-copilot) — 23 PTYs

Killed 2 leaking processes.

=== Summary ===
Total PTYs in use: 137 (was 247)
Processes holding PTYs: 16 (was 18)
Freed: 110 PTYs
```

---

### 3. `honk watchdog pty watch`

**Purpose:** Monitor PTY usage and auto-clean when thresholds are exceeded.

**Signature:**
```bash
honk watchdog pty watch [--interval INT] [--max-ptys INT] [--json]
```

**Options:**
- `--interval` (int, default: 5): Check interval in seconds
- `--max-ptys` (int, default: 200): Auto-clean when total exceeds this
- `--json` (bool, default: false): Stream JSON events to stdout
- `--events-jsonl` (path, optional): Log events to JSONL file in `tmp/`
- `--no-color` (bool, default: false): Disable Rich formatting

**Behavior:**
1. Run `global` doctor pack once at startup
2. Loop indefinitely (Ctrl+C to stop):
   - Scan PTYs (silent, no output)
   - If total > `--max-ptys`, trigger cleanup
   - Sleep for `--interval` seconds
   - Print status line or JSON event
3. On SIGINT/SIGTERM, print summary and exit gracefully

**Exit Codes:**
- `0` - User interrupted (Ctrl+C)
- `10` - Prerequisites failed
- `50` - Internal error

**Event Stream (JSON mode):**
```json
{"event": "scan", "timestamp": "2025-11-18T09:17:00Z", "total_ptys": 247, "process_count": 18}
{"event": "threshold_exceeded", "timestamp": "2025-11-18T09:17:05Z", "total_ptys": 312, "max_ptys": 200}
{"event": "cleanup_started", "timestamp": "2025-11-18T09:17:05Z"}
{"event": "cleanup_completed", "timestamp": "2025-11-18T09:17:06Z", "killed_count": 3, "freed_ptys": 175}
{"event": "scan", "timestamp": "2025-11-18T09:17:10Z", "total_ptys": 137, "process_count": 15}
```

**Human-Friendly Output (Rich):**
```
Watching PTY usage every 5s… Ctrl+C to stop.

[09:17:00] PTYs=247  procs=18
[09:17:05] PTYs=312  procs=21  !! HIGH — cleaning…
[09:17:06]   → Killed 3 processes (175 PTYs freed)
[09:17:10] PTYs=137  procs=15
[09:17:15] PTYs=142  procs=16
^C
=== Watch Summary ===
Total scans: 24
Cleanups triggered: 1
Processes killed: 3
Uptime: 2m 15s
```

---

## Implementation Details

### Module Structure

Following Honk's conventions:

```
src/honk/tools/watchdog/
├── __init__.py              # Area registration
├── pty.py                   # Main PTY tool logic
└── pty_scanner.py           # PTY enumeration & process detection
```

**File:** `src/honk/tools/watchdog/__init__.py`
```python
"""Watchdog area: system health monitoring and cleanup tools."""

import typer
from ..registry import AreaMetadata

watchdog_app = typer.Typer(
    help="System health monitoring and cleanup tools",
    no_args_is_help=True
)

def register(app: typer.Typer) -> AreaMetadata:
    """Register watchdog area with the main CLI."""
    from . import pty
    
    app.add_typer(watchdog_app, name="watchdog")
    watchdog_app.add_typer(pty.pty_app, name="pty")
    
    return AreaMetadata(
        area="watchdog",
        summary="System health monitoring and cleanup",
        prereqs=["global"],
    )
```

**File:** `src/honk/tools/watchdog/pty.py`
```python
"""PTY watchdog commands."""

import sys
import time
import signal
import typer
from typing import Optional
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...result import ResultEnvelope, NextStep, Link, EXIT_OK, EXIT_PREREQ_FAILED, EXIT_SYSTEM
from ...internal.doctor import run_all_packs
from ...registry import register_command, CommandMetadata, CommandOption, CommandExample
from .pty_scanner import scan_ptys, kill_processes, is_leak_candidate

console = Console()
pty_app = typer.Typer(help="PTY session monitoring and cleanup")

@pty_app.command("show")
def show(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Display current PTY usage and detect potential leaks."""
    # Implementation details below...

@pty_app.command("clean")
def clean(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    plan: bool = typer.Option(False, "--plan", help="Dry-run mode (show what would be killed)"),
    threshold: int = typer.Option(4, "--threshold", help="Minimum PTYs to trigger cleanup"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Kill processes with orphaned PTY sessions."""
    # Implementation details below...

@pty_app.command("watch")
def watch(
    interval: int = typer.Option(5, "--interval", help="Check interval in seconds"),
    max_ptys: int = typer.Option(200, "--max-ptys", help="Auto-clean threshold"),
    json_output: bool = typer.Option(False, "--json", help="Stream JSON events"),
    events_jsonl: Optional[str] = typer.Option(None, "--events-jsonl", help="Log events to JSONL file"),
):
    """Monitor PTY usage and auto-clean when thresholds are exceeded."""
    # Implementation details below...

# Register commands with introspection system
register_command(CommandMetadata(...))
```

**File:** `src/honk/tools/watchdog/pty_scanner.py`
```python
"""PTY scanner and process detection."""

import subprocess
import os
import signal
from typing import Dict, List, Tuple
from dataclasses import dataclass

@dataclass
class PTYProcess:
    """Process holding PTY sessions."""
    pid: int
    command: str | None
    ptys: List[str]
    
    @property
    def pty_count(self) -> int:
        return len(self.ptys)

def run_lsof() -> str:
    """Execute lsof to enumerate PTYs."""
    try:
        return subprocess.check_output(
            ["lsof", "-FpnT"],
            text=True,
            stderr=subprocess.DEVNULL
        )
    except subprocess.CalledProcessError:
        return ""
    except FileNotFoundError:
        raise RuntimeError("lsof not found - install it via Homebrew or system package manager")

def parse_lsof_output(output: str) -> Dict[int, PTYProcess]:
    """Parse lsof output into process → PTY mapping."""
    processes: Dict[int, PTYProcess] = {}
    current_pid: int | None = None
    current_cmd: str | None = None
    
    for line in output.splitlines():
        if line.startswith("p"):  # PID
            current_pid = int(line[1:])
            if current_pid not in processes:
                processes[current_pid] = PTYProcess(
                    pid=current_pid,
                    command=None,
                    ptys=[]
                )
        elif line.startswith("c"):  # Command
            current_cmd = line[1:]
            if current_pid and current_pid in processes:
                processes[current_pid].command = current_cmd
        elif line.startswith("n/dev/ttys"):  # PTY path
            if current_pid and current_pid in processes:
                processes[current_pid].ptys.append(line[1:])
    
    return processes

def scan_ptys() -> Dict[int, PTYProcess]:
    """Scan system for PTY usage."""
    output = run_lsof()
    return parse_lsof_output(output)

def is_leak_candidate(proc: PTYProcess, threshold: int = 4) -> bool:
    """Determine if process is a leak candidate."""
    if not proc.command:
        return False
    
    cmd = proc.command.lower()
    
    # Heuristic: copilot-like processes
    if "copilot" in cmd:
        return proc.pty_count > threshold
    if "node" in cmd and "copilot" in cmd:
        return proc.pty_count > threshold
    if "agent" in cmd and "copilot" in cmd:
        return proc.pty_count > threshold
    
    # Heavy users (fallback)
    return proc.pty_count > threshold * 2

def kill_processes(pids: List[int]) -> Dict[int, bool]:
    """Kill processes and return success status."""
    results = {}
    for pid in pids:
        try:
            os.kill(pid, signal.SIGTERM)
            results[pid] = True
        except ProcessLookupError:
            results[pid] = False  # Already dead
        except PermissionError:
            results[pid] = False  # Can't kill
    return results

def get_heavy_users(processes: Dict[int, PTYProcess], threshold: int = 4) -> List[PTYProcess]:
    """Find processes using more than threshold PTYs."""
    return [p for p in processes.values() if p.pty_count > threshold]

def get_suspected_leaks(processes: Dict[int, PTYProcess], threshold: int = 4) -> List[PTYProcess]:
    """Find suspected leak candidates."""
    return [p for p in processes.values() if is_leak_candidate(p, threshold)]
```

---

## Doctor Pack Requirements

**Pack:** `watchdog.pty` (optional, inherits from `global`)

**Checks:**
1. `lsof` binary available (`which lsof`)
2. User has permission to read PTY descriptors
3. Sufficient `/dev/ttys*` capacity

**Remediation:**
- macOS: `brew install lsof` (usually pre-installed)
- Linux: `apt install lsof` or `yum install lsof`

**Integration:**
- Runs automatically via inherited `global` pack
- No custom pack needed unless specific checks are required

---

## Testing Strategy

### Unit Tests

**File:** `tests/tools/watchdog/test_pty_scanner.py`

```python
"""Unit tests for PTY scanner."""

import pytest
from honk.tools.watchdog.pty_scanner import (
    parse_lsof_output,
    is_leak_candidate,
    get_heavy_users,
    PTYProcess
)

def test_parse_lsof_output():
    """Test lsof output parsing."""
    output = """p12345
cnode /usr/local/bin/copilot-agent
n/dev/ttys001
n/dev/ttys002
p67890
cbash
n/dev/ttys003
"""
    processes = parse_lsof_output(output)
    
    assert len(processes) == 2
    assert processes[12345].command == "node /usr/local/bin/copilot-agent"
    assert processes[12345].pty_count == 2
    assert processes[67890].command == "bash"
    assert processes[67890].pty_count == 1

def test_is_leak_candidate_copilot():
    """Test leak detection for copilot processes."""
    proc = PTYProcess(
        pid=12345,
        command="node /usr/local/bin/copilot-agent",
        ptys=[f"/dev/ttys{i:03d}" for i in range(10)]
    )
    assert is_leak_candidate(proc, threshold=4)

def test_is_leak_candidate_normal():
    """Test leak detection for normal processes."""
    proc = PTYProcess(
        pid=12345,
        command="bash",
        ptys=["/dev/ttys001"]
    )
    assert not is_leak_candidate(proc, threshold=4)

def test_get_heavy_users():
    """Test heavy user detection."""
    processes = {
        1: PTYProcess(1, "bash", ["/dev/ttys001"]),
        2: PTYProcess(2, "node", [f"/dev/ttys{i:03d}" for i in range(10)]),
    }
    heavy = get_heavy_users(processes, threshold=4)
    assert len(heavy) == 1
    assert heavy[0].pid == 2
```

### Integration Tests

**File:** `tests/tools/watchdog/test_pty_integration.py`

```python
"""Integration tests for PTY commands."""

import subprocess
import json
import pytest

def test_show_command():
    """Test show command runs successfully."""
    result = subprocess.run(
        ["uv", "run", "honk", "watchdog", "pty", "show", "--json"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    
    envelope = json.loads(result.stdout)
    assert envelope["version"] == "1.0"
    assert envelope["command"] == ["honk", "watchdog", "pty", "show"]
    assert envelope["status"] == "ok"
    assert "total_ptys" in envelope["facts"]

def test_clean_plan_mode():
    """Test clean command in plan mode."""
    result = subprocess.run(
        ["uv", "run", "honk", "watchdog", "pty", "clean", "--plan", "--json"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
    
    envelope = json.loads(result.stdout)
    assert envelope["changed"] is False  # Plan mode makes no changes
    assert "killed" in envelope["facts"]
```

### Contract Tests

**File:** `tests/contract/test_watchdog_pty_contract.py`

```python
"""Contract tests for watchdog pty schema compliance."""

import subprocess
import json
import jsonschema

def test_show_envelope_schema():
    """Verify show command result envelope matches schema."""
    result = subprocess.run(
        ["uv", "run", "honk", "watchdog", "pty", "show", "--json"],
        capture_output=True,
        text=True
    )
    envelope = json.loads(result.stdout)
    
    # Validate against result.v1.json schema
    with open("schemas/result.v1.json") as f:
        schema = json.load(f)
    jsonschema.validate(envelope, schema)

def test_help_json_schema():
    """Verify help-json output matches schema."""
    result = subprocess.run(
        ["uv", "run", "honk", "help-json", "watchdog"],
        capture_output=True,
        text=True
    )
    help_data = json.loads(result.stdout)
    
    # Validate against help.v1.json schema
    with open("schemas/help.v1.json") as f:
        schema = json.load(f)
    jsonschema.validate(help_data, schema)
```

---

## Documentation Updates

### 1. Update `docs/spec.md`

Add section under "1.9 Adding a new tool":

```markdown
### Example: watchdog pty

The `honk watchdog pty` tool monitors PTY sessions and cleans up leaking processes. See `docs/references/watchdog-pty-spec.md` for full details.

Key patterns demonstrated:
- Scanner module (`pty_scanner.py`) separates detection logic from CLI
- Rich output helpers for tables and status lines
- Watch mode with signal handling (SIGINT for graceful exit)
- Threshold-based heuristics for safety
```

### 2. Update `docs/plans/main.md`

Add to "Active Tasks":

```markdown
- [ ] Implement `honk watchdog pty` tool per `docs/references/watchdog-pty-spec.md`
  - [ ] Create `src/honk/tools/watchdog/` structure
  - [ ] Implement `pty_scanner.py` (lsof parsing, leak detection)
  - [ ] Implement `pty.py` (CLI commands: show, clean, watch)
  - [ ] Add unit tests (`tests/tools/watchdog/`)
  - [ ] Add integration tests
  - [ ] Register area with plugin system
  - [ ] Update introspection registry
```

### 3. Create User Guide

**File:** `docs/references/watchdog-pty-guide.md`

```markdown
# Watchdog PTY - User Guide

## Quick Start

### Check current PTY usage
\`\`\`bash
honk watchdog pty show
\`\`\`

### Clean up leaking processes
\`\`\`bash
# Dry-run first
honk watchdog pty clean --plan

# Actually clean
honk watchdog pty clean
\`\`\`

### Monitor continuously
\`\`\`bash
honk watchdog pty watch --interval 10 --max-ptys 300
\`\`\`

## When to Use

- Terminal/shell becomes slow or unresponsive
- Error messages about "too many open files"
- Copilot/Node processes accumulating
- System PTY limit reached (kern.tty.ptmx_max on macOS)

## Safety Notes

- Only kills copilot-like processes by default
- Uses SIGTERM (graceful shutdown)
- Never touches system processes (PID < 100)
- Use `--plan` to preview before cleaning
- Adjust `--threshold` for custom sensitivity

## Troubleshooting

### "lsof not found"
Install via Homebrew: `brew install lsof`

### "Permission denied" when cleaning
Some processes require elevated privileges. Run with `sudo` if needed (use with caution).

### False positives
Increase `--threshold` or exclude specific patterns (future feature).
```

---

## Dependencies

**New:** None required beyond existing Honk deps.

**Used:**
- `subprocess` - Execute `lsof`
- `signal` - Send SIGTERM to processes
- `time` - Watch mode timing
- `typer` - CLI framework
- `rich` - Output formatting
- `pydantic` - Result envelope

---

## Security Considerations

### Process Killing Safety

1. **Never kill system processes:**
   - PID < 100
   - UID 0 (root-owned)
   - Parent of honk process itself

2. **Conservative defaults:**
   - High threshold (4 PTYs)
   - Copilot-specific patterns only
   - SIGTERM not SIGKILL

3. **Audit logging:**
   - Log all killed PIDs to `tmp/watchdog-pty.log`
   - Include timestamp, PID, command, reason

### Permission Handling

- Fail gracefully on permission errors
- Surface actionable error messages
- Never prompt for sudo automatically

### Race Conditions

- PTY enumeration is snapshot-in-time
- Process may exit between scan and kill
- Handle `ProcessLookupError` gracefully

---

## Performance Characteristics

### `show` Command
- **Time:** 100-300ms (depends on process count)
- **Memory:** <10MB
- **I/O:** Single `lsof` execution

### `clean` Command
- **Time:** 200-500ms (scan + kill + rescan)
- **Memory:** <10MB
- **I/O:** Two `lsof` executions + SIGTERM

### `watch` Command
- **Time:** Continuous (low CPU between scans)
- **Memory:** <15MB resident
- **I/O:** `lsof` every `--interval` seconds

---

## Future Enhancements

### Phase 2 (Optional)
1. **Custom leak patterns:** User-configurable process filters
2. **Exclusion lists:** Never kill specified PIDs/patterns
3. **Slack/webhooks:** Alert on threshold breaches
4. **Metrics export:** Prometheus/StatsD integration
5. **History tracking:** Persist scan results in SQLite

### Phase 3 (Advanced)
1. **ML-based detection:** Learn normal PTY patterns
2. **Process tree analysis:** Kill parent instead of children
3. **Resource correlation:** Cross-reference with memory/CPU usage
4. **Remediation suggestions:** "Your Copilot config may be misconfigured"

---

## Acceptance Criteria

### Functionality
- [ ] `honk watchdog pty show` displays PTY usage with rich formatting
- [ ] `honk watchdog pty show --json` emits valid result envelope
- [ ] `honk watchdog pty clean` kills copilot-like processes
- [ ] `honk watchdog pty clean --plan` shows preview without changes
- [ ] `honk watchdog pty watch` monitors continuously and auto-cleans
- [ ] All commands respect `--no-color` and `--json` flags

### Safety
- [ ] Never kills system processes (PID < 100, UID 0)
- [ ] Uses SIGTERM not SIGKILL
- [ ] Handles permission errors gracefully
- [ ] Respects `--threshold` parameter

### Testing
- [ ] Unit tests achieve >90% coverage
- [ ] Integration tests verify all commands run
- [ ] Contract tests validate result envelope schema
- [ ] Snapshot tests capture Rich output

### Documentation
- [ ] `honk watchdog pty --help` is descriptive and complete
- [ ] `honk help-json watchdog` emits valid schema
- [ ] User guide exists in `docs/references/`
- [ ] Spec document is complete (this file)

### CI/CD
- [ ] All tests pass in `ci-core` workflow
- [ ] macOS-specific tests pass in `ci-macos` workflow
- [ ] Help output validated in contract tests
- [ ] No regressions in existing commands

---

### 4. `honk watchdog pty daemon`

**Purpose:** Background service for continuous PTY monitoring with caching.

**Signature:**
```bash
honk watchdog pty daemon [--start|--stop|--status] [--scan-interval SECONDS] [--auto-kill-threshold NUM] [--json]
```

**Options:**
- `--start` (bool): Start daemon in background (detached process)
- `--stop` (bool): Stop running daemon gracefully
- `--status` (bool): Check if daemon is running
- `--scan-interval` (int, default: 30): Seconds between PTY scans
- `--auto-kill-threshold` (int, default: 0): Auto-kill processes above this PTY count (0=disabled)
- `--json` (bool): Output result envelope

**Behavior:**

**Start Mode (`--start`):**
1. Check if daemon already running (PID file exists)
2. Fork detached process using `subprocess.Popen` with `start_new_session=True`
3. Write PID to `tmp/pty-daemon.pid`
4. Daemon loop:
   - Scan PTYs every `--scan-interval` seconds
   - Write results to `tmp/pty-cache.json` atomically
   - If `--auto-kill-threshold` > 0, kill processes exceeding threshold
   - Log activity to `tmp/pty-daemon.log`
5. Handle SIGTERM for graceful shutdown

**Stop Mode (`--stop`):**
1. Read PID from `tmp/pty-daemon.pid`
2. Send SIGTERM to process
3. Wait up to 5s for clean exit
4. Remove PID file
5. Return success or error envelope

**Status Mode (`--status`):**
1. Check if PID file exists
2. Verify process is alive: `os.kill(pid, 0)`
3. Read cache timestamp from `tmp/pty-cache.json`
4. Return status envelope with facts

**Exit Codes:**
- `0` - Success
- `10` - Prerequisites failed
- `30` - System error (can't start/stop daemon)
- `50` - Internal error

**Result Envelope (start):**
```json
{
  "version": "1.0",
  "command": ["honk", "watchdog", "pty", "daemon", "--start"],
  "status": "ok",
  "changed": true,
  "code": "watchdog.pty.daemon.started",
  "summary": "PTY monitoring daemon started",
  "run_id": "uuid",
  "duration_ms": 50,
  "facts": {
    "pid": 12345,
    "scan_interval": 30,
    "auto_kill_threshold": 0,
    "cache_file": "tmp/pty-cache.json",
    "log_file": "tmp/pty-daemon.log"
  },
  "next": [
    {
      "run": ["honk", "watchdog", "pty", "daemon", "--status"],
      "summary": "Check daemon status"
    },
    {
      "run": ["honk", "watchdog", "pty", "observer"],
      "summary": "View live PTY data"
    }
  ]
}
```

**Cache File Format (`tmp/pty-cache.json`):**
```json
{
  "timestamp": "2025-11-19T08:00:00Z",
  "scan_number": 42,
  "total_ptys": 247,
  "process_count": 18,
  "processes": [
    {
      "pid": 12345,
      "command": "node copilot-agent",
      "pty_count": 87,
      "ptys": ["/dev/ttys001", "..."],
      "first_seen": "2025-11-19T07:30:00Z",
      "last_seen": "2025-11-19T08:00:00Z"
    }
  ],
  "heavy_users": [...],
  "suspected_leaks": [...]
}
```

**Implementation Notes:**
- Use Python's `daemon` library or manual fork/detach
- Atomic writes to cache (write to temp, then rename)
- Graceful signal handling (SIGTERM → cleanup → exit)
- PID file locking to prevent multiple daemons
- Log rotation for daemon log file

---

### 5. `honk watchdog pty observer`

**Purpose:** TUI dashboard displaying cached PTY data from daemon.

**Signature:**
```bash
honk watchdog pty observer [--live] [--history MINUTES]
```

**Options:**
- `--live` (bool, default: true): Auto-refresh display every 5s
- `--history` (int, default: 60): Show data from last N minutes
- No `--json` (this is interactive TUI only)

**Behavior:**
1. Check if daemon is running (warn if not)
2. Read `tmp/pty-cache.json` for current data
3. Launch Textual TUI application
4. Display dashboard with:
   - **Header:** Timestamp, scan interval, daemon status
   - **Summary Cards:** Total PTYs, process count, heavy users count
   - **Line Chart:** PTY usage over time (if history data exists)
   - **Process Table:** PID, command, PTY count, actions
   - **Footer:** Keyboard shortcuts
5. Auto-refresh every 5s if `--live`
6. Handle keyboard commands:
   - `q` - Quit
   - `k` - Kill selected process
   - `r` - Refresh now
   - `↑/↓` - Navigate process list
   - `Enter` - View process details

**Exit Codes:**
- `0` - Normal exit (user quit)
- `10` - Prerequisites failed (Textual not installed)
- `30` - System error (can't read cache)

**TUI Layout (Textual):**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ PTY Monitor Dashboard                    Last scan: 2s ago     ┃
┃ Daemon: ● Running (PID 12345)           Scan interval: 30s     ┃
┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │ Total PTYs   │  │ Processes    │  │ Heavy Users  │        │
│  │    247       │  │      18      │  │       3      │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
│                                                                 │
│  PTY Usage (Last Hour)                                         │
│  ┌───────────────────────────────────────────────────────┐    │
│  │ 300├╮                                                  │    │
│  │    │ ╰╮                                                │    │
│  │ 200│  ╰─╮                                              │    │
│  │    │    ╰──╮                                           │    │
│  │ 100│       ╰────────                                   │    │
│  │   0└───────────────────────────────────────────────── │    │
│  └───────────────────────────────────────────────────────┘    │
│                                                                 │
│  Active Processes                                              │
│  ┌──────┬──────────────────────────┬──────────┬─────────┐    │
│  │ PID  │ Command                  │ PTY Count│ Actions │    │
│  ├──────┼──────────────────────────┼──────────┼─────────┤    │
│  │12345 │ node copilot-agent       │    87    │ [Kill]  │ ◄─ │
│  │12346 │ python honk.py           │    42    │ [Kill]  │    │
│  │12347 │ zsh                      │     5    │ [Kill]  │    │
│  └──────┴──────────────────────────┴──────────┴─────────┘    │
│                                                                 │
│  [q] Quit  [k] Kill  [r] Refresh  [↑↓] Navigate               │
└─────────────────────────────────────────────────────────────────┘
```

**Implementation Notes:**
- Use Textual library (already in dependencies: 0.61.0)
- Reactive components that update on timer
- Confirm before killing processes (modal dialog)
- Show kill results inline
- Graceful fallback if cache file missing/corrupt
- Warn if cache is stale (>2x scan_interval)

---

### 6. Process Ranking Algorithm

**Purpose:** Define criteria for ranking processes when auto-killing.

**Ranking Score Formula:**
```python
score = (
    pty_count * 10.0 +              # Primary: PTY count
    process_age_hours * 2.0 +       # Secondary: Age (newer = higher score)
    is_copilot_like * 50.0 +        # Boost: Known leak patterns
    is_orphaned * 30.0 +            # Boost: No parent process
    cpu_percent * 0.1 +             # Minor: CPU usage (idle first)
    memory_mb * 0.001               # Minor: Memory usage
)
```

**Ranking Criteria (in priority order):**

1. **PTY Count** (weight: 10.0)
   - Most important factor
   - Process using 50 PTYs scores higher than 5 PTYs

2. **Process Age** (weight: 2.0)
   - Newer processes are more likely to be leaks
   - Calculated from process start time

3. **Copilot/Node Pattern** (weight: 50.0)
   - Command contains "copilot", "node", or "agent"
   - Heuristic for known leak sources

4. **Orphaned Status** (weight: 30.0)
   - Parent process no longer exists (PPID = 1)
   - Likely zombie/leak

5. **CPU Usage** (weight: 0.1)
   - Idle processes (0% CPU) rank higher
   - Active processes left alone

6. **Memory Usage** (weight: 0.001)
   - Minor tie-breaker
   - Higher memory = slightly higher score

**Safety Rules:**
- Never kill processes owned by other users
- Never kill processes with PID < 1000 (system processes)
- Never kill self (current Python process)
- Require explicit threshold (no auto-kill by default)
- Confirmation required in interactive mode
- Log all kills with justification

**Example Ranking:**
```python
Process A: node copilot-agent
  - PTY count: 87 (870 pts)
  - Age: 2 hours (4 pts)
  - Copilot-like: yes (50 pts)
  - Orphaned: no (0 pts)
  - CPU: 0.1% (0.01 pts)
  - Memory: 200MB (0.2 pts)
  Total: 924.21 pts → RANK 1 (kill first)

Process B: zsh
  - PTY count: 5 (50 pts)
  - Age: 10 hours (20 pts)
  - Copilot-like: no (0 pts)
  - Orphaned: no (0 pts)
  - CPU: 2% (0.2 pts)
  - Memory: 50MB (0.05 pts)
  Total: 70.25 pts → RANK 2 (kill after A if needed)
```

---

## Implementation Checklist

### 1. Setup (5 min)
- [ ] Create `src/honk/tools/watchdog/` directory
- [ ] Create `__init__.py`, `pty.py`, `pty_scanner.py`
- [ ] Create `tests/tools/watchdog/` directory

### 2. Core Scanner (30 min)
- [ ] Implement `run_lsof()` function
- [ ] Implement `parse_lsof_output()` function
- [ ] Implement `PTYProcess` dataclass
- [ ] Implement `is_leak_candidate()` heuristics
- [ ] Implement `kill_processes()` function
- [ ] Add unit tests for scanner

### 3. Show Command (20 min)
- [ ] Implement `show()` command
- [ ] Add Rich formatting for human output
- [ ] Build result envelope
- [ ] Add statistics calculation
- [ ] Register with introspection system
- [ ] Add integration tests

### 4. Clean Command (25 min)
- [ ] Implement `clean()` command
- [ ] Add `--plan` dry-run logic
- [ ] Implement before/after comparison
- [ ] Add Rich formatting for results
- [ ] Build result envelope with killed list
- [ ] Add integration tests

### 5. Watch Command (20 min)
- [ ] Implement `watch()` command
- [ ] Add signal handling (SIGINT/SIGTERM)
- [ ] Implement scan loop with timing
- [ ] Add JSON event streaming
- [ ] Add Rich status line output
- [ ] Add integration tests

### 6. Integration (15 min)
- [ ] Register area in plugin system
- [ ] Update `cli.py` to load watchdog area
- [ ] Add command metadata to registry
- [ ] Verify `honk introspect --json` includes watchdog

### 7. Testing (30 min)
- [ ] Write unit tests for all scanner functions
- [ ] Write integration tests for all commands
- [ ] Write contract tests for schema validation
- [ ] Verify test coverage >90%
- [ ] Run full test suite locally

### 8. Documentation (20 min)
- [ ] Complete this spec document
- [ ] Write user guide (`watchdog-pty-guide.md`)
- [ ] Update `docs/spec.md`
- [ ] Update `docs/plans/main.md`
- [ ] Add docstrings to all functions

### 9. CI Integration (10 min)
- [ ] Verify tests pass in `ci-core`
- [ ] Verify tests pass in `ci-macos`
- [ ] Add to GitHub Actions if needed
- [ ] Verify help validation passes

### 10. Polish (15 min)
- [ ] Run `uv run ruff check` and fix issues
- [ ] Run `uv run mypy` and fix type errors
- [ ] Test all commands manually
- [ ] Verify help text is complete
- [ ] Verify JSON output is valid

**Total Estimated Time:** ~3 hours

---

## Rollout Plan

### Phase 1: Internal Testing (Week 1)
- Implement core functionality
- Run locally on development machines
- Gather feedback from team

### Phase 2: Beta Release (Week 2)
- Merge to main branch
- Tag as `v0.2.0-beta`
- Document in release notes
- Monitor for issues

### Phase 3: General Availability (Week 3)
- Address beta feedback
- Tag as `v0.2.0`
- Update README with watchdog examples
- Announce in project channels

---

## Changelog Entries

### Added
- **watchdog area:** System health monitoring tools
- **honk watchdog pty show:** Display PTY usage and detect leaks
- **honk watchdog pty clean:** Kill leaking processes
- **honk watchdog pty watch:** Monitor and auto-clean continuously
- **pty_scanner module:** lsof parsing and leak detection

### Changed
- None (new functionality)

### Deprecated
- None

### Removed
- None

### Fixed
- None (initial implementation)

### Security
- Process killing limited to copilot-like patterns
- Uses SIGTERM for graceful shutdown
- Never touches system processes (PID < 100)

---

## References

- [Honk Spec](../spec.md) - Main project specification
- [Main Work Tracking](../plans/main.md) - Task tracking
- [Result Envelope Schema](../../schemas/result.v1.json) - JSON schema
- macOS PTY limits: `sysctl kern.tty.ptmx_max`
- lsof documentation: `man lsof`

---

**Spec Status:** ✅ Complete and ready for implementation

**Approver:** [Name]  
**Approved Date:** [Date]
