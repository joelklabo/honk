import pytest
from pathlib import Path
import json

from honk.internal.validation.yaml_validator import YAMLFrontmatterValidator, ValidationResult

@pytest.fixture
def valid_schema_path(tmp_path) -> Path:
    """Fixture for a valid agent schema file."""
    schema_content = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "description": {"type": "string"},
            "tools": {"type": "array", "items": {"type": "string"}}
        },
        "required": ["name", "description"]
    }
    schema_file = tmp_path / "test_schema.json"
    with open(schema_file, 'w') as f:
        json.dump(schema_content, f)
    return schema_file

@pytest.fixture
def invalid_schema_path(tmp_path) -> Path:
    """Fixture for an invalid schema file (e.g., malformed JSON)."""
    schema_file = tmp_path / "invalid_schema.json"
    schema_file.write_text("{invalid json")
    return schema_file

@pytest.fixture
def validator(valid_schema_path) -> YAMLFrontmatterValidator:
    """Fixture for a YAMLFrontmatterValidator instance."""
    return YAMLFrontmatterValidator(schema_path=valid_schema_path)

class TestYAMLFrontmatterValidator:
    """Tests for the YAMLFrontmatterValidator."""

    def test_validator_initialization(self, valid_schema_path):
        """Test validator initializes correctly."""
        validator = YAMLFrontmatterValidator(schema_path=valid_schema_path)
        assert validator.schema_path == valid_schema_path
        assert validator._schema is None # Schema loaded lazily

    def test_schema_loading(self, validator):
        """Test schema is loaded correctly on first access."""
        assert validator.schema is not None
        assert "name" in validator.schema["properties"]

    def test_validate_file_not_found(self, validator, tmp_path):
        """Test validation fails for a non-existent file."""
        non_existent_file = tmp_path / "non_existent.md"
        result = validator.validate_file(non_existent_file)
        assert not result.valid
        assert "File not found" in result.errors[0]

    def test_validate_no_frontmatter(self, validator, tmp_path):
        """Test validation fails if no YAML frontmatter is present."""
        file_content = "This is some content without frontmatter."
        test_file = tmp_path / "no_frontmatter.md"
        test_file.write_text(file_content)
        result = validator.validate_file(test_file)
        assert not result.valid
        assert "No YAML frontmatter found." in result.errors[0]

    def test_validate_invalid_yaml(self, validator, tmp_path):
        """Test validation fails for malformed YAML frontmatter."""
        file_content = """---
name: test-agent
description: "A test agent"
tools:
  - read
  - search
invalid_key: : invalid value
---
Content.
"""
        test_file = tmp_path / "invalid_yaml.md"
        test_file.write_text(file_content)
        result = validator.validate_file(test_file)
        assert not result.valid
        assert "Invalid YAML in frontmatter" in result.errors[0]

    def test_validate_valid_frontmatter(self, validator, tmp_path):
        """Test validation succeeds for valid YAML frontmatter."""
        file_content = """---
name: test-agent
description: "A test agent"
tools:
  - read
  - search
---
Content.
"""
        test_file = tmp_path / "valid_frontmatter.md"
        test_file.write_text(file_content)
        result = validator.validate_file(test_file)
        assert result.valid
        assert not result.errors

    def test_validate_missing_required_field(self, validator, tmp_path):
        """Test validation fails if a required field is missing."""
        file_content = """---
name: test-agent
tools:
  - read
---
Content.
"""
        test_file = tmp_path / "missing_field.md"
        test_file.write_text(file_content)
        result = validator.validate_file(test_file)
        assert not result.valid
        assert "Validation Error: 'description' is a required property" in result.errors[0]

    def test_validate_invalid_type(self, validator, tmp_path):
        """Test validation fails if a field has an incorrect type."""
        file_content = """---
name: test-agent
description: "A test agent"
tools: "read" # Should be an array
---
Content.
"""
        test_file = tmp_path / "invalid_type.md"
        test_file.write_text(file_content)
        result = validator.validate_file(test_file)
        assert not result.valid
        assert "Validation Error: 'read' is not of type 'array'" in result.errors[0]

    def test_validate_empty_frontmatter_data(self, validator, tmp_path):
        """Test validation fails if frontmatter is empty."""
        file_content = """---
---
Content.
"""
        test_file = tmp_path / "empty_frontmatter.md"
        test_file.write_text(file_content)
        result = validator.validate_file(test_file)
        assert not result.valid
        assert "Validation Error: 'name' is a required property" in result.errors[0]
