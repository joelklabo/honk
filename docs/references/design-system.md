# Honk CLI Design System

## Overview

The Honk CLI design system provides a consistent, configurable visual language for all terminal output. It's built on Python Rich and uses semantic design tokens defined in YAML for easy customization and maintenance.

## Architecture

```
src/honk/
├── ui/
│   ├── __init__.py         # Public API exports
│   ├── theme.py            # Theme loader and Rich Theme creation
│   ├── components.py       # Reusable UI components
│   └── design-tokens.yaml  # Design system configuration (single source of truth)
```

## Design Tokens (YAML Configuration)

All visual design decisions are centralized in `design-tokens.yaml`:

- **Colors**: Semantic color tokens (primary, success, error, etc.)
- **Typography**: Text styles (heading, body, code, etc.)
- **Components**: Component-specific styling (table, panel, progress, etc.)
- **Layout**: Spacing, borders, and layout rules

### Token Structure

```yaml
version: "1.0"

colors:
  # Semantic colors (by purpose)
  primary:
    base: "#2563EB"       # Blue-600
    foreground: "#FFFFFF"
  
  status:
    success: "#10B981"    # Green-500
    warning: "#F59E0B"    # Amber-500
    error: "#EF4444"      # Red-500
    info: "#3B82F6"       # Blue-500
  
  # UI element colors
  surface:
    background: "#1F2937"  # Gray-800
    foreground: "#F9FAFB"  # Gray-50
  
  border:
    default: "#4B5563"     # Gray-600
    accent: "#6366F1"      # Indigo-500

typography:
  heading:
    color: "primary.base"
    weight: "bold"
  
  body:
    color: "surface.foreground"
    weight: "normal"
  
  code:
    color: "#A78BFA"       # Purple-400
    background: "#374151"  # Gray-700

components:
  table:
    header:
      color: "primary.base"
      weight: "bold"
    border:
      color: "border.default"
      style: "rounded"
  
  panel:
    border:
      color: "border.default"
      style: "rounded"
    title:
      color: "primary.base"
      weight: "bold"
  
  progress:
    complete:
      color: "status.success"
    incomplete:
      color: "border.default"
    pulse:
      color: "primary.base"

layout:
  spacing:
    small: 1
    medium: 2
    large: 4
  
  borders:
    enabled: true
    default_style: "rounded"
```

## Component Library

### Core Components

All components are accessible via `from honk.ui import <component>`:

#### 1. Status Messages

```python
from honk.ui import success, error, warning, info

success("Operation completed successfully!")
error("Failed to connect to server")
warning("Deprecated feature in use")
info("Processing 100 items...")
```

#### 2. Panels (Grouping/Highlighting)

```python
from honk.ui import panel

panel("Important information", title="Notice", style="info")
panel("Error details here", title="Error", style="error")
```

#### 3. Tables

```python
from honk.ui import table

# Create a table
tbl = table(title="Results")
tbl.add_column("ID", justify="right")
tbl.add_column("Name")
tbl.add_column("Status")
tbl.add_row("1", "Item A", "✓ Complete")
tbl.render()
```

#### 4. Progress Indicators

```python
from honk.ui import progress, spinner

# Progress bar for known tasks
with progress() as p:
    task = p.add_task("Processing", total=100)
    for i in range(100):
        p.update(task, advance=1)

# Spinner for indeterminate tasks
with spinner("Loading..."):
    do_work()
```

#### 5. Lists

```python
from honk.ui import bullet_list, numbered_list

bullet_list(["First item", "Second item", "Third item"])
numbered_list(["Step one", "Step two", "Step three"])
```

#### 6. Key-Value Display

```python
from honk.ui import key_value

key_value({
    "Status": "Active",
    "Duration": "1.2s",
    "Items": "42"
})
```

#### 7. Dividers

```python
from honk.ui import divider

divider()  # Horizontal line
divider("Section Title")  # With label
```

### Result Envelope Rendering

Special component for rendering `ResultEnvelope` objects consistently:

```python
from honk.ui import render_result
from honk.result import ResultEnvelope

result = ResultEnvelope(...)
render_result(result, json_mode=False)  # Rich formatted
render_result(result, json_mode=True)   # JSON output
```

## Usage Patterns

### 1. Command Output Structure

**Standard pattern for command output:**

```python
from honk.ui import panel, key_value, success, divider

# 1. Show what's happening
panel("Running demo command", title="Honk Demo", style="info")

# 2. Show key information
key_value({
    "Target": "World",
    "Mode": "standard",
    "Run ID": "abc-123"
})

divider()

# 3. Show result
success("Command completed successfully!")

# 4. Show facts/output
key_value(result.facts)

# 5. Show next steps (if any)
if result.next:
    panel("\n".join(f"• honk {' '.join(step.run)}" for step in result.next),
          title="Try Next", style="info")
```

### 2. Error Handling

**Consistent error presentation:**

```python
from honk.ui import error, panel, bullet_list

error("Authentication failed")

panel(
    "The following issues were found:\n\n" +
    "\n".join(f"• {issue}" for issue in issues),
    title="Problems Detected",
    style="error"
)

# Remediation steps
panel(
    "To fix this:\n\n1. Run: honk auth login\n2. Try again",
    title="How to Fix",
    style="info"
)
```

### 3. Doctor Pack Results

**Visual presentation of prerequisite checks:**

```python
from honk.ui import table, success, error

tbl = table(title="Prerequisite Checks")
tbl.add_column("Pack", style="bold")
tbl.add_column("Status")
tbl.add_column("Duration")

for pack in pack_results:
    status_icon = "✓" if pack.status == "ok" else "✗"
    status_style = "success" if pack.status == "ok" else "error"
    tbl.add_row(
        pack.pack,
        f"[{status_style}]{status_icon} {pack.status}[/]",
        f"{pack.duration_ms}ms"
    )

tbl.render()
```

## Theming & Customization

### Theme Variants

The design system supports theme variants for different contexts:

- **Default**: Balanced for general use
- **Dark**: Optimized for dark terminals
- **Light**: Optimized for light terminals
- **Monochrome**: No colors (accessibility/plain output)
- **High Contrast**: Enhanced contrast (accessibility)

### Switching Themes

```python
from honk.ui import set_theme

set_theme("dark")     # Use dark variant
set_theme("default")  # Back to default
```

### Runtime Theme Override

```bash
# Via environment variable
export HONK_THEME=monochrome
honk demo hello

# Via CLI flag (if implemented)
honk --theme=high-contrast demo hello
```

## Design Principles

### 1. Consistency
- Same component for same purpose across all commands
- Predictable visual hierarchy
- Consistent color meanings (green = success, red = error)

### 2. Accessibility
- Text labels alongside colors
- Screen reader friendly (no ASCII art)
- High contrast mode available
- Keyboard navigation support

### 3. Scannability
- Clear visual hierarchy (titles, headings, body)
- Appropriate use of whitespace
- Important information stands out
- Tables for structured data

### 4. Feedback
- Clear success/error indicators
- Progress indication for long operations
- Contextual help and next steps
- Exit codes match visual feedback

### 5. Maintainability
- Single source of truth (design-tokens.yaml)
- Semantic tokens (not raw colors in code)
- Reusable components
- Easy to change globally

## Implementation Guidelines

### For Command Authors

1. **Use semantic components**, not raw Rich calls
2. **Never hardcode colors** - use theme tokens
3. **Structure output** consistently (title → info → result → next)
4. **Provide context** - users should understand what happened
5. **Include next steps** - guide users to next action

### For Component Authors

1. **Load styles from theme** - never hardcode
2. **Support all theme variants** - test with each
3. **Document component API** - clear usage examples
4. **Keep components focused** - single responsibility
5. **Make components composable** - panels can contain tables, etc.

## Migration Plan

### Phase 1: Foundation (Current)
- Create design-tokens.yaml
- Implement theme loader
- Build core components

### Phase 2: Adoption
- Migrate existing commands to use components
- Add render_result() helper
- Update documentation

### Phase 3: Enhancement
- Add theme variants
- Implement theme switching
- Add advanced components (tree, graph, etc.)

## Examples

See `src/honk/demo/hello.py` for a reference implementation using the design system.

## References

- [Rich Documentation](https://rich.readthedocs.io/)
- [PatternFly CLI Handbook](https://www.patternfly.org/developer-resources/cli-handbook/)
- [CLI Guidelines](https://clig.dev/)
