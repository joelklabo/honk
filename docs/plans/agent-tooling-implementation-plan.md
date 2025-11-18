# Agent & Prompt Tooling - Implementation Plan for Planloop

**Status:** Ready for Implementation  
**Created:** 2025-11-18  
**Based On:** `agent-and-prompt-tooling-spec.md` (Proposal C)  
**Executor:** planloop  
**Target:** Full implementation of `honk agent` tool with research agent memory system

---

## Executive Summary

Implement `honk agent` tool to create, validate, test, and manage GitHub Copilot CLI custom agents. This includes building infrastructure for the research agent's self-improvement memory system.

**Key Enhancement:** The research agent template will include persistent memory (sessions, strategies, knowledge base) enabling continuous self-improvement over time.

---

## Implementation Phases

### Phase 1: Core Foundation & Memory System (Week 1)
**Goal:** Basic agent creation, validation, and memory infrastructure

#### Tasks:
1. **Module Structure Setup**
   - Create `src/honk/tools/agent/` directory structure
   - Set up area registration (`__init__.py`)
   - Create sub-apps for scaffold, validate, test, etc.

2. **Shared Infrastructure - Validation**
   - Create `src/honk/internal/validation/` module
   - Implement YAML frontmatter validator
   - Create `schemas/agent.v1.json` (see Appendix C in spec)
   - Add unit tests for validator

3. **Shared Infrastructure - Memory System**
   - Create `src/honk/internal/memory/` module for research agent memory
   - Implement `SessionRecorder` class (records research sessions)
   - Implement `StrategyManager` class (tracks what works/doesn't)
   - Implement `KnowledgeBase` class (reusable insights)
   - Create memory directory structure: `~/.copilot/research-memory/`
     - `sessions.json` - All past research sessions
     - `strategies.json` - Successful/failed patterns
     - `knowledge-base.json` - Topic-specific insights
   - Add JSON schemas for memory structures

4. **Command: `honk agent validate`**
   - Implement validation command
   - Support `--all` flag (validate all agents)
   - Support `--strict` flag (extra checks)
   - Rich output formatting (errors, warnings, success)
   - Return result envelope

5. **Testing**
   - Unit tests for YAML validator
   - Unit tests for memory system
   - Integration tests for validate command

**Deliverables:**
- ✅ Can validate agent YAML frontmatter
- ✅ Memory system infrastructure in place
- ✅ All tests passing

---

### Phase 2: Agent Scaffolding & Templates (Week 1-2)
**Goal:** Generate new agents from templates

#### Tasks:
6. **Shared Infrastructure - Template Engine**
   - Create `src/honk/internal/templates/` module
   - Implement template rendering with variable substitution
   - Support placeholders: `{{AGENT_NAME}}`, `{{DESCRIPTION}}`, `{{TOOLS}}`
   - Add template validation

7. **Built-in Templates**
   - Create `src/honk/tools/agent/templates/` directory
   - Implement 7 built-in templates:
     1. `research.agent.md` - **WITH MEMORY SYSTEM** (self-improving research agent)
     2. `test-writer.agent.md` - Test generation specialist
     3. `code-reviewer.agent.md` - Code review assistant
     4. `documentation.agent.md` - Documentation writer
     5. `refactor.agent.md` - Refactoring specialist
     6. `debug.agent.md` - Debugging assistant
     7. `architect.agent.md` - Architecture designer
   - Each template has proper YAML frontmatter and instructions

8. **Research Agent Template - Memory Integration**
   - Implement full research agent instructions (from user-provided spec)
   - Add memory hooks:
     - **Step 0:** Check past sessions before starting research
     - **Session Recording:** After completing research
     - **Strategy Learning:** Update strategies database
     - **Meta-Reflection:** Analyze own performance
   - Include memory usage examples in instructions

9. **Command: `honk agent scaffold create`**
   - Interactive mode (prompts for details)
   - Quick mode (CLI flags: `--name`, `--description`, `--tools`, `--location`, `--template`)
   - Template selection
   - Location selection (project/.github/agents, org, user/~/.copilot/agents)
   - Validate before writing
   - Git staging (if applicable)
   - Return result envelope with `facts`, `links`, `next`

10. **Command: `honk agent template list|show|add`**
    - List: Show all available templates (built-in + custom)
    - Show: Display template content with placeholders
    - Add: Save existing agent as reusable template
    - Support custom templates in `~/.copilot/honk/agent-templates/`

11. **Testing**
    - Unit tests for template engine
    - Integration tests for scaffold command
    - Validate all built-in templates
    - Test custom template addition

**Deliverables:**
- ✅ Can create new agents from templates
- ✅ Research agent template includes full memory system
- ✅ Template management commands working
- ✅ All tests passing

---

### Phase 3: Testing & Integration (Week 2)
**Goal:** Test agents programmatically, integrate with Copilot CLI

#### Tasks:
12. **Shared Infrastructure - Copilot CLI Wrapper**
    - Create `src/honk/internal/copilot/` module
    - Implement `CopilotCLI` class
    - Methods:
      - `query(prompt, agent=None)` - One-shot query
      - `agent_exists(name)` - Check if agent file exists
      - `list_agents(location=None)` - List available agents
      - `validate_agent(name)` - Check agent is valid
    - Handle authentication via existing `honk auth gh` system
    - Error handling and retries
    - Parse Copilot CLI outputs

13. **Command: `honk agent test`**
    - Interactive mode: Launch `gh copilot --agent <name>`
    - One-shot mode: `--prompt "text"` flag
    - Test suite mode: `--suite tests/file.yml` flag
    - Create test suite YAML schema (`schemas/agent-test-suite.v1.json`)
    - Capture test results (timing, errors, quality assessment)
    - Save test logs to `tmp/agent-tests/`
    - Return result envelope with test summary

14. **Command: `honk agent list`**
    - Scan agent directories (project, org, user)
    - Parse agent frontmatter
    - Display in table format (Rich tables)
    - Support `--location` filter
    - Support `--verbose` flag (show more details)
    - Return result envelope with agent metadata

15. **Testing**
    - Unit tests for Copilot CLI wrapper (with mocks)
    - Integration tests for test command (if gh CLI available)
    - Integration tests for list command
    - Create sample test suites

**Deliverables:**
- ✅ Can test agents with Copilot CLI
- ✅ Can list available agents
- ✅ Copilot integration working
- ✅ All tests passing

---

### Phase 4: Refinement & Publishing (Week 3)
**Goal:** Improve and share agents

#### Tasks:
16. **Shared Infrastructure - Prompt Library**
    - Create `src/honk/internal/prompts/` module
    - Implement `PromptLibrary` class
    - Methods:
      - `get(name)` - Load prompt
      - `save(name, content, metadata)` - Save refined prompt
      - `list(category=None)` - List available prompts
    - Built-in prompts in `src/honk/internal/prompts/library/`
    - User prompts in `~/.copilot/honk/prompts/` (symlinked)

17. **Command: `honk agent refine`**
    - Interactive mode: Ask questions, generate suggestions
    - Guided mode: `--from-test-results` flag (auto-improve based on failures)
    - Quick mode: `--add-example` flag
    - Use Copilot CLI one-shot query to generate improvement suggestions
    - Show diff preview (before/after)
    - Create backup before applying changes
    - Re-validate after refinement
    - Return result envelope with changes

18. **Command: `honk agent publish`**
    - Commit mode: Stage and commit agent file
    - Org mode: `--to-org` flag (copy to org location, create PR)
    - Export mode: `--export` flag (create standalone shareable file)
    - Validate before publishing
    - Return result envelope with publish status

19. **Memory System Integration - Research Agent**
    - Update research agent template to use memory system
    - Add memory initialization on first use
    - Add session recording helpers
    - Add strategy update helpers
    - Document memory system in agent instructions

20. **Testing**
    - Unit tests for prompt library
    - Integration tests for refine command
    - Integration tests for publish command
    - Contract tests for all commands
    - Test memory system with sample sessions

**Deliverables:**
- ✅ Can refine agents iteratively
- ✅ Can publish agents to team/org
- ✅ Prompt library working
- ✅ Research agent memory system integrated
- ✅ All tests passing

---

### Phase 5: Polish & Release (Week 3-4)
**Goal:** Production-ready release

#### Tasks:
21. **Introspection & Help**
    - Add `--help-json` support for all commands
    - Register commands in registry (`src/honk/registry.py`)
    - Add command metadata (area, tool, action, description, options, examples)
    - Implement `honk introspect` integration

22. **Result Envelopes**
    - Ensure all commands return proper `ResultEnvelope`
    - Include `facts`, `links`, `next` for all commands
    - Implement `--json` output flag
    - Test JSON schema validation (`schemas/result.v1.json`)

23. **Doctor Pack Integration**
    - Create `agent-prerequisites` doctor pack
    - Check for `gh` CLI availability
    - Check for GitHub authentication
    - Check for agent directory permissions
    - Integrate with `run_all_packs()` for commands that need it

24. **Documentation**
    - Create `docs/references/agent-tool-spec.md` (technical spec)
    - Create `docs/references/agent-tool-guide.md` (user guide)
    - Add examples to each command's help text
    - Update `docs/spec.md` with agent tool architecture
    - Update `docs/plans/main.md` with completion status

25. **Full Test Suite**
    - Run all unit tests: `uv run pytest tests/tools/agent/`
    - Run all integration tests: `uv run pytest tests/tools/agent/test_*_integration.py`
    - Run contract tests: `uv run pytest tests/contract/test_agent_contract.py`
    - Run linting: `uv run ruff check src/honk/tools/agent/`
    - Run type checking: `uv run mypy src/honk/tools/agent/`

26. **Tutorial & Examples**
    - Create tutorial: "Creating Your First Custom Agent"
    - Create example: "Research Agent Workflow"
    - Create example: "Test-Writer Agent Workflow"
    - Add to `docs/tutorials/` directory

27. **Optional: Demo & Announcement**
    - Record demo video
    - Write release notes
    - Prepare announcement

**Deliverables:**
- ✅ Shippable `honk agent` tool
- ✅ Full documentation
- ✅ All tests passing (100% coverage goal)
- ✅ Ready for production use

---

## File Structure

```
src/honk/
├── tools/
│   └── agent/
│       ├── __init__.py                  # Area registration
│       ├── scaffold.py                  # honk agent scaffold create
│       ├── validate.py                  # honk agent validate
│       ├── test.py                      # honk agent test
│       ├── refine.py                    # honk agent refine
│       ├── publish.py                   # honk agent publish
│       ├── template.py                  # honk agent template list|show|add
│       ├── list_agents.py               # honk agent list
│       └── templates/                   # Built-in templates
│           ├── research.agent.md        # Research agent (with memory)
│           ├── test-writer.agent.md
│           ├── code-reviewer.agent.md
│           ├── documentation.agent.md
│           ├── refactor.agent.md
│           ├── debug.agent.md
│           └── architect.agent.md
├── internal/
│   ├── validation/
│   │   ├── __init__.py
│   │   └── yaml_validator.py           # YAML frontmatter validator
│   ├── templates/
│   │   ├── __init__.py
│   │   └── engine.py                   # Template rendering
│   ├── copilot/
│   │   ├── __init__.py
│   │   └── cli.py                      # Copilot CLI wrapper
│   ├── prompts/
│   │   ├── __init__.py
│   │   ├── manager.py                  # Prompt library
│   │   └── library/                    # Built-in prompts
│   │       ├── research.md
│   │       ├── code-review.md
│   │       └── refactoring.md
│   └── memory/
│       ├── __init__.py
│       ├── session_recorder.py         # Session recording
│       ├── strategy_manager.py         # Strategy learning
│       └── knowledge_base.py           # Knowledge management
├── schemas/
│   ├── agent.v1.json                   # Agent YAML schema
│   ├── agent-test-suite.v1.json        # Test suite schema
│   ├── research-session.v1.json        # Research session schema
│   └── research-strategy.v1.json       # Research strategy schema
└── tests/
    ├── tools/
    │   └── agent/
    │       ├── test_validate.py
    │       ├── test_scaffold.py
    │       ├── test_test.py
    │       ├── test_refine.py
    │       ├── test_publish.py
    │       ├── test_template.py
    │       ├── test_list.py
    │       └── test_agent_integration.py
    ├── internal/
    │   ├── test_yaml_validator.py
    │   ├── test_template_engine.py
    │   ├── test_copilot_cli.py
    │   ├── test_prompt_library.py
    │   └── test_memory_system.py
    └── contract/
        └── test_agent_contract.py
```

**User Directories Created:**
```
~/.copilot/
├── agents/                              # User's personal agents
├── research-memory/                     # Research agent memory
│   ├── sessions.json                    # Past research sessions
│   ├── strategies.json                  # Successful/failed patterns
│   └── knowledge-base.json              # Reusable insights
└── honk/
    ├── agent-templates/                 # Custom agent templates
    └── prompts/                         # User's prompt library
```

**Project Directories:**
```
.github/
├── agents/                              # Project-specific agents
└── prompts/                             # Project-specific prompts
```

---

## Success Criteria

### Phase 1 Complete When:
- ✅ `honk agent validate` works for any agent file
- ✅ Memory system stores and retrieves sessions/strategies
- ✅ All unit tests pass

### Phase 2 Complete When:
- ✅ `honk agent scaffold create` generates valid agent files
- ✅ 7 built-in templates available and tested
- ✅ Research agent template includes full memory system
- ✅ Template management commands work

### Phase 3 Complete When:
- ✅ `honk agent test` can run agents via Copilot CLI
- ✅ `honk agent list` shows all available agents
- ✅ Copilot CLI integration functional

### Phase 4 Complete When:
- ✅ `honk agent refine` can improve agents iteratively
- ✅ `honk agent publish` can share agents to team/org
- ✅ Research agent memory system fully integrated
- ✅ Prompt library functional

### Phase 5 Complete When:
- ✅ All commands return proper result envelopes
- ✅ All commands support `--help-json` and `--json`
- ✅ Full test suite passes (unit, integration, contract)
- ✅ Documentation complete
- ✅ Ready for production use

---

## Testing Strategy

### Unit Tests
- **Validation:** Test YAML parsing, schema validation, error messages
- **Templates:** Test rendering, variable substitution, validation
- **Copilot CLI:** Test wrapper with mocked subprocess calls
- **Memory System:** Test session recording, strategy updates, knowledge base
- **Prompt Library:** Test save, load, list operations

### Integration Tests
- **Scaffold:** Create agents, validate files, check git staging
- **Validate:** Run against real agent files
- **Test:** Run agents via Copilot CLI (if available, else skip)
- **List:** Scan real directories, parse frontmatter
- **Refine:** Apply changes, validate diffs
- **Publish:** Commit, export, test outputs

### Contract Tests
- **Result Envelopes:** Validate all commands return proper JSON schema
- **Introspection:** Validate `--help-json` output schema
- **Agent Files:** Validate generated agents against schema

### Manual Testing
- Create agent from scratch using interactive mode
- Test agent with Copilot CLI
- Refine agent based on test results
- Publish agent to team

---

## Dependencies

### Existing Honk Infrastructure (Reuse)
- ✅ `honk.result.ResultEnvelope` - Result enveloping
- ✅ `honk.registry.register_command()` - Command registration
- ✅ `honk.internal.doctor` - Prerequisite checking
- ✅ `honk.auth.gh` - GitHub authentication
- ✅ Typer + Rich - CLI framework

### New Dependencies (Check pyproject.toml)
- ✅ `jsonschema` - Already in dependencies
- ✅ `pyyaml` - Likely already in dependencies
- ⚠️ Check: `jinja2` - For template engine (if not present, add)

### External Tools Required
- ✅ `gh` CLI - Already required by Honk
- ✅ GitHub Copilot subscription - Assumed available

---

## Risks & Mitigations

### Risk: Copilot CLI Unavailable
**Mitigation:** Check in doctor pack, provide clear error with installation instructions

### Risk: Memory System File Corruption
**Mitigation:** JSON validation on read, backup before write, graceful degradation if corrupted

### Risk: Template Rendering Errors
**Mitigation:** Validate templates at build time, catch rendering errors, show helpful messages

### Risk: Agent Files Invalid After Creation
**Mitigation:** Validate immediately after creation, don't write if validation fails

---

## Planloop Instructions

**For the planloop executor:**

1. **Work through phases sequentially** - Complete Phase 1 fully before moving to Phase 2
2. **Test continuously** - Run tests after each task, don't accumulate test debt
3. **Follow TDD** - Write tests first where applicable (unit tests especially)
4. **Commit frequently** - Commit after each completed task with descriptive messages
5. **Update docs** - Keep `docs/plans/main.md` updated with progress
6. **Ask for clarification** - If anything is unclear, note it and continue with best judgment
7. **Provide feedback** - Note any planloop improvements discovered during implementation
8. **Use result envelopes** - Every command must return proper ResultEnvelope
9. **Validate early** - Validate all schemas, templates, and outputs as soon as created
10. **Document decisions** - If you make implementation decisions not specified here, document them

**Feedback to Collect:**
- Situations where planloop needs better context
- Places where task breakdown could be improved
- Moments where planloop execution could be more efficient
- Ideas for planloop self-improvement

---

## Next Steps

1. **Approve this plan** (or request changes)
2. **Hand off to planloop** with instruction: "Implement `honk agent` tool following this plan"
3. **Let planloop execute** all 27 tasks across 5 phases without stopping
4. **Review completed implementation** once all phases done
5. **Test in real scenarios** (create research agent, use it, see memory system work)

---

**Ready to hand off to planloop? Confirm and I'll begin implementation.**
