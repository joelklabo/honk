"""Tests for PTY scanner."""

from unittest.mock import patch

from honk.watchdog.pty_scanner import (
    PTYProcess,
    parse_lsof_output,
    scan_ptys,
    get_heavy_users,
    get_suspected_leaks,
    kill_processes,
)


class TestPTYProcess:
    """Test PTYProcess dataclass."""
    
    def test_pty_count(self):
        """Test pty_count property."""
        process = PTYProcess(
            pid=1234,
            command="node",
            ptys=["/dev/ttys001", "/dev/ttys002", "/dev/ttys003"]
        )
        assert process.pty_count == 3
    
    def test_parent_pid_field(self):
        """Test parent_pid field is optional."""
        # Without parent_pid (orphan or unknown)
        proc1 = PTYProcess(
            pid=1234,
            command="node",
            ptys=["/dev/ttys001"]
        )
        assert proc1.parent_pid is None
        
        # With parent_pid
        proc2 = PTYProcess(
            pid=1234,
            command="node",
            ptys=["/dev/ttys001"],
            parent_pid=5678
        )
        assert proc2.parent_pid == 5678


class TestParseLsofOutput:
    """Test lsof output parsing."""
    
    def test_parse_simple_output(self):
        """Test parsing simple lsof output."""
        output = """p1234
cnode
n/dev/ttys001
p5678
cpython3
n/dev/ttys002
"""
        processes = parse_lsof_output(output)
        
        assert len(processes) == 2
        assert 1234 in processes
        assert 5678 in processes
        
        node_proc = processes[1234]
        assert node_proc.pid == 1234
        assert node_proc.command == "node"
        assert "/dev/ttys001" in node_proc.ptys
        
        python_proc = processes[5678]
        assert python_proc.pid == 5678
        assert python_proc.command == "python3"
        assert "/dev/ttys002" in python_proc.ptys
    
    def test_parse_multiple_ptys_per_process(self):
        """Test parsing process with multiple PTYs."""
        output = """p1234
cnode
n/dev/ttys001
n/dev/ttys002
n/dev/ttys003
"""
        processes = parse_lsof_output(output)
        
        assert len(processes) == 1
        node_proc = processes[1234]
        assert node_proc.pty_count == 3
        assert "/dev/ttys001" in node_proc.ptys
        assert "/dev/ttys002" in node_proc.ptys
        assert "/dev/ttys003" in node_proc.ptys
    
    def test_parse_empty_output(self):
        """Test parsing empty output."""
        processes = parse_lsof_output("")
        assert len(processes) == 0
    
    def test_parse_with_parent_pid(self):
        """Test parsing lsof output with parent PID (R field)."""
        output = """p1234
R5000
cnode
n/dev/ttys001
p5678
R1
cpython3
n/dev/ttys002
"""
        processes = parse_lsof_output(output)
        
        assert len(processes) == 2
        
        # Check parent PIDs
        assert processes[1234].parent_pid == 5000
        assert processes[5678].parent_pid == 1  # Orphan (launchd parent)
    
    def test_parse_without_parent_pid(self):
        """Test parsing when parent PID not available."""
        output = """p1234
cnode
n/dev/ttys001
"""
        processes = parse_lsof_output(output)
        
        # Should have None if no R field
        assert processes[1234].parent_pid is None


class TestScanPtys:
    """Test PTY scanning."""
    
    @patch("honk.watchdog.pty_scanner.run_lsof")
    def test_scan_ptys_success(self, mock_lsof):
        """Test successful PTY scan."""
        mock_lsof.return_value = """p1234
cnode
n/dev/ttys001
p5678
cpython3
n/dev/ttys002
"""
        processes = scan_ptys()
        
        assert len(processes) == 2
        assert 1234 in processes
        assert 5678 in processes
    
    @patch("honk.watchdog.pty_scanner.run_lsof")
    def test_scan_ptys_empty(self, mock_lsof):
        """Test scan with no PTYs."""
        mock_lsof.return_value = ""
        processes = scan_ptys()
        assert len(processes) == 0


class TestGetHeavyUsers:
    """Test heavy user detection."""
    
    def test_identifies_heavy_users(self):
        """Test identification of processes with many PTYs."""
        processes = {
            1234: PTYProcess(1234, "node", [f"/dev/ttys{i:03d}" for i in range(10)]),
            5678: PTYProcess(5678, "python3", ["/dev/ttys001", "/dev/ttys002"]),
            9999: PTYProcess(9999, "bash", ["/dev/ttys100"]),
        }
        
        heavy = get_heavy_users(processes, threshold=4)
        
        assert len(heavy) == 1
        assert heavy[0].pid == 1234
        assert heavy[0].pty_count == 10
    
    def test_respects_threshold(self):
        """Test threshold parameter."""
        processes = {
            1234: PTYProcess(1234, "node", [f"/dev/ttys{i:03d}" for i in range(5)]),
            5678: PTYProcess(5678, "python3", ["/dev/ttys001", "/dev/ttys002", "/dev/ttys003"]),
        }
        
        heavy_4 = get_heavy_users(processes, threshold=4)
        assert len(heavy_4) == 1
        assert heavy_4[0].pid == 1234
        
        heavy_2 = get_heavy_users(processes, threshold=2)
        assert len(heavy_2) == 2


class TestGetSuspectedLeaks:
    """Test leak detection."""
    
    @patch('honk.watchdog.safety.is_safe_to_kill')
    def test_detects_copilot_leaks(self, mock_is_safe_to_kill):
        """Test detection of Copilot agent leaks."""
        # Mock safety check to say the copilot process IS safe to kill
        # (simulating a leak - no terminal, orphaned, etc.)
        def safety_check(pid, proc, threshold=4):
            if "copilot" in (proc.command or "").lower() and proc.pty_count >= 8:
                return (True, "Copilot process with excessive PTYs")
            return (False, "Below threshold")
        
        mock_is_safe_to_kill.side_effect = safety_check
        
        processes = {
            1234: PTYProcess(1234, "node /usr/local/bin/copilot-agent", 
                           [f"/dev/ttys{i:03d}" for i in range(8)]),
            5678: PTYProcess(5678, "python3", ["/dev/ttys001", "/dev/ttys002"]),
        }
        
        leaks = get_suspected_leaks(processes)
        
        assert len(leaks) == 1
        assert leaks[0].pid == 1234
        assert leaks[0].pty_count == 8
    
    @patch('honk.watchdog.safety.is_safe_to_kill')
    def test_no_false_positives(self, mock_is_safe_to_kill):
        """Test that normal processes aren't flagged."""
        # Mock safety check to protect all these processes
        mock_is_safe_to_kill.return_value = (False, "Protected")
        
        processes = {
            1234: PTYProcess(1234, "bash", ["/dev/ttys001"]),
            5678: PTYProcess(5678, "vim", ["/dev/ttys002", "/dev/ttys003"]),
            9999: PTYProcess(9999, "node app.js", ["/dev/ttys004"]),
        }
        
        leaks = get_suspected_leaks(processes)
        assert len(leaks) == 0


class TestKillProcesses:
    """Test process killing."""
    
    @patch("honk.watchdog.pty_scanner.os.kill")
    def test_kills_processes(self, mock_kill):
        """Test killing specified processes."""
        pids = [1234, 5678]
        results = kill_processes(pids)
        
        assert len(results) == 2
        assert results[1234] is True
        assert results[5678] is True
        assert mock_kill.call_count == 2
    
    @patch("honk.watchdog.pty_scanner.os.kill")
    def test_handles_permission_error(self, mock_kill):
        """Test handling of permission errors."""
        mock_kill.side_effect = PermissionError("Access denied")
        
        pids = [1234]
        results = kill_processes(pids)
        
        assert results[1234] is False
    
    @patch("honk.watchdog.pty_scanner.os.kill")
    def test_handles_process_not_found(self, mock_kill):
        """Test handling of non-existent processes."""
        mock_kill.side_effect = ProcessLookupError("No such process")
        
        pids = [99999]
        results = kill_processes(pids)
        
        assert results[99999] is False
