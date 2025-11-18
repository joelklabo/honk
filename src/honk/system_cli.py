"""System diagnostics commands."""

import sys
import typer
import json
import os
import psutil
import time

from .result import EXIT_OK, EXIT_SYSTEM
from .ui import console, print_error
from .watchdog.pty_scanner import scan_ptys

system_app = typer.Typer(help="System diagnostics suite")


def get_process_count():
    """Get the total number of processes for the current user."""
    # A simplified placeholder. A real implementation would be more robust.
    import subprocess
    import os
    result = subprocess.run(['ps', '-U', str(os.getuid())], capture_output=True, text=True)
    return len(result.stdout.strip().split('\n'))


@system_app.command("summary")
def summary(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    """A high-level dashboard of system health."""
    try:
        pty_processes = scan_ptys()
        total_ptys = sum(p.pty_count for p in pty_processes.values())
        
        # Placeholder for other metrics
        user_process_count = get_process_count()
        
        facts = {
            "pty_usage": {
                "total_ptys": total_ptys,
                "process_count": len(pty_processes),
            },
            "process_usage": {
                "user_process_count": user_process_count,
            }
        }
        
        if json_output:
            print(json.dumps({"command": "system summary", "status": "ok", "facts": facts}, indent=2))
        else:
            console.print("\n[bold cyan]System Health Summary[/bold cyan]\n")
            console.print(f"PTY Usage: [bold]{total_ptys}[/bold] active sessions")
            console.print(f"Process Count: [bold]{user_process_count}[/bold] user processes")
            console.print("\n[dim]More checks coming soon...[/dim]")

        sys.exit(EXIT_OK)

    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)


@system_app.command("processes")
def processes(
    sort_by: str = typer.Option("cpu", "--sort-by", help="Sort by 'cpu' or 'mem'."),
    top: int = typer.Option(10, "--top", help="Number of processes to show."),
):
    """Show running processes, sorted by CPU or memory."""
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 'memory_percent']):
            if p.info['username'] == os.getlogin():
                procs.append(p.info)

        if sort_by == 'cpu':
            # The first call to cpu_percent is 0.0, so call it again after a short interval
            time.sleep(0.1)
            for p in procs:
                p['cpu_percent'] = psutil.Process(p['pid']).cpu_percent()
            procs.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif sort_by == 'mem':
            procs.sort(key=lambda x: x['memory_percent'], reverse=True)
        else:
            print_error(f"Invalid sort key: {sort_by}")
            raise typer.Exit(1)

        from rich.table import Table
        table = Table(title=f"Top {top} Processes by {sort_by.upper()} Usage")
        table.add_column("PID", justify="right")
        table.add_column("Process Name")
        table.add_column("CPU %", justify="right")
        table.add_column("Mem %", justify="right")

        for p in procs[:top]:
            table.add_row(
                str(p['pid']),
                p['name'],
                f"{p['cpu_percent']:.1f}",
                f"{p['memory_percent']:.1f}"
            )
        
        console.print(table)
        sys.exit(EXIT_OK)

    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)
