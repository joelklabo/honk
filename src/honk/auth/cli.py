"""CLI commands for auth subsystem."""

import sys
import uuid
from typing import Optional
import typer

from ..result import ResultEnvelope, NextStep, EXIT_OK, EXIT_NEEDS_AUTH
from ..ui import print_success, print_error, print_info, print_dim
from .providers.github import GitHubAuthProvider


gh_app = typer.Typer()
az_app = typer.Typer()


def _convert_next_steps(steps: list[str]) -> list[NextStep]:
    """Convert string list to NextStep objects.
    
    Args:
        steps: List of command strings
        
    Returns:
        List of NextStep objects
    """
    next_steps = []
    for step in steps:
        # Parse "Run: command" or just "command"
        if step.startswith("Run: "):
            cmd_str = step[5:]  # Remove "Run: " prefix
        else:
            cmd_str = step
        
        # Split command string into list
        parts = cmd_str.split()
        
        next_steps.append(NextStep(
            run=parts,
            summary=step
        ))
    
    return next_steps


@gh_app.command("status")
def gh_status(
    hostname: Optional[str] = typer.Option(None, "--hostname", help="GitHub hostname (default: github.com)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Check GitHub authentication status."""
    import time
    start_time = time.time()
    
    provider = GitHubAuthProvider()
    result = provider.status(hostname=hostname)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Build result envelope
    status = "ok" if result.success else "needs_auth"
    exit_code = EXIT_OK if result.success else EXIT_NEEDS_AUTH
    
    facts = {
        "auth": {
            "provider": "github",
            "status": result.status.value,
            "hostname": result.metadata.hostname if result.metadata else (hostname or "github.com"),
        }
    }
    
    if result.metadata:
        facts["auth"]["user"] = result.metadata.user
        facts["auth"]["scopes"] = result.metadata.scopes  # type: ignore[assignment]
        facts["auth"]["source"] = result.metadata.source
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "gh", "status"],
        status=status,
        code=f"auth.gh.status.{result.status.value}",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=False,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        if result.success:
            print_success(result.message)
            if result.metadata:
                print_dim(f"  User: {result.metadata.user}")
                print_dim(f"  Hostname: {result.metadata.hostname}")
                if result.metadata.scopes:
                    print_dim(f"  Scopes: {', '.join(result.metadata.scopes)}")
        else:
            print_error(result.message)
            if result.next_steps:
                print_info("Next steps:")
                for step in result.next_steps:
                    print_dim(f"  • {step}")
    
    sys.exit(exit_code)


@gh_app.command("login")
def gh_login(
    hostname: Optional[str] = typer.Option(None, "--hostname", help="GitHub hostname (default: github.com)"),
    scopes: Optional[str] = typer.Option(None, "--scopes", help="Comma-separated OAuth scopes"),
    web: bool = typer.Option(True, "--web/--no-web", help="Use web-based authentication"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Login to GitHub."""
    import time
    start_time = time.time()
    
    provider = GitHubAuthProvider()
    
    # Parse scopes
    scope_list = None
    if scopes:
        scope_list = [s.strip() for s in scopes.split(",")]
    
    result = provider.login(hostname=hostname, scopes=scope_list, web=web)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Build result envelope
    status = "ok" if result.success else "needs_auth"
    exit_code = EXIT_OK if result.success else EXIT_NEEDS_AUTH
    
    facts = {
        "auth": {
            "provider": "github",
            "status": result.status.value,
            "hostname": result.metadata.hostname if result.metadata else (hostname or "github.com"),
        }
    }
    
    if result.metadata:
        facts["auth"]["user"] = result.metadata.user
        facts["auth"]["scopes"] = result.metadata.scopes  # type: ignore[assignment]
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "gh", "login"],
        status=status,
        code=f"auth.gh.login.{result.status.value}",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=result.success,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        if result.success:
            print_success(result.message)
            if result.metadata:
                print_dim(f"  User: {result.metadata.user}")
                print_dim(f"  Scopes: {', '.join(result.metadata.scopes)}")
        else:
            print_error(result.message)
            if result.next_steps:
                print_info("Next steps:")
                for step in result.next_steps:
                    print_dim(f"  • {step}")
    
    sys.exit(exit_code)


@gh_app.command("refresh")
def gh_refresh(
    hostname: Optional[str] = typer.Option(None, "--hostname", help="GitHub hostname (default: github.com)"),
    scopes: Optional[str] = typer.Option(None, "--scopes", help="Comma-separated OAuth scopes to add/refresh"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Refresh GitHub authentication and update scopes."""
    import time
    start_time = time.time()
    
    provider = GitHubAuthProvider()
    
    # Parse scopes
    scope_list = None
    if scopes:
        scope_list = [s.strip() for s in scopes.split(",")]
    
    result = provider.refresh(hostname=hostname, scopes=scope_list)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Build result envelope
    status = "ok" if result.success else "needs_auth"
    exit_code = EXIT_OK if result.success else EXIT_NEEDS_AUTH
    
    facts = {
        "auth": {
            "provider": "github",
            "status": result.status.value,
            "hostname": result.metadata.hostname if result.metadata else (hostname or "github.com"),
        }
    }
    
    if result.metadata:
        facts["auth"]["user"] = result.metadata.user
        facts["auth"]["scopes"] = result.metadata.scopes  # type: ignore[assignment]
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "gh", "refresh"],
        status=status,
        code=f"auth.gh.refresh.{result.status.value}",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=result.success,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        if result.success:
            print_success(result.message)
            if result.metadata:
                print_dim(f"  User: {result.metadata.user}")
                print_dim(f"  Scopes: {', '.join(result.metadata.scopes)}")
        else:
            print_error(result.message)
            if result.next_steps:
                print_info("Next steps:")
                for step in result.next_steps:
                    print_dim(f"  • {step}")
    
    sys.exit(exit_code)


@gh_app.command("logout")
def gh_logout(
    hostname: Optional[str] = typer.Option(None, "--hostname", help="GitHub hostname (default: github.com)"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Logout from GitHub."""
    import time
    start_time = time.time()
    
    provider = GitHubAuthProvider()
    result = provider.logout(hostname=hostname)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Build result envelope
    status = "ok" if result.success else "error"
    exit_code = EXIT_OK if result.success else EXIT_NEEDS_AUTH
    
    facts = {
        "auth": {
            "provider": "github",
            "status": result.status.value,
            "hostname": hostname or "github.com",
        }
    }
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "gh", "logout"],
        status=status,
        code=f"auth.gh.logout.{result.status.value}",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=result.success,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        if result.success:
            print_success(result.message)
        else:
            print_error(result.message)
            if result.next_steps:
                print_info("Next steps:")
                for step in result.next_steps:
                    print_dim(f"  • {step}")
    
    sys.exit(exit_code)


# Azure DevOps commands
@az_app.command("status")
def az_status(
    org: Optional[str] = typer.Option(None, "--org", help="Azure DevOps organization URL"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Check Azure DevOps authentication status."""
    import time
    from .providers.azure import AzureAuthProvider
    
    start_time = time.time()
    
    provider = AzureAuthProvider()
    result = provider.status(org=org)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Build result envelope
    status = "ok" if result.success else "needs_auth"
    exit_code = EXIT_OK if result.success else EXIT_NEEDS_AUTH
    
    facts = {
        "auth": {
            "provider": "azure_devops",
            "status": result.status.value,
            "org": org or "none",
        }
    }
    
    if result.metadata:
        facts["auth"]["user"] = result.metadata.user
        facts["auth"]["scopes"] = result.metadata.scopes  # type: ignore[assignment]
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "az", "status"],
        status=status,
        code=f"auth.az.status.{result.status.value}",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=False,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        if result.success:
            print_success(result.message)
            if result.metadata:
                print_dim(f"  User: {result.metadata.user}")
                print_dim(f"  Org: {org}")
        else:
            print_error(result.message)
            if result.next_steps:
                print_info("Next steps:")
                for step in result.next_steps:
                    print_dim(f"  • {step}")
    
    sys.exit(exit_code)


@az_app.command("login")
def az_login(
    org: Optional[str] = typer.Option(None, "--org", help="Azure DevOps organization URL"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Login to Azure DevOps."""
    import time
    from .providers.azure import AzureAuthProvider
    
    start_time = time.time()
    
    provider = AzureAuthProvider()
    result = provider.login(org=org)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    # Build result envelope
    status = "ok" if result.success else "needs_auth"
    exit_code = EXIT_OK if result.success else EXIT_NEEDS_AUTH
    
    facts = {
        "auth": {
            "provider": "azure_devops",
            "status": result.status.value,
            "org": org or "none",
        }
    }
    
    if result.metadata:
        facts["auth"]["user"] = result.metadata.user
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "az", "login"],
        status=status,
        code=f"auth.az.login.{result.status.value}",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=result.success,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        if result.success:
            print_success(result.message)
            if result.metadata:
                print_dim(f"  User: {result.metadata.user}")
        else:
            print_error(result.message)
            if result.next_steps:
                print_info("Next steps:")
                for step in result.next_steps:
                    print_dim(f"  • {step}")
    
    sys.exit(exit_code)


@az_app.command("refresh")
def az_refresh(
    org: Optional[str] = typer.Option(None, "--org", help="Azure DevOps organization URL"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Refresh Azure DevOps authentication (provides PAT recreation guidance)."""
    import time
    from .providers.azure import AzureAuthProvider
    
    start_time = time.time()
    
    provider = AzureAuthProvider()
    result = provider.refresh(org=org)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    facts = {
        "auth": {
            "provider": "azure_devops",
            "org": org or "none",
        }
    }
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "az", "refresh"],
        status="ok",
        code="auth.az.refresh.guidance",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=False,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        print_info(result.message)
        if result.next_steps:
            print_info("Steps to refresh:")
            for step in result.next_steps:
                print_dim(f"  • {step}")
    
    sys.exit(EXIT_OK)


@az_app.command("logout")
def az_logout(
    org: Optional[str] = typer.Option(None, "--org", help="Azure DevOps organization URL"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
):
    """Logout from Azure DevOps."""
    import time
    from .providers.azure import AzureAuthProvider
    
    start_time = time.time()
    
    provider = AzureAuthProvider()
    result = provider.logout(org=org)
    
    duration_ms = int((time.time() - start_time) * 1000)
    
    facts = {
        "auth": {
            "provider": "azure_devops",
            "status": result.status.value,
            "org": org or "none",
        }
    }
    
    envelope = ResultEnvelope(
        command=["honk", "auth", "az", "logout"],
        status="ok" if result.success else "error",
        code=f"auth.az.logout.{result.status.value}",
        summary=result.message,
        run_id=str(uuid.uuid4()),
        duration_ms=duration_ms,
        changed=result.success,
        facts=facts,
        next=_convert_next_steps(result.next_steps)
    )
    
    if json_output:
        print(envelope.model_dump_json(indent=2))
    else:
        if result.success:
            print_success(result.message)
        else:
            print_error(result.message)
        if result.next_steps:
            print_info("Notes:")
            for step in result.next_steps:
                print_dim(f"  • {step}")
    
    sys.exit(EXIT_OK if result.success else EXIT_NEEDS_AUTH)
