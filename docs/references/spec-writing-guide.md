# Specification Writing Guide

**Version:** 1.0.0  
**Last Updated:** 2025-11-18  
**Status:** Living Document

## Purpose

This guide establishes best practices for writing technical specifications in the Honk project. Following these guidelines ensures consistency, clarity, and implementability across all specs.

---

## Core Principles

### 1. **Flat Task Lists (MANDATORY)**

**Rule**: All implementation tasks must be organized as a single flat list, not divided into phases, milestones, or nested hierarchies.

**Why:**
- Easier to track progress linearly
- Simpler for planloop to process
- Reduces cognitive overhead for implementers
- No ambiguity about task ordering
- Prevents artificial phase boundaries that don't reflect actual work

**✅ Good Example:**
```markdown
## Implementation Tasks

1. Create module structure under `src/honk/tools/release/`
2. Implement Git operations helper (`git_ops.py`)
3. Implement commit parser (`parser.py`)
4. Implement version bumper (`version.py`)
5. Create CLI commands module (`cli.py`)
...
```

**❌ Bad Example:**
```markdown
## Implementation Plan

### Phase 1: Foundation
1. Create module structure
2. Implement helpers

### Phase 2: Core Features
3. Implement parser
4. Implement bumper
...
```

### 2. **Specification Structure**

Every spec should follow this structure:

```markdown
# [Tool/Feature Name] Specification

**Version:** [semver]
**Status:** [Draft/Review/Approved/Implemented]
**Last Updated:** [date]

## Overview

### Purpose
[What problem does this solve?]

### Goals
- [Goal 1]
- [Goal 2]

### Non-Goals
- [What this explicitly does NOT do]

## Architecture

### System Design
[High-level architecture diagram or description]

### Components
[List of major components and their responsibilities]

### Data Flow
[How data moves through the system]

## Technical Specifications

### Module Structure
[File organization and module layout]

### APIs/Interfaces
[Public interfaces, function signatures]

### Dependencies
[External libraries, internal modules]

### Configuration
[Settings, environment variables, config files]

## Implementation Tasks

[FLAT LIST - See Rule #1]

1. Task 1
2. Task 2
3. Task 3
...

## Testing Strategy

### Test Coverage
- Unit tests: [What to test]
- Integration tests: [What to test]
- Contract tests: [What to test]

### Test Cases
[Key test scenarios]

## Documentation Requirements

- [ ] API documentation
- [ ] User guide
- [ ] Examples
- [ ] Migration guide (if applicable)

## Success Criteria

- [ ] Criterion 1
- [ ] Criterion 2

## References

- [Related docs]
- [External resources]
- [Prior art]
```

### 3. **Task Writing Guidelines**

**Each task should be:**
- **Atomic**: One clear, testable deliverable
- **Actionable**: Can be started immediately when reached
- **Testable**: Clear success criteria
- **Ordered**: Follows logical dependency order
- **Sized**: 1-4 hours of work (split larger tasks)

**Task Template:**
```
[N]. [Action verb] [specific deliverable] ([module/file if applicable])
```

**Examples:**
- ✅ "Create `git_ops.py` with commit history fetching"
- ✅ "Implement conventional commit parser in `parser.py`"
- ✅ "Add unit tests for version bumper logic"
- ❌ "Work on Git integration" (too vague)
- ❌ "Implement everything for the parser" (too broad)

### 4. **Dependency Management**

**Dependencies should be:**
- Listed explicitly in the spec
- Minimal (only what's truly needed)
- Version-pinned (specify exact versions)
- Justified (explain why each is needed)

**Template:**
```markdown
## Dependencies

### Required
- `library-name==x.y.z` - [Why needed]
- `another-lib>=a.b.c,<a.(b+1).0` - [Why needed]

### Optional
- `optional-lib` - [When needed, why]

### Development
- `dev-tool` - [What it's for]
```

### 5. **Examples and Code Samples**

**Include concrete examples:**
- API usage examples
- CLI command examples
- Configuration examples
- Test examples

**Format:**
```markdown
### Example: [Scenario]

**Command:**
```bash
honk area tool action --flag value
```

**Expected Output:**
```json
{
  "status": "ok",
  "result": {...}
}
```

**Explanation:**
[What this demonstrates]
```

### 6. **Clarity and Precision**

**Write specs that are:**
- **Unambiguous**: One clear interpretation
- **Complete**: All information needed to implement
- **Concise**: No unnecessary verbosity
- **Scannable**: Headers, bullets, code blocks
- **Current**: Update as decisions change

**Avoid:**
- ❌ "Implement something like..."
- ❌ "Maybe we could..."
- ❌ "This might work..."
- ❌ "Details TBD"

**Use:**
- ✅ "Implement X using Y approach"
- ✅ "Must support Z"
- ✅ "Returns JSON with schema S"
- ✅ "Follows pattern P from module M"

### 7. **Version Control**

**Track spec evolution:**
- Version number at top (semantic versioning)
- Status indicator (Draft/Review/Approved/Implemented)
- Last updated date
- Change log section for major revisions

**Example:**
```markdown
## Change Log

### v1.1.0 (2025-11-18)
- Added AI changelog generation
- Removed manual editing requirement
- Updated task list to reflect new workflow

### v1.0.0 (2025-11-15)
- Initial specification
```

### 8. **Cross-References**

**Link related documentation:**
- Architecture docs
- User guides
- Related specs
- Implementation files
- Test files

**Example:**
```markdown
## References

### Related Specs
- [Release Tool Spec](./release-tool-spec.md) - Overall release automation
- [Versioning Strategy](./versioning-strategy.md) - Version scheme

### Implementation
- Source: `src/honk/tools/release/`
- Tests: `tests/tools/release/`

### Documentation
- User Guide: [Release Tool Guide](./release-tool-guide.md)
```

---

## Common Patterns

### Pattern: CLI Command Spec

```markdown
### Command: `honk area tool action`

**Purpose:** [What it does]

**Arguments:**
- `arg1` (required) - [Description]
- `arg2` (optional) - [Description]

**Options:**
- `--flag` - [What it does]
- `--option VALUE` - [What it does]

**Returns:** [Output format and schema]

**Examples:**
```bash
honk area tool action arg1 --flag
```

**Error Handling:**
- [Error case 1] → [Exit code, message]
- [Error case 2] → [Exit code, message]
```

### Pattern: Module Spec

```markdown
### Module: `module_name.py`

**Purpose:** [What this module does]

**Public API:**
```python
def function_name(arg: Type) -> ReturnType:
    """Brief description."""
    ...
```

**Usage:**
```python
from honk.tools.area import module_name

result = module_name.function_name(arg)
```

**Dependencies:**
- [List internal and external dependencies]

**Testing:**
- Unit tests: `tests/path/test_module_name.py`
```

### Pattern: Feature Spec

```markdown
### Feature: [Name]

**Description:** [What it does]

**User Story:**
As a [user type], I want [goal] so that [benefit].

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

**Technical Approach:**
[How it will be implemented]

**Alternatives Considered:**
1. [Alternative 1] - Rejected because [reason]
2. [Alternative 2] - Rejected because [reason]
```

---

## Spec Review Checklist

Before finalizing a spec, verify:

- [ ] **Structure**: Follows standard template
- [ ] **Tasks**: Flat list, atomic, ordered
- [ ] **Clarity**: Unambiguous, complete, concise
- [ ] **Examples**: Concrete code/command samples included
- [ ] **Dependencies**: All listed and justified
- [ ] **Testing**: Test strategy defined
- [ ] **Documentation**: Docs requirements listed
- [ ] **Success Criteria**: Clear, measurable
- [ ] **Cross-References**: Links to related docs
- [ ] **Version Info**: Version, status, date present

---

## Anti-Patterns to Avoid

### ❌ Phased Task Lists

**Problem:** Creates artificial boundaries, complicates tracking

**Solution:** Use flat list with natural dependency ordering

### ❌ Vague Tasks

**Problem:** "Implement the thing" - not actionable

**Solution:** "Create `module.py` with `function()` that does X"

### ❌ Missing Context

**Problem:** Assumes reader knows background

**Solution:** Include "Overview" and "Purpose" sections

### ❌ No Examples

**Problem:** Hard to understand abstract descriptions

**Solution:** Always include concrete code/command examples

### ❌ Incomplete Dependencies

**Problem:** Implementer discovers missing libs mid-work

**Solution:** List ALL dependencies upfront

### ❌ Spec Drift

**Problem:** Implementation diverges from spec, spec not updated

**Solution:** Update spec when decisions change, track versions

---

## When to Write a Spec

**Write a spec for:**
- ✅ New tools/commands
- ✅ New subsystems
- ✅ Major features
- ✅ Complex integrations
- ✅ Public APIs

**Don't write a spec for:**
- ❌ Trivial bug fixes
- ❌ One-line changes
- ❌ Obvious refactors
- ❌ Documentation-only changes

**Rule of Thumb:** If implementation requires more than 4 hours or affects multiple modules, write a spec.

---

## Spec Lifecycle

```
1. Draft → Initial version, work in progress
2. Review → Ready for feedback, may have TODOs
3. Approved → Finalized, ready for implementation
4. Implemented → Code complete, spec archived
```

**Update spec status as it progresses.**

---

## Tools and Automation

### Using planloop with Specs

Specs should be written to work seamlessly with planloop:

1. **Flat task list** - planloop expects linear progression
2. **Clear task boundaries** - each task is a distinct work unit
3. **Ordered dependencies** - tasks can be executed in sequence
4. **Testable milestones** - progress is verifiable

### Spec Templates

Create templates for common spec types:
- CLI command spec
- Module spec
- Feature spec
- Integration spec

Store in `docs/templates/` for reuse.

---

## Examples

### Good Spec Example

See: `docs/references/agent-tooling-spec.md`
- Clear flat task list
- Concrete examples throughout
- Complete dependency list
- Well-defined success criteria

### Bad Spec Example (What NOT to Do)

```markdown
## Implementation

### Phase 1
Do some stuff

### Phase 2
Do more stuff

[No details, no examples, no clear tasks]
```

---

## Continuous Improvement

This guide is a living document. As we learn better practices:

1. Update this guide
2. Refactor existing specs to follow new patterns
3. Document lessons learned
4. Share improvements with team

**Last major revision:** 2025-11-18

---

## Summary

**Golden Rules:**
1. ✅ Always use flat task lists
2. ✅ Make tasks atomic and actionable
3. ✅ Include concrete examples
4. ✅ List all dependencies
5. ✅ Write clear, unambiguous specifications
6. ✅ Update specs when decisions change
7. ✅ Link to related documentation

**Follow these guidelines to write specs that are clear, complete, and implementable.**
