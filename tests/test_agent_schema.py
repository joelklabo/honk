"""Tests for agent.v1.json schema validation."""
import json
from pathlib import Path


class TestAgentSchema:
    """Test suite for agent schema validation."""

    def test_schema_file_exists(self):
        """Schema file should exist at schemas/agent.v1.json."""
        schema_path = Path("schemas/agent.v1.json")
        assert schema_path.exists(), f"Schema file not found at {schema_path}"

    def test_schema_is_valid_json(self):
        """Schema file should contain valid JSON."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        assert isinstance(schema, dict), "Schema should be a JSON object"

    def test_schema_has_required_fields(self):
        """Schema should have all required JSON Schema fields."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        
        # Check required JSON Schema fields
        assert "$schema" in schema, "Schema missing $schema field"
        assert "type" in schema, "Schema missing type field"
        assert "properties" in schema, "Schema missing properties field"
        assert "required" in schema, "Schema missing required field"
        
        # Check schema meta fields
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
        assert schema["type"] == "object"

    def test_schema_requires_only_description(self):
        """Schema should require only 'description' field per GitHub spec."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        
        assert schema["required"] == ["description"], \
            "Only 'description' should be required per GitHub Copilot spec"

    def test_schema_has_name_property(self):
        """Schema should define 'name' property with pattern validation."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        
        assert "name" in schema["properties"]
        name_prop = schema["properties"]["name"]
        assert name_prop["type"] == "string"
        assert "pattern" in name_prop
        assert name_prop["pattern"] == "^[a-z0-9-]+$"

    def test_schema_has_description_property(self):
        """Schema should define 'description' property with length constraints."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        
        assert "description" in schema["properties"]
        desc_prop = schema["properties"]["description"]
        assert desc_prop["type"] == "string"
        assert desc_prop["minLength"] == 10
        assert desc_prop["maxLength"] == 200

    def test_schema_has_tools_property(self):
        """Schema should define 'tools' property allowing array or string."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        
        assert "tools" in schema["properties"]
        tools_prop = schema["properties"]["tools"]
        assert "oneOf" in tools_prop
        
        # Should allow array of tool names OR string "*"
        assert len(tools_prop["oneOf"]) == 2

    def test_schema_has_metadata_property(self):
        """Schema should define 'metadata' property with category enum."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        
        assert "metadata" in schema["properties"]
        metadata_prop = schema["properties"]["metadata"]
        assert metadata_prop["type"] == "object"
        
        # Check category enum
        assert "category" in metadata_prop["properties"]
        category = metadata_prop["properties"]["category"]
        assert "enum" in category
        assert "research" in category["enum"]
        assert "testing" in category["enum"]

    def test_schema_has_mcp_servers_property(self):
        """Schema should define 'mcp-servers' property for MCP integration."""
        schema_path = Path("schemas/agent.v1.json")
        with open(schema_path) as f:
            schema = json.load(f)
        
        assert "mcp-servers" in schema["properties"]
        mcp_prop = schema["properties"]["mcp-servers"]
        assert mcp_prop["type"] == "object"
