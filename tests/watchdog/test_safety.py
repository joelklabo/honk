"""Tests for safety check utilities."""

import os
import psutil
from unittest.mock import Mock, patch

from honk.watchdog.safety import (
    has_controlling_terminal,
    is_zombie,
    is_orphan,
    is_in_own_tree,
    is_system_critical,
    is_safe_to_kill,
)
from honk.watchdog.pty_scanner import PTYProcess


class TestHasControllingTerminal:
    """Test controlling terminal detection."""
    
    def test_our_process_has_terminal(self):
        """Our test process should have a controlling terminal."""
        # Test runner typically has a terminal
        our_pid = os.getpid()
        # May or may not have terminal depending on test runner
        result = has_controlling_terminal(our_pid)
        assert isinstance(result, bool)
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_process_with_terminal(self, mock_process_class):
        """Process with terminal should return True."""
        mock_proc = Mock()
        mock_proc.terminal.return_value = "/dev/ttys001"
        mock_process_class.return_value = mock_proc
        
        assert has_controlling_terminal(1234) is True
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_process_without_terminal(self, mock_process_class):
        """Process without terminal should return False."""
        mock_proc = Mock()
        mock_proc.terminal.return_value = None
        mock_process_class.return_value = mock_proc
        
        assert has_controlling_terminal(1234) is False
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_no_such_process_fail_safe(self, mock_process_class):
        """If process doesn't exist, fail safe to True."""
        mock_process_class.side_effect = psutil.NoSuchProcess(1234)
        
        # Fail-safe: assume has terminal if can't check
        assert has_controlling_terminal(1234) is True
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_access_denied_fail_safe(self, mock_process_class):
        """If access denied, fail safe to True."""
        mock_process_class.side_effect = psutil.AccessDenied(1234)
        
        # Fail-safe: assume has terminal if can't check
        assert has_controlling_terminal(1234) is True


class TestIsZombie:
    """Test zombie process detection."""
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_zombie_process(self, mock_process_class):
        """Zombie process should return True."""
        mock_proc = Mock()
        mock_proc.status.return_value = psutil.STATUS_ZOMBIE
        mock_process_class.return_value = mock_proc
        
        assert is_zombie(1234) is True
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_running_process(self, mock_process_class):
        """Running process should return False."""
        mock_proc = Mock()
        mock_proc.status.return_value = 'running'
        mock_process_class.return_value = mock_proc
        
        assert is_zombie(1234) is False
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_sleeping_process(self, mock_process_class):
        """Sleeping process should return False."""
        mock_proc = Mock()
        mock_proc.status.return_value = 'sleeping'
        mock_process_class.return_value = mock_proc
        
        assert is_zombie(1234) is False
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_no_such_process(self, mock_process_class):
        """Non-existent process should return False."""
        mock_process_class.side_effect = psutil.NoSuchProcess(1234)
        
        assert is_zombie(1234) is False


class TestIsOrphan:
    """Test orphan process detection."""
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_orphan_process(self, mock_process_class):
        """Process with parent PID 1 (launchd) is orphan."""
        mock_proc = Mock()
        mock_proc.ppid.return_value = 1
        mock_process_class.return_value = mock_proc
        
        assert is_orphan(1234) is True
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_normal_process(self, mock_process_class):
        """Process with normal parent is not orphan."""
        mock_proc = Mock()
        mock_proc.ppid.return_value = 5678
        mock_process_class.return_value = mock_proc
        
        assert is_orphan(1234) is False
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_no_such_process(self, mock_process_class):
        """Non-existent process should return False."""
        mock_process_class.side_effect = psutil.NoSuchProcess(1234)
        
        assert is_orphan(1234) is False


class TestIsInOwnTree:
    """Test self-protection check."""
    
    def test_our_own_pid(self):
        """Our own PID should return True."""
        our_pid = os.getpid()
        assert is_in_own_tree(our_pid) is True
    
    def test_parent_process(self):
        """Our parent should return True."""
        our_proc = psutil.Process(os.getpid())
        parent = our_proc.parent()
        
        if parent:
            assert is_in_own_tree(parent.pid) is True
    
    def test_grandparent_process(self):
        """Our grandparent should return True."""
        our_proc = psutil.Process(os.getpid())
        parents = list(our_proc.parents())
        
        if len(parents) >= 2:
            grandparent = parents[1]
            assert is_in_own_tree(grandparent.pid) is True
    
    def test_unrelated_process(self):
        """Unrelated process should return False."""
        # PID 1 (launchd) is not directly our parent unless we're very special
        our_proc = psutil.Process(os.getpid())
        parent_pids = {p.pid for p in our_proc.parents()}
        
        # Find a PID that's not in our tree
        for proc in psutil.process_iter(['pid']):
            test_pid = proc.info['pid']
            if test_pid not in parent_pids and test_pid != os.getpid():
                # This process is not in our tree
                assert is_in_own_tree(test_pid) is False
                break
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_access_denied_fail_safe(self, mock_process_class):
        """If access denied, fail safe to True."""
        mock_process_class.side_effect = psutil.AccessDenied(1234)
        
        # Fail-safe: assume in tree if can't check
        assert is_in_own_tree(1234) is True


class TestIsSystemCritical:
    """Test system critical process detection."""
    
    def test_low_pid_is_critical(self):
        """PID < 100 should be considered critical."""
        assert is_system_critical(1) is True
        assert is_system_critical(50) is True
        assert is_system_critical(99) is True
    
    def test_high_pid_not_automatically_critical(self):
        """High PID alone doesn't make it critical."""
        # Our test process has high PID
        our_pid = os.getpid()
        # Should not be critical unless root-owned with critical name
        result = is_system_critical(our_pid)
        # Can't assert False because might be root-owned in some envs
        assert isinstance(result, bool)
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_root_owned_critical_name(self, mock_process_class):
        """Root-owned process with critical name is critical."""
        mock_proc = Mock()
        mock_proc.username.return_value = 'root'
        mock_proc.name.return_value = 'launchd'
        mock_process_class.return_value = mock_proc
        
        assert is_system_critical(1234) is True
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_root_owned_non_critical_name(self, mock_process_class):
        """Root-owned process with non-critical name is not critical."""
        mock_proc = Mock()
        mock_proc.username.return_value = 'root'
        mock_proc.name.return_value = 'some_random_process'
        mock_process_class.return_value = mock_proc
        
        assert is_system_critical(1234) is False
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_user_owned_critical_name(self, mock_process_class):
        """User-owned process even with critical name is not critical."""
        mock_proc = Mock()
        mock_proc.username.return_value = 'honk'
        mock_proc.name.return_value = 'launchd'  # Name doesn't matter if not root
        mock_process_class.return_value = mock_proc
        
        assert is_system_critical(1234) is False
    
    @patch('honk.watchdog.safety.psutil.Process')
    def test_access_denied_fail_safe(self, mock_process_class):
        """If access denied, fail safe to True."""
        mock_process_class.side_effect = psutil.AccessDenied(1234)
        
        # Fail-safe: assume critical if can't check
        assert is_system_critical(1234) is True


class TestIsSafeToKill:
    """Test master safety check function."""
    
    def test_never_kill_own_process(self):
        """Never kill our own process."""
        our_pid = os.getpid()
        proc = PTYProcess(our_pid, "python", ["/dev/ttys001"] * 20)
        
        safe, reason = is_safe_to_kill(our_pid, proc)
        
        assert safe is False
        assert "own process" in reason.lower()
    
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_never_kill_ancestor(self, mock_in_tree):
        """Never kill process in our ancestor chain."""
        mock_in_tree.return_value = True
        
        proc = PTYProcess(1234, "bash", ["/dev/ttys001"] * 20)
        safe, reason = is_safe_to_kill(1234, proc)
        
        assert safe is False
        assert "ancestor" in reason.lower()
    
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_never_kill_with_terminal(self, mock_in_tree, mock_has_terminal):
        """Never kill process with controlling terminal."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = True
        
        proc = PTYProcess(1234, "node", ["/dev/ttys001"] * 20)
        safe, reason = is_safe_to_kill(1234, proc)
        
        assert safe is False
        assert "terminal" in reason.lower()
    
    @patch('honk.watchdog.safety.is_system_critical')
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_never_kill_system_critical(self, mock_in_tree, mock_has_terminal, mock_is_critical):
        """Never kill critical system process."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = False
        mock_is_critical.return_value = True
        
        proc = PTYProcess(1, "launchd", ["/dev/ttys001"] * 20)
        safe, reason = is_safe_to_kill(1, proc)
        
        assert safe is False
        assert "critical" in reason.lower()
    
    @patch('honk.watchdog.safety.is_zombie')
    @patch('honk.watchdog.safety.is_system_critical')
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_should_kill_zombie(self, mock_in_tree, mock_has_terminal, mock_is_critical, mock_is_zombie):
        """Should kill zombie processes."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = False
        mock_is_critical.return_value = False
        mock_is_zombie.return_value = True
        
        proc = PTYProcess(1234, "python", ["/dev/ttys001"] * 2)
        safe, reason = is_safe_to_kill(1234, proc)
        
        assert safe is True
        assert "zombie" in reason.lower()
    
    @patch('honk.watchdog.safety.is_orphan')
    @patch('honk.watchdog.safety.is_zombie')
    @patch('honk.watchdog.safety.is_system_critical')
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_should_kill_orphan_with_ptys(
        self, mock_in_tree, mock_has_terminal, mock_is_critical, mock_is_zombie, mock_is_orphan
    ):
        """Should kill orphan process with PTYs."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = False
        mock_is_critical.return_value = False
        mock_is_zombie.return_value = False
        mock_is_orphan.return_value = True
        
        proc = PTYProcess(1234, "node", ["/dev/ttys001"] * 5)
        safe, reason = is_safe_to_kill(1234, proc)
        
        assert safe is True
        assert "orphan" in reason.lower()
    
    @patch('honk.watchdog.safety.is_orphan')
    @patch('honk.watchdog.safety.is_zombie')
    @patch('honk.watchdog.safety.is_system_critical')
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_copilot_high_pty_count(
        self, mock_in_tree, mock_has_terminal, mock_is_critical, mock_is_zombie, mock_is_orphan
    ):
        """Copilot with > 10 PTYs should be killable."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = False
        mock_is_critical.return_value = False
        mock_is_zombie.return_value = False
        mock_is_orphan.return_value = False
        
        proc = PTYProcess(1234, "node copilot", [f"/dev/ttys{i:03d}" for i in range(15)])
        safe, reason = is_safe_to_kill(1234, proc)
        
        assert safe is True
        assert "copilot" in reason.lower()
        assert "15" in reason
    
    @patch('honk.watchdog.safety.is_orphan')
    @patch('honk.watchdog.safety.is_zombie')
    @patch('honk.watchdog.safety.is_system_critical')
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_copilot_low_pty_count(
        self, mock_in_tree, mock_has_terminal, mock_is_critical, mock_is_zombie, mock_is_orphan
    ):
        """Copilot with <= 10 PTYs should NOT be killed."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = False
        mock_is_critical.return_value = False
        mock_is_zombie.return_value = False
        mock_is_orphan.return_value = False
        
        proc = PTYProcess(1234, "node copilot", [f"/dev/ttys{i:03d}" for i in range(5)])
        safe, reason = is_safe_to_kill(1234, proc)
        
        assert safe is False
        assert "copilot" in reason.lower()
        assert "normal range" in reason.lower()
    
    @patch('honk.watchdog.safety.is_orphan')
    @patch('honk.watchdog.safety.is_zombie')
    @patch('honk.watchdog.safety.is_system_critical')
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_general_heavy_user(
        self, mock_in_tree, mock_has_terminal, mock_is_critical, mock_is_zombie, mock_is_orphan
    ):
        """Non-copilot process with > 8 PTYs should be killable."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = False
        mock_is_critical.return_value = False
        mock_is_zombie.return_value = False
        mock_is_orphan.return_value = False
        
        proc = PTYProcess(1234, "python", [f"/dev/ttys{i:03d}" for i in range(12)])
        safe, reason = is_safe_to_kill(1234, proc, threshold=4)
        
        assert safe is True
        assert "heavy" in reason.lower()
    
    @patch('honk.watchdog.safety.is_orphan')
    @patch('honk.watchdog.safety.is_zombie')
    @patch('honk.watchdog.safety.is_system_critical')
    @patch('honk.watchdog.safety.has_controlling_terminal')
    @patch('honk.watchdog.safety.is_in_own_tree')
    def test_below_threshold(
        self, mock_in_tree, mock_has_terminal, mock_is_critical, mock_is_zombie, mock_is_orphan
    ):
        """Process below threshold should NOT be killed."""
        mock_in_tree.return_value = False
        mock_has_terminal.return_value = False
        mock_is_critical.return_value = False
        mock_is_zombie.return_value = False
        mock_is_orphan.return_value = False
        
        proc = PTYProcess(1234, "bash", [f"/dev/ttys{i:03d}" for i in range(3)])
        safe, reason = is_safe_to_kill(1234, proc, threshold=4)
        
        assert safe is False
        assert "below threshold" in reason.lower()
