"""Contract tests for JSON schema validation."""

import json
import subprocess
import jsonschema
from pathlib import Path


def test_result_envelope_schema_validates_demo_hello():
    """Test that honk demo hello --json output validates against result schema."""
    # Load schema
    schema_path = Path("schemas/result.v1.json")
    with open(schema_path) as f:
        schema = json.load(f)
    
    # Get actual output from command
    result = subprocess.run(
        ["uv", "run", "honk", "demo", "hello", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    
    # Validate
    jsonschema.validate(output, schema)
    
    # Assert key fields exist
    assert output["version"] == "1.0"
    assert output["status"] == "ok"
    assert "command" in output
    assert "facts" in output


def test_result_envelope_schema_validates_version_json():
    """Test that honk version --json output validates against result schema."""
    schema_path = Path("schemas/result.v1.json")
    with open(schema_path) as f:
        schema = json.load(f)
    
    result = subprocess.run(
        ["uv", "run", "honk", "version", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    
    jsonschema.validate(output, schema)
    assert output["version"] == "1.0"
    assert output["facts"]["honk_version"] == "0.1.0"


def test_result_envelope_schema_validates_info_json():
    """Test that honk info --json output validates against result schema."""
    schema_path = Path("schemas/result.v1.json")
    with open(schema_path) as f:
        schema = json.load(f)
    
    result = subprocess.run(
        ["uv", "run", "honk", "info", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    
    jsonschema.validate(output, schema)
    assert output["version"] == "1.0"
    assert output["facts"]["name"] == "honk"


def test_introspection_schema_validates_introspect_json():
    """Test that honk introspect --json output validates against introspection schema."""
    schema_path = Path("schemas/introspect.v1.json")
    with open(schema_path) as f:
        schema = json.load(f)
    
    result = subprocess.run(
        ["uv", "run", "honk", "introspect", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    
    jsonschema.validate(output, schema)
    
    # Assert structure
    assert output["version"] == "1.0"
    assert "commands" in output
    assert len(output["commands"]) > 0
    
    # Check first command has required fields
    cmd = output["commands"][0]
    assert "area" in cmd
    assert "tool" in cmd
    assert "action" in cmd
    assert "full_path" in cmd
    assert "description" in cmd


def test_doctor_json_output_validates():
    """Test that honk doctor --json output validates against result schema."""
    schema_path = Path("schemas/result.v1.json")
    with open(schema_path) as f:
        schema = json.load(f)
    
    result = subprocess.run(
        ["uv", "run", "honk", "doctor", "--json"],
        capture_output=True,
        text=True,
        check=True,
    )
    output = json.loads(result.stdout)
    
    jsonschema.validate(output, schema)
    assert "pack_results" in output
