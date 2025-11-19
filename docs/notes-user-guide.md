# Honk Notes - AI-Assisted Note-Taking 🤖

**Terminal-based note-taking with automatic AI organization**

Honk Notes is a beautiful, flicker-free terminal UI for taking and organizing notes using GitHub Copilot's AI. It automatically reorganizes your notes into clean, structured markdown after you stop typing.

---

## ✨ Features

- **🎨 Beautiful TUI** - Polished interface using Honk's design system
- **🤖 AI Organization** - Automatic note reorganization via GitHub Copilot
- **⚡ Real-time Editing** - Smooth, flicker-free markdown editing
- **💾 Auto-save** - Never lose your work (debounced to avoid spam)
- **⏱️ Smart Idle Detection** - AI kicks in after 30s of inactivity (configurable)
- **🎯 Event-driven** - No polling, all updates triggered by events
- **⌨️ Keyboard Shortcuts** - Vim-inspired efficient workflows

---

## 🚀 Quick Start

### Launch the Editor

```bash
# Edit or create a file
honk notes edit meeting-notes.md

# Edit with custom idle timeout
honk notes edit --idle 60 notes.md

# Edit without auto-save
honk notes edit --no-auto-save draft.md
```

### Organize Existing File (Non-interactive)

```bash
# Organize and save in-place
honk notes organize messy-notes.md

# Organize to new file
honk notes organize draft.md -o organized.md

# Preview without saving
honk notes organize notes.md --dry-run
```

---

## ⌨️ Keyboard Shortcuts

| Shortcut | Action | Description |
|----------|--------|-------------|
| `Ctrl+O` | Organize Now | Manually trigger AI organization |
| `Ctrl+S` | Save | Manually save file |
| `Ctrl+Z` | Undo | Undo last change |
| `Ctrl+Q` | Quit | Exit the editor |

---

## 🎯 How It Works

### Automatic Organization

1. **Type your notes** freely - bullets, ideas, meeting notes, whatever
2. **Stop typing for 30 seconds** (configurable)
3. **AI automatically organizes** your notes into:
   - Clear sections with headers (`##`)
   - Grouped related items
   - Action items with checkboxes (`[ ]`)
   - Important notes as blockquotes (`>`)
   - Better structure and scannability

### Manual Organization

Press `Ctrl+O` anytime to manually trigger AI organization without waiting.

### Auto-save

Changes are automatically saved 2 seconds after you stop typing (debounced to avoid excessive writes).

---

## 🎨 Visual Design

Honk Notes uses Honk's design system for consistent, professional appearance:

- **Brand Colors** - Cyan accents for interactive elements
- **Semantic Tokens** - Meaningful colors (success = green, error = red)
- **Progress Indicators** - Beautiful spinners and progress bars
- **Smooth Animations** - Flicker-free updates

```
┌─────────────────────────────────────────────────────────┐
│ Honk Notes - meeting-notes.md                     [⚡]  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  # Team Standup Notes                                   │
│                                                         │
│  ## Action Items                                        │
│  - [ ] Review PR #123                                   │
│  - [ ] Fix login bug                                    │
│  - [ ] Update docs                                      │
│                                                         │
│  ## Discussion                                          │
│  • Deployment scheduled for Friday                      │
│  • Need to backup database first                        │
│                                                         │
│  > Important: Remember team meeting at 3pm              │
│                                                         │
├─────────────────────────────────────────────────────────┤
│ Idle: 0s | ^O Organize | ^S Save                  [✓]  │
└─────────────────────────────────────────────────────────┘
```

---

## 🛠️ Configuration

### Custom Idle Timeout

```bash
# Wait 60 seconds instead of 30
honk notes edit --idle 60 notes.md
```

### Custom AI Prompt

Create a custom prompt template:

```bash
# custom-prompt.txt
Organize these notes concisely:
{content}
Use bullet points and keep it brief.
```

```bash
honk notes edit --prompt custom-prompt.txt notes.md
```

### Disable Auto-save

```bash
honk notes edit --no-auto-save draft.md
```

---

## 📖 Usage Examples

### Meeting Notes

```bash
# During meeting, type freely:
- discussed API redesign
- bob suggested GraphQL
- alice prefers REST
- need to decide by Friday
- important: backwards compatibility

# After 30s idle, AI organizes to:

## Meeting Summary

### API Redesign Discussion

**Options Discussed:**
- GraphQL (suggested by Bob)
- REST (preferred by Alice)

### Action Items
- [ ] Make architecture decision by Friday

> Important: Ensure backwards compatibility
```

### Daily Journal

```bash
# Your raw notes:
woke up early
good workout
productive coding session
learned about Swift actors
need to review PR
dinner with team was fun

# AI organizes to:

## Daily Journal - [Date]

### Morning
- Woke up early
- Good workout

### Work
- Productive coding session
- Learned about Swift actors
- [ ] Review PR

### Evening
- Dinner with team was fun
```

### Project Planning

```bash
# Brainstorm dump:
need user auth
dashboard for analytics
payment integration
mobile app eventually
testing important
deploy to cloud
performance monitoring

# AI structures it:

## Project Plan

### Core Features
- User authentication
- Analytics dashboard
- Payment integration

### Quality & Operations
- Comprehensive testing
- Performance monitoring
- Cloud deployment

### Future Enhancements
- Mobile app
```

---

## 🐛 Troubleshooting

### AI Organization Not Working

**Problem**: Notes aren't being organized after idle timeout

**Solutions**:
1. Check GitHub Copilot CLI is installed: `copilot --version`
2. Verify authentication: `gh auth status`
3. Try manual organization: Press `Ctrl+O`
4. Check console for errors

### File Won't Save

**Problem**: Changes aren't being saved

**Solutions**:
1. Check file permissions: `ls -la yourfile.md`
2. Verify disk space: `df -h`
3. Try manual save: `Ctrl+S`
4. Check terminal output for error messages

### Editor Feels Slow

**Problem**: Typing or updates feel laggy

**Solutions**:
1. Check file size (works best with <1MB files)
2. Close other terminal applications
3. Try disabling auto-save: `--no-auto-save`

### Progress Indicator Doesn't Show

**Problem**: No visual feedback during AI processing

**Solutions**:
1. Check if `NO_COLOR` environment variable is set
2. Verify terminal supports colors
3. Try different terminal (iTerm2, Terminal.app)

---

## 🔧 Advanced Usage

### Integration with Other Tools

**Git integration:**
```bash
# Take notes during code review
honk notes edit review-$(git rev-parse --short HEAD).md
```

**Task management:**
```bash
# Extract action items
honk notes organize meeting.md | grep "- \[ \]" > tasks.md
```

**Scripting:**
```bash
# Batch organize all markdown files
for file in *.md; do
  honk notes organize "$file"
done
```

---

## 🎯 Best Practices

### For Best Results

1. **Write naturally** - Don't worry about formatting while taking notes
2. **Be concise** - AI works best with clear, brief notes
3. **Use keywords** - Include important terms and names
4. **Let AI structure** - Focus on content, let AI handle organization
5. **Review after organization** - AI isn't perfect, verify important details

### What Works Well

- ✅ Meeting notes and discussions
- ✅ Brainstorming sessions
- ✅ Daily journals and logs
- ✅ Project planning
- ✅ Learning notes
- ✅ Task lists and TODOs

### What Doesn't Work Well

- ❌ Code snippets (use proper code blocks manually)
- ❌ Tables (AI may restructure poorly)
- ❌ Precise formatting requirements
- ❌ Very long documents (>10,000 lines)

---

## 🤝 Contributing

Found a bug or have a feature request? 

1. Check existing issues
2. Create detailed bug report or feature request
3. Include terminal output and steps to reproduce

---

## 📚 Learn More

- **Honk Documentation**: See main README
- **GitHub Copilot**: https://github.com/features/copilot
- **Textual Framework**: https://textual.textualize.io
- **Design System**: `src/honk/ui/theme.py`

---

## 🎉 Happy Note-Taking!

Honk Notes combines the simplicity of terminal editing with the power of AI organization. Focus on capturing ideas, let the AI handle the structure.

**Questions? Issues? Ideas?** Open an issue on GitHub!
