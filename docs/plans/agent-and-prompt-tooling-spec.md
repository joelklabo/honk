# Agent & Prompt Management Tooling - Proposal C (Recommended)

**Status:** Draft  
**Created:** 2025-11-18  
**Author:** Research Agent  
**Related:** `docs/plans/main.md`, `docs/agents.md`

---

## Executive Summary

After comprehensive research into GitHub Copilot CLI capabilities, DSPy limitations, and prompt optimization tooling, I recommend **Proposal C: Lightweight Infrastructure-First Approach** as the optimal path forward for Honk's agent and prompt management needs.

**Key Decision:** Build a `honk agent` tool that creates, validates, and manages GitHub Copilot CLI custom agents and prompt files, leveraging native Copilot CLI features rather than complex optimization frameworks like DSPy.

**Confidence Level:** **HIGH (9/10)**

**Rationale:**
1. GitHub Copilot CLI now has native custom agent support (Oct 2025 release)
2. No external API costs (uses existing Copilot subscription)
3. Simpler, more maintainable than DSPy (which showed mixed production reliability)
4. Direct alignment with existing workflow (already using Copilot CLI)
5. Can share infrastructure with future `honk spec` optimization tool

---

## Research Findings Summary

### 1. GitHub Copilot CLI Native Agent Support (NEW in 2025)

**Discovery:** GitHub released custom agent support in October 2025, which dramatically changes the landscape.

**Key Capabilities:**
- **Agent Definition Files:** `.agent.md` files with YAML frontmatter
- **Agent Storage Locations:**
  - Project: `.github/agents/` (repo-specific)
  - Organization: `{org}/.github/agents/` (shared across repos)
  - User: `~/.copilot/agents/` (personal)
- **Invocation:** `/agent <name>` in interactive mode or `gh copilot --agent <name> -p "prompt"`
- **One-Shot Queries:** `gh copilot -p "prompt text"` for programmatic use
- **Tool Control:** Specify allowed tools (`read`, `edit`, `search`, `shell`)
- **MCP Integration:** Optional Model Context Protocol servers for advanced tooling

**YAML Frontmatter Schema:**
```yaml
---
name: agent-name                    # Optional, defaults to filename
description: "What this agent does" # Required
target: github-copilot              # Optional: vscode, github-copilot
tools:                              # Optional, defaults to all
  - read
  - edit
  - search
metadata:                           # Optional key-value pairs
  owner: team-name
  version: "1.0"
---
```

**Validation Tools Available:**
- `remark-lint-frontmatter-schema` (remark plugin for YAML validation)
- `eslint-plugin-markdown-frontmatter-schema` (ESLint support)
- JSON Schema validation (can enforce required fields, types, enums)

**Sources:** GitHub Changelog, GitHub Docs (Custom Agents Configuration)

### 2. DSPy Production Reliability Assessment

**Findings:** DSPy has significant limitations for our use case.

**Pros:**
- Systematic, automated prompt optimization
- Reproducible results
- Strong academic backing
- Works well for certain tasks (prompt evaluation showed good gains)

**Cons (Critical for Our Decision):**
- **Variable Results:** Mixed success across use cases; minor gains for guardrails/hallucination detection
- **Steep Learning Curve:** Meta-programming paradigm requires significant expertise
- **Production Immaturity:** Documentation gaps, integration issues, idiosyncratic behaviors
- **Opaque Optimization:** Hard to debug or explain prompt changes (compliance risk)
- **Data Dependency:** Needs high-quality training datasets to optimize
- **Model Drift:** Requires re-tuning when LLMs update
- **Previous Experience:** You mentioned "didn't really work very well" in past attempt

**Confidence:** **LOW (3/10)** - Not recommended for this use case

**Sources:** arXiv multi-use case study, DSPy documentation, production reliability reviews

### 3. Alternative Prompt Optimization Tools

**Evaluated Options:**

| Tool | Strength | Fit for Honk | API Needed | Cost |
|------|----------|--------------|------------|------|
| **DSPy** | Systematic optimization | Low | OpenAI/Anthropic | Per-call |
| **TensorZero** | Full-stack LLM optimization | Medium | Yes | Self-hosted/paid |
| **Future AGI** | Dashboard-based | Low | Yes | Subscription |
| **Prompt Management** (Maxim AI, Langfuse) | Version control, governance | Medium | Yes | Subscription |
| **Native Copilot CLI** | **Zero setup, native integration** | **HIGH** | **No (uses Copilot sub)** | **$0** |

**Decision:** Native Copilot CLI wins on simplicity, cost, and integration.

### 4. Prompt Files & Custom Instructions

**Additional Discovery:** Copilot CLI supports "prompt files" for reusable prompts.

**Locations:**
- `.github/prompts/task-name.prompt.md`
- `.github/copilot-instructions.md` (workspace-wide instructions)
- `.github/instructions/*.instructions.md` (scoped by file pattern)

**Use Case:** Store refined prompts as files, reference them programmatically or in agent definitions.

**Benefit:** Builds library of proven prompts without complex optimization frameworks.

---

## Proposal C: `honk agent` Tool - Detailed Spec

### Overview

Build a `honk agent` area with tools to create, validate, test, and manage GitHub Copilot CLI custom agents and prompt files.

**Grammar:** `honk agent <tool> <action>`

### Tools & Actions

#### 1. `honk agent scaffold create`

**Purpose:** Generate a new custom agent from template or interactive prompts.

**Usage:**
```bash
# Interactive mode
honk agent scaffold create

# Quick mode with options
honk agent scaffold create \
  --name researcher \
  --description "Expert research specialist" \
  --tools read,search \
  --location project \
  --template research
```

**Implementation:**
- Prompt for agent details (name, description, purpose)
- Select tools (read, edit, search, shell, all)
- Choose storage location (project, org, user)
- Optional: Select from template library (research, testing, documentation, etc.)
- Generate `.agent.md` file with proper YAML frontmatter
- Validate YAML schema before writing
- Add to git (if project/org location)

**Output:**
```
✓ Created agent: .github/agents/researcher.agent.md
✓ Validated YAML schema
✓ Added to git staging

Next steps:
  1. Review and customize: .github/agents/researcher.agent.md
  2. Test agent: honk agent test researcher
  3. Commit changes: git commit -m "Add researcher agent"
```

**Facts:**
- `agent_name`: Name of created agent
- `file_path`: Path to agent file
- `location`: project/org/user
- `tools_enabled`: List of tools

**Links:**
- Agent file path
- GitHub Docs: Custom Agents Configuration
- Honk docs: Agent development guide

**Next:**
- `honk agent test researcher`
- `honk agent validate researcher`

#### 2. `honk agent validate [name|--all]`

**Purpose:** Validate agent YAML frontmatter against schema.

**Usage:**
```bash
# Validate specific agent
honk agent validate researcher

# Validate all agents
honk agent validate --all

# Validate with strict mode (extra checks)
honk agent validate researcher --strict
```

**Implementation:**
- Load agent file(s)
- Parse YAML frontmatter
- Validate against JSON schema:
  - Required fields present (`description`)
  - Correct types (tools is array/string)
  - Valid tool names
  - Valid target values
  - No unsupported fields (for target environment)
- Check markdown body:
  - Non-empty
  - Well-formed markdown
  - No suspicious patterns (e.g., unescaped frontmatter delimiters)
- Strict mode adds:
  - Style checks (consistent formatting)
  - Best practice warnings (e.g., "description too short")
  - Link validation in markdown body

**Output:**
```
✓ Validated: researcher.agent.md
  - Schema: valid
  - Required fields: present
  - Tools: [read, search] (valid)
  - Markdown body: 42 lines, well-formed

Warnings:
  ⚠ Consider adding 'metadata.owner' for team context
```

**Facts:**
- `agent_name`
- `validation_status`: pass/fail/warning
- `errors`: List of errors (if any)
- `warnings`: List of warnings
- `schema_version`: Version validated against

**Links:**
- JSON schema file path
- GitHub Docs: Agent Configuration

**Next:**
- `honk agent test <name>` (if valid)
- `honk agent fix <name>` (if errors)

#### 3. `honk agent test <name>`

**Purpose:** Test agent with sample prompts.

**Usage:**
```bash
# Interactive test (opens Copilot CLI session)
honk agent test researcher

# One-shot test
honk agent test researcher --prompt "Research Swift 6 concurrency"

# Test suite (run multiple prompts from file)
honk agent test researcher --suite tests/researcher-suite.yml
```

**Implementation:**
- Verify agent exists and is valid
- For interactive: Launch `gh copilot --agent <name>` session
- For one-shot: Run `gh copilot --agent <name> -p "<prompt>"` and capture output
- For suite: Load prompts from YAML file, run each, capture outputs
- Record test results (response quality, errors, timing)
- Optional: Save test session to `tmp/agent-tests/<name>-<timestamp>.log`

**Test Suite Format:**
```yaml
# tests/researcher-suite.yml
tests:
  - name: Basic research query
    prompt: "Research GraphQL best practices"
    expected_topics:
      - queries
      - mutations
      - best practices
    
  - name: Comparison research
    prompt: "Compare SwiftUI vs UIKit"
    expected_structure:
      - pros_cons_table
      - code_examples
```

**Output:**
```
Testing agent: researcher

Test 1: Basic research query
  Prompt: "Research GraphQL best practices"
  Status: ✓ Passed (12.3s)
  Topics covered: queries, mutations, best practices, performance
  Quality: High

Test 2: Comparison research
  Prompt: "Compare SwiftUI vs UIKit"
  Status: ✓ Passed (18.7s)
  Structure: Table present, examples included
  Quality: High

Summary: 2/2 tests passed (31.0s total)
```

**Facts:**
- `agent_name`
- `test_count`: Number of tests run
- `passed`: Number passed
- `failed`: Number failed
- `average_duration_ms`
- `test_results`: Array of individual results

**Links:**
- Test log path
- Test suite file (if used)

**Next:**
- `honk agent refine <name>` (if quality issues)
- `honk agent publish <name>` (if tests pass)

#### 4. `honk agent refine <name>`

**Purpose:** Iteratively improve agent instructions using feedback.

**Usage:**
```bash
# Interactive refinement (asks questions)
honk agent refine researcher

# Apply specific improvement
honk agent refine researcher --add-example "Use tables for comparisons"

# Guided refinement with test results
honk agent refine researcher --from-test-results tmp/agent-tests/researcher-latest.log
```

**Implementation:**
- Load current agent file
- Analyze agent instructions (markdown body)
- Interactive mode:
  - Ask: "What problems did you observe?"
  - Ask: "What specific improvements do you want?"
  - Generate refinement suggestions using Copilot CLI one-shot query:
    ```bash
    gh copilot -p "Improve these agent instructions: [current instructions]. 
                   Problems observed: [user feedback]. 
                   Generate improved instructions maintaining structure."
    ```
  - Preview changes (diff view)
  - Apply or iterate
- From-test-results mode:
  - Parse test log for failures/issues
  - Auto-generate improvement suggestions
  - Apply and re-test

**Output:**
```
Refining agent: researcher

Current issues identified:
  1. Responses sometimes lack code examples
  2. Citations not always formatted consistently

Suggested improvements:
  + Add instruction: "Always include code examples where applicable"
  + Add instruction: "Format citations as [Source Name](URL)"
  + Add section: "## Output Format Examples"

Apply these changes? [Y/n]: y

✓ Applied improvements
✓ Validated updated agent
✓ Saved backup: .github/agents/researcher.agent.md.backup

Next steps:
  1. Test improvements: honk agent test researcher
  2. Compare with backup if needed
```

**Facts:**
- `agent_name`
- `refinement_type`: interactive/guided/auto
- `changes_applied`: Number of changes
- `backup_path`

**Links:**
- Updated agent file
- Backup file
- Diff view (if applicable)

**Next:**
- `honk agent test <name>` (verify improvements)

#### 5. `honk agent list [--location=all|project|org|user]`

**Purpose:** List all available agents.

**Usage:**
```bash
# List all agents
honk agent list

# List project agents only
honk agent list --location project

# List with details
honk agent list --verbose
```

**Implementation:**
- Scan agent directories:
  - `.github/agents/` (project)
  - `{org}/.github/agents/` (org) - if in org context
  - `~/.copilot/agents/` (user)
- Parse each agent file
- Extract name, description, tools, metadata
- Display in table format

**Output:**
```
Available Copilot Agents:

Project (.github/agents/):
  researcher        Expert research specialist [read, search]
  test-writer       Automated test generation [read, edit, shell]
  
User (~/.copilot/agents/):
  code-reviewer     Code review assistant [read, edit]
  
Total: 3 agents
```

**Facts:**
- `agent_count`: Total number of agents
- `agents`: Array of agent metadata
- `locations`: Locations scanned

**Links:**
- Agent files

**Next:**
- `honk agent validate --all`
- `honk agent test <name>`

#### 6. `honk agent publish <name>`

**Purpose:** Publish agent to team or community.

**Usage:**
```bash
# Commit to project (already tracked by git)
honk agent publish researcher

# Copy to org location (if org member)
honk agent publish researcher --to-org

# Export as shareable file
honk agent publish researcher --export researcher-v1.0.agent.md
```

**Implementation:**
- Validate agent (must pass validation)
- To-org mode:
  - Check org permissions
  - Copy to `{org}/.github/agents/`
  - Create PR or commit (depending on permissions)
- Export mode:
  - Add version metadata
  - Include usage instructions
  - Create standalone file
- Commit mode:
  - Ensure file is staged
  - Provide commit message template
  - Optionally push

**Output:**
```
Publishing agent: researcher

✓ Validation passed
✓ Copied to org: myorg/.github/agents/researcher.agent.md
✓ Created PR: https://github.com/myorg/.github/pull/42

Your agent is now available to the entire organization!

To use: gh copilot --agent researcher -p "your prompt"
```

**Facts:**
- `agent_name`
- `publish_target`: project/org/export
- `publish_url`: URL (if applicable)

**Links:**
- Published agent location
- PR URL (if created)

**Next:**
- Share documentation with team

#### 7. `honk agent template list|show|add`

**Purpose:** Manage agent templates.

**Usage:**
```bash
# List available templates
honk agent template list

# Show template details
honk agent template show research

# Add custom template
honk agent template add my-template --from .github/agents/researcher.agent.md
```

**Implementation:**
- Built-in templates stored in `src/honk/tools/agent/templates/`
- Templates are `.agent.md` files with placeholders:
  - `{{AGENT_NAME}}`
  - `{{DESCRIPTION}}`
  - `{{TOOLS}}`
- User can add custom templates to `~/.copilot/honk/agent-templates/`
- List shows all available templates with descriptions
- Show displays full template with placeholders marked
- Add saves agent as reusable template

**Built-in Templates:**
1. **research** - Research specialist (like the one you're using now)
2. **test-writer** - Automated test generation
3. **code-reviewer** - Code review assistant
4. **documentation** - Documentation writer
5. **refactor** - Code refactoring specialist
6. **debug** - Debugging assistant
7. **architect** - System design and architecture

**Output:**
```
Available Agent Templates:

Built-in:
  research         Expert research specialist with web search
  test-writer      Automated test generation and TDD workflows
  code-reviewer    Enforce standards and provide feedback
  documentation    Technical writing and docs generation
  
Custom (~/.copilot/honk/agent-templates/):
  my-specialist    Custom specialist for internal workflows
  
Total: 5 templates
```

**Facts:**
- `template_count`
- `templates`: Array of template metadata
- `custom_templates`: Count of user templates

**Links:**
- Template directory

**Next:**
- `honk agent scaffold create --template <name>`

### Shared Infrastructure Components

These components can be reused by future tools (like `honk spec optimize`):

#### 1. **Prompt Library Manager** (`src/honk/internal/prompts/`)

**Purpose:** Store, version, and retrieve refined prompts.

**Structure:**
```
src/honk/internal/prompts/
├── __init__.py
├── manager.py        # PromptLibrary class
├── validator.py      # Prompt validation
├── library/          # Built-in prompts
│   ├── research.md
│   ├── code-review.md
│   └── refactoring.md
└── user/             # User-defined prompts (symlink to ~/.copilot/honk/prompts/)
```

**API:**
```python
from honk.internal.prompts import PromptLibrary

library = PromptLibrary()

# Load prompt
prompt = library.get("research/deep-dive")

# Save refined prompt
library.save("my-prompt", content, metadata={"version": "1.1"})

# List prompts
prompts = library.list(category="research")
```

#### 2. **YAML Schema Validator** (`src/honk/internal/validation/`)

**Purpose:** Validate YAML frontmatter in markdown files.

**Implementation:**
- Use `jsonschema` library (already in dependencies)
- Store schemas in `schemas/agent.v1.json`
- Provide clear error messages with line numbers
- Support multiple schema versions

**API:**
```python
from honk.internal.validation import YAMLFrontmatterValidator

validator = YAMLFrontmatterValidator(schema_path="schemas/agent.v1.json")

# Validate file
result = validator.validate_file(".github/agents/researcher.agent.md")

if result.valid:
    print("✓ Valid")
else:
    for error in result.errors:
        print(f"Line {error.line}: {error.message}")
```

#### 3. **Copilot CLI Wrapper** (`src/honk/internal/copilot/`)

**Purpose:** Programmatic interface to `gh copilot` commands.

**Implementation:**
- Subprocess wrapper around `gh copilot`
- Handle authentication via `gh auth` (reuse existing auth system)
- Parse outputs
- Error handling and retries

**API:**
```python
from honk.internal.copilot import CopilotCLI

copilot = CopilotCLI()

# One-shot query
response = copilot.query(
    prompt="Research GraphQL best practices",
    agent="researcher"
)

# Check agent exists
exists = copilot.agent_exists("researcher")

# List agents
agents = copilot.list_agents()
```

#### 4. **Template Engine** (`src/honk/internal/templates/`)

**Purpose:** Render templates with placeholders.

**Implementation:**
- Simple Jinja2-like variable substitution
- Support for conditionals and loops
- Validate rendered output

**API:**
```python
from honk.internal.templates import TemplateEngine

engine = TemplateEngine(template_dir="src/honk/tools/agent/templates/")

# Render template
output = engine.render(
    "research.agent.md",
    {
        "AGENT_NAME": "researcher",
        "DESCRIPTION": "Expert research specialist",
        "TOOLS": ["read", "search"]
    }
)
```

---

## Future: `honk spec` Tool (Shared Infrastructure)

The infrastructure built for `honk agent` can be reused for a future `honk spec optimize` tool:

### Potential Actions:

1. **`honk spec optimize <spec-file>`**
   - Use Copilot CLI one-shot queries to improve spec clarity
   - Apply prompt library patterns
   - Validate against spec template schema

2. **`honk spec review <spec-file>`**
   - Use custom "spec-reviewer" agent
   - Check for completeness, clarity, consistency
   - Suggest improvements

3. **`honk spec generate <concept>`**
   - Generate spec from high-level concept
   - Use research agent to gather context
   - Apply spec template

**Shared Components:**
- Prompt library (reuse refined prompts)
- Copilot CLI wrapper (same API)
- Template engine (spec templates)
- YAML validator (spec frontmatter)

---

## Implementation Plan

**Timeline:** 3-4 weeks for full implementation

### All Implementation Tasks (Flat List)

1. Set up module structure (`src/honk/tools/agent/`)
2. Implement YAML schema for agents (`schemas/agent.v1.json`)
3. Build YAML frontmatter validator (`src/honk/internal/validation/`)
4. Create `honk agent validate` command
5. Create basic agent templates
6. Write unit tests for validator
7. Build template engine (`src/honk/internal/templates/`)
8. Create 7 built-in templates (research, test-writer, documenter, reviewer, debugger, architect, refactorer)
9. Implement `honk agent scaffold create` (interactive + quick modes)
10. Implement `honk agent template list|show|add`
11. Write integration tests for scaffolding
12. Update agent documentation
13. Build Copilot CLI wrapper (`src/honk/internal/copilot/`)
14. Implement `honk agent test` (interactive, one-shot, suite modes)
15. Create test suite YAML schema (`schemas/agent-test-suite.v1.json`)
16. Implement `honk agent list` command
17. Write tests for Copilot wrapper (using mocks/respx)
18. Create sample test suites for each template
19. Build prompt library manager (`src/honk/internal/prompts/`)
20. Implement `honk agent refine` (interactive + guided modes)
21. Implement `honk agent publish` (commit, org, export modes)
22. Add refinement suggestions via Copilot CLI one-shot queries
23. Write contract tests for all commands (validate result envelopes against `schemas/result.v1.json`)
24. Create user documentation (`docs/references/agent-tool-guide.md`)
25. Add `honk agent --help-json` for introspection
26. Register all commands in registry with metadata (area, tool, action, prereqs, examples)
27. Add result envelopes to all commands (status, facts, links, next, pack_results)
28. Implement `--json` output for all commands
29. Run full test suite (unit, integration, contract) and ensure all pass
30. Update `docs/spec.md` with agent tool architecture and patterns
31. Update `docs/plans/main.md` with completion status and learnings
32. Delete obsolete spec files: `agent-tooling-implementation-plan.md`, `research-agent-refined-spec.md`, `research-agent-complete-spec.md`
33. Create tutorial and examples (`docs/references/agent-tool-examples.md`)
34. Optional: Create demo video or GIF walkthrough

**Key Milestones:**
- **MVP (Tasks 1-12):** Basic agent creation and validation - 1-2 weeks
- **Testing (Tasks 13-18):** Programmatic testing capability - 2 weeks
- **Full Lifecycle (Tasks 19-34):** Complete refinement, publishing, and polish - 3-4 weeks

---

## Cost Analysis

### Development Time
- **Total estimated time:** 3-4 weeks for full implementation
- **MVP (Phases 1-2):** 1-2 weeks
- **Production-ready (All phases):** 3-4 weeks

### Runtime Costs
- **GitHub Copilot Subscription:** $10-20/month (already have)
- **Additional API costs:** $0 (uses Copilot subscription)
- **Infrastructure:** $0 (no external services)

### Maintenance Costs
- **Low:** Leverages native GitHub features
- **Schema updates:** When GitHub updates agent spec (rare)
- **Template updates:** As best practices evolve (quarterly?)

---

## Alternatives Considered

### Alternative A: DSPy-Based Optimization
**Pros:** Systematic, automated optimization  
**Cons:** Complex, unreliable, requires external API, steep learning curve, past negative experience  
**Cost:** OpenAI API usage (~$50-200/month for optimization runs)  
**Verdict:** ❌ Not recommended

### Alternative B: Third-Party Prompt Management (Future AGI, Maxim AI)
**Pros:** Full-featured, dashboard UI, team collaboration  
**Cons:** Subscription costs, vendor lock-in, not aligned with CLI-first workflow  
**Cost:** $50-500/month depending on tier  
**Verdict:** ❌ Not recommended (but could integrate later if needed)

### Alternative C: Native Copilot CLI (Recommended)
**Pros:** Zero cost, native integration, simple, maintainable, aligns with workflow  
**Cons:** Less automated optimization (but can add iterative refinement)  
**Cost:** $0 (uses existing Copilot subscription)  
**Verdict:** ✅ **Recommended**

---

## Decision Framework

Use this tool for:
- ✅ Creating custom Copilot CLI agents
- ✅ Validating and testing agents
- ✅ Building a library of proven prompts
- ✅ Iteratively refining agent instructions
- ✅ Sharing agents across teams
- ✅ Learning from agent usage patterns

Don't use this for:
- ❌ Fully automated prompt optimization (use DSPy if needed later)
- ❌ Enterprise prompt governance at scale (use dedicated platforms)
- ❌ Multi-model orchestration (stick to Copilot ecosystem)

---

## Success Metrics

### Quantitative
- **Agent creation time:** < 5 minutes from concept to tested agent
- **Validation speed:** < 1 second per agent
- **Test suite execution:** < 30 seconds for typical suite
- **Refinement iterations:** 2-3 iterations to production-ready agent

### Qualitative
- **Developer experience:** Intuitive, minimal learning curve
- **Agent quality:** Consistent, reliable responses
- **Maintainability:** Easy to update and improve over time
- **Reusability:** Agents and prompts can be shared and remixed

---

## Risks & Mitigations

### Risk 1: GitHub Changes Agent Spec
**Likelihood:** Low (new feature, should be stable)  
**Impact:** Medium (need to update schema and validator)  
**Mitigation:**
- Monitor GitHub Changelog
- Keep schema versioned (`agent.v1.json`, `agent.v2.json`)
- Automated tests will catch breaking changes

### Risk 2: Copilot CLI Limitations
**Likelihood:** Medium (may discover edge cases)  
**Impact:** Low (can work around with fallbacks)  
**Mitigation:**
- Start with core features, expand incrementally
- Document known limitations
- Fallback to manual workflows if needed

### Risk 3: Low Adoption (Not Useful)
**Likelihood:** Low (directly addresses stated needs)  
**Impact:** Medium (wasted development time)  
**Mitigation:**
- Build MVP first (Phases 1-2) and validate usefulness
- Gather feedback early
- Iterate based on real usage

### Risk 4: Scope Creep (Adding Too Many Features)
**Likelihood:** Medium (easy to over-engineer)  
**Impact:** Medium (delays release)  
**Mitigation:**
- Stick to phased plan
- Ship MVP, then iterate
- Defer complex features (auto-optimization) to later

---

## Next Steps

1. **Decision:** Approve this spec (or request changes)
2. **Setup:** Create GitHub project/issues for tracking
3. **Implementation:** Use `planloop` to execute phased plan
4. **Feedback Loop:** Test MVP (Phases 1-2) with real use cases before continuing
5. **Iteration:** Refine based on usage, then continue to Phases 3-5

---

## Appendices

### Appendix A: Example Agent File

```markdown
---
name: researcher
description: Expert research specialist who conducts thorough web research and synthesizes findings
target: github-copilot
tools:
  - read
  - search
metadata:
  owner: honk-team
  version: "1.0"
  category: research
---

# Research Specialist Agent

You are an expert research specialist who conducts thorough web research and synthesizes findings into actionable, well-organized knowledge.

## Your Core Mission

Transform vague research requests into comprehensive, well-cited, actionable knowledge by:
1. **Clarifying** the research goal through interactive questions
2. **Researching** using multi-hop, iterative web searches
3. **Synthesizing** information with deduplication and organization
4. **Delivering** structured output in the appropriate format

## Research Modes

[... rest of research agent instructions ...]
```

### Appendix B: Example Test Suite

```yaml
# tests/agent-suites/researcher.yml
name: Researcher Agent Test Suite
description: Validate research agent capabilities
version: "1.0"

tests:
  - name: Basic research query
    prompt: "Research GraphQL best practices for iOS apps"
    expected_topics:
      - GraphQL fundamentals
      - iOS integration
      - Apollo client
      - best practices
    expected_structure:
      - executive_summary
      - code_examples
      - references
    timeout_seconds: 30
    
  - name: Comparison research
    prompt: "Compare SwiftUI vs UIKit for new iOS projects"
    expected_topics:
      - SwiftUI features
      - UIKit features
      - pros and cons
      - recommendation
    expected_structure:
      - comparison_table
      - code_examples
      - decision_framework
    timeout_seconds: 45
    
  - name: Current state check
    prompt: "What's new in Swift 6 concurrency in 2025?"
    expected_topics:
      - Swift 6 features
      - concurrency improvements
      - migration guide
      - 2025 updates
    expected_structure:
      - whats_changed_summary
      - code_examples
      - migration_notes
    timeout_seconds: 30
```

### Appendix C: JSON Schema for Agent Frontmatter

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "$id": "https://honk.dev/schemas/agent.v1.json",
  "title": "GitHub Copilot Agent Configuration",
  "description": "Schema for validating GitHub Copilot custom agent YAML frontmatter",
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Unique name for the agent",
      "pattern": "^[a-z0-9-]+$",
      "minLength": 3,
      "maxLength": 50
    },
    "description": {
      "type": "string",
      "description": "Describes the agent's purpose and capabilities",
      "minLength": 10,
      "maxLength": 200
    },
    "target": {
      "type": "string",
      "description": "Target environment for the agent",
      "enum": ["vscode", "github-copilot", "both"],
      "default": "github-copilot"
    },
    "tools": {
      "oneOf": [
        {
          "type": "array",
          "items": {
            "type": "string",
            "enum": ["read", "edit", "search", "shell", "*"]
          },
          "minItems": 1,
          "uniqueItems": true
        },
        {
          "type": "string",
          "enum": ["*"]
        }
      ],
      "description": "Tools the agent is allowed to use"
    },
    "mcp-servers": {
      "type": "object",
      "description": "Additional MCP server configurations",
      "additionalProperties": {
        "type": "object"
      }
    },
    "metadata": {
      "type": "object",
      "description": "Custom metadata key-value pairs",
      "properties": {
        "owner": {
          "type": "string",
          "description": "Team or person responsible for this agent"
        },
        "version": {
          "type": "string",
          "description": "Semantic version of the agent",
          "pattern": "^\\d+\\.\\d+(\\.\\d+)?$"
        },
        "category": {
          "type": "string",
          "description": "Category or domain of the agent",
          "enum": ["research", "testing", "documentation", "review", "refactor", "debug", "architecture", "other"]
        }
      },
      "additionalProperties": true
    }
  },
  "required": ["description"],
  "additionalProperties": false
}
```

### Appendix D: Built-in Template Descriptions

#### 1. Research Template
**Purpose:** Conduct thorough research and synthesize findings  
**Tools:** read, search  
**Use Cases:** Technology research, comparison studies, current state analysis  
**Based On:** The research agent instructions provided in this conversation

#### 2. Test-Writer Template
**Purpose:** Generate comprehensive test suites (unit, integration, contract)  
**Tools:** read, edit, shell  
**Use Cases:** TDD workflows, test coverage expansion, test refactoring  
**Follows:** Honk's TDD guidelines from `docs/agents.md`

#### 3. Code-Reviewer Template
**Purpose:** Review code for quality, style, and best practices  
**Tools:** read, search  
**Use Cases:** PR reviews, style enforcement, architecture validation  
**Enforces:** Team standards, security patterns, performance best practices

#### 4. Documentation Template
**Purpose:** Write and maintain technical documentation  
**Tools:** read, edit, search  
**Use Cases:** API docs, user guides, architecture docs, README files  
**Style:** Clear, concise, example-driven

#### 5. Refactor Template
**Purpose:** Safely refactor code while preserving behavior  
**Tools:** read, edit, shell (for tests)  
**Use Cases:** Code cleanup, pattern extraction, dependency updates  
**Approach:** Test-driven, incremental, documented

#### 6. Debug Template
**Purpose:** Diagnose and fix bugs systematically  
**Tools:** read, edit, search, shell  
**Use Cases:** Bug investigation, error analysis, fix implementation  
**Method:** Root cause analysis, minimal fixes, test verification

#### 7. Architect Template
**Purpose:** Design system architecture and make technical decisions  
**Tools:** read, search  
**Use Cases:** System design, technology selection, architecture reviews  
**Output:** Architecture docs, decision records, diagrams

---

## Research Sources

### GitHub Copilot CLI & Agents
- GitHub Changelog: Custom agents for GitHub Copilot (Oct 2025)
- GitHub Docs: Creating custom agents
- GitHub Docs: Custom agents configuration
- GitHub Docs: About GitHub Copilot CLI
- GitHub Blog: Copilot CLI 101
- Community tutorials and examples

### DSPy & Prompt Optimization
- arXiv: "Is It Time To Treat Prompts As Code?" (Multi-use case study)
- DSPy Documentation: Optimizers
- ADaSci: DSPy Hands-On Guide
- Pondhouse Data: DSPy Tutorial 2025
- Production reliability reviews

### Validation & Tooling
- GitHub: remark-lint-frontmatter-schema
- GitHub: eslint-plugin-markdown-frontmatter-schema
- JSON Schema documentation
- GitHub: awesome-copilot (community resources)

### Alternative Tools
- TensorZero documentation (comparison with DSPy)
- Future AGI: Prompt Optimization Tools 2025
- Maxim AI: Prompt Management Platforms
- Various prompt generator tools (Prompt Cowboy, etc.)

---

**End of Spec**

*This document represents a comprehensive, research-backed proposal for building agent and prompt management tooling for Honk. It prioritizes simplicity, cost-effectiveness, and alignment with existing workflows while providing a clear path to implementation.*

*Next step: Review and approve (or request changes), then use `planloop` to implement the phased plan.*
