# Bash Completion for honk CLI

## Overview

The honk CLI includes a dynamic bash completion system that automatically discovers all commands, subcommands, and options using the `honk introspect --json` command. This means completion works for all current commands and any commands added in the future without manual updates.

## Features

- **Dynamic Command Discovery**: Automatically completes all commands via `honk introspect --json`
- **Intelligent Caching**: Caches introspection data (1 hour TTL) for fast completion
- **Multi-level Command Support**: Completes nested commands like `honk auth gh status`
- **Option Completion**: Completes flags like `--json`, `--help`, `--no-color`, `--plan`
- **Future-Proof**: Works with any new tools added to honk

## Quick Start

### Generate and test completion (temporary)

```bash
# Test completion in current shell (temporary)
eval "$(honk completion generate bash)"

# Now try TAB completion
honk <TAB>
honk demo <TAB>
honk auth gh <TAB>
```

### Install permanently

```bash
# See installation instructions
honk completion install bash

# Follow the instructions to install permanently
```

## Installation

### Option 1: User-level (Recommended)

```bash
# Create completion directory
mkdir -p ~/.local/share/bash-completion/completions

# Generate and save completion script
honk completion generate bash > ~/.local/share/bash-completion/completions/honk

# Restart your shell or source bashrc
source ~/.bashrc
```

### Option 2: System-wide (Requires sudo)

```bash
# Generate and install system-wide
sudo honk completion generate bash > /etc/bash_completion.d/honk

# Restart your shell
```

### Option 3: Direct eval in ~/.bashrc

Add to your `~/.bashrc`:

```bash
# Load honk completion
eval "$(honk completion generate bash)"
```

## How It Works

The completion system works in three stages:

### 1. Introspection Cache

On first TAB press, the completion script:
- Runs `honk introspect --json` to discover all commands
- Caches the result in `~/.cache/honk/introspect.json`
- Refreshes cache automatically after 1 hour

### 2. Command Path Parsing

When you press TAB:
- Parses your current command path (e.g., `honk auth gh`)
- Filters out flags and their values
- Builds a command path for lookup

### 3. Completion Suggestions

Based on the command path:
- **If typing a flag** (`--`): Suggests available options
- **If at command level**: Suggests subcommands
- **If no subcommands**: Falls back to file completion

## Commands

### `honk completion generate [SHELL]`

Generate completion script for the specified shell.

**Arguments:**
- `SHELL`: Shell type (default: `bash`)
  - `bash`: Bash completion (fully implemented)
  - `zsh`: Zsh completion (planned, not yet implemented)

**Examples:**

```bash
# Generate bash completion
honk completion generate bash

# Save to file
honk completion generate bash > /tmp/honk-completion.bash

# Install directly
honk completion generate bash > ~/.local/share/bash-completion/completions/honk
```

### `honk completion install [SHELL]`

Show platform-specific installation instructions.

**Arguments:**
- `SHELL`: Shell type (default: `bash`)

**Examples:**

```bash
# Show bash installation instructions
honk completion install bash

# Show zsh installation instructions (when implemented)
honk completion install zsh
```

### `honk completion doctor`

Diagnose completion installation issues.

Checks:
- Current shell type
- Existence of completion script in standard locations
- bash-completion package availability
- Cache file status and age

**Examples:**

```bash
# Check completion status
honk completion doctor
```

## Troubleshooting

### Completion not working

1. **Check if bash-completion is installed:**

   ```bash
   # macOS
   brew install bash-completion@2
   
   # Ubuntu/Debian
   sudo apt install bash-completion
   ```

2. **Verify completion script is installed:**

   ```bash
   honk completion doctor
   ```

3. **Check if completion is sourced:**

   ```bash
   # Test in new shell
   bash
   honk <TAB>
   ```

4. **Manually test completion script:**

   ```bash
   eval "$(honk completion generate bash)"
   honk <TAB>
   ```

### Completion is slow

The first TAB press builds the cache, which may take 1-2 seconds. Subsequent completions are instant.

To pre-populate the cache:

```bash
mkdir -p ~/.cache/honk
honk introspect --json > ~/.cache/honk/introspect.json
```

### Cache is stale

The cache auto-refreshes after 1 hour. To force refresh:

```bash
rm ~/.cache/honk/introspect.json
# Next TAB press will rebuild
```

### Commands not showing up

If you've added new commands but they don't appear in completion:

```bash
# Clear cache
rm ~/.cache/honk/introspect.json

# Test introspection
honk introspect --json | grep "your-new-command"
```

## Architecture

### Completion Script Structure

```bash
_honk_completion() {
    # 1. Initialize bash completion variables
    local cur prev words cword
    _init_completion || return
    
    # 2. Check/update introspection cache
    local cache_file="~/.cache/honk/introspect.json"
    if cache is old:
        honk introspect --json > cache_file
    
    # 3. Parse current command path from $words
    cmd_path = "honk" + non-flag arguments
    
    # 4. Generate completions
    if completing flag:
        suggest --options from introspect
    else:
        suggest subcommands from introspect
}

complete -F _honk_completion honk
```

### Cache Format

The cache is the output of `honk introspect --json`:

```json
{
  "version": "1.0",
  "commands": [
    {
      "full_path": ["honk", "demo", "hello"],
      "description": "Demo command",
      "options": [
        {"name": "name", "type_hint": "str"},
        {"name": "json", "type_hint": "bool"}
      ]
    }
  ]
}
```

### Performance

- **Cache hit**: <1ms (reads from JSON file)
- **Cache miss**: 100-200ms (runs `honk introspect --json`)
- **Cache TTL**: 1 hour (configurable in script)
- **Cache location**: `~/.cache/honk/introspect.json`

## Future Enhancements

### Planned

- [ ] Zsh completion support
- [ ] Fish completion support
- [ ] PowerShell completion support (Windows)
- [ ] Configurable cache TTL
- [ ] Completion for command arguments (not just subcommands/flags)
- [ ] Context-aware completion (e.g., suggest repos for `honk auth gh`)

### Maybe

- [ ] Completion preview with descriptions
- [ ] Smart suggestions based on usage frequency
- [ ] Tab completion for flag values
- [ ] Completion for environment variables

## Examples

### Basic Usage

```bash
# Complete top-level commands
$ honk <TAB>
agent       auth        completion  demo        doctor
help-json   info        introspect  notes       release
system      version     watchdog

# Complete subcommands
$ honk auth <TAB>
az  ensure-az  ensure-gh  gh

# Complete nested commands
$ honk auth gh <TAB>
login  logout  refresh  status

# Complete flags
$ honk demo hello --<TAB>
--help  --json  --name  --no-color  --plan
```

### Advanced Usage

```bash
# Complete after flags
$ honk demo hello --name Alice --<TAB>
--help  --json  --no-color  --plan

# Complete mixed with paths
$ honk notes save --note-file <TAB>
[file completion]

# Complete with global flags
$ honk --no-color demo <TAB>
hello
```

## Testing

The completion system includes comprehensive tests in `tests/test_completion.py`:

```bash
# Run completion tests
uv run pytest tests/test_completion.py -v

# Test manually
eval "$(honk completion generate bash)"
honk <TAB>
```

## Related Commands

- `honk introspect --json` - Command catalog used by completion
- `honk help-json <command>` - Detailed help for specific command
- `honk --help` - General help and command list
