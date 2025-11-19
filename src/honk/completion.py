"""Bash completion generation for honk CLI."""

import sys
import typer
from .ui import console, print_success, print_info, print_dim

completion_app = typer.Typer(help="Shell completion management")


def _generate_bash_completion() -> str:
    """Generate bash completion script that uses introspect."""
    return '''#!/bin/bash
# Bash completion for honk CLI
# Generated dynamically using 'honk introspect --json'

_honk_completion() {
    local cur prev words cword
    _init_completion || return

    # Cache introspection data for performance
    local cache_file="${XDG_CACHE_HOME:-$HOME/.cache}/honk/introspect.json"
    local cache_max_age=3600  # 1 hour

    # Update cache if missing or old
    if [[ ! -f "$cache_file" ]] || [[ $(find "$cache_file" -mmin +60 2>/dev/null) ]]; then
        mkdir -p "$(dirname "$cache_file")"
        honk introspect --json > "$cache_file" 2>/dev/null || return
    fi

    # Parse command structure from current position
    local honk_idx=0
    for ((i=0; i < ${#words[@]}; i++)); do
        if [[ "${words[i]}" == "honk" ]]; then
            honk_idx=$i
            break
        fi
    done

    # Build current command path (honk + args before cursor, excluding flags)
    local cmd_path="honk"
    local arg_count=0
    for ((i=honk_idx+1; i < cword; i++)); do
        local word="${words[i]}"
        # Skip flags and their values
        if [[ "$word" == -* ]]; then
            # Skip flag
            if [[ "$word" == --* ]] && [[ "$word" == *=* ]]; then
                # --flag=value format, no next word to skip
                continue
            fi
            # Check if next word is a value (not starting with -)
            if [[ $((i+1)) -lt ${#words[@]} ]] && [[ "${words[i+1]}" != -* ]]; then
                ((i++))  # Skip the value too
            fi
            continue
        fi
        cmd_path="$cmd_path $word"
        ((arg_count++))
    done

    # If completing a flag or after a flag
    if [[ "$cur" == -* ]]; then
        # Complete common flags for all commands
        local flags="--help --json --no-color --plan --version"
        
        # Add command-specific flags from introspect
        local cmd_flags=$(jq -r --arg path "$cmd_path" '
            .commands[] | 
            select(.full_path | join(" ") | startswith($path)) | 
            .options[]? // empty | 
            "--" + .name
        ' "$cache_file" 2>/dev/null | sort -u)
        
        flags="$flags $cmd_flags"
        COMPREPLY=($(compgen -W "$flags" -- "$cur"))
        return
    fi

    # Get available subcommands at current level
    local subcommands=$(jq -r --arg path "$cmd_path" '
        .commands[] | 
        select(.full_path | join(" ") | startswith($path)) | 
        .full_path | 
        join(" ") | 
        sub($path + " "; "") | 
        split(" ")[0] // empty
    ' "$cache_file" 2>/dev/null | sort -u)

    # Provide completions
    if [[ -n "$subcommands" ]]; then
        COMPREPLY=($(compgen -W "$subcommands" -- "$cur"))
    else
        # Fall back to file completion if no subcommands
        _filedir
    fi
}

# Register completion
complete -F _honk_completion honk
'''


def _generate_zsh_completion() -> str:
    """Generate zsh completion script (future implementation)."""
    return '''#compdef honk
# Zsh completion for honk CLI
# TODO: Implement zsh completion using honk introspect --json

_honk() {
    local -a commands
    commands=(
        'version:Show version information'
        'info:Show CLI information'
        'introspect:Emit command catalog'
        'doctor:Check prerequisites'
        'completion:Shell completion management'
    )
    
    _describe 'command' commands
}

_honk "$@"
'''


@completion_app.command("generate")
def generate(
    shell: str = typer.Argument("bash", help="Shell type (bash, zsh)"),
):
    """Generate shell completion script.
    
    The completion script dynamically discovers commands using 'honk introspect --json'
    and caches the results for performance.
    
    Examples:
    
        # Generate bash completion
        honk completion generate bash > /tmp/honk-completion.bash
        
        # Install to user completion directory
        honk completion generate bash > ~/.local/share/bash-completion/completions/honk
        
        # Or source directly in ~/.bashrc
        eval "$(honk completion generate bash)"
    """
    if shell == "bash":
        print(_generate_bash_completion())
    elif shell == "zsh":
        print(_generate_zsh_completion())
    else:
        print(f"Error: Unsupported shell '{shell}'. Supported: bash, zsh", file=sys.stderr)
        raise typer.Exit(1)


@completion_app.command("install")
def install(
    shell: str = typer.Argument("bash", help="Shell type (bash, zsh)"),
):
    """Show instructions for installing shell completion.
    
    This command provides platform-specific instructions for installing
    the completion script permanently.
    """
    if shell == "bash":
        console.print("[bold]Installing Bash Completion for honk[/bold]\n")
        
        print_info("Option 1: User-level installation (recommended)")
        console.print("  1. Generate completion script:")
        print_dim("     mkdir -p ~/.local/share/bash-completion/completions")
        print_dim("     honk completion generate bash > ~/.local/share/bash-completion/completions/honk")
        console.print("  2. Restart your shell or run:")
        print_dim("     source ~/.bashrc")
        
        console.print("\n")
        print_info("Option 2: System-wide installation (requires sudo)")
        console.print("  1. Generate completion script:")
        print_dim("     sudo honk completion generate bash > /etc/bash_completion.d/honk")
        console.print("  2. Restart your shell")
        
        console.print("\n")
        print_info("Option 3: Direct eval (temporary, for testing)")
        console.print("  Add to ~/.bashrc:")
        print_dim('     eval "$(honk completion generate bash)"')
        
        console.print("\n")
        print_success("After installation, completion will work automatically:")
        console.print("  $ honk <TAB>")
        console.print("  $ honk demo <TAB>")
        console.print("  $ honk auth gh <TAB>")
        
    elif shell == "zsh":
        console.print("[bold]Installing Zsh Completion for honk[/bold]\n")
        
        print_info("User-level installation:")
        console.print("  1. Generate completion script:")
        print_dim("     mkdir -p ~/.zsh/completion")
        print_dim("     honk completion generate zsh > ~/.zsh/completion/_honk")
        console.print("  2. Add to ~/.zshrc (if not already present):")
        print_dim("     fpath=(~/.zsh/completion $fpath)")
        print_dim("     autoload -Uz compinit && compinit")
        console.print("  3. Restart your shell")
        
        console.print("\n")
        print_info("Note: Zsh completion is not fully implemented yet.")
        
    else:
        print(f"Error: Unsupported shell '{shell}'. Supported: bash, zsh", file=sys.stderr)
        raise typer.Exit(1)


@completion_app.command("doctor")
def doctor():
    """Check if completion is installed and working.
    
    This command helps diagnose completion installation issues.
    """
    import os
    import subprocess
    from pathlib import Path
    
    console.print("[bold]Completion Installation Status[/bold]\n")
    
    # Detect current shell
    shell = os.environ.get("SHELL", "unknown")
    shell_name = Path(shell).name if shell != "unknown" else "unknown"
    
    print_info(f"Current shell: {shell_name}")
    
    if shell_name == "bash":
        # Check for bash-completion package
        completion_paths = [
            Path.home() / ".local/share/bash-completion/completions/honk",
            Path("/etc/bash_completion.d/honk"),
            Path("/usr/share/bash-completion/completions/honk"),
        ]
        
        found_completion = False
        for path in completion_paths:
            if path.exists():
                print_success(f"Found completion script: {path}")
                found_completion = True
                
        if not found_completion:
            console.print("  ⚠️  No completion script found")
            console.print("     Run: honk completion install bash")
        
        # Check if bash-completion is available
        try:
            result = subprocess.run(
                ["bash", "-c", "type _init_completion"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                print_success("bash-completion package is installed")
            else:
                console.print("  ⚠️  bash-completion package not found")
                console.print("     Install with: brew install bash-completion@2  (macOS)")
                console.print("                   apt install bash-completion      (Ubuntu/Debian)")
        except Exception as e:
            console.print(f"  ⚠️  Could not check bash-completion: {e}")
        
        # Check cache
        cache_file = Path.home() / ".cache/honk/introspect.json"
        if cache_file.exists():
            print_success(f"Cache exists: {cache_file}")
            import time
            age_seconds = time.time() - cache_file.stat().st_mtime
            age_minutes = int(age_seconds / 60)
            console.print(f"     Cache age: {age_minutes} minutes")
        else:
            console.print(f"  ℹ️  Cache will be created on first completion: {cache_file}")
            
    elif shell_name == "zsh":
        console.print("  ℹ️  Zsh completion support is planned but not yet implemented")
        console.print("     Track progress at: [link]https://github.com/honk/honk[/link]")
    else:
        console.print(f"  ⚠️  Unknown or unsupported shell: {shell_name}")
    
    console.print("\n")
    print_info("Test completion manually:")
    console.print("  1. Source completion in current shell:")
    print_dim('     eval "$(honk completion generate bash)"')
    console.print("  2. Test with TAB:")
    print_dim("     honk <TAB>")
    print_dim("     honk demo <TAB>")
