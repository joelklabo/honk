# AI Agent Configuration

> **⚠️ IMPORTANT:** This file (`docs/agents.md`) is the **SINGLE SOURCE OF TRUTH** for all AI agent instructions.
> 
> The following files are **SYMLINKS** to this file:
> - `AGENTS.md` → `docs/agents.md`
> - `CLAUDE.md` → `docs/agents.md`
> - `GEMINI.md` → `docs/agents.md`
> - `.github/instructions.md` → `docs/agents.md`
>
> **ONLY EDIT THIS FILE** (`docs/agents.md`) when updating AI agent context or instructions.
> Changes here automatically apply to all AI assistants (Agents, Claude, Gemini, GitHub Copilot).

## Project Structure

```
.
├── .github/
│   └── instructions.md -> ../docs/agents.md  (symlink)
├── .gitignore
├── AGENTS.md -> docs/agents.md               (symlink)
├── CLAUDE.md -> docs/agents.md               (symlink)
├── GEMINI.md -> docs/agents.md               (symlink)
├── docs/
│   ├── agents.md                 ← YOU ARE HERE (source of truth)
│   ├── plans/
│   │   └── main.md               ← Main work tracking document
│   ├── references/               # Documentation, research, notes
│   └── README.md
└── tmp/                          # Temporary files (gitignored)
```

## General Guidelines

- Follow project conventions and style
- Reference `docs/` for context
- **Use `docs/plans/main.md` for work tracking**
  - This is the primary document for tasks, progress, decisions, and next steps
  - Update this file as you complete tasks or make progress
  - Document important decisions and their rationale here
- **Use the project's `tmp/` directory** for all temporary files, scratch work, and outputs
  - ⚠️ **DO NOT use `/tmp/` or system temp directories**
  - All temporary files should go in `./tmp/` (relative to project root)
  - This directory is gitignored and safe for any temporary content
  - Examples: logs, cache files, build artifacts, test outputs, scratch files
- Check `docs/plans/` for project planning documents
- Check `docs/references/` for reference documentation

### ⚠️ CRITICAL: CLI Tool Distinction

**`gh` is NOT the same as `copilot`** - These are two completely different CLI tools:

- **`gh`** - Official GitHub CLI for repository/issue/PR management
  - Command: `gh` (e.g., `gh pr list`, `gh issue create`)
  - Purpose: Interact with GitHub API (repos, issues, PRs, workflows, etc.)
  - Install: `brew install gh` or similar
  - Auth: `gh auth login`
  
- **`copilot`** - GitHub Copilot CLI for AI-powered command suggestions
  - Command: `copilot` (standalone, NOT `gh copilot`)
  - Purpose: AI assistance for terminal commands and explanations
  - Install: Separate installation (not part of `gh`)
  - Usage: `copilot suggest`, `copilot explain`

**Common Mistake:**
- ❌ `gh copilot --agent planloop` - This does NOT exist
- ❌ `gh copilot suggest` - Wrong, `copilot` is not a `gh` subcommand
- ✅ `copilot suggest "install git"` - Correct standalone usage
- ✅ `gh pr list` - Correct GitHub CLI usage

**When to use which:**
- Use `gh` for GitHub API operations (repos, issues, PRs, auth)
- Use `copilot` for AI command suggestions and explanations
- These tools do NOT interact with each other

## Project Context

- **Goal:** Honk is an agent-first CLI that standardizes automation flows (doctor packs, auth, tooling). The first shipping tool is `honk demo hello`, which exercises the shared scaffolding.
- **Authoritative spec:** `docs/spec.md` captures the architecture, pinned dependencies, command documentation expectations, and CI workflows. Update it before making structural changes.
- **Work tracking:** `docs/plans/main.md` lists the current tasks, decisions, and blockers. Keep it current whenever you ship meaningful changes.

### Tech Stack

- Python 3.12.2 managed via uv 0.4.20 (`uv run …` is preferred for every command).
- Typer 0.12.3 + Rich 13.7.1 for CLI UX and help output; Textual 0.61.0 is an optional TUI dependency.
- Pydantic 2.8.2 + jsonschema 4.23.0 for result enveloping/introspection.
- HTTPX 0.27.2 + RESPX 0.21.1 for HTTP integrations/mocking.
- Tooling: pytest 8.3.3, pytest-xdist 3.6.1, ruff 0.6.9, mypy 1.11.2, nox 2024.4.15, pre-commit hooks.
- System CLIs: `gh` ≥ 2.58.0, `az` ≥ 2.63.0 (with DevOps extension), Node.js 20.13.1 via Volta when the optional Next.js site comes online.

### Python Environment Standards (MANDATORY)

**⚠️ CRITICAL: Always use `uv` for ALL Python operations in this project.**

**DO:**
```bash
✅ uv run python script.py          # Run Python scripts
✅ uv run pytest                     # Run tests
✅ uv run pytest tests/notes/ -v    # Run specific tests
✅ uv run mypy src/                  # Type checking
✅ uv run ruff check src/            # Linting
✅ uv pip install package            # Install dependencies
✅ uv sync                           # Sync environment
```

**DON'T:**
```bash
❌ python3 script.py                # Wrong - bypasses uv environment
❌ pytest                           # Wrong - might use wrong env
❌ pip install package              # Wrong - installs outside uv
❌ python -m pytest                 # Wrong - not using uv
```

**Why This Matters:**
- Ensures consistent Python version (3.12.2)
- Uses pinned dependencies from `uv.lock`
- Avoids environment conflicts
- Reproducible builds and tests
- Works identically on all machines

**Exception:** The installed `honk` command itself doesn't need `uv run` because it's installed as a tool via `uv tool install`. But for development tasks (testing, linting, scripts), always use `uv run`.

### Architecture Overview

**CLI Structure:**
- **Grammar:** `honk <area> <tool> <action>` - consistent three-level hierarchy
- **Areas:** Top-level namespaces (e.g., `demo`, `auth`, `watchdog`) grouping related tools
- **Plugin System:** Areas register via `entry_points(group="honk.areas")` or namespace scan
- **Module Layout:**
  ```
  src/honk/
  ├── cli.py              # Root Typer app, global options, plugin loader
  ├── result.py           # Result envelope models and exit codes
  ├── registry.py         # Command introspection metadata
  ├── help.py             # JSON help schema generation
  ├── internal/           # Shared systems (doctor, logging)
  │   └── doctor/         # Prerequisite checking framework
  ├── auth/               # Authentication subsystem
  └── tools/<area>/       # Area-specific implementations
      ├── __init__.py     # Area registration (exports register() function)
      └── <tool>.py       # Tool commands (Typer sub-app)
  ```

**Result Envelope Pattern:**
- Every command returns a structured `ResultEnvelope` (JSON schema: `schemas/result.v1.json`)
- Required fields: `version`, `command`, `status`, `changed`, `code`, `summary`, `run_id`, `duration_ms`
- Extended fields: `facts{}` (command output data), `pack_results[]` (doctor checks), `links[]` (docs/resources), `next[]` (suggested follow-up commands)
- Exit codes: `0` (ok), `10` (prereq_failed), `11` (needs_auth), `12` (token_expired), `20` (network), `30` (system), `50` (bug), `60` (rate_limited)
- Humans see Rich-formatted output; agents consume JSON via `--json` flag

**Doctor Packs (Prerequisite System):**
- Framework for checking requirements before command execution
- Built-in packs: `global` (OS, disk, network), `auth-gh[scopes]`, `auth-az[org]`
- Packs declare dependencies (`requires=["global"]`) and emit remediation steps
- Commands call `run_all_packs(plan=plan)` before mutations
- Results included in `pack_results[]` array of result envelope

**Auth Subsystem:**
- Providers: GitHub (`gh` CLI wrapper), Azure DevOps (`az devops` CLI wrapper)
- Token storage: `keyring` library for secure credential management
- Commands: `honk auth <provider> {status,ensure,login,refresh,logout}`
- Auto-upgrade scopes via `gh auth refresh --scopes ...` or `az devops login`
- Expiry warnings when PAT < 7 days remaining

**Introspection System:**
- `honk introspect --json` emits full command catalog (areas, tools, actions, args, prereqs, examples)
- `honk help-json <command>` returns single-command schema
- Registry populated via `register_command(CommandMetadata(...))` calls
- Schema version: `schemas/introspect.v1.json`

### Coding Standards

- Always run commands through `uv run …` (or an activated `.venv` created by uv) to guarantee the locked environment.
- Implement CLI actions with Typer; provide descriptive docstrings, option `help=` text, and examples so `--help`/`--help-json` stay self-documenting.
- Use the shared result envelope helper for every command outcome. Surface prereq/auth problems via `status="prereq_failed"`/`"needs_auth"` and include actionable `next[]` entries.
- All temporary files, logs, or JSON streams belong under `tmp/` (never `/tmp`).
- Update `docs/spec.md` when changing architecture, dependencies, or process expectations, and log the decision in `docs/plans/main.md`.
- Keep lint/type/test suites passing locally (`uv run ruff check`, `uv run mypy`, `uv run pytest`) before sending changes upstream.

### Development Workflow (TDD Cycle)

**ALWAYS follow Test-Driven Development - Test first, implementation second, never the reverse.**

#### Phase 1: Write Failing Test (🔴 RED)

**NEVER write implementation code before the test fails.**

**Test Requirements:**
- Test must be specific to the task
- Test must fail for the right reason (not syntax error)
- Test must be clear and readable
- Test name describes expected behavior

**Python/pytest Pattern:**
```python
def test_feature_specific_behavior():
    """Should do X when Y happens."""
    # Arrange - Set up test conditions
    sut = SystemUnderTest()
    test_input = "example"
    
    # Act - Execute the behavior
    result = sut.perform_action(test_input)
    
    # Assert - Verify expectations
    assert result == expected_value
    assert result.status == "success"
```

**Run test to confirm failure:**
```bash
uv run pytest -k "test_feature_specific_behavior" -v
```

**Verify:**
- ✅ Test runs without syntax errors
- ✅ Test fails with clear error message
- ✅ Failure is for expected reason (feature not implemented)
- ✅ Error message makes sense

**Document the failure output** - you'll compare after implementation.

**Optional but recommended:** Commit the failing test
```bash
git add tests/
git commit -m "test(feature): add failing test for specific behavior

- Tests that [expected behavior]
- Currently fails with: [error message]
- Will implement in next commit

Related to: [Task ID]"
```

#### Phase 2: Implement Solution (✅ GREEN)

**Write MINIMAL code to make the test pass.**

**Principles:**
- Write simplest code that works
- Don't over-engineer or add features not tested
- Follow existing project patterns
- Make test pass, nothing more

**Run test until it passes:**
```bash
uv run pytest -k "test_feature_specific_behavior" -v
```

**If test continues failing after attempts:**
- **Attempt 1**: Debug implementation and test logic
- **Attempt 2**: Try different implementation approach
- **Attempt 3**: Document issue and escalate (see Failure Handling)

#### Phase 3: Refactor (🔵 BLUE)

**Now that test passes, improve code quality:**
- Extract duplicated code into functions/classes
- Improve variable and function naming
- Add comments for complex logic
- Optimize performance if needed
- Check for edge cases and add tests

**CRITICAL: Run tests after EVERY refactor step**
```bash
uv run pytest -k "test_feature" -v  # After each change
```

If test fails during refactor, you broke something - revert and try smaller change.

#### Phase 4: Verify Full Suite

**Run complete test suite to ensure no regressions:**
```bash
uv run pytest  # All tests
uv run pytest --cov=src/honk --cov-report=term-missing  # With coverage
```

**Check:**
- ✅ Your new test passes
- ✅ All existing tests still pass
- ⚠️ If existing tests fail: You broke something - fix it

#### Phase 5: Self-Reflection (🤔 REFLECT)

**Before committing, answer these questions:**

**Code Quality:**
- ✅ Does code follow project style guide? (`uv run ruff check`)
- ✅ Does code pass type checking? (`uv run mypy`)
- ✅ Are variables/functions named clearly?
- ✅ Is code DRY (Don't Repeat Yourself)?
- ✅ Are there magic numbers/strings that should be constants?
- ✅ Is error handling comprehensive?
- ✅ Are complex sections commented?

**Test Quality:**
- ✅ Does test cover happy path?
- ✅ Does test cover edge cases?
- ✅ Does test cover error conditions?
- ✅ Is test readable and maintainable?
- ✅ Will test catch regressions?
- ✅ Are test names descriptive?

**Integration:**
- ✅ Does this work with existing code?
- ✅ Did I break any existing functionality?
- ✅ Are there TODO comments I need to address?
- ✅ Does this follow honk architecture patterns?
- ✅ Does result envelope match schema?

**Documentation:**
- ✅ Are public CLI commands documented with help text?
- ✅ Are docstrings present on public functions?
- ✅ Did I update relevant docs in `docs/` if needed?
- ✅ Should I add learnings to agents.md?

**If ANY answer is NO: Fix before committing.**

#### Phase 6: Commit (💾 COMMIT)

Use **Conventional Commits** format (see Commit Message Standards section).

**Complete example:**
```bash
git add .
git commit -m "feat(release): add commit parser for conventional commits

- Parse commit messages into type/scope/subject/body/footer
- Support breaking change detection (BREAKING CHANGE:)
- Handle multi-line commit bodies correctly
- Add comprehensive error handling for malformed commits

Tests:
- test_parse_conventional_commit: ✅ passes
- test_parse_breaking_change: ✅ passes
- test_parse_multiline_body: ✅ passes
- test_invalid_format_returns_error: ✅ passes
- All existing tests: ✅ pass (48/48)

Implementation approach:
- Used regex for robust parsing
- Followed existing honk result envelope pattern
- Added validation helper functions
- Extracted parsing logic into separate module

Edge cases handled:
- Missing scope (optional)
- Empty commit body
- Multiple BREAKING CHANGE markers
- Invalid commit format

Related to: Task #3 - Release Tool Foundation
Time taken: 2.5 hours
Complexity: Medium"

git push origin main
```

#### Phase 7: Document (📝 DOCUMENT)

**Update agents.md if you learned something valuable:**

Add to "Known Issues & Solutions" section:
```markdown
#### Issue: [Problem description]
**Solution**: [How you fixed it]
**Example**: [Code snippet if helpful]
**When to use**: [Context]
**Time saved**: ~X minutes for next agent
```

**What to document:**
- ✅ Problems that took >30 min to solve
- ✅ Non-obvious errors and their solutions
- ✅ Successful tool/library usage patterns
- ✅ Architecture decisions and rationale
- ✅ Performance optimizations
- ✅ Security patterns discovered
- ✅ Integration quirks with third-party code

**Don't document:**
- ❌ Obvious things (how to write a function)
- ❌ One-off issues unlikely to recur
- ❌ Implementation details (code is self-documenting)
- ❌ Temporary workarounds you plan to fix

#### Phase 8: Update Plan (✏️ UPDATE PLAN)

**Mark task complete in docs/plans/main.md:**

```markdown
## Task: Implement Commit Parser
**Status**: ✅ Done
**Started**: 2025-11-18 10:00 AM
**Completed**: 2025-11-18 12:30 PM
**Assignee**: github-copilot
**Time Taken**: 2.5 hours
**Complexity**: Medium
**Commit**: abc1234 - feat(release): add commit parser

### Implementation Notes:
- Used regex for parsing conventional commit format
- Integrated with existing result envelope pattern
- Added comprehensive error handling
- All tests passing (48/48)

### Challenges Encountered:
- Multi-line body parsing required careful regex
  - Solution: Used re.DOTALL flag
- Breaking change detection across multiple formats
  - Solution: Check both footer and body

### Files Changed:
- src/honk/tools/release/commit_parser.py (new)
- tests/tools/release/test_commit_parser.py (new)

### agents.md Updated: Yes
- Added regex pattern for commit parsing
- Documented re.DOTALL flag usage
```

#### TDD Cycle Summary

```
1. 🔴 RED - Write failing test
   ↓
2. ✅ GREEN - Implement minimum code to pass
   ↓
3. 🔵 BLUE - Refactor (test still passes)
   ↓
4. 🤔 REFLECT - Quality check
   ↓
5. 💾 COMMIT - Conventional commit message
   ↓
6. 📝 DOCUMENT - Update agents.md if learned something
   ↓
7. ✏️ UPDATE PLAN - Mark done in docs/plans/main.md
   ↓
8. 🔁 LOOP - Next task
```

**Remember:** TDD is non-negotiable. Test first, always.

### Failure Handling & Recovery

**When tests keep failing after implementation:**

**Attempt 1 (15-30 min):** Debug normally
- Check test logic is correct
- Check implementation matches test expectations
- Run test in isolation to rule out state pollution
- Add print statements / use debugger
- Check for typos in assertions

**Attempt 2 (30-60 min):** Try different approach
- Re-read task requirements carefully
- Check for similar implementations in codebase
- Search for existing patterns to follow
- Review relevant documentation
- Try alternate algorithm or data structure

**Attempt 3 (Document & Escalate):** Don't spin indefinitely
```markdown
## Task: [Task Name]
**Status**: ⚠️ Blocked
**Attempts**: 3/3
**Time Spent**: 4 hours
**Issue**: Tests keep failing with [specific error]

### What I Tried:
1. [Approach 1] - Failed because [reason]
   - Error: [error message]
   - Hypothesis: [what you thought was wrong]
   
2. [Approach 2] - Failed because [reason]
   - Error: [error message]
   - Hypothesis: [what you thought was wrong]
   
3. [Approach 3] - Failed because [reason]
   - Error: [error message]
   - Hypothesis: [what you thought was wrong]

### Current State:
- Test: `test_feature_behavior` fails with: [error]
- Implementation: [what's working, what's not]
- Test passes: [which parts work]
- Test fails: [which specific assertion fails]

### Relevant Code:
```python
# Test that's failing
def test_feature_behavior():
    result = feature.do_thing()
    assert result == expected  # ← Fails here
```

### Requesting Help:
Need guidance on:
- Should I try different architecture approach?
- Is there a specialist agent who can help? (release-expert, python-testing-expert)
- Should I revise task requirements?
- Am I misunderstanding the expected behavior?
```

**Don't spin indefinitely.** After 3 genuine attempts (not quick tries), escalate.

**When stuck on architecture decisions:**

Pause and ask for architectural guidance rather than implementing incorrectly:
```markdown
## Architectural Decision Needed

Task: [Task Name]
Question: [Specific architectural question]

Options I'm considering:
1. **Option A**: [Description]
   - Pros: [advantages]
   - Cons: [disadvantages]
   - Complexity: Low/Medium/High
   
2. **Option B**: [Description]
   - Pros: [advantages]
   - Cons: [disadvantages]
   - Complexity: Low/Medium/High

Context:
- Existing patterns: [what project already does]
- Performance requirements: [if any]
- Integration points: [what this needs to work with]

My recommendation: Option A because [reasoning]

Should I proceed with Option A, or would you like to discuss?
```

**When task requirements are unclear:**

Don't assume - ask for clarification:
```markdown
## Task Clarification Needed

Task: [Task Name as written in plan]

Ambiguities I've identified:
1. [What's unclear or has multiple interpretations]
2. [Missing requirements or edge case handling]
3. [Unclear acceptance criteria]

Questions:
- Should this handle [edge case]?
- What's expected behavior when [scenario]?
- Are there performance requirements?
- What error conditions should be handled?
- Should this work with [related feature]?

My interpretation: [What I think it means]
Implementation impact: [How interpretation affects code]

Please clarify before I proceed with implementation.
```

### Commit Message Standards

Use **Conventional Commits** format:

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `test:` - Adding/modifying tests
- `refactor:` - Code restructure (no behavior change)
- `docs:` - Documentation only
- `chore:` - Build/tooling changes

**Good commit example:**
```
feat(release): add commit parser for conventional commits

- Parse commit messages into type/scope/subject/body
- Support breaking change detection
- Handle multi-line commit bodies
- Add comprehensive error handling

Tests:
- test_parse_conventional_commit: ✅
- test_parse_with_breaking_change: ✅
- test_invalid_format_handling: ✅
- All existing tests: ✅ pass (45/45)

Implementation:
- Used regex for robust parsing
- Followed existing honk patterns
- Added validation for commit format

Related to: Task #3 - Release Tool Foundation
Time: 2 hours
```

### Task Selection Strategy

**Don't just pick the first incomplete task.** Use smart selection:

1. **Dependency Check**: 
   - ❌ Don't start Task 5 if it depends on incomplete Task 3
   - ✅ Look for "Depends on:", "Blocked by:", or "Requires:" indicators

2. **Value vs Complexity**:
   - 🔥 High Value + Low Complexity → Do first (quick wins)
   - ⚡ High Value + High Complexity → Do after quick wins
   - 📝 Low Value + Low Complexity → Batch together
   - ⚠️ Low Value + High Complexity → Lowest priority

3. **Batch Related Work**: 
   - If tasks 5, 6, 7 share code, implement foundation first
   - Then tackle each specific task
   - Commit per task (not all at once)

4. **Skill Match**:
   - If stuck after 3 attempts, document and escalate
   - Don't spin indefinitely on blockers

### Before Starting Any Task

**Read and understand thoroughly:**
1. Read related code files in project
2. Understand existing patterns (check similar implementations)
3. Review `docs/agents.md` for context
4. Check git history: `git log --oneline --grep="<keyword>"`
5. Look for TODO/FIXME comments: `rg "TODO|FIXME"`

**Ask yourself:**
- What is the actual problem being solved?
- Why does this need implementation?
- What are the edge cases?
- How does this integrate with existing code?
- What could go wrong?

### Testing Best Practices (Python/pytest)

**Test Structure:**
```python
def test_feature_behavior():
    """Should do X when Y happens."""
    # Arrange
    sut = SystemUnderTest()
    
    # Act
    result = sut.perform_action()
    
    # Assert
    assert result == expected_value
```

**Running Tests:**
```bash
# Single test
uv run pytest -k "test_name" -v

# Test file
uv run pytest tests/path/test_file.py -v

# Full suite
uv run pytest

# With coverage
uv run pytest --cov=src/honk --cov-report=term-missing
```

**Test Coverage Expectations:**
- Core logic: >90% coverage
- CLI commands: >80% coverage
- Integration tests: Happy path + error cases
- Contract tests: Validate result envelope schema

### Known Issues & Solutions

*(Add learnings here as you encounter and solve problems)*

#### Issue: --no-color flag doesn't work after subcommand
**Problem**: `honk demo hello --no-color` gives "No such option" error
**Solution**: Global flags must come BEFORE subcommands (standard CLI pattern)
  - ✅ Correct: `honk --no-color demo hello`
  - ❌ Wrong: `honk demo hello --no-color`
**Alternative**: Use environment variable: `NO_COLOR=1 honk demo hello`
**Why**: This is standard CLI behavior (like git, docker, kubectl). Global options always precede subcommands.
**Reference**: See `tmp/task-23-nocolor-resolution.md` for full analysis
**When**: Users expect flags to work anywhere on command line
**Time saved**: ~10 minutes explaining proper CLI syntax

#### Issue: Confusing `gh` with `copilot` CLI tools
**Solution**: `gh` and `copilot` are DIFFERENT tools. `gh` is GitHub CLI for API operations. `copilot` is standalone AI assistant CLI. Commands like `gh copilot` or `gh copilot --agent` do NOT exist.
**Reference**: See `docs/references/cli-tools-reference.md` for complete distinction guide
**When**: Working with GitHub authentication or trying to invoke AI assistance
**Time saved**: ~15 minutes per occurrence

#### Issue: Import errors with new modules
**Solution**: Always add `__init__.py` files and update `pyproject.toml` if adding new packages
**When**: Creating new tool areas or shared utilities

#### Issue: Tests passing locally but failing in CI
**Solution**: Run `uv run pytest` (not just `pytest`) to ensure locked environment
**When**: After adding new dependencies

#### Issue: Typer command not showing in help
**Solution**: Ensure command is registered via `app.command()` and area is loaded in `cli.py`
**When**: Adding new commands to existing areas

#### Issue: Result envelope validation fails
**Solution**: Match schema exactly (`schemas/result.v1.json`). Use helper functions from `result.py`
**When**: Creating new commands or modifying result structure

### Self-Reflection Checklist

**Before every commit, verify:**

**Code Quality:**
- ✅ Follows project style guide (ruff/mypy pass)
- ✅ Variables/functions named clearly
- ✅ No code duplication (DRY principle)
- ✅ No magic numbers/strings (use constants)
- ✅ Comprehensive error handling
- ✅ Docstrings on public functions

**Test Quality:**
- ✅ Tests cover happy path
- ✅ Tests cover edge cases
- ✅ Tests cover error conditions  
- ✅ Tests are readable and maintainable
- ✅ Tests will catch regressions

**Integration:**
- ✅ Works with existing code
- ✅ Didn't break existing functionality (run full test suite)
- ✅ No new TODO/FIXME comments without issue tracking
- ✅ Follows honk architecture patterns (result envelope, doctor packs, etc.)

**Documentation:**
- ✅ Complex sections have comments
- ✅ Public CLI commands have help text
- ✅ Updated relevant docs in `docs/` if needed
- ✅ Added learnings to agents.md if applicable

**If ANY answer is NO: Fix before committing.**

### Adding New Tools (Quick Reference)

When implementing a new tool (e.g., `honk watchdog pty`):

1. **Create area structure** under `src/honk/tools/<area>/`:
   - `__init__.py` - Area registration with `register(app: typer.Typer) -> AreaMetadata`
   - `<tool>.py` - Typer sub-app with commands (actions)
   - `<tool>_<module>.py` - Supporting logic (scanners, parsers, helpers)

2. **Implement commands** following patterns:
   - Call `run_all_packs(plan=plan)` for prerequisite checks
   - Use `auth.ensure()` for authentication when needed
   - Build `ResultEnvelope` with `facts`, `links`, `next` populated
   - Support `--json`, `--plan`, `--no-color` flags
   - Use Rich formatting for human output (panels, tables, status)

3. **Register metadata** for introspection:
   - Call `register_command(CommandMetadata(...))` for each action
   - Include `area`, `tool`, `action`, `full_path`, `description`, `options`, `arguments`, `prereqs`, `examples`

4. **Write tests** mirroring runtime layout:
   - Unit: `tests/tools/<area>/test_<tool>_<module>.py`
   - Integration: `tests/tools/<area>/test_<tool>_integration.py`
   - Contract: `tests/contract/test_<area>_<tool>_contract.py` (schema validation)

5. **Document**:
   - Implementation spec in `docs/references/<tool>-spec.md`
   - User guide in `docs/references/<tool>-guide.md` (optional)
   - Update `docs/plans/main.md` with task tracking
   - Update `docs/spec.md` if new patterns emerge

6. **Verify**:
   - `uv run honk <area> <tool> --help` renders correctly
   - `uv run honk introspect --json` includes new commands
   - All tests pass: `uv run pytest`
   - Linting passes: `uv run ruff check && uv run mypy`

## Important Files & Directories

- **docs/plans/main.md** - Main work tracking document (tasks, progress, decisions)
- **docs/plans/** - Additional project plans, architecture decisions, roadmaps
- **docs/references/** - Reference documentation, research notes
- **docs/agents.md** - This file (AI configuration)
- **tmp/** - Temporary files and scratch work (gitignored)

### Progress Reporting Template

**After completing each task:**

```
📊 Progress Report - Task #X Complete

Task: [Task Name]
Status: ✅ Done
Commit: [commit-hash]
Time: X hours

Test Results:
- New tests added: X
- Tests passing: X/X ✅
- Coverage: XX% → XX% ⬆️/⬇️/➡️

Code Changes:
- Files added: X
- Files modified: X
- Lines added: ~XXX
- Lines removed: ~XX

Quality Checks:
✅ Code follows style guide (ruff/mypy pass)
✅ All tests pass
✅ No linter warnings
✅ agents.md updated (if learned something)
✅ Self-reflection complete
✅ docs/plans/main.md updated

Next Task: #X - [Task Name]
Estimated: X hours
```

### When to Update docs/plans/main.md

**Always update after:**
- Completing a task (mark done with commit hash)
- Starting a new task (mark in progress with timestamp)
- Getting blocked (document issue and attempts)
- Making architectural decisions (document rationale)
- Discovering new requirements (add to backlog)

**Update format in main.md:**
```markdown
## Task: [Task Name]
**Status**: ✅ Done / 🚧 In Progress / ⚠️ Blocked
**Started**: 2025-11-18 10:00 AM
**Completed**: 2025-11-18 12:30 PM (if done)
**Assignee**: [agent name or "next agent"]
**Time Taken**: 2.5 hours
**Complexity**: Low / Medium / High
**Commit**: abc1234 (if done)

### Implementation Notes:
- [Key decisions made]
- [Patterns used]
- [Challenges overcome]

### Files Changed:
- src/honk/... (added/modified)
- tests/... (added/modified)

### agents.md Updated: Yes/No
[If yes, what was added]
```

## Custom Agents

Define custom GitHub Copilot agents below:

### Example Agent

```markdown
---
name: Example Agent
description: A sample custom agent
---

# Agent Instructions

Your instructions here...
```

### Azure CLI Auth Agent

```markdown
---
name: Azure CLI Auth Agent
description: Deep specialist for az CLI + Azure DevOps authentication flows
---

# Agent Instructions

- Reference `docs/references/azure-cli-auth.md` before answering.
- Always describe which credential type fits the user’s scenario (interactive dev, CI, GitHub-hosted runners, Azure resources) and call out security trade-offs.
- When discussing Azure DevOps, detail PAT handling, `AZURE_DEVOPS_EXT_PAT`, `az devops login`, and Entra token acquisition via `az account get-access-token --resource 499b84ac-1321-427f-aa17-267ca6975798`.
- Include remediation checklists for failures (e.g., `AADSTS50076`, missing scopes, expired PAT) and link to the relevant Microsoft Learn articles you rely on.
- Default to automation-friendly advice (device code, non-interactive flows, secure secret storage in keyring/Key Vault) and remind users to rotate secrets.
```

### GitHub CLI Auth Agent

```markdown
---
name: GitHub CLI Auth Agent
description: Expert navigator for gh CLI authentication, scopes, and multi-host setups
---

# Agent Instructions

- Use `docs/references/github-cli-auth.md` as your quick sheet. Reconcile every answer with the `gh auth login/status/refresh/token/logout` manuals you’ve studied.
- Explain how to choose between OAuth browser flow, `--with-token`, and environment-driven auth (`GH_TOKEN`, `GH_ENTERPRISE_TOKEN`, `GH_HOST`). Offer copy-pasteable sequences.
- Advise on scope hygiene using `gh auth refresh --scopes/--remove-scopes`, and mention the minimum (`repo`, `read:org`, `gist`) whenever relevant.
- Coach users on multi-account setups: when to `gh auth switch`, how to isolate credentials via `GH_CONFIG_DIR`, and how to export tokens safely to other tools.
- When tokens must be revoked, list the exact UI path (`Settings → Applications → GitHub CLI`) and caution against leaving secrets in shell history.
```

# planloop Agent Instructions
<!-- PLANLOOP-INSTALLED v2.0 -->

## Goal Prompt
# planloop Goal Prompt

You are preparing instructions for an AI coding agent that will use
`planloop` to implement a project. Respond with:

1. **Summary** – One paragraph that restates the goal, success criteria, and
   notable constraints (platforms, deadlines, CI requirements, stakeholders).
2. **Signals** – Bulleted list of known blockers/risk signals. Include CI or
   lint references when provided. If none exist, write `- None reported`.
3. **Initial Tasks** – Numbered list of commit-sized tasks that follow the
   planloop workflow (TDD, small increments, green tests). Each task should
   include:
   - short imperative title,
   - success definition or exit criteria,
   - obvious dependencies on earlier tasks.
4. **Open Questions** – Any clarifications the agent should raise before
   coding (optional).

Keep the response under 350 words. Use concise Markdown and avoid code unless
the user explicitly asks for scaffolding.


## Handshake
# planloop Handshake

You are an AI coding agent operating under planloop. Follow these rules:

## Core Loop
- Before every action call `planloop status --json` and read `now.reason`.
- If `now.reason == ci_blocker` or references a signal, diagnose/fix it before
  touching planned tasks.
- If `now.reason == task`, work strictly on the referenced task. Apply TDD,
  keep commits small, and ensure tests are green before moving on.
- When all tasks are done and you have a final summary, run
  `planloop update --json` with the results.
- After every status, mention the observed `now.reason` / next suggested task in
  your update so we can track compliance across runs.

## Updates
- Never edit PLAN.md manually; all changes go through `planloop update`.
- Include `last_seen_version` from the previous status output to avoid stale
  writes.
- Valid update payload fields:
  - `tasks`: change status/title for existing IDs.
  - `add_tasks`: new tasks with optional dependencies.
  - `context_notes`, `next_steps`, `artifacts`, `final_summary` when relevant.
- After applying an update, re-run `planloop status` to confirm the next step.

## Locks & Deadlocks
- If status reports `waiting_on_lock`, sleep briefly and retry; do not attempt
  to write until the lock clears.
- If `deadlocked`, inspect signals and recent work log to break the stalemate.
- Check the `lock_queue` output from `planloop status`—it lists pending agents and your queue position. If you are not at `position == 1`, wait until you reach the head of the queue before issuing structural edits and mention that you are pausing so the trace log stays honest.

## Etiquette
- Keep responses concise, reference files/lines precisely, and cite test runs.
- When unsure, add questions to PLAN.md via `context_notes` and pause coding.
- Do not assume hidden state; always trust planloop outputs over memory.

## Signal Handling
- Always close reported CI blocker signals via `planloop alert --close` before editing tasks.
- After closing a blocker, rerun `planloop status` and mention the newly observed `now.reason` in your next update.
- When encountering a signal, record `signal-open` plus the blocker id inside `next_steps` or `context_notes` so the trace log captures the interaction.


## Summary Prompt
# planloop Summary Prompt

Produce the final wrap-up for a session when all tasks and signals are closed.
Include the following sections:

1. **Completion Summary** – 2–3 sentences describing the overall result,
   referencing key features or fixes delivered. Mention the test suite / CI
   status.
2. **Task Outcomes** – Bulleted list highlighting each task ID and whether it
   shipped, was skipped, or changed scope.
3. **Signals Resolved** – Bullets referencing any CI/lint/system signals that
   were opened during the session and how they were addressed.
4. **Risks / Follow-ups** – Items that should become future tasks (if empty,
   write `- None`).

Keep the tone factual and reference file paths or PR numbers when relevant.


## Reuse Template Prompt
# planloop Template Reuse Prompt

You are preparing context so a new planloop session can reuse a past template.
Respond with:

1. **Why this template** – 1–2 sentences describing what makes the referenced
   session a good example (tech stack, workflow style, test strategy).
2. **Key Tasks to Mirror** – Bullet list summarizing 3–5 tasks from the
   template that the next agent should follow, with short rationale for each.
3. **Adjustments Needed** – Bullet list describing what must change to adapt
   the template to the new goal (optional if nothing differs).

Use short Markdown bullets and avoid copying large diffs; the goal is to give
the next agent a crisp recipe inspired by the previous success.

