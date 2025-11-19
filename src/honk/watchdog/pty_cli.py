"PTY watchdog commands."

import sys
import time
import signal
import json
import subprocess
import os
import typer

from ..result import EXIT_OK, EXIT_PREREQ_FAILED, EXIT_SYSTEM
from ..ui import console, print_success, print_error, print_info
from .pty_scanner import scan_ptys, kill_processes, get_heavy_users, get_suspected_leaks
from ..log import log_event, LOG_FILE_PATH

pty_app = typer.Typer(help="PTY session monitoring and cleanup")


def build_result_envelope(command: list, status: str, changed: bool, code: str, summary: str, facts: dict) -> dict:
    """Build a result envelope."""
    return {
        "version": "1.0",
        "command": command,
        "status": status,
        "changed": changed,
        "code": code,
        "summary": summary,
        "facts": facts,
    }


@pty_app.command("show")
def show(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Display current PTY usage and detect potential leaks."""
    try:
        processes = scan_ptys()
        total_ptys = sum(p.pty_count for p in processes.values())
        heavy_users = get_heavy_users(processes, threshold=4)
        suspected_leaks = get_suspected_leaks(processes, threshold=4)
        
        facts = {
            "total_ptys": total_ptys,
            "process_count": len(processes),
            "heavy_users": [
                {
                    "pid": p.pid,
                    "command": p.command,
                    "pty_count": p.pty_count,
                    "ptys": p.ptys[:5] + (["..."] if p.pty_count > 5 else [])
                }
                for p in heavy_users
            ],
            "suspected_leaks": [
                {
                    "pid": p.pid,
                    "command": p.command,
                    "pty_count": p.pty_count,
                    "reason": "copilot-like process with >4 PTYs"
                }
                for p in suspected_leaks
            ],
        }
        
        if json_output:
            envelope = build_result_envelope(
                command=["honk", "watchdog", "pty", "show"],
                status="ok",
                changed=False,
                code="watchdog.pty.show.ok",
                summary=f"Found {total_ptys} PTYs across {len(processes)} processes",
                facts=facts
            )
            print(json.dumps(envelope, indent=2))
        else:
            console.print("\n[bold cyan]PTY Usage[/bold cyan]\n")
            console.print(f"Total PTYs in use: [bold]{total_ptys}[/bold]")
            console.print(f"Processes holding PTYs: [bold]{len(processes)}[/bold]\n")
            
            if heavy_users:
                console.print("[bold yellow]Heavy PTY users (>4 PTYs):[/bold yellow]")
                for p in heavy_users:
                    console.print(f"  • PID {p.pid} ({p.command}) — {p.pty_count} PTYs")
                console.print()
            
            if suspected_leaks:
                console.print("[bold red]Suspected Copilot/Node leaks:[/bold red]")
                for p in suspected_leaks:
                    console.print(f"  • PID {p.pid} ({p.command}) — {p.pty_count} PTYs")
                console.print()
        
        sys.exit(EXIT_OK)
        
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(EXIT_PREREQ_FAILED)
    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)


@pty_app.command("clean")
def clean(
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
    plan: bool = typer.Option(False, "--plan", help="Dry-run mode (show what would be killed)"),
    interactive: bool = typer.Option(False, "--interactive", help="Prompt for confirmation before killing each process."),
    threshold: int = typer.Option(4, "--threshold", help="Minimum PTYs to trigger cleanup"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Kill processes with orphaned PTY sessions."""
    try:
        processes_before = scan_ptys()
        total_ptys_before = sum(p.pty_count for p in processes_before.values())
        suspected_leaks = get_suspected_leaks(processes_before, threshold=threshold)
        
        if not suspected_leaks:
            if json_output:
                envelope = build_result_envelope(
                    command=["honk", "watchdog", "pty", "clean"],
                    status="ok",
                    changed=False,
                    code="watchdog.pty.clean.none",
                    summary="No leaking processes found",
                    facts={"before": {"total_ptys": total_ptys_before, "process_count": len(processes_before)}, "killed": [], "freed_ptys": 0}
                )
                print(json.dumps(envelope, indent=2))
            else:
                print_info("No leaking processes found")
            sys.exit(EXIT_OK)
        
        if plan:
            if json_output:
                envelope = build_result_envelope(
                    command=["honk", "watchdog", "pty", "clean", "--plan"],
                    status="ok",
                    changed=False,
                    code="watchdog.pty.clean.plan",
                    summary=f"Would kill {len(suspected_leaks)} processes",
                    facts={"would_kill": [{"pid": p.pid, "command": p.command, "pty_count": p.pty_count} for p in suspected_leaks]}
                )
                print(json.dumps(envelope, indent=2))
            else:
                console.print("\n[bold yellow]Would kill:[/bold yellow]")
                for p in suspected_leaks:
                    console.print(f"  • PID {p.pid} ({p.command}) — {p.pty_count} PTYs")
                console.print()
            sys.exit(EXIT_OK)
        
        if interactive:
            pids_to_kill = []
            if not json_output:
                console.print()
            for p in suspected_leaks:
                if typer.confirm(f"Kill PID {p.pid} ({p.command}) — {p.pty_count} PTYs?"):
                    pids_to_kill.append(p.pid)
        else:
            pids_to_kill = [p.pid for p in suspected_leaks]

        if not pids_to_kill:
            print_info("No processes selected for cleanup.")
            sys.exit(EXIT_OK)

        kill_results = kill_processes(pids_to_kill)
        
        time.sleep(0.5)
        processes_after = scan_ptys()
        total_ptys_after = sum(p.pty_count for p in processes_after.values())
        freed_ptys = total_ptys_before - total_ptys_after
        
        killed_list = [{"pid": p.pid, "command": p.command, "pty_count": p.pty_count, "success": kill_results.get(p.pid, False)} for p in suspected_leaks if p.pid in pids_to_kill]
        
        if json_output:
            envelope = build_result_envelope(
                command=["honk", "watchdog", "pty", "clean"],
                status="ok",
                changed=True,
                code="watchdog.pty.clean.ok",
                summary=f"Killed {len(killed_list)} leaking processes, freed {freed_ptys} PTYs",
                facts={"before": {"total_ptys": total_ptys_before, "process_count": len(processes_before)}, "after": {"total_ptys": total_ptys_after, "process_count": len(processes_after)}, "killed": killed_list, "freed_ptys": freed_ptys}
            )
            print(json.dumps(envelope, indent=2))
        else:
            console.print("\n[bold green]Cleaning PTY leaks[/bold green]\n")
            for item in killed_list:
                status = "✓" if item["success"] else "✗"
                console.print(f"  {status} Killed PID {item['pid']} ({item['command']}) — {item['pty_count']} PTYs")
            console.print()
            print_success(f"Freed {freed_ptys} PTYs")
        
        sys.exit(EXIT_OK)
        
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(EXIT_PREREQ_FAILED)
    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)


def send_notification(title, message):
    """Send a system notification on macOS."""
    try:
        subprocess.run(['osascript', '-e', f'display notification "{message}" with title "{title}"'])
    except FileNotFoundError:
        pass


@pty_app.command("watch")
def watch(
    interval: int = typer.Option(5, "--interval", help="Check interval in seconds"),
    max_ptys: int = typer.Option(200, "--max-ptys", help="Auto-clean threshold"),
    json_output: bool = typer.Option(False, "--json", help="Stream JSON events"),
    notify: bool = typer.Option(False, "--notify", help="Send a system notification on cleanup."),
):
    """Monitor PTY usage and auto-clean when thresholds are exceeded."""
    try:
        def signal_handler(sig, frame):
            if not json_output:
                console.print("\n[bold]Stopping watch...[/bold]")
            sys.exit(EXIT_OK)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if not json_output:
            console.print(f"\n[bold cyan]Watching PTY usage every {interval}s...[/bold cyan] [dim](Ctrl+C to stop)[/dim]\n")
        
        while True:
            processes = scan_ptys()
            total_ptys = sum(p.pty_count for p in processes.values())
            
            if json_output:
                event = {"event": "scan", "total_ptys": total_ptys, "process_count": len(processes)}
                console.print(json.dumps(event))
            else:
                timestamp = time.strftime("%H:%M:%S")
                status_line = f"[{timestamp}] PTYs={total_ptys}  procs={len(processes)}"
                
                if total_ptys > max_ptys:
                    console.print(f"{status_line}  [bold red]!! HIGH — cleaning…[/bold red]")
                    
                    suspected_leaks = get_suspected_leaks(processes, threshold=4)
                    if suspected_leaks:
                        pids_to_kill = [p.pid for p in suspected_leaks]
                        kill_processes(pids_to_kill)
                        
                        time.sleep(0.5)
                        processes_after = scan_ptys()
                        freed = total_ptys - sum(p.pty_count for p in processes_after.values())
                        
                        console.print(f"  [green]→ Killed {len(suspected_leaks)} processes ({freed} PTYs freed)[/green]")

                        if notify:
                            send_notification("Honk PTY Watchdog", f"Killed {len(suspected_leaks)} processes, freed {freed} PTYs")

                        log_event("pty_cleanup", {
                            "killed_count": len(suspected_leaks),
                            "freed_ptys": freed,
                            "killed_pids": pids_to_kill
                        })
                else:
                    console.print(status_line)
            
            time.sleep(interval)
        
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(EXIT_PREREQ_FAILED)
    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)


@pty_app.command("history")
def history(
    limit: int = typer.Option(20, "--limit", help="Number of entries to show."),
):
    """Show a history of cleanup events from the log file."""
    if not os.path.exists(LOG_FILE_PATH):
        print_info(f"Log file not found: {LOG_FILE_PATH}")
        sys.exit(EXIT_OK)
        
    try:
        with open(LOG_FILE_PATH, "r") as f:
            lines = f.readlines()
            
        from typing import Any
        entries: list[dict[str, Any]] = []
        for line in reversed(lines):
            if len(entries) >= limit:
                break
            try:
                log_entry = json.loads(line)
                data_str = log_entry.get("data")
                if data_str:
                    data = json.loads(data_str)
                    if data.get("event_type") == "pty_cleanup":
                        data['timestamp'] = log_entry.get("timestamp")
                        entries.append(data)
            except (json.JSONDecodeError, KeyError):
                pass
        
        if not entries:
            print_info("No PTY cleanup history found in log file.")
            sys.exit(EXIT_OK)
            
        console.print("\n[bold cyan]PTY Cleanup History[/bold cyan]\n")
        for entry in entries:
            timestamp = entry.get("timestamp")
            killed_count = entry.get("killed_count", 0)
            freed_ptys = entry.get("freed_ptys", 0)
            console.print(f"[{timestamp}] Killed {killed_count} processes, freed {freed_ptys} PTYs")

        sys.exit(EXIT_OK)

    except Exception as e:
        print_error(f"Failed to read or parse log file: {e}")
        sys.exit(EXIT_SYSTEM)


@pty_app.command("daemon")
def daemon(
    start: bool = typer.Option(False, "--start", help="Start daemon in background"),
    stop: bool = typer.Option(False, "--stop", help="Stop running daemon"),
    status: bool = typer.Option(False, "--status", help="Check daemon status"),
    scan_interval: int = typer.Option(30, "--scan-interval", help="Seconds between scans"),
    auto_kill_threshold: int = typer.Option(0, "--auto-kill-threshold", help="Auto-kill processes above this PTY count (0=disabled)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Background PTY monitoring service with caching."""
    from .pty_daemon import PTYDaemon, DaemonConfig
    from pathlib import Path
    
    config = DaemonConfig(
        scan_interval=scan_interval,
        auto_kill_threshold=auto_kill_threshold
    )
    
    daemon_obj = PTYDaemon(config)
    
    # Determine action
    if not any([start, stop, status]):
        status = True  # Default to status if no action specified
    
    try:
        if start:
            result = daemon_obj.start()
            if result["success"]:
                facts = {
                    "pid": result["pid"],
                    "scan_interval": result["scan_interval"],
                    "auto_kill_threshold": result["auto_kill_threshold"],
                    "cache_file": result["cache_file"],
                    "log_file": result["log_file"]
                }
                
                if json_output:
                    envelope = build_result_envelope(
                        command=["honk", "watchdog", "pty", "daemon", "--start"],
                        status="ok",
                        changed=True,
                        code="watchdog.pty.daemon.started",
                        summary=f"PTY daemon started (PID {result['pid']})",
                        facts=facts
                    )
                    print(json.dumps(envelope, indent=2))
                else:
                    print_success(f"PTY daemon started (PID {result['pid']})")
                    console.print(f"Scan interval: [bold]{scan_interval}s[/bold]")
                    console.print(f"Cache file: [dim]{result['cache_file']}[/dim]")
                    console.print(f"Log file: [dim]{result['log_file']}[/dim]")
                    console.print("\nView live data: [bold]honk watchdog pty observer[/bold]")
                sys.exit(EXIT_OK)
            else:
                if json_output:
                    envelope = build_result_envelope(
                        command=["honk", "watchdog", "pty", "daemon", "--start"],
                        status="error",
                        changed=False,
                        code="watchdog.pty.daemon.start_failed",
                        summary=result["error"],
                        facts={}
                    )
                    print(json.dumps(envelope, indent=2))
                else:
                    print_error(result["error"])
                sys.exit(EXIT_SYSTEM)
        
        elif stop:
            result = daemon_obj.stop()
            if result["success"]:
                if json_output:
                    envelope = build_result_envelope(
                        command=["honk", "watchdog", "pty", "daemon", "--stop"],
                        status="ok",
                        changed=True,
                        code="watchdog.pty.daemon.stopped",
                        summary=f"PTY daemon stopped (PID {result['pid']})",
                        facts={"pid": result["pid"]}
                    )
                    print(json.dumps(envelope, indent=2))
                else:
                    print_success(f"PTY daemon stopped (PID {result['pid']})")
                sys.exit(EXIT_OK)
            else:
                if json_output:
                    envelope = build_result_envelope(
                        command=["honk", "watchdog", "pty", "daemon", "--stop"],
                        status="error",
                        changed=False,
                        code="watchdog.pty.daemon.stop_failed",
                        summary=result["error"],
                        facts={}
                    )
                    print(json.dumps(envelope, indent=2))
                else:
                    print_error(result["error"])
                sys.exit(EXIT_SYSTEM)
        
        elif status:
            result = daemon_obj.status()
            
            if result["running"]:
                facts = {
                    "running": True,
                    "pid": result["pid"],
                    "cache_age_seconds": result.get("cache_age_seconds"),
                    "cache_stale": result.get("cache_stale", False),
                    "last_scan": result.get("last_scan"),
                    "scan_count": result.get("scan_count")
                }
                
                if json_output:
                    envelope = build_result_envelope(
                        command=["honk", "watchdog", "pty", "daemon", "--status"],
                        status="ok",
                        changed=False,
                        code="watchdog.pty.daemon.running",
                        summary=f"PTY daemon running (PID {result['pid']})",
                        facts=facts
                    )
                    print(json.dumps(envelope, indent=2))
                else:
                    console.print(f"\n[green]✓[/green] PTY daemon is running")
                    console.print(f"  PID: [bold]{result['pid']}[/bold]")
                    if result.get("last_scan"):
                        console.print(f"  Last scan: [dim]{result['last_scan']}[/dim]")
                    if result.get("cache_age_seconds"):
                        console.print(f"  Cache age: [dim]{result['cache_age_seconds']}s[/dim]")
                    if result.get("cache_stale"):
                        console.print("  [yellow]⚠ Cache is stale[/yellow]")
                sys.exit(EXIT_OK)
            else:
                if json_output:
                    envelope = build_result_envelope(
                        command=["honk", "watchdog", "pty", "daemon", "--status"],
                        status="ok",
                        changed=False,
                        code="watchdog.pty.daemon.not_running",
                        summary="PTY daemon not running",
                        facts={"running": False}
                    )
                    print(json.dumps(envelope, indent=2))
                else:
                    console.print("\n[red]✗[/red] PTY daemon is not running")
                    console.print("  Start it with: [bold]honk watchdog pty daemon --start[/bold]")
                sys.exit(EXIT_OK)
    
    except Exception as e:
        if json_output:
            envelope = build_result_envelope(
                command=["honk", "watchdog", "pty", "daemon"],
                status="error",
                changed=False,
                code="watchdog.pty.daemon.error",
                summary=str(e),
                facts={}
            )
            print(json.dumps(envelope, indent=2))
        else:
            print_error(f"Daemon error: {e}")
        sys.exit(EXIT_SYSTEM)


@pty_app.command("observer")
def observer(
    live: bool = typer.Option(True, "--live/--no-live", help="Auto-refresh every 5s"),
    cache_file: str = typer.Option("tmp/pty-cache.json", "--cache-file", help="Path to cache file"),
):
    """TUI dashboard displaying cached PTY data."""
    from pathlib import Path
    
    try:
        # Check if Textual is available
        from .pty_observer import run_observer
    except ImportError:
        print_error("Textual library not installed. Install with: uv add textual")
        sys.exit(EXIT_PREREQ_FAILED)
    
    try:
        cache_path = Path(cache_file)
        
        # Check if cache exists
        if not cache_path.exists():
            console.print("[yellow]⚠[/yellow] Cache file not found")
            console.print(f"  Expected: [dim]{cache_path}[/dim]")
            console.print("\nStart the daemon first:")
            console.print("  [bold]honk watchdog pty daemon --start[/bold]")
            sys.exit(EXIT_PREREQ_FAILED)
        
        # Run observer TUI
        exit_code = run_observer(cache_path)
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print_info("Observer stopped")
        sys.exit(EXIT_OK)
    except Exception as e:
        print_error(f"Observer error: {e}")
        sys.exit(EXIT_SYSTEM)
