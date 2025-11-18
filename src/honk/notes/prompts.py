"""AI prompt templates for note organization."""

DEFAULT_ORGANIZE_PROMPT = """Organize the following notes into clear, structured sections.

Guidelines:
- Use markdown headers (##) for main sections
- Group related items together logically
- Add checkboxes [ ] for action items
- Add > blockquotes for important notes
- Preserve all original information
- Make it more scannable and organized

Notes to organize:
{content}

Return only the organized markdown, no explanations."""
