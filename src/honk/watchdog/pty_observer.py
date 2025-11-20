"""PTY Observer TUI - Dashboard for cached PTY data."""

import json
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Header, Footer, Static, DataTable, Label
from textual.reactive import reactive


class StatsCard(Static):
    """A card showing a statistic."""
    
    value: reactive[str] = reactive("")
    label: reactive[str] = reactive("")
    
    def __init__(self, label: str, value: str = "0", **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.value = value
    
    def render(self) -> str:
        return f"[bold cyan]{self.label}[/bold cyan]\n[bold white]{self.value}[/bold white]"


class PTYObserver(App):
    """TUI dashboard for PTY monitoring data."""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #stats {
        height: 5;
        margin: 1 2;
    }
    
    .stat-card {
        width: 1fr;
        height: 100%;
        border: solid $primary;
        padding: 1;
        margin: 0 1;
    }
    
    #process-table {
        height: 1fr;
        margin: 1 2;
    }
    
    #status-bar {
        height: 3;
        margin: 1 2;
        padding: 1;
        border: solid $accent;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]
    
    def __init__(self, cache_file: Path = Path("tmp/pty-cache.json")):
        super().__init__()
        self.cache_file = cache_file
        self.cache_data = None
        self.auto_refresh = True
        
    def compose(self) -> ComposeResult:
        """Create UI components."""
        yield Header()
        
        # Status bar
        yield Container(
            Label("Loading...", id="status-text"),
            id="status-bar"
        )
        
        # Stats cards
        with Horizontal(id="stats"):
            yield StatsCard("Total PTYs", "0", classes="stat-card", id="total-ptys")
            yield StatsCard("Processes", "0", classes="stat-card", id="process-count")
            yield StatsCard("Heavy Users", "0", classes="stat-card", id="heavy-users")
        
        # Process table
        yield DataTable(id="process-table")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up UI after mounting."""
        table = self.query_one(DataTable)
        table.add_columns("PID", "Command", "PTY Count")
        table.cursor_type = "row"
        
        # Initial load
        self.load_cache()
        
        # Set up auto-refresh timer (every 5 seconds) - use call_later for async safety
        if self.auto_refresh:
            self.refresh_timer()
    
    def refresh_timer(self) -> None:
        """Schedule next cache refresh."""
        self.load_cache()
        if self.auto_refresh:
            self.call_later(5.0, self.refresh_timer)
    
    def load_cache(self) -> None:
        """Load data from cache file."""
        try:
            if not self.cache_file.exists():
                self.update_status("⚠ Cache file not found. Start daemon first.", "warning")
                return
            
            # Read cache
            self.cache_data = json.loads(self.cache_file.read_text())
            
            # Update status
            timestamp = self.cache_data.get("timestamp", "unknown")
            scan_num = self.cache_data.get("scan_number", 0)
            self.update_status(f"✓ Last scan: {timestamp} (#{scan_num})", "success")
            
            # Update stats cards
            self.update_stats()
            
            # Update process table
            self.update_table()
            
        except json.JSONDecodeError as e:
            self.update_status(f"✗ Invalid cache file: {e}", "error")
        except Exception as e:
            self.update_status(f"✗ Error loading cache: {e}", "error")
    
    def update_status(self, text: str, status_type: str = "info") -> None:
        """Update status bar text."""
        status_label = self.query_one("#status-text", Label)
        
        if status_type == "success":
            status_label.update(f"[green]{text}[/green]")
        elif status_type == "warning":
            status_label.update(f"[yellow]{text}[/yellow]")
        elif status_type == "error":
            status_label.update(f"[red]{text}[/red]")
        else:
            status_label.update(text)
    
    def update_stats(self) -> None:
        """Update statistics cards."""
        if not self.cache_data:
            return
        
        total_ptys = self.cache_data.get("total_ptys", 0)
        process_count = self.cache_data.get("process_count", 0)
        heavy_users = len(self.cache_data.get("heavy_users", []))
        
        # Update cards
        self.query_one("#total-ptys", StatsCard).value = str(total_ptys)
        self.query_one("#process-count", StatsCard).value = str(process_count)
        self.query_one("#heavy-users", StatsCard).value = str(heavy_users)
    
    def update_table(self) -> None:
        """Update process table."""
        if not self.cache_data:
            return
        
        table = self.query_one(DataTable)
        table.clear()
        
        processes = self.cache_data.get("processes", [])
        
        # Sort by PTY count (descending)
        processes.sort(key=lambda p: p.get("pty_count", 0), reverse=True)
        
        # Add rows (limit to top 20)
        for proc in processes[:20]:
            pid = proc.get("pid", "?")
            command = proc.get("command", "unknown")
            pty_count = proc.get("pty_count", 0)
            
            # Truncate long commands
            if len(command) > 40:
                command = command[:37] + "..."
            
            table.add_row(str(pid), command, str(pty_count))
    
    def action_refresh(self) -> None:
        """Refresh action (R key)."""
        self.load_cache()
        self.update_status("Refreshed", "success")
    
    def action_quit(self) -> None:
        """Quit action (Q key)."""
        self.exit()


def run_observer(cache_file: Path = Path("tmp/pty-cache.json")) -> int:
    """Run the observer TUI.
    
    Returns:
        Exit code
    """
    app = PTYObserver(cache_file=cache_file)
    app.run()
    return 0
