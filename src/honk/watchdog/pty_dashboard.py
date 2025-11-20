"""PTY Dashboard - Comprehensive monitoring TUI for PTY usage and management.

Shows all PTY tools in a grid layout with real-time stats, graphs, and threshold indicators.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional
import json

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, DataTable, Sparkline
from textual.reactive import reactive
from rich.console import RenderableType
from rich.panel import Panel
from rich.text import Text
from rich.table import Table as RichTable


class StatusCard(Static):
    """A card showing status of a PTY tool component."""
    
    def __init__(self, title: str, status: str = "unknown", details: str = "", **kwargs):
        super().__init__(**kwargs)
        self.title_text = title
        self.status_value = status
        self.details_text = details
    
    def render(self) -> RenderableType:
        """Render the status card."""
        # Status indicators
        status_map = {
            "running": "🟢",
            "stopped": "🔴",
            "warning": "🟡",
            "unknown": "⚪"
        }
        
        indicator = status_map.get(self.status_value, "⚪")
        
        content = Text()
        content.append(f"{indicator} ", style="bold")
        content.append(self.title_text, style="bold cyan")
        content.append("\n")
        content.append(self.details_text, style="dim")
        
        return Panel(
            content,
            border_style="green" if self.status_value == "running" else "red",
            padding=(0, 1)
        )
    
    def update_status(self, status: str, details: str = "") -> None:
        """Update card status and details."""
        self.status_value = status
        self.details_text = details
        self.refresh()


class PTYGraph(Static):
    """Graph showing PTY usage over time with threshold lines."""
    
    def __init__(self, max_value: int = 256, **kwargs):
        super().__init__(**kwargs)
        self.max_value = max_value
        self.history: list[int] = []
        self.max_history = 60  # Keep last 60 data points
        
        # Threshold levels (from pty_clean.py leak detection)
        self.thresholds = {
            "critical": int(max_value * 0.90),  # 90% - aggressive cleanup
            "high": int(max_value * 0.80),      # 80% - moderate cleanup
            "warning": int(max_value * 0.70),   # 70% - watch closely
        }
    
    def add_data_point(self, value: int) -> None:
        """Add a new data point to the graph."""
        self.history.append(value)
        if len(self.history) > self.max_history:
            self.history.pop(0)
        self.refresh()
    
    def render(self) -> RenderableType:
        """Render the PTY usage graph."""
        if not self.history:
            return Panel("No data yet...", title="PTY Usage History")
        
        current = self.history[-1] if self.history else 0
        peak = max(self.history) if self.history else 0
        
        # Create ASCII sparkline
        height = 10
        width = min(len(self.history), 60)
        
        # Normalize data to fit in height
        if peak > 0:
            normalized = [int((v / self.max_value) * height) for v in self.history[-width:]]
        else:
            normalized = [0] * width
        
        # Build graph
        lines = []
        for row in range(height, -1, -1):
            line_parts = []
            
            # Y-axis label
            value = int((row / height) * self.max_value)
            label = f"{value:3d} "
            
            # Check if this row is a threshold
            threshold_marker = ""
            if abs(value - self.thresholds["critical"]) < 5:
                threshold_marker = "═ CRITICAL"
                style = "red bold"
            elif abs(value - self.thresholds["high"]) < 5:
                threshold_marker = "─ HIGH"
                style = "yellow bold"
            elif abs(value - self.thresholds["warning"]) < 5:
                threshold_marker = "┄ WARNING"
                style = "orange1 dim"
            else:
                style = "dim"
            
            line = Text(label, style="dim")
            
            # Plot data points
            for val in normalized:
                if val >= row:
                    if val >= (self.thresholds["critical"] / self.max_value * height):
                        line.append("█", style="red bold")
                    elif val >= (self.thresholds["high"] / self.max_value * height):
                        line.append("█", style="yellow")
                    elif val >= (self.thresholds["warning"] / self.max_value * height):
                        line.append("█", style="orange1")
                    else:
                        line.append("█", style="green")
                else:
                    line.append(" ")
            
            if threshold_marker:
                line.append(f" {threshold_marker}", style=style)
            
            lines.append(line)
        
        # Add X-axis
        x_axis = Text("    " + "─" * width, style="dim")
        lines.append(x_axis)
        lines.append(Text("    " + "Now".rjust(width), style="dim"))
        
        # Combine all lines
        graph = Text("\n").join(lines)
        
        # Add stats below
        stats = Text("\n\n")
        stats.append(f"Current: ", style="bold")
        stats.append(f"{current}", style="cyan bold")
        stats.append(f" / {self.max_value}", style="dim")
        
        percent = (current / self.max_value * 100) if self.max_value > 0 else 0
        stats.append(f"  ({percent:.1f}%)", style="dim")
        
        stats.append(f"\nPeak: ", style="bold")
        stats.append(f"{peak}", style="yellow")
        stats.append(f"  ({(peak/self.max_value*100):.1f}%)", style="dim")
        
        final = Text()
        final.append(graph)
        final.append(stats)
        
        # Choose border color based on current level
        if current >= self.thresholds["critical"]:
            border_style = "red bold"
        elif current >= self.thresholds["high"]:
            border_style = "yellow"
        elif current >= self.thresholds["warning"]:
            border_style = "orange1"
        else:
            border_style = "green"
        
        return Panel(
            final,
            title=f"PTY Usage History (Max: {self.max_value})",
            border_style=border_style,
            padding=(1, 2)
        )


class PTYDashboard(App):
    """Comprehensive PTY monitoring dashboard."""
    
    CSS = """
    Screen {
        layout: vertical;
    }
    
    #top-row {
        height: 12;
        layout: horizontal;
    }
    
    .status-card {
        width: 1fr;
        height: 100%;
        margin: 0 1;
    }
    
    #graph-container {
        height: 25;
        margin: 1 0;
    }
    
    #process-table-container {
        height: 1fr;
        margin: 1 0;
    }
    
    DataTable {
        height: 100%;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("c", "clean", "Clean PTYs"),
    ]
    
    def __init__(self, cache_file: Path = Path("tmp/pty-cache.json")):
        super().__init__()
        self.cache_file = cache_file
        self.cache_data: Optional[dict] = None
        self.max_ptys = 256  # macOS default limit
        
    def compose(self) -> ComposeResult:
        """Create dashboard UI components."""
        yield Header()
        
        # Top row: Status cards for each tool
        with Container(id="top-row"):
            yield StatusCard("Daemon", id="daemon-card", classes="status-card")
            yield StatusCard("Observer", id="observer-card", classes="status-card")
            yield StatusCard("Scanner", id="scanner-card", classes="status-card")
            yield StatusCard("Cleaner", id="cleaner-card", classes="status-card")
        
        # Middle: PTY usage graph
        with Container(id="graph-container"):
            yield PTYGraph(max_value=self.max_ptys, id="pty-graph")
        
        # Bottom: Process table
        with Container(id="process-table-container"):
            yield DataTable(id="process-table")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up dashboard after mounting."""
        # Configure process table
        table = self.query_one("#process-table", DataTable)
        table.add_columns("Application", "Processes", "Total PTYs", "% of Limit")
        table.cursor_type = "row"
        
        # Initial load
        self.load_data()
        
        # Set up auto-refresh (every 2 seconds for dashboard)
        self.set_interval(2.0, self.load_data)
    
    def load_data(self) -> None:
        """Load data from cache and update all components."""
        try:
            if not self.cache_file.exists():
                self.update_daemon_status("stopped", "Cache not found")
                return
            
            # Read cache
            cache_text = self.cache_file.read_text()
            self.cache_data = json.loads(cache_text) if cache_text else {}
            
            if not self.cache_data:
                self.update_daemon_status("warning", "Empty cache")
                return
            
            # Update components
            self.update_status_cards()
            self.update_graph()
            self.update_process_table()
            
        except json.JSONDecodeError as e:
            self.cache_data = None
            self.update_daemon_status("warning", f"Invalid cache: {e}")
        except Exception as e:
            self.cache_data = None
            self.update_daemon_status("warning", f"Error: {e}")
    
    def update_status_cards(self) -> None:
        """Update all status cards."""
        if not self.cache_data:
            return
        
        # Daemon status
        timestamp_str = self.cache_data.get("timestamp", "")
        if timestamp_str:
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                age_seconds = (datetime.now(timestamp.tzinfo) - timestamp).total_seconds()
                
                if age_seconds < 10:
                    status = "running"
                    details = f"Active ({age_seconds:.0f}s ago)"
                elif age_seconds < 60:
                    status = "running"
                    details = f"Running ({age_seconds:.0f}s ago)"
                else:
                    status = "warning"
                    details = f"Stale ({age_seconds/60:.0f}m ago)"
            except Exception:
                status = "unknown"
                details = "Invalid timestamp"
        else:
            status = "unknown"
            details = "No timestamp"
        
        daemon_card = self.query_one("#daemon-card", StatusCard)
        daemon_card.update_status(status, details)
        
        # Observer status (check if TUI process is running)
        observer_card = self.query_one("#observer-card", StatusCard)
        observer_card.update_status("running", "Dashboard active")
        
        # Scanner status (based on cache data)
        total_processes = len(self.cache_data.get("processes", {}))
        scanner_card = self.query_one("#scanner-card", StatusCard)
        if total_processes > 0:
            scanner_card.update_status("running", f"{total_processes} processes")
        else:
            scanner_card.update_status("warning", "No data")
        
        # Cleaner status (based on leak detection)
        total_ptys = self.cache_data.get("total_ptys", 0)
        percent = (total_ptys / self.max_ptys * 100) if self.max_ptys > 0 else 0
        
        cleaner_card = self.query_one("#cleaner-card", StatusCard)
        if percent >= 90:
            cleaner_card.update_status("warning", f"CRITICAL: {percent:.0f}%")
        elif percent >= 80:
            cleaner_card.update_status("warning", f"HIGH: {percent:.0f}%")
        elif percent >= 70:
            cleaner_card.update_status("running", f"Watch: {percent:.0f}%")
        else:
            cleaner_card.update_status("running", f"Normal: {percent:.0f}%")
    
    def update_graph(self) -> None:
        """Update PTY usage graph."""
        if not self.cache_data:
            return
        
        total_ptys = self.cache_data.get("total_ptys", 0)
        graph = self.query_one("#pty-graph", PTYGraph)
        graph.add_data_point(total_ptys)
    
    def update_process_table(self) -> None:
        """Update process table with application summary."""
        if not self.cache_data:
            return
        
        table = self.query_one("#process-table", DataTable)
        table.clear()
        
        # Get application summary
        app_summary = self.cache_data.get("application_summary", [])
        
        if not app_summary:
            table.add_row("No processes found", "-", "-", "-")
            return
        
        # Add rows (already sorted by total_ptys in cache)
        for app in app_summary[:20]:  # Top 20 applications
            app_name = app.get("application", "Unknown")
            process_count = app.get("process_count", 0)
            total_ptys = app.get("total_ptys", 0)
            percent = (total_ptys / self.max_ptys * 100) if self.max_ptys > 0 else 0
            
            table.add_row(
                app_name,
                str(process_count),
                str(total_ptys),
                f"{percent:.1f}%"
            )
    
    def update_daemon_status(self, status: str, details: str) -> None:
        """Update daemon status card."""
        try:
            daemon_card = self.query_one("#daemon-card", StatusCard)
            daemon_card.update_status(status, details)
        except Exception:
            pass  # Card might not be mounted yet
    
    def action_refresh(self) -> None:
        """Manual refresh action."""
        self.load_data()
        self.notify("Refreshed")
    
    async def action_clean(self) -> None:
        """Trigger PTY cleanup action."""
        self.notify("Cleanup not implemented in TUI yet. Use: honk watchdog pty clean")
    
    async def action_quit(self) -> None:
        """Quit action."""
        self.exit()


def run_dashboard(cache_file: Path = Path("tmp/pty-cache.json")) -> int:
    """Run the PTY dashboard TUI.
    
    Returns:
        Exit code
    """
    app = PTYDashboard(cache_file=cache_file)
    app.run()
    return 0
