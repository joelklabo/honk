"""PTY watchdog commands."""

import sys
import time
import signal
import json
import typer

from ..result import EXIT_OK, EXIT_PREREQ_FAILED, EXIT_SYSTEM
from ..ui import console, print_success, print_error, print_info
from .pty_scanner import scan_ptys, kill_processes, get_heavy_users, get_suspected_leaks

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
        
        # Build facts
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
            # Human-friendly output
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
    threshold: int = typer.Option(4, "--threshold", help="Minimum PTYs to trigger cleanup"),
    no_color: bool = typer.Option(False, "--no-color", help="Disable color output"),
):
    """Kill processes with orphaned PTY sessions."""
    try:
        # Initial scan
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
                    facts={
                        "before": {"total_ptys": total_ptys_before, "process_count": len(processes_before)},
                        "killed": [],
                        "freed_ptys": 0
                    }
                )
                print(json.dumps(envelope, indent=2))
            else:
                print_info("No leaking processes found")
            sys.exit(EXIT_OK)
        
        # Plan mode or actual cleanup
        if plan:
            if json_output:
                envelope = build_result_envelope(
                    command=["honk", "watchdog", "pty", "clean", "--plan"],
                    status="ok",
                    changed=False,
                    code="watchdog.pty.clean.plan",
                    summary=f"Would kill {len(suspected_leaks)} processes",
                    facts={
                        "would_kill": [
                            {"pid": p.pid, "command": p.command, "pty_count": p.pty_count}
                            for p in suspected_leaks
                        ]
                    }
                )
                print(json.dumps(envelope, indent=2))
            else:
                console.print("\n[bold yellow]Would kill:[/bold yellow]")
                for p in suspected_leaks:
                    console.print(f"  • PID {p.pid} ({p.command}) — {p.pty_count} PTYs")
                console.print()
            sys.exit(EXIT_OK)
        
        # Actually kill processes
        pids_to_kill = [p.pid for p in suspected_leaks]
        kill_results = kill_processes(pids_to_kill)
        
        # Rescan
        time.sleep(0.5)  # Give processes time to die
        processes_after = scan_ptys()
        total_ptys_after = sum(p.pty_count for p in processes_after.values())
        freed_ptys = total_ptys_before - total_ptys_after
        
        killed_list = [
            {
                "pid": p.pid,
                "command": p.command,
                "pty_count": p.pty_count,
                "success": kill_results.get(p.pid, False)
            }
            for p in suspected_leaks
        ]
        
        if json_output:
            envelope = build_result_envelope(
                command=["honk", "watchdog", "pty", "clean"],
                status="ok",
                changed=True,
                code="watchdog.pty.clean.ok",
                summary=f"Killed {len(suspected_leaks)} leaking processes, freed {freed_ptys} PTYs",
                facts={
                    "before": {"total_ptys": total_ptys_before, "process_count": len(processes_before)},
                    "after": {"total_ptys": total_ptys_after, "process_count": len(processes_after)},
                    "killed": killed_list,
                    "freed_ptys": freed_ptys
                }
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


@pty_app.command("watch")
def watch(
    interval: int = typer.Option(5, "--interval", help="Check interval in seconds"),
    max_ptys: int = typer.Option(200, "--max-ptys", help="Auto-clean threshold"),
    json_output: bool = typer.Option(False, "--json", help="Stream JSON events"),
):
    """Monitor PTY usage and auto-clean when thresholds are exceeded."""
    try:
        cleanup_count = 0
        scan_count = 0
        
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
            scan_count += 1
            
            if json_output:
                event = {"event": "scan", "total_ptys": total_ptys, "process_count": len(processes)}
                console.print(json.dumps(event))
            else:
                timestamp = time.strftime("%H:%M:%S")
                status_line = f"[{timestamp}] PTYs={total_ptys}  procs={len(processes)}"
                
                if total_ptys > max_ptys:
                    console.print(f"{status_line}  [bold red]!! HIGH — cleaning…[/bold red]")
                    
                    # Trigger cleanup
                    suspected_leaks = get_suspected_leaks(processes, threshold=4)
                    if suspected_leaks:
                        pids_to_kill = [p.pid for p in suspected_leaks]
                        kill_processes(pids_to_kill)
                        cleanup_count += 1
                        
                        time.sleep(0.5)
                        processes_after = scan_ptys()
                        freed = total_ptys - sum(p.pty_count for p in processes_after.values())
                        
                        console.print(f"  [green]→ Killed {len(suspected_leaks)} processes ({freed} PTYs freed)[/green]")
                else:
                    console.print(status_line)
            
            time.sleep(interval)
        
    except RuntimeError as e:
        print_error(str(e))
        sys.exit(EXIT_PREREQ_FAILED)
    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)
