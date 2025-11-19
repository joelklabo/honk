from pathlib import Path
from string import Template
from typing import Dict, Any, List

class TemplateEngine:
    """
    Simple template engine for rendering files with variable substitution.
    Supports basic Jinja2-like variable substitution (e.g., ${VARIABLE_NAME}).
    """
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        if not self.template_dir.is_dir():
            raise ValueError(f"Template directory not found: {template_dir}")

    def render(self, template_name: str, context: Dict[str, Any]) -> str:
        """
        Renders a template file with the given context.
        Variables in the template should be in the format ${VARIABLE_NAME}.
        """
        template_path = self.template_dir / template_name
        if not template_path.is_file():
            raise FileNotFoundError(f"Template file not found: {template_path}")

        template_content = template_path.read_text()
        template = Template(template_content)
        
        # Perform substitution. Missing keys will raise KeyError.
        # For more Jinja2-like behavior (e.g., silent missing keys),
        # a more complex implementation or actual Jinja2 would be needed.
        return template.substitute(context)

    def validate_template(self, template_name: str, required_vars: List[str]) -> None:
        """
        Validates if a template contains all required variables.
        This is a basic check and can be enhanced.
        """
        template_path = self.template_dir / template_name
        if not template_path.is_file():
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        template_content = template_path.read_text()
        
        for var in required_vars:
            if f"${{{var}}}" not in template_content:
                raise ValueError(f"Template '{template_name}' is missing required variable: ${{{var}}}")
