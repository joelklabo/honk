"""Tests for Azure DevOps authentication provider."""

import json
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from honk.cli import app

runner = CliRunner()


class TestAzureAuthStatus:
    """Test Azure DevOps auth status command."""

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_status_when_authenticated(self, mock_run):
        """Test status shows valid when user is authenticated."""
        # Mock az --version check
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "azure-cli 2.50.0"
        
        # Mock az account show (check Azure login)
        account_result = Mock()
        account_result.returncode = 0
        account_result.stdout = json.dumps({
            "user": {"name": "user@example.com"},
            "id": "subscription-id"
        })
        
        # Mock az devops project list (check PAT)
        project_result = Mock()
        project_result.returncode = 0
        project_result.stdout = json.dumps({"value": [{"name": "TestProject"}]})
        
        mock_run.side_effect = [version_result, account_result, project_result]

        result = runner.invoke(app, ["auth", "az", "status", "--org", "https://dev.azure.com/test-org", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["facts"]["auth"]["status"] == "valid"
        assert output["facts"]["auth"]["org"] == "https://dev.azure.com/test-org"

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_status_when_not_authenticated(self, mock_run):
        """Test status shows missing when not authenticated."""
        # Mock az --version
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "azure-cli 2.50.0"
        
        # Mock az account show failure
        account_result = Mock()
        account_result.returncode = 1
        account_result.stderr = "Please run 'az login'"
        
        mock_run.side_effect = [version_result, account_result]

        result = runner.invoke(app, ["auth", "az", "status", "--org", "https://dev.azure.com/test-org", "--json"])
        
        assert result.exit_code == 11  # EXIT_NEEDS_AUTH
        output = json.loads(result.stdout)
        assert output["status"] == "needs_auth"
        assert output["facts"]["auth"]["status"] == "missing"
        assert "next" in output
        assert any("login" in step["summary"] for step in output["next"])


class TestAzureAuthLogin:
    """Test Azure DevOps auth login command."""

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_login_success(self, mock_run):
        """Test successful login."""
        # Mock az devops login
        login_result = Mock()
        login_result.returncode = 0
        login_result.stdout = "✓ Logged in"
        
        # Mock status check after login
        version_result = Mock()
        version_result.returncode = 0
        
        account_result = Mock()
        account_result.returncode = 0
        account_result.stdout = json.dumps({"user": {"name": "user@example.com"}})
        
        project_result = Mock()
        project_result.returncode = 0
        project_result.stdout = json.dumps({"value": [{"name": "TestProject"}]})
        
        mock_run.side_effect = [login_result, version_result, account_result, project_result]

        result = runner.invoke(app, ["auth", "az", "login", "--org", "https://dev.azure.com/test-org", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["changed"] is True


class TestAzureAuthRefresh:
    """Test Azure DevOps auth refresh command."""

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_refresh_requires_new_pat(self, mock_run):
        """Test that refresh explains PATs cannot be extended."""
        # Azure PATs can't be refreshed, only recreated
        # This test ensures proper messaging
        result = runner.invoke(app, ["auth", "az", "refresh", "--org", "https://dev.azure.com/test-org", "--json"])
        
        # Should explain that PATs must be recreated
        assert result.exit_code in [0, 11]  # Either ok or needs_auth
        if result.exit_code == 0:
            output = json.loads(result.stdout)
            # Should have guidance about PAT recreation
            assert "next" in output or "message" in output["summary"]


class TestAzureAuthLogout:
    """Test Azure DevOps auth logout command."""

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_logout_success(self, mock_run):
        """Test successful logout."""
        # Mock az devops logout
        logout_result = Mock()
        logout_result.returncode = 0
        logout_result.stdout = "✓ Logged out"
        
        mock_run.return_value = logout_result

        result = runner.invoke(app, ["auth", "az", "logout", "--org", "https://dev.azure.com/test-org", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["changed"] is True
