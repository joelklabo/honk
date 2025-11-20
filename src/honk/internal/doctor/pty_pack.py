"""PTY diagnostics doctor pack."""

import platform
import subprocess
import time
from typing import Dict, List
from .pack import PackCheck, PackResult


def get_pty_limit() -> int:
    """Get the maximum number of PTYs allowed."""
    try:
        if platform.system() == "Darwin":  # macOS
            result = subprocess.run(
                ["sysctl", "-n", "kern.tty.ptmx_max"],
                capture_output=True,
                text=True,
                timeout=2
            )
            if result.returncode == 0:
                return int(result.stdout.strip())
    except Exception:
        pass
    return 511  # Default macOS limit


def count_active_ptys() -> int:
    """Count active PTY sessions."""
    try:
        result = subprocess.run(
            ["sh", "-c", "ls -1 /dev/ttys* 2>/dev/null | wc -l"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if result.returncode == 0:
            return int(result.stdout.strip())
    except Exception:
        pass
    return 0


def get_pty_processes() -> Dict[int, dict]:
    """Get processes holding PTYs using lsof."""
    processes: Dict[int, dict] = {}
    try:
        result = subprocess.run(
            ["lsof", "-FpcnT"],
            capture_output=True,
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5
        )
        
        current_pid = None
        for line in result.stdout.splitlines():
            if line.startswith("p"):
                current_pid = int(line[1:])
                if current_pid not in processes:
                    processes[current_pid] = {
                        "pid": current_pid,
                        "command": None,
                        "ptys": []
                    }
            elif line.startswith("c") and current_pid:
                processes[current_pid]["command"] = line[1:]
            elif line.startswith("n/dev/ttys") and current_pid:
                processes[current_pid]["ptys"].append(line[1:])
        
        # Filter to only processes with PTYs
        return {pid: p for pid, p in processes.items() if p["ptys"]}
    except Exception:
        return {}


class PTYDoctorPack:
    """PTY system diagnostics pack."""

    name = "pty"
    requires: List[str] = []

    def run(self, plan: bool = False) -> PackResult:
        """Run PTY diagnostics checks."""
        start = time.time()
        checks: List[PackCheck] = []

        # Check 1: PTY limit
        pty_limit = get_pty_limit()
        checks.append(
            PackCheck(
                name="pty_limit",
                passed=True,
                message=f"PTY limit: {pty_limit}"
            )
        )

        # Check 2: Active PTY count
        active_ptys = count_active_ptys()
        utilization = (active_ptys / pty_limit * 100) if pty_limit > 0 else 0
        
        # Thresholds: warn at 80%, critical at 95%
        if utilization >= 95:
            status = "CRITICAL"
            passed = False
            remedy = "Run 'honk doctor fix pty' to clean up PTY leaks"
        elif utilization >= 80:
            status = "WARNING"
            passed = False
            remedy = f"Monitor PTY usage - approaching limit ({active_ptys}/{pty_limit})"
        else:
            status = "OK"
            passed = True
            remedy = None
        
        checks.append(
            PackCheck(
                name="pty_usage",
                passed=passed,
                message=f"PTY usage: {active_ptys}/{pty_limit} ({utilization:.1f}%) - {status}",
                remedy=remedy
            )
        )

        # Check 3: Process count with PTYs
        pty_processes = get_pty_processes()
        process_count = len(pty_processes)
        
        checks.append(
            PackCheck(
                name="pty_processes",
                passed=True,
                message=f"Processes holding PTYs: {process_count}"
            )
        )

        # Check 4: Heavy PTY users
        heavy_users = [
            p for p in pty_processes.values()
            if len(p["ptys"]) > 10
        ]
        
        if heavy_users:
            heavy_user_summary = ", ".join([
                f"{p['command']}({p['pid']}): {len(p['ptys'])} PTYs"
                for p in sorted(heavy_users, key=lambda x: len(x["ptys"]), reverse=True)[:3]
            ])
            checks.append(
                PackCheck(
                    name="heavy_users",
                    passed=False,
                    message=f"Heavy PTY users detected: {heavy_user_summary}",
                    remedy="Investigate processes with excessive PTY usage"
                )
            )
        else:
            checks.append(
                PackCheck(
                    name="heavy_users",
                    passed=True,
                    message="No heavy PTY users detected (>10 PTYs)"
                )
            )

        # Check 5: Suspected leaks (Copilot-related processes)
        leak_candidates = [
            p for p in pty_processes.values()
            if p["command"] and (
                "copilot" in p["command"].lower() or
                "github" in p["command"].lower()
            ) and len(p["ptys"]) > 4
        ]
        
        if leak_candidates:
            leak_summary = ", ".join([
                f"{p['command']}({p['pid']}): {len(p['ptys'])} PTYs"
                for p in sorted(leak_candidates, key=lambda x: len(x["ptys"]), reverse=True)[:3]
            ])
            checks.append(
                PackCheck(
                    name="leak_candidates",
                    passed=False,
                    message=f"Suspected PTY leaks: {leak_summary}",
                    remedy="Run 'honk doctor fix pty --auto' to clean up automatically"
                )
            )
        else:
            checks.append(
                PackCheck(
                    name="leak_candidates",
                    passed=True,
                    message="No suspected PTY leaks detected"
                )
            )

        duration_ms = int((time.time() - start) * 1000)
        all_passed = all(check.passed for check in checks)

        # Build remediation commands
        next_commands = []
        if not all_passed:
            if utilization >= 95:
                next_commands.append("honk doctor fix pty --emergency")
            elif leak_candidates:
                next_commands.append("honk doctor fix pty --auto")
            else:
                next_commands.append("honk system pty  # View detailed PTY usage")

        return PackResult(
            pack=self.name,
            status="ok" if all_passed else "failed",
            duration_ms=duration_ms,
            summary=f"PTY health: {active_ptys}/{pty_limit} ({utilization:.1f}%) - {len(checks)} checks, {sum(1 for c in checks if c.passed)} passed",
            checks=checks,
            next=next_commands
        )


# Create singleton instance
pty_pack = PTYDoctorPack()
