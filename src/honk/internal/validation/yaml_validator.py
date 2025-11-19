import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from jsonschema import validate, ValidationError

class ValidationResult:
    """Represents the result of a YAML frontmatter validation."""
    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.errors = errors if errors is not None else []

    @property
    def valid(self) -> bool:
        return self.is_valid

    def __bool__(self) -> bool:
        return self.is_valid

class YAMLFrontmatterValidator:
    """
    Validates YAML frontmatter in markdown files against a JSON schema.
    """
    def __init__(self, schema_path: Path):
        self.schema_path = schema_path
        self._schema: Optional[Dict[str, Any]] = None

    @property
    def schema(self) -> Dict[str, Any]:
        if self._schema is None:
            with open(self.schema_path, 'r') as f:
                self._schema = yaml.safe_load(f)
        return self._schema

    def validate_file(self, file_path: Path) -> ValidationResult:
        """
        Reads a file, extracts YAML frontmatter, and validates it.
        """
        if not file_path.exists():
            return ValidationResult(False, [f"File not found: {file_path}"])

        content = file_path.read_text()
        frontmatter_match = re.search(r"^\s*---\s*\n(?P<frontmatter>.*?)\n*---\s*", content, re.DOTALL)

        if not frontmatter_match:
            return ValidationResult(False, ["No YAML frontmatter found."])

        frontmatter_str = frontmatter_match.group('frontmatter')
        
        try:
            frontmatter_data = yaml.safe_load(frontmatter_str)
            if frontmatter_data is None: # Handle empty frontmatter block
                frontmatter_data = {}
        except yaml.YAMLError as e:
            return ValidationResult(False, [f"Invalid YAML in frontmatter: {e}"])

        if not isinstance(frontmatter_data, dict):
            return ValidationResult(False, ["Frontmatter is not a valid YAML object (must be a dictionary)."])

        try:
            validate(instance=frontmatter_data, schema=self.schema)
            return ValidationResult(True)
        except ValidationError as e:
            errors = [f"Validation Error: {e.message} (Path: {e.path})"]
            return ValidationResult(False, errors)
        except Exception as e:
            return ValidationResult(False, [f"An unexpected error occurred during validation: {e}"])

