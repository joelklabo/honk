"""Built-in doctor packs."""
import os
import platform
import shutil
import socket
import time
from .pack import PackCheck, PackResult


class GlobalPack:
    """Global system checks pack."""
    
    name = "global"
    requires: list[str] = []
    
    def run(self, plan: bool = False) -> PackResult:
        """Run global system checks."""
        start = time.time()
        checks: list[PackCheck] = []
        
        # Check OS
        os_name = platform.system()
        checks.append(PackCheck(
            name="os",
            passed=True,
            message=f"Operating system: {os_name}"
        ))
        
        # Check architecture
        arch = platform.machine()
        checks.append(PackCheck(
            name="arch",
            passed=True,
            message=f"Architecture: {arch}"
        ))
        
        # Check disk space
        try:
            stat = shutil.disk_usage("/")
            free_gb = stat.free / (1024**3)
            passed = free_gb > 1.0  # At least 1GB free
            checks.append(PackCheck(
                name="disk",
                passed=passed,
                message=f"Free disk space: {free_gb:.2f} GB",
                remedy="Free up disk space" if not passed else None
            ))
        except Exception as e:
            checks.append(PackCheck(
                name="disk",
                passed=False,
                message=f"Could not check disk space: {e}",
                remedy="Ensure disk is accessible"
            ))
        
        # Check network connectivity
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=2)
            checks.append(PackCheck(
                name="network",
                passed=True,
                message="Network connectivity: OK"
            ))
        except Exception:
            checks.append(PackCheck(
                name="network",
                passed=False,
                message="Network connectivity: Failed",
                remedy="Check network connection"
            ))
        
        # Check tmp directory
        tmp_dir = "/tmp" if os.name != "nt" else os.environ.get("TEMP", "C:\\temp")
        try:
            writable = os.access(tmp_dir, os.W_OK)
            checks.append(PackCheck(
                name="tmp_dir",
                passed=writable,
                message=f"Temp directory writable: {tmp_dir}",
                remedy=f"Ensure {tmp_dir} exists and is writable" if not writable else None
            ))
        except Exception as e:
            checks.append(PackCheck(
                name="tmp_dir",
                passed=False,
                message=f"Could not check tmp directory: {e}",
                remedy=f"Ensure {tmp_dir} exists"
            ))
        
        duration_ms = int((time.time() - start) * 1000)
        all_passed = all(check.passed for check in checks)
        
        return PackResult(
            pack=self.name,
            status="ok" if all_passed else "failed",
            duration_ms=duration_ms,
            summary=f"Completed {len(checks)} checks, {sum(1 for c in checks if c.passed)} passed",
            checks=checks,
            next=[] if all_passed else [
                check.remedy for check in checks if not check.passed and check.remedy
            ]
        )


# Create singleton instance
global_pack = GlobalPack()
