"System diagnostics commands."

import sys
import typer
import json
import os
import psutil
import time

from .result import EXIT_OK, EXIT_SYSTEM
from .ui import console, print_error, print_info
from .watchdog.pty_scanner import scan_ptys

system_app = typer.Typer(help="System diagnostics suite")


def get_process_count():
    """Get the total number of processes for the current user."""
    import subprocess
    result = subprocess.run(['ps', '-U', str(os.getuid())], capture_output=True, text=True)
    return len(result.stdout.strip().split('\n'))


@system_app.command("summary")
def summary(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    """A high-level dashboard of system health."""
    try:
        pty_processes = scan_ptys()
        total_ptys = sum(p.pty_count for p in pty_processes.values())
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
            time.sleep(0.1)
            for p in procs:
                try:
                    p['cpu_percent'] = psutil.Process(p['pid']).cpu_percent()
                except psutil.NoSuchProcess:
                    p['cpu_percent'] = 0
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


@system_app.command("pty")
def pty(json_output: bool = typer.Option(False, "--json", help="Output as JSON")):
    """A detailed report of all processes currently holding PTYs."""
    try:
        pty_processes = scan_ptys()
        
        if json_output:
            facts = [
                {
                    "pid": p.pid,
                    "command": p.command,
                    "pty_count": p.pty_count,
                    "ptys": p.ptys,
                }
                for p in pty_processes.values()
            ]
            print(json.dumps({"command": "system pty", "status": "ok", "facts": facts}, indent=2))
        else:
            from rich.table import Table
            table = Table(title="PTY Usage Details")
            table.add_column("PID", justify="right")
            table.add_column("Command")
            table.add_column("PTY Count", justify="right")
            table.add_column("PTYs")

            sorted_procs = sorted(pty_processes.values(), key=lambda p: p.pty_count, reverse=True)

            for p in sorted_procs:
                pty_list = ", ".join(p.ptys)
                table.add_row(
                    str(p.pid),
                    p.command,
                    str(p.pty_count),
                    pty_list
                )
            
            console.print(table)

        sys.exit(EXIT_OK)

    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)


@system_app.command("fds")
def fds(
    top: int = typer.Option(5, "--top", help="Number of top processes to show."),
    pid: int = typer.Option(None, "--pid", help="Show open files for a specific PID."),
):
    """Report on file descriptor usage."""
    try:
        from rich.table import Table
        if pid:
            proc = psutil.Process(pid)
            files = proc.open_files()
            title = f"Open File Descriptors for PID {pid} ({proc.name()})"
            table = Table(title=title)
            table.add_column("Path")
            table.add_column("Mode")
            for f in files:
                table.add_row(f.path, f.mode)
            console.print(table)
        else:
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'username']):
                if p.info['username'] == os.getlogin():
                    try:
                        p.info['num_fds'] = p.num_fds()
                        procs.append(p.info)
                    except psutil.AccessDenied:
                        pass
            
            procs.sort(key=lambda x: x['num_fds'], reverse=True)

            table = Table(title=f"Top {top} Processes by File Descriptor Count")
            table.add_column("PID", justify="right")
            table.add_column("Process Name")
            table.add_column("FD Count", justify="right")

            for p in procs[:top]:
                table.add_row(
                    str(p['pid']),
                    p['name'],
                    str(p['num_fds'])
                )
            console.print(table)

        sys.exit(EXIT_OK)

    except psutil.NoSuchProcess:
        print_error(f"Process with PID {pid} not found.")
        sys.exit(EXIT_SYSTEM)
    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)


@system_app.command("network")
def network(
    kind: str = typer.Option("listen", "--kind", help="Show 'listen' or 'established' connections."),
):
    """Show network connections."""
    try:
        if kind not in ["listen", "established"]:
            print_error("Invalid kind: must be 'listen' or 'established'")
            raise typer.Exit(1)

        connections = psutil.net_connections(kind='inet')
        
        from rich.table import Table
        title = f"Network Connections (Status: {kind.upper()})"
        table = Table(title=title)
        table.add_column("PID", justify="right")
        table.add_column("Process Name")
        table.add_column("Local Address")
        table.add_column("Remote Address")
        table.add_column("Status")

        for conn in connections:
            if conn.status and conn.status.lower() == kind:
                try:
                    p = psutil.Process(conn.pid)
                    proc_name = p.name()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    proc_name = "?"

                laddr = f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else ""
                raddr = f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else ""
                
                table.add_row(
                    str(conn.pid) if conn.pid else "",
                    proc_name,
                    laddr,
                    raddr,
                    conn.status
                )
        
        console.print(table)
        sys.exit(EXIT_OK)

    except Exception as e:
        print_error(f"Internal error: {e}")
        sys.exit(EXIT_SYSTEM)