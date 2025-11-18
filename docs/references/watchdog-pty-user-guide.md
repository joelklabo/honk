# Honk Watchdog PTY User Guide

## Overview

The `honk watchdog pty` tool monitors and manages pseudo-terminal (PTY) device usage on your system. It helps identify and clean up orphaned PTY sessions, particularly those caused by long-running Node.js processes and development tools.

## Why PTY Monitoring Matters

PTY devices are limited system resources. When processes don't properly clean up their PTY sessions, you can experience:

- Terminal applications failing to start
- SSH connections being refused
- IDE/editor terminals not working
- System instability

Common culprits:
- GitHub Copilot agent processes
- Node.js development servers
- Language server processes (LSP)
- Container runtimes
- Tmux/screen sessions gone wrong

## Quick Start

```bash
# Show current PTY usage
honk watchdog pty show

# Show leaking processes
honk watchdog pty show --no-color

# Preview what would be cleaned
honk watchdog pty clean --plan

# Clean up PTY leaks
honk watchdog pty clean

# Continuous monitoring
honk watchdog pty watch --interval 10
```

## Commands

### show - Display PTY Usage

View current PTY device usage and identify heavy users:

```bash
honk watchdog pty show
```

Example output:
```
PTY Usage

Total PTYs in use: 186
Processes holding PTYs: 1162

Heavy PTY users (>4 PTYs):
  • PID 12919 (Code - Insiders Helper (Plugin)) — 5 PTYs
  • PID 12931 (node) — 7 PTYs
  • PID 14131 (node) — 9 PTYs

Suspected Copilot/Node leaks:
  • PID 14131 (node) — 9 PTYs
```

**JSON output:**
```bash
honk watchdog pty show --json
```

```json
{
  "version": "1.0",
  "command": ["honk", "watchdog", "pty", "show"],
  "status": "ok",
  "facts": {
    "total_ptys": 186,
    "process_count": 1162,
    "heavy_users": [
      {
        "pid": 14131,
        "command": "node /usr/local/bin/copilot-agent",
        "pty_count": 9,
        "ptys": ["/dev/ttys001", "/dev/ttys002", "..."]
      }
    ],
    "suspected_leaks": [
      {
        "pid": 14131,
        "command": "node /usr/local/bin/copilot-agent",
        "pty_count": 9,
        "reason": "copilot-like process with >4 PTYs"
      }
    ]
  }
}
```

### clean - Kill Leaking Processes

Remove processes with orphaned PTY sessions:

```bash
# Preview mode (safe, no changes)
honk watchdog pty clean --plan

# Actually clean up leaks
honk watchdog pty clean

# Set custom threshold (default is 4 PTYs)
honk watchdog pty clean --threshold 6
```

**Plan mode output:**
```
Would kill:
  • PID 14131 (node /usr/local/bin/copilot-agent) — 9 PTYs
```

**Actual cleanup:**
```
Killed 1 process(es)

Before cleanup:
  Total PTYs: 186
  Processes: 1162

After cleanup:
  Total PTYs: 177 (freed 9 PTYs)
  Processes: 1161
```

**Safety features:**
- Only targets suspected leaks (Copilot agents, heavy Node.js processes)
- Never kills system processes or shells
- Requires >4 PTYs by default (configurable)
- Plan mode lets you preview before acting

### watch - Continuous Monitoring

Monitor PTY usage continuously and auto-clean when thresholds are exceeded:

```bash
# Watch with 5-second intervals (default)
honk watchdog pty watch

# Custom interval
honk watchdog pty watch --interval 10

# Custom threshold for auto-cleanup
honk watchdog pty watch --max-ptys 250

# JSON event stream
honk watchdog pty watch --json
```

Example output:
```
Watching PTY usage every 5s... (Ctrl+C to stop)

[16:30:15] PTYs=186  procs=1162
[16:30:20] PTYs=189  procs=1165
[16:30:25] PTYs=203  procs=1180  !! HIGH — cleaning…
  → Killed 2 processes (15 PTYs freed)
[16:30:30] PTYs=188  procs=1178
```

Press Ctrl+C to stop monitoring.

## Understanding PTY Leaks

### What is a PTY?

A PTY (pseudo-terminal) is a virtual terminal device that applications use to simulate a terminal connection. Each terminal window, SSH session, or terminal-based application typically uses one or more PTYs.

### Leak Detection Heuristics

The tool identifies suspected leaks using these rules:

1. **Copilot agents:** Any process with "copilot" in the name holding >4 PTYs
2. **Heavy Node.js:** Node processes with >8 PTYs
3. **Other processes:** Any process with >10 PTYs

These thresholds are conservative to avoid false positives.

### Common Leak Scenarios

**GitHub Copilot Agent:**
```
PID 14131 (node /usr/local/bin/copilot-agent) — 15 PTYs
```
Copilot agents sometimes don't clean up PTYs when VS Code restarts or crashes.

**Development Servers:**
```
PID 23456 (node /app/server.js) — 12 PTYs
```
Hot-reload servers can accumulate PTYs during rapid restart cycles.

**Language Servers:**
```
PID 34567 (typescript-language-server) — 8 PTYs
```
LSP processes can leak PTYs when editors don't shut down cleanly.

## Best Practices

### Regular Monitoring

Check PTY usage periodically:

```bash
# Add to your shell profile
alias pty='honk watchdog pty show'

# Or run daily
echo "0 9 * * * honk watchdog pty clean --plan >> ~/pty-cleanup.log" | crontab -
```

### Automated Cleanup

For development machines with frequent Copilot/Node usage:

```bash
# Run cleanup on login
# Add to ~/.zshrc or ~/.bashrc
honk watchdog pty clean --plan >/dev/null 2>&1
if [ $? -eq 0 ]; then
  honk watchdog pty clean --threshold 6
fi
```

### CI/CD Integration

Clean up PTYs in CI environments:

```yaml
# GitHub Actions
- name: Clean PTY Leaks
  run: honk watchdog pty clean --threshold 8

# Azure Pipelines
- script: honk watchdog pty clean --threshold 8
  displayName: 'Clean PTY Leaks'
```

### Integration with Monitoring

Export metrics for monitoring systems:

```bash
# Prometheus exporter format
honk watchdog pty show --json | jq -r '
  "pty_total \(.facts.total_ptys)",
  "pty_processes \(.facts.process_count)",
  "pty_suspected_leaks \(.facts.suspected_leaks | length)"
'
```

## Troubleshooting

### "lsof not found"

**Problem:** System missing `lsof` command.

**Solution:**
```bash
# macOS (should be preinstalled)
xcode-select --install

# Linux
sudo apt-get install lsof  # Debian/Ubuntu
sudo yum install lsof       # RHEL/CentOS
```

### Permission Denied

**Problem:** Can't kill processes owned by other users.

**Solution:**
- Only your own processes can be killed
- System processes are automatically excluded
- Run as appropriate user for development tools

### False Positives

**Problem:** Tool wants to kill legitimate processes.

**Solution:**
```bash
# Increase threshold
honk watchdog pty clean --threshold 10

# Use plan mode first
honk watchdog pty clean --plan
```

### No Leaks Detected

**Problem:** PTY exhaustion but no leaks found.

**Solution:**
```bash
# Check all heavy users
honk watchdog pty show

# Lower threshold
honk watchdog pty clean --threshold 3

# Check system limits
ulimit -n  # Max file descriptors
```

## Advanced Usage

### Custom Thresholds

Adjust leak detection sensitivity:

```bash
# Conservative (fewer false positives)
honk watchdog pty clean --threshold 8

# Aggressive (catch more leaks)
honk watchdog pty clean --threshold 3
```

### Scripted Automation

```bash
#!/bin/bash
# cleanup-ptys.sh

# Get current PTY count
CURRENT=$(honk watchdog pty show --json | jq '.facts.total_ptys')

# Threshold for action
THRESHOLD=200

if [ "$CURRENT" -gt "$THRESHOLD" ]; then
  echo "PTY count ($CURRENT) exceeds threshold ($THRESHOLD)"
  
  # Show what would be cleaned
  honk watchdog pty clean --plan
  
  # Confirm and clean
  read -p "Proceed with cleanup? (y/N) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    honk watchdog pty clean
  fi
fi
```

### JSON Event Processing

Process watch events in real-time:

```bash
# Stream events
honk watchdog pty watch --json | while read -r line; do
  EVENT=$(echo "$line" | jq -r '.event')
  PTYS=$(echo "$line" | jq -r '.total_ptys')
  
  if [ "$PTYS" -gt 200 ]; then
    echo "Alert: PTY count is $PTYS"
    # Send notification, alert, etc.
  fi
done
```

### Integration with System Monitoring

```bash
# Export to monitoring system
export_metrics() {
  DATA=$(honk watchdog pty show --json)
  
  # Push to Prometheus pushgateway
  echo "$DATA" | jq -r '
    "pty_total_count \(.facts.total_ptys)",
    "pty_process_count \(.facts.process_count)",
    "pty_heavy_users_count \(.facts.heavy_users | length)"
  ' | curl --data-binary @- http://pushgateway:9091/metrics/job/honk_watchdog
}

# Run periodically
while true; do
  export_metrics
  sleep 60
done
```

## System Limits

### Check Current Limits

```bash
# macOS/Linux: Max file descriptors (includes PTYs)
ulimit -n

# macOS: Max PTY devices
sysctl -a | grep pty

# Linux: PTY limits
cat /proc/sys/kernel/pty/max
cat /proc/sys/kernel/pty/nr  # Current usage
```

### Increase Limits

**macOS:**
```bash
# Temporary (current session)
ulimit -n 4096

# Permanent
sudo launchctl limit maxfiles 65536 200000
```

**Linux:**
```bash
# Edit /etc/security/limits.conf
* soft nofile 65536
* hard nofile 65536

# For systemd services
LimitNOFILE=65536
```

## Safety Considerations

### What Gets Killed

The tool **will** kill:
- Node.js processes with "copilot" in the name and >4 PTYs
- Node.js processes with >8 PTYs
- Other processes with >10 PTYs

The tool **won't** kill:
- Your shell (bash, zsh, fish, etc.)
- System processes (owned by root)
- Processes with normal PTY usage
- Any process in plan mode

### Data Loss Risk

**Low risk:** Most affected processes are agents/servers that can restart
**Medium risk:** Development servers may need manual restart
**High risk:** (Rare) Active editor sessions if threshold is too low

**Recommendation:** Always run `--plan` first to preview.

### Recovery

If you accidentally kill the wrong process:

```bash
# Restart VS Code (which restarts Copilot)
# Restart your development server
# Re-open terminals as needed
```

Most development tools are designed to recover from crashes.

## Performance Impact

### Resource Usage

The tool is lightweight:
- `show`: ~10ms to scan system
- `clean`: ~50ms including process termination
- `watch`: Minimal CPU, negligible memory

### System Load

- Uses `lsof` which is efficient even with many processes
- No kernel hooks or tracing
- Safe to run continuously

## Examples

### Daily Cleanup Script

```bash
#!/bin/bash
# ~/.local/bin/daily-pty-cleanup

LOG_FILE="$HOME/.honk/pty-cleanup.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "[$(date)] Starting PTY cleanup" >> "$LOG_FILE"

# Show current state
honk watchdog pty show --json | jq '.facts.total_ptys' >> "$LOG_FILE"

# Clean up
honk watchdog pty clean --threshold 6 >> "$LOG_FILE" 2>&1

echo "[$(date)] Cleanup complete" >> "$LOG_FILE"
```

### VS Code Task

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Clean PTY Leaks",
      "type": "shell",
      "command": "honk watchdog pty clean --plan && honk watchdog pty clean",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

### Alfred/Raycast Workflow

```bash
# Alfred script
honk watchdog pty show --json | jq -r '
  "Total PTYs: \(.facts.total_ptys)\n" +
  "Processes: \(.facts.process_count)\n" +
  "Suspected leaks: \(.facts.suspected_leaks | length)"
'
```

## Related Documentation

- [Watchdog PTY Spec](./watchdog-pty-spec.md) - Technical implementation details
- [Doctor Packs](../spec.md#prereq-engine) - Prerequisite checking system

## Support

For issues:
1. Check `honk watchdog pty --help`
2. Run with `--json` for detailed output
3. Verify `lsof` is installed
4. Check system PTY limits

## API Reference

### Exit Codes

- `0` - Success
- `10` - Prerequisites failed (lsof not found)
- `50` - Internal error

### Thresholds

- **Default:** 4 PTYs triggers leak detection
- **Copilot:** Any count >4 is suspicious
- **Node.js:** Counts >8 are flagged
- **Other:** Counts >10 are flagged

Adjust with `--threshold` flag.
