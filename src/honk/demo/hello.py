"""Demo hello command that demonstrates full CLI contract."""

import time
import uuid
from ..result import ResultEnvelope, NextStep, Link


def run_hello(
    name: str = "World", json_output: bool = False, plan: bool = False
) -> ResultEnvelope:
    """Run the hello demo command.

    Args:
        name: Name to greet
        json_output: Output as JSON
        plan: Run in plan mode (dry-run)

    Returns:
        ResultEnvelope with greeting result
    """
    start = time.time()
    run_id = str(uuid.uuid4())

    # In plan mode, show what would happen
    if plan:
        greeting = f"Would greet: {name}"
        changed = False
    else:
        greeting = f"Hello, {name}!"
        changed = False  # This demo doesn't change anything

    duration_ms = int((time.time() - start) * 1000)

    return ResultEnvelope(
        command=["honk", "demo", "hello"],
        status="ok",
        changed=changed,
        code="demo.hello.ok",
        summary=f"Sent greeting to {name}",
        run_id=run_id,
        duration_ms=duration_ms,
        facts={"greeting": greeting, "name": name},
        links=[Link(rel="docs", href="https://example.com/honk/demo/hello")],
        next=[
            NextStep(
                run=["honk", "demo", "hello", "--name", "Agent"],
                summary="Try with a different name",
            )
        ],
    )
