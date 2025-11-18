"""Doctor pack registry and runner."""
import time
from .pack import DoctorPack, PackResult

_pack_registry: dict[str, DoctorPack] = {}


def register_pack(pack: DoctorPack) -> None:
    """Register a doctor pack."""
    _pack_registry[pack.name] = pack


def get_pack(name: str) -> DoctorPack | None:
    """Get a registered pack by name."""
    return _pack_registry.get(name)


def run_pack(name: str, plan: bool = False) -> PackResult:
    """Run a specific doctor pack.
    
    Args:
        name: Name of the pack to run
        plan: If True, run in plan mode
        
    Returns:
        PackResult from the pack
        
    Raises:
        KeyError: If pack is not found
    """
    pack = get_pack(name)
    if not pack:
        raise KeyError(f"Doctor pack '{name}' not found")
    
    start = time.time()
    result = pack.run(plan=plan)
    
    # Ensure duration is set
    if result.duration_ms == 0:
        result.duration_ms = int((time.time() - start) * 1000)
    
    return result


def run_all_packs(plan: bool = False) -> list[PackResult]:
    """Run all registered doctor packs in dependency order.
    
    Args:
        plan: If True, run in plan mode
        
    Returns:
        List of PackResult from all packs
    """
    results: list[PackResult] = []
    completed: set[str] = set()
    
    def can_run(pack: DoctorPack) -> bool:
        """Check if pack dependencies are satisfied."""
        return all(req in completed for req in pack.requires)
    
    # Simple dependency resolution
    while len(completed) < len(_pack_registry):
        ran_any = False
        for name, pack in _pack_registry.items():
            if name not in completed and can_run(pack):
                result = run_pack(name, plan=plan)
                results.append(result)
                completed.add(name)
                ran_any = True
        
        if not ran_any:
            # Deadlock or circular dependency
            remaining = set(_pack_registry.keys()) - completed
            raise RuntimeError(f"Cannot resolve dependencies for packs: {remaining}")
    
    return results
