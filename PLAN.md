# Honk CLI Agent Discoverability Improvements

**Session**: honk-tree-command-implementation  
**Started**: 2025-11-19 08:57 UTC  
**Goal**: Implement `honk tree` command and fix `honk introspect` to enable 100% command discoverability for AI agents

---

## Context

Agent missed `honk watchdog pty` commands during PTY diagnostics session because:
1. `honk introspect` only returns 6/12 commands (50% missing)
2. No visual command hierarchy available
3. No scoped exploration mechanism
4. Cross-references between related commands missing

**Solution**: Implement comprehensive discoverability system with `honk tree` as the centerpiece.

---

## Goals

1. ✅ **Fix `honk introspect`** - Return ALL commands (currently only returns 6/12)
2. ✅ **Implement `honk tree`** - Visual command hierarchy at any scope level
3. ✅ **Add agent onboarding** - `honk agent onboard` command
4. ✅ **Cross-reference system** - Commands suggest related commands
5. ✅ **Command metadata** - Tag commands by capability

---

## Tasks

### Phase 1: Critical Fixes (Priority 1)

#### P1.0.1: Debug why direct commands aren't discovered by introspect
- **Status**: TODO
- **Type**: Debug/Investigation
- **Goal**: Understand why version/info/doctor/introspect commands are missing from discovery
- **Actions**:
  1. Run debug script: `python3 debug_introspect.py`
  2. Check stderr output: `honk introspect 2>&1 | head -20`
  3. Look for debug line: "DEBUG: Discovering from ['honk'], app has X direct commands, Y sub-apps"
  4. Expected: X should be 5+ (version, info, introspect, help-json, doctor)
  5. If X=0 or low, timing issue confirmed
- **Files**: `debug_introspect.py`, `src/honk/internal/command_discovery.py` (line 32)
- **Reference**: `tmp/P1.1-TEST-FAILURE-FIX.md`
- **Dependencies**: None

#### P1.0.2: Fix command discovery to capture direct commands on main app
- **Status**: TODO  
- **Type**: Implementation
- **Goal**: Modify discovery to properly find @app.command() decorators on main app
- **Try these solutions in order**:
  1. **Option 1**: Force Typer compilation in `introspect()` before discovery
     ```python
     _ = app.registered_commands  # Trigger command compilation
     _ = app.registered_groups    # Trigger group compilation
     ```
  2. **Option 2**: Access via Click command object
     ```python
     from typer.main import get_command
     click_app = get_command(app)
     # Use click_app.commands instead
     ```
  3. **Option 3**: Hybrid approach - manual registration + discovery
     - Keep `_register_builtins()` for direct commands
     - Use discovery for sub-apps only
     - Merge both lists in `introspect()`
- **Test After Each**: `.venv/bin/pytest tests/test_introspect_completeness.py::test_introspect_includes_all_top_level_commands -v`
- **Files**: `src/honk/cli.py` (introspect function) OR `src/honk/internal/command_discovery.py`
- **Success**: All 4 tests pass, version/info/doctor/introspect appear in output
- **Dependencies**: P1.0.1

#### P1.0.3: Verify all introspect tests pass and commit the fix
- **Status**: TODO
- **Type**: Verification/Commit
- **Actions**:
  1. Run full test suite: `.venv/bin/pytest tests/test_introspect_completeness.py -v`
  2. Verify all 4 tests pass
  3. Manual verification:
     - `honk introspect --json | jq '.commands | length'` → 45+
     - `honk introspect --json | jq '.commands[] | select(.full_path[1] == "version")'` → exists
     - `honk introspect | grep -E 'version|info|doctor'` → all appear
  4. Remove debug output from `command_discovery.py` line 32-33
  5. Clean up: `rm debug_introspect.py` or move to tmp/
  6. Commit: `git commit --amend --no-edit` OR new commit with proper message
  7. Update PLAN.md: Change P1.1 status to DONE
- **Success**: All tests green, debug removed, committed, P1.1 complete
- **Dependencies**: P1.0.2

#### P1.1: Fix `honk introspect` to recurse into all Typer sub-apps
- **Status**: MOSTLY DONE - 1 Test Failing (see P1.0.1-P1.0.3 to complete)
- **File**: `src/honk/cli.py` (introspect command)
- **Success**: Returns all 12+ top-level commands and nested subcommands
- **Test**: `honk introspect --json | jq '.commands | length'` should be 40+
- **Why**: Currently only returns 6 commands, missing 50% of functionality
- **Implementation**:
  - ✅ Created `src/honk/internal/command_discovery.py` - automatic command discovery
  - ✅ Updated `introspect` command to use `discover_commands_from_app()`
  - ✅ Created test `tests/test_introspect_completeness.py`
  - ✅ Committed to git (commit 63bfb02)
  - ✅ 3/4 tests passing (45 commands discovered, watchdog/pty commands work)
  - ❌ 1 test failing - direct commands (version, info, doctor, introspect) not discovered
  - ⏳ Need to fix discovery of direct commands on main app
- **Next**: Debug why `app.registered_commands` doesn't include direct commands
- **Debug file**: `tmp/P1.1-TEST-FAILURE-FIX.md`

#### P1.2: Implement core `honk tree` command with rich output
- **Status**: TODO
- **Files**: `src/honk/internal/tree_builder.py`, `src/honk/internal/tree_renderer.py`
- **Success**: `honk tree` displays full command hierarchy with emoji categories
- **Test**: Visual inspection shows all commands organized by category
- **Design**: See `/Users/honk/code/planloop/tmp/honk-tree-command-design.md`

#### P1.3: Add `tree` command to all sub-apps
- **Status**: TODO
- **Files**: `src/honk/watchdog/pty_cli.py`, `src/honk/system_cli.py`, etc.
- **Success**: `honk watchdog tree` and `honk watchdog pty tree` work
- **Test**: Scoped trees show only relevant subtrees
- **Pattern**: Every Typer app gets a tree command

#### P1.4: Add JSON output format for `honk tree --json`
- **Status**: TODO
- **File**: `src/honk/internal/tree_renderer.py`
- **Success**: Machine-readable tree structure with metadata
- **Test**: `honk tree --json | jq '.tree.honk.subapps.watchdog'` succeeds

### Phase 2: Enhanced Discovery (Priority 2)

#### P2.1: Implement `honk agent onboard` command
- **Status**: TODO
- **File**: `src/honk/tools/agent/onboard.py`
- **Success**: Returns complete agent primer with command catalog
- **Test**: `honk agent onboard --json` includes workflows and best practices
- **Output**: Command catalog, when to use what, common workflows, best practices

#### P2.2: Add command metadata system
- **Status**: TODO
- **File**: `src/honk/internal/command_metadata.py`
- **Success**: Commands tagged with metadata (tags, capabilities, use_cases)
- **Test**: Metadata appears in `honk tree` and `honk introspect` output
- **Example**: `@command_metadata(tags=["monitoring"], capabilities=["leak-detection"])`

#### P2.3: Implement cross-reference system
- **Status**: TODO
- **Files**: `src/honk/internal/doctor/pty_pack.py`, etc.
- **Success**: `honk doctor` failing on PTY suggests `honk watchdog pty show`
- **Test**: Doctor output includes "next" field with related commands
- **Pattern**: Commands suggest related commands in output

### Phase 3: Advanced Features (Priority 3)

#### P3.1: Add tree command options
- **Status**: TODO
- **File**: `src/honk/internal/tree_renderer.py`
- **Success**: Tree supports `--depth`, `--format`, `--show-options`
- **Test**: All format options work correctly
- **Formats**: rich (default), compact, json, markdown

#### P3.2: Implement `honk discover` command
- **Status**: TODO
- **File**: `src/honk/tools/agent/discover.py`
- **Success**: `honk discover --query "monitor pty"` returns relevant commands
- **Test**: Semantic matching works with various queries
- **Features**: Natural language query, capability-based search

#### P3.3: Generate static command registry
- **Status**: TODO
- **Success**: `honk introspect --json > ~/.honk/command-registry.json`
- **Test**: Registry file is valid and complete
- **Purpose**: Agents can read this file on startup

### Phase 4: Testing & Documentation

#### P4.1: Add comprehensive tests for tree command
- **Status**: TODO
- **File**: `tests/test_tree_command.py`
- **Success**: All tree functionality tested
- **Test**: `pytest tests/test_tree_command.py -v` passes
- **Coverage**: All formats, scoping, options

#### P4.2: Add tests for introspect completeness
- **Status**: TODO
- **File**: `tests/test_introspect.py`
- **Success**: Introspect returns all commands
- **Test**: Assert introspect includes watchdog, system, auth, etc.
- **Coverage**: Verify 100% command coverage

#### P4.3: Update documentation
- **Status**: TODO
- **File**: `README.md`, `docs/agent-guide.md`
- **Success**: Documentation shows tree command usage
- **Test**: Docs include visual tree examples
- **Content**: Agent best practices, discovery workflows

---

## Success Criteria

1. ✅ `honk introspect --json` returns 100% of commands (currently 50%)
2. ✅ `honk tree` provides visual command hierarchy
3. ✅ `honk watchdog tree` and `honk watchdog pty tree` work
4. ✅ `honk agent onboard` command exists
5. ✅ Cross-references between related commands work
6. ✅ All tests pass

---

## Design Documents

- `/Users/honk/code/planloop/tmp/honk-cli-discoverability-proposal.md` (444 lines)
  - Complete analysis and 9 prioritized solutions
  - Testing strategy and success metrics
  - Implementation phases

- `/Users/honk/code/planloop/tmp/honk-tree-command-design.md` (550+ lines)
  - Visual examples for all scoping levels
  - JSON output format specification
  - Implementation details with code examples
  - 4-phase rollout plan

---

## Current Bug Analysis

**Problem**: `honk introspect` only returns 6 commands:
- ✅ Returns: version, info, introspect, help-json, doctor, demo/hello
- ❌ Missing: agent, auth, notes, release, system, watchdog

**Impact**: Agents cannot discover 50% of functionality!

**Root Cause**: Introspect command doesn't recurse into Typer sub-apps (watchdog_app, system_app, auth_app, etc.)

**Fix Location**: `src/honk/cli.py` - introspect command needs to walk all registered sub-apps recursively

---

## Implementation Strategy

### TDD Workflow for Each Task

1. **Write test first** - Define expected behavior
2. **Run test** - Watch it fail (red)
3. **Implement** - Minimal code to pass
4. **Run test** - Verify it passes (green)
5. **Refactor** - Clean up while keeping tests green
6. **Commit** - Single commit per task

### Order of Implementation

1. Start with P1.1 (fix introspect) - Unblocks everything else
2. Then P1.2 (core tree) - Provides foundation
3. Then P1.3 (scoped tree) - Extends pattern
4. Continue through phases in order

### Dependencies

- P1.2, P1.3, P1.4 depend on tree builder infrastructure
- P2.1 can proceed in parallel
- P2.2 enhances P1.2 output
- P2.3 requires P2.2 metadata
- P3.x all enhance existing features
- P4.x validates everything

---

## Notes

- **PTY exhaustion**: We discovered this issue while implementing! System went from 432 → 106 PTYs after cleanup
- **Agent missed commands**: This entire project started because agent couldn't find `honk watchdog pty` commands
- **Tree pattern**: User suggestion to make tree a command (not flag) was brilliant - allows scoping at any level
- **Introspect is critical**: Fix this first - it's the foundation for agent discovery

---

## Session Metadata

- **Repository**: `/Users/honk/code/honk`
- **Python**: Use `.venv/bin/python` for honk development
- **Testing**: `pytest tests/ -v`
- **Linting**: `ruff check src/`
- **Agent**: GitHub Copilot CLI

---

## Next Immediate Steps

1. Fix PTY exhaustion issue (restart terminal session if needed)
2. Start P1.1 - Fix `honk introspect` command
3. Write test for introspect completeness
4. Implement recursive Typer app walking
5. Verify all commands appear in introspect output
6. Commit with message: "fix: Make introspect recurse into all Typer sub-apps (P1.1)"
