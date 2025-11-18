# Honk Release Tool - Technical Specification

## Architecture

### Module Structure

```
src/honk/release/
├── __init__.py              # Package initialization
├── cli.py                   # Typer CLI commands
├── workflow.py              # Orchestration logic
├── analyzer.py              # Commit analysis
├── commit_parser.py         # Conventional commits parser
├── versioning/
│   ├── __init__.py
│   └── bumper.py           # Version bumping
├── changelog/
│   ├── __init__.py
│   ├── generator.py        # Traditional changelog
│   └── ai_generator.py     # AI-powered changelog
├── ai/
│   ├── __init__.py
│   └── copilot.py          # GitHub Copilot CLI integration
├── builders/
│   ├── __init__.py
│   ├── pypi.py             # PyPI package builder
│   └── homebrew.py         # Homebrew formula generator
└── publishers/
    ├── __init__.py
    ├── pypi.py             # PyPI publisher
    └── github.py           # GitHub Releases publisher
```

## Components

### 1. CLI Commands (`cli.py`)

**Commands:**
- `honk release status` - Show current release state
- `honk release preview` - Preview next release
- `honk release patch` - Create patch release
- `honk release minor` - Create minor release
- `honk release major` - Create major release

**Common Options:**
- `--dry-run` - Don't make changes
- `--no-ai` - Disable AI changelog
- `--no-build` - Skip building
- `--no-publish` - Skip publishing
- `--no-github` - Skip GitHub release

### 2. Workflow Orchestrator (`workflow.py`)

**Class: `ReleaseWorkflow`**

Coordinates the release process:

1. **Pre-flight checks**
   - Verify clean working tree
   - Check for commits since last tag
   
2. **Analysis**
   - Parse conventional commits
   - Determine release type
   
3. **Version bump**
   - Update version files
   - Generate new version string
   
4. **Changelog**
   - Generate with AI (if enabled)
   - Fallback to conventional parser
   
5. **Commit and tag**
   - Commit version changes
   - Create annotated tag
   
6. **Build** (optional)
   - Build Python packages
   - Generate Homebrew formula
   
7. **Publish** (optional)
   - Publish to PyPI
   - Create GitHub release

**Result Envelope:**
```python
@dataclass
class ReleaseResult:
    success: bool
    old_version: str
    new_version: str
    release_type: ReleaseType
    changelog: str
    commit_sha: Optional[str]
    tag_name: Optional[str]
    error: Optional[str]
```

### 3. Commit Analyzer (`analyzer.py`)

**Class: `CommitAnalyzer`**

Analyzes commits to determine release type:

```python
@dataclass
class CommitAnalysis:
    has_breaking: bool
    has_features: bool
    has_fixes: bool
    recommended_type: ReleaseType
    breaking_commits: List[Commit]
    feature_commits: List[Commit]
    fix_commits: List[Commit]
```

**Analysis Rules:**
- Breaking change → MAJOR
- Features → MINOR
- Fixes only → PATCH

### 4. Conventional Commit Parser (`commit_parser.py`)

**Class: `ConventionalCommitParser`**

Parses commit messages:

```python
@dataclass
class ParsedCommit:
    type: Optional[CommitType]  # feat, fix, etc.
    scope: Optional[str]
    description: str
    body: Optional[str]
    breaking: bool
```

**Supported Types:**
```python
class CommitType(Enum):
    FEAT = "feat"
    FIX = "fix"
    DOCS = "docs"
    STYLE = "style"
    REFACTOR = "refactor"
    PERF = "perf"
    TEST = "test"
    CHORE = "chore"
```

### 5. Version Bumper (`versioning/bumper.py`)

**Class: `VersionBumper`**

Manages version numbers:

```python
class Version:
    major: int
    minor: int
    patch: int
    
    def bump_major() -> Version
    def bump_minor() -> Version
    def bump_patch() -> Version
```

**Version File Updates:**
- `pyproject.toml` - `[project.version]`
- `src/honk/__init__.py` - `__version__`
- Any `__version__.py` files

### 6. Changelog Generators

#### Traditional Generator (`changelog/generator.py`)

**Class: `ChangelogGenerator`**

Generates changelogs from commits:

**Format:** Keep a Changelog

**Sections:**
- Added (feat)
- Changed (refactor, perf)
- Deprecated
- Removed
- Fixed (fix)
- Security

**Breaking Changes:** Highlighted at top

#### AI Generator (`changelog/ai_generator.py`)

**Class: `AIChangelogGenerator`**

Uses GitHub Copilot CLI for human-friendly changelogs:

**Prompt Template:**
```
Generate a changelog entry for version {version}.

Commits since last release:
{commit_list}

Format:
- Use Keep a Changelog format
- Group by type (Added, Fixed, etc.)
- Write user-friendly descriptions
- Highlight breaking changes
- Include upgrade instructions if needed
```

**Fallback:** Uses traditional generator if AI unavailable

### 7. Builders

#### PyPI Builder (`builders/pypi.py`)

**Class: `PyPIBuilder`**

Builds Python packages:

```python
def build(clean_first: bool = True) -> List[Path]:
    """Build wheel and sdist."""
    # Uses: uv build
    # Output: dist/*.whl, dist/*.tar.gz
```

#### Homebrew Builder (`builders/homebrew.py`)

**Class: `HomebrewBuilder`**

Generates Homebrew formula:

```python
def generate_formula(
    version: str,
    tarball_url: str,
    sha256: str
) -> str:
    """Generate .rb formula file."""
```

### 8. Publishers

#### PyPI Publisher (`publishers/pypi.py`)

**Class: `PyPIPublisher`**

Publishes to PyPI:

```python
def publish(
    artifacts: List[Path],
    token: str,
    repository: str = "pypi"
) -> None:
    """Publish packages."""
    # Uses: uv publish
```

**Authentication:**
- Token from `PYPI_TOKEN` env var
- Or explicit parameter

#### GitHub Publisher (`publishers/github.py`)

**Class: `GitHubPublisher`**

Creates GitHub releases:

```python
def create_release(
    version: str,
    changelog: str,
    artifacts: List[Path],
    draft: bool = False,
    prerelease: bool = False
) -> None:
    """Create GitHub release."""
    # Uses: gh release create
```

## Dependencies

### Required

- `typer` - CLI framework
- `rich` - Terminal UI
- `gitpython` (or subprocess) - Git operations

### Optional

- GitHub CLI (`gh`) - For GitHub releases and Copilot
- `uv` - For building and publishing

### System Requirements

- Git repository
- Clean working tree (for non-dry-run)
- GitHub authentication (for releases)
- PyPI token (for publishing)

## Configuration

### pyproject.toml

```toml
[project]
name = "honk"
version = "0.1.0"  # Managed by release tool

[tool.honk.release]
# Enable AI changelog generation
ai_enabled = true

# Changelog file
changelog_file = "CHANGELOG.md"

# Auto-push after release
auto_push = false

# Build artifacts
build_wheel = true
build_sdist = true
build_homebrew = false

# Publishing
publish_pypi = false
publish_github = true

# PyPI settings
pypi_repository = "pypi"  # or "testpypi"

# GitHub settings
github_draft = false
github_prerelease = false
```

## Error Handling

### Exit Codes

- `0` - Success
- `1` - General error
- `10` - Pre-flight check failed (dirty tree, no commits)
- `11` - Version bump failed
- `12` - Build failed
- `13` - Publish failed
- `20` - Git operation failed
- `30` - AI service failed (falls back to traditional)

### Error Messages

All errors include:
- Clear description
- Suggested remediation
- Relevant context

## Testing Strategy

### Unit Tests

**Each module independently:**
- `tests/release/test_analyzer.py`
- `tests/release/test_commit_parser.py`
- `tests/release/test_version_bumper.py`
- `tests/release/test_builders.py`
- `tests/release/test_publishers.py`

### Integration Tests

**End-to-end workflow:**
- `tests/release/test_workflow_integration.py`

**Test scenarios:**
- Clean release (happy path)
- Dirty working tree
- No commits since last release
- Various release types
- Dry run mode
- AI failures and fallback

### Contract Tests

**CLI interface:**
- `tests/contract/test_release_cli_contract.py`

Ensures:
- Commands work as documented
- Options behave correctly
- Output formats stable
- Exit codes correct

## Performance

### Benchmarks

- Commit analysis: < 100ms for 100 commits
- Version bump: < 50ms
- Changelog generation (traditional): < 200ms
- Changelog generation (AI): 2-5 seconds
- Full release workflow: < 10 seconds (excl. publishing)

### Optimization

- Cache parsed commits
- Lazy load modules
- Parallel operations where safe
- Stream large outputs

## Security

### Credentials

- Never log tokens/credentials
- Use environment variables
- Support secure credential stores (keyring)
- Clear sensitive data after use

### Git Operations

- Verify commit signatures
- Validate tag integrity
- Check remote authenticity

## Future Enhancements

### Phase 2 (Future)

1. **Enhanced AI Integration**
   - Custom AI prompts
   - Multiple AI providers
   - Context-aware suggestions

2. **Advanced Publishing**
   - Docker images
   - Chocolatey packages
   - APT/RPM repositories

3. **Release Management**
   - Rollback support
   - Hotfix branches
   - Release branches

4. **Analytics**
   - Release metrics
   - Commit statistics
   - Team productivity

5. **Webhooks**
   - Slack notifications
   - Discord updates
   - Email announcements

## See Also

- [User Guide](./release-tool-guide.md)
- [Semantic Versioning](https://semver.org/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Keep a Changelog](https://keepachangelog.com/)
