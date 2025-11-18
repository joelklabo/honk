"""Integration tests for auth subsystem."""

import json
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from honk.cli import app

runner = CliRunner()


class TestAuthCommandStructure:
    """Test auth command structure and integration."""

    def test_auth_help_shows_providers(self):
        """Test that auth help shows both GitHub and Azure providers."""
        result = runner.invoke(app, ["auth", "--help"])
        
        assert result.exit_code == 0
        assert "gh" in result.stdout
        assert "az" in result.stdout
        assert "GitHub" in result.stdout or "Azure" in result.stdout

    def test_gh_help_shows_commands(self):
        """Test that gh help shows all commands."""
        result = runner.invoke(app, ["auth", "gh", "--help"])
        
        assert result.exit_code == 0
        assert "status" in result.stdout
        assert "login" in result.stdout
        assert "refresh" in result.stdout
        assert "logout" in result.stdout

    def test_az_help_shows_commands(self):
        """Test that az help shows all commands."""
        result = runner.invoke(app, ["auth", "az", "--help"])
        
        assert result.exit_code == 0
        assert "status" in result.stdout
        assert "login" in result.stdout
        assert "refresh" in result.stdout
        assert "logout" in result.stdout


class TestGitHubWorkflow:
    """Test complete GitHub auth workflow."""

    @patch("honk.auth.providers.github.subprocess.run")
    def test_complete_workflow(self, mock_run):
        """Test status -> login -> status -> logout workflow."""
        # Step 1: Check status (not logged in)
        version_result = Mock()
        version_result.returncode = 0
        
        status_fail = Mock()
        status_fail.returncode = 1
        status_fail.stderr = "Not logged in"
        
        # Step 2: Login
        login_result = Mock()
        login_result.returncode = 0
        
        # Step 3: Check status (logged in)
        status_success = Mock()
        status_success.returncode = 0
        status_success.stdout = "✓ Logged in to github.com as testuser"
        
        # Step 4: Logout
        logout_result = Mock()
        logout_result.returncode = 0
        
        mock_run.side_effect = [
            # status (not logged in)
            version_result, status_fail,
            # login
            login_result, version_result, status_success, status_success,
            # status (logged in)
            version_result, status_success, status_success,
            # logout
            logout_result, status_fail,
        ]
        
        # Check initial status (should fail)
        result = runner.invoke(app, ["auth", "gh", "status", "--json"])
        assert result.exit_code == 11  # needs_auth
        output = json.loads(result.stdout)
        assert output["status"] == "needs_auth"
        
        # Login
        result = runner.invoke(app, ["auth", "gh", "login", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["changed"] is True
        
        # Check status again (should succeed)
        result = runner.invoke(app, ["auth", "gh", "status", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        
        # Logout
        result = runner.invoke(app, ["auth", "gh", "logout", "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["changed"] is True


class TestAzureWorkflow:
    """Test complete Azure DevOps auth workflow."""

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_complete_workflow(self, mock_run):
        """Test status -> login -> status workflow."""
        org = "https://dev.azure.com/test-org"
        
        # Step 1: Check status (not logged in to Azure)
        version_result = Mock()
        version_result.returncode = 0
        
        account_fail = Mock()
        account_fail.returncode = 1
        account_fail.stderr = "Please run 'az login'"
        
        # Step 2: Login (assuming Azure login is done, just PAT)
        account_success = Mock()
        account_success.returncode = 0
        account_success.stdout = json.dumps({"user": {"name": "user@example.com"}})
        
        login_result = Mock()
        login_result.returncode = 0
        
        project_result = Mock()
        project_result.returncode = 0
        project_result.stdout = json.dumps({"value": [{"name": "TestProject"}]})
        
        mock_run.side_effect = [
            # status (not logged in)
            version_result, account_fail,
            # login
            account_success, login_result, version_result, account_success, project_result,
            # status (logged in)
            version_result, account_success, project_result,
        ]
        
        # Check initial status (should fail)
        result = runner.invoke(app, ["auth", "az", "status", "--org", org, "--json"])
        assert result.exit_code == 11  # needs_auth
        output = json.loads(result.stdout)
        assert output["status"] == "needs_auth"
        
        # Login
        result = runner.invoke(app, ["auth", "az", "login", "--org", org, "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["changed"] is True
        
        # Check status again (should succeed)
        result = runner.invoke(app, ["auth", "az", "status", "--org", org, "--json"])
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"


class TestResultEnvelopeContract:
    """Test that auth commands follow result envelope contract."""

    @patch("honk.auth.providers.github.subprocess.run")
    def test_gh_status_json_has_required_fields(self, mock_run):
        """Test gh status JSON output has all required fields."""
        # Mock successful status
        version_result = Mock()
        version_result.returncode = 0
        
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.com as testuser"
        
        mock_run.side_effect = [version_result, status_result, status_result]
        
        result = runner.invoke(app, ["auth", "gh", "status", "--json"])
        assert result.exit_code == 0
        
        output = json.loads(result.stdout)
        
        # Check required envelope fields
        assert "version" in output
        assert "command" in output
        assert "status" in output
        assert "changed" in output
        assert "code" in output
        assert "summary" in output
        assert "run_id" in output
        assert "duration_ms" in output
        assert "facts" in output
        
        # Check auth-specific facts
        assert "auth" in output["facts"]
        assert "provider" in output["facts"]["auth"]
        assert "status" in output["facts"]["auth"]

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_az_status_json_has_required_fields(self, mock_run):
        """Test az status JSON output has all required fields."""
        import json as json_lib
        
        # Mock successful status
        version_result = Mock()
        version_result.returncode = 0
        
        account_result = Mock()
        account_result.returncode = 0
        account_result.stdout = json_lib.dumps({"user": {"name": "user@example.com"}})
        
        project_result = Mock()
        project_result.returncode = 0
        project_result.stdout = json_lib.dumps({"value": [{"name": "Test"}]})
        
        mock_run.side_effect = [version_result, account_result, project_result]
        
        result = runner.invoke(app, ["auth", "az", "status", "--org", "https://dev.azure.com/test", "--json"])
        assert result.exit_code == 0
        
        output = json.loads(result.stdout)
        
        # Check required envelope fields
        assert "version" in output
        assert "command" in output
        assert "status" in output
        assert "changed" in output
        assert "code" in output
        assert "summary" in output
        assert "run_id" in output
        assert "duration_ms" in output
        assert "facts" in output
        
        # Check auth-specific facts
        assert "auth" in output["facts"]
        assert "provider" in output["facts"]["auth"]
        assert "status" in output["facts"]["auth"]
