"""Tests for PTY CLI commands."""

import json
import pytest
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from honk.cli import app
from honk.watchdog.pty_scanner import PTYProcess

runner = CliRunner()


class TestPtyShow:
    """Test pty show command."""
    
    @patch("honk.watchdog.pty_cli.scan_ptys")
    def test_show_command_text_output(self, mock_scan):
        """Test show command with text output."""
        mock_scan.return_value = {
            1234: PTYProcess(1234, "node /usr/local/bin/copilot-agent", 
                           [f"/dev/ttys{i:03d}" for i in range(10)]),
            5678: PTYProcess(5678, "python3", ["/dev/ttys001", "/dev/ttys002"]),
        }
        
        result = runner.invoke(app, ["watchdog", "pty", "show", "--no-color"])
        
        assert result.exit_code == 0
        assert "PTY Usage" in result.stdout
        assert "12" in result.stdout  # Total PTYs
        assert "node" in result.stdout
    
    @patch("honk.watchdog.pty_cli.scan_ptys")
    def test_show_command_json_output(self, mock_scan):
        """Test show command with JSON output."""
        mock_scan.return_value = {
            1234: PTYProcess(1234, "node /usr/local/bin/copilot-agent", 
                           [f"/dev/ttys{i:03d}" for i in range(10)]),
            5678: PTYProcess(5678, "python3", ["/dev/ttys001", "/dev/ttys002"]),
        }
        
        result = runner.invoke(app, ["watchdog", "pty", "show", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        
        assert output["status"] == "ok"
        assert output["facts"]["total_ptys"] == 12
        assert output["facts"]["process_count"] == 2
    
    @patch("honk.watchdog.pty_cli.scan_ptys")
    def test_show_no_ptys(self, mock_scan):
        """Test show with no PTYs."""
        mock_scan.return_value = {}
        
        result = runner.invoke(app, ["watchdog", "pty", "show", "--no-color"])
        
        assert result.exit_code == 0
        assert "0" in result.stdout


class TestPtyClean:
    """Test pty clean command."""
    
    @patch("honk.watchdog.pty_cli.kill_processes")
    @patch("honk.watchdog.pty_cli.get_suspected_leaks")
    @patch("honk.watchdog.pty_cli.scan_ptys")
    def test_clean_command_plan_mode(self, mock_scan, mock_leaks, mock_kill):
        """Test clean command in plan mode."""
        leak_process = PTYProcess(1234, "node /usr/local/bin/copilot-agent", 
                                 [f"/dev/ttys{i:03d}" for i in range(10)])
        mock_scan.return_value = {1234: leak_process}
        mock_leaks.return_value = [leak_process]
        
        result = runner.invoke(app, ["watchdog", "pty", "clean", "--plan", "--no-color"])
        
        assert result.exit_code == 0
        assert "Would kill" in result.stdout
        mock_kill.assert_not_called()
    
    @patch("honk.watchdog.pty_cli.kill_processes")
    @patch("honk.watchdog.pty_cli.get_suspected_leaks")
    @patch("honk.watchdog.pty_cli.scan_ptys")
    def test_clean_no_leaks(self, mock_scan, mock_leaks, mock_kill):
        """Test clean with no leaks found."""
        mock_scan.return_value = {
            1234: PTYProcess(1234, "bash", ["/dev/ttys001"]),
        }
        mock_leaks.return_value = []
        
        result = runner.invoke(app, ["watchdog", "pty", "clean", "--no-color"])
        
        assert result.exit_code == 0
        assert "No leaking" in result.stdout
        mock_kill.assert_not_called()
    
    @patch("honk.watchdog.pty_cli.kill_processes")
    @patch("honk.watchdog.pty_cli.get_suspected_leaks")
    @patch("honk.watchdog.pty_cli.scan_ptys")
    def test_clean_json_output(self, mock_scan, mock_leaks, mock_kill):
        """Test clean command with JSON output."""
        leak_process = PTYProcess(1234, "node /usr/local/bin/copilot-agent", 
                                 [f"/dev/ttys{i:03d}" for i in range(10)])
        mock_scan.return_value = {1234: leak_process}
        mock_leaks.return_value = [leak_process]
        
        result = runner.invoke(app, ["watchdog", "pty", "clean", "--plan", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        
        assert output["status"] == "ok"
        assert "would_kill" in output["facts"]


class TestPtyWatch:
    """Test pty watch command."""
    
    @pytest.mark.skip(reason="KeyboardInterrupt handling in watch requires real signal handling")
    @patch("honk.watchdog.pty_cli.time.sleep")
    @patch("honk.watchdog.pty_cli.kill_processes")
    @patch("honk.watchdog.pty_cli.get_suspected_leaks")
    @patch("honk.watchdog.pty_cli.scan_ptys")
    def test_watch_command(self, mock_scan, mock_leaks, mock_kill, mock_sleep):
        """Test watch command monitors PTYs."""
        # Simulate KeyboardInterrupt to exit loop
        mock_scan.side_effect = [
            {},  # First scan
            KeyboardInterrupt(),  # Exit
        ]
        mock_leaks.return_value = []
        
        result = runner.invoke(app, ["watchdog", "pty", "watch", "--interval", "1", "--no-color"])
        
        # Should exit gracefully on KeyboardInterrupt
        assert result.exit_code == 0
