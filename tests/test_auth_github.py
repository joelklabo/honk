"""Tests for GitHub authentication provider."""

import json
from unittest.mock import Mock, patch
from typer.testing import CliRunner

from honk.cli import app

runner = CliRunner()


class TestGitHubAuthStatus:
    """Test GitHub auth status command."""

    @patch("honk.auth.providers.github.subprocess.run")
    def test_status_when_authenticated(self, mock_run):
        """Test status shows valid when user is authenticated."""
        # Mock gh --version (check)
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "gh version 2.0.0"
        
        # Mock gh auth status (check auth)
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.com as testuser (oauth_token)\n  - Token: gho_****\n  - Token scopes: repo, read:org, gist"
        
        # Return different mocks for different calls
        mock_run.side_effect = [version_result, status_result, status_result]

        result = runner.invoke(app, ["auth", "gh", "status", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["facts"]["auth"]["status"] == "valid"
        assert output["facts"]["auth"]["user"] == "testuser"
        assert output["facts"]["auth"]["hostname"] == "github.com"

    @patch("honk.auth.providers.github.subprocess.run")
    def test_status_when_not_authenticated(self, mock_run):
        """Test status shows missing when not authenticated."""
        # Mock gh --version (check)
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "gh version 2.0.0"
        
        # Mock gh auth status failure
        status_result = Mock()
        status_result.returncode = 1
        status_result.stderr = "You are not logged into any GitHub hosts"
        
        mock_run.side_effect = [version_result, status_result]

        result = runner.invoke(app, ["auth", "gh", "status", "--json"])
        
        assert result.exit_code == 11  # EXIT_NEEDS_AUTH
        output = json.loads(result.stdout)
        assert output["status"] == "needs_auth"
        assert output["facts"]["auth"]["status"] == "missing"
        assert "next" in output
        assert any("login" in step["summary"] for step in output["next"])

    @patch("honk.auth.providers.github.subprocess.run")
    def test_status_with_hostname_parameter(self, mock_run):
        """Test status with specific hostname."""
        # Mock gh --version
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "gh version 2.0.0"
        
        # Mock gh auth status for custom hostname
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.example.com as testuser (oauth_token)"
        
        mock_run.side_effect = [version_result, status_result, status_result]

        result = runner.invoke(app, ["auth", "gh", "status", "--hostname", "github.example.com", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["facts"]["auth"]["hostname"] == "github.example.com"

    # TODO: Add test_status_shows_expiry_warning when expiry tracking is implemented
    # See docs/spec-auth.md for specification


class TestGitHubAuthLogin:
    """Test GitHub auth login command."""

    @patch("honk.auth.providers.github.subprocess.run")
    def test_login_interactive_success(self, mock_run):
        """Test interactive login flow."""
        # Mock gh auth login success
        login_result = Mock()
        login_result.returncode = 0
        login_result.stdout = "✓ Logged in as testuser"
        
        # Mock status check after login
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "gh version 2.0.0"
        
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.com as testuser (oauth_token)\n  - Token scopes: repo, read:org, gist"
        
        mock_run.side_effect = [login_result, version_result, status_result, status_result]

        result = runner.invoke(app, ["auth", "gh", "login", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["changed"] is True

    @patch("honk.auth.providers.github.subprocess.run")
    def test_login_with_scopes(self, mock_run):
        """Test login with specific scopes."""
        # Mock gh auth login success
        login_result = Mock()
        login_result.returncode = 0
        login_result.stdout = "✓ Logged in"
        
        # Mock status check after login
        version_result = Mock()
        version_result.returncode = 0
        
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.com as testuser"
        
        mock_run.side_effect = [login_result, version_result, status_result, status_result]

        result = runner.invoke(app, ["auth", "gh", "login", "--scopes", "repo,workflow", "--json"])
        
        assert result.exit_code == 0
        # Verify gh auth login was called with correct scopes
        call_args = mock_run.call_args_list[0][0][0]
        assert "gh" in call_args
        assert "login" in call_args
        assert "--scopes" in call_args


class TestGitHubAuthRefresh:
    """Test GitHub auth refresh command."""

    @patch("honk.auth.providers.github.subprocess.run")
    def test_refresh_scopes_success(self, mock_run):
        """Test refreshing token with additional scopes."""
        # Mock initial status check
        version_result = Mock()
        version_result.returncode = 0
        
        status_check = Mock()
        status_check.returncode = 0
        status_check.stdout = "✓ Logged in to github.com as testuser"
        
        # Mock gh auth refresh
        refresh_result = Mock()
        refresh_result.returncode = 0
        refresh_result.stdout = "✓ Refreshed scopes"
        
        # Mock final status check
        final_status = Mock()
        final_status.returncode = 0
        final_status.stdout = "✓ Logged in to github.com as testuser\n  - Token scopes: repo, admin:org"
        
        mock_run.side_effect = [version_result, status_check, status_check, refresh_result, version_result, final_status, final_status]

        result = runner.invoke(app, ["auth", "gh", "refresh", "--scopes", "admin:org", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["changed"] is True

    @patch("honk.auth.providers.github.subprocess.run")
    def test_refresh_failure(self, mock_run):
        """Test refresh failure when not authenticated."""
        # Mock initial status check showing not authenticated
        version_result = Mock()
        version_result.returncode = 0
        
        status_check = Mock()
        status_check.returncode = 1
        status_check.stderr = "Not authenticated"
        
        mock_run.side_effect = [version_result, status_check]

        result = runner.invoke(app, ["auth", "gh", "refresh", "--json"])
        
        assert result.exit_code == 11  # EXIT_NEEDS_AUTH
        output = json.loads(result.stdout)
        assert output["status"] == "needs_auth"


class TestGitHubAuthLogout:
    """Test GitHub auth logout command."""

    @patch("honk.auth.providers.github.subprocess.run")
    def test_logout_success(self, mock_run):
        """Test successful logout."""
        # Mock gh auth logout
        logout_result = Mock()
        logout_result.returncode = 0
        logout_result.stdout = "✓ Logged out"
        
        # Mock status check (will fail after logout)
        status_result = Mock()
        status_result.returncode = 1
        status_result.stderr = "Not logged in"
        
        mock_run.side_effect = [logout_result, status_result]

        result = runner.invoke(app, ["auth", "gh", "logout", "--json"])
        
        assert result.exit_code == 0
        output = json.loads(result.stdout)
        assert output["status"] == "ok"
        assert output["changed"] is True

    @patch("honk.auth.providers.github.subprocess.run")
    def test_logout_with_hostname(self, mock_run):
        """Test logout from specific hostname."""
        # Mock gh auth logout with hostname
        logout_result = Mock()
        logout_result.returncode = 0
        logout_result.stdout = "✓ Logged out"
        
        status_result = Mock()
        status_result.returncode = 1
        
        mock_run.side_effect = [logout_result, status_result]

        result = runner.invoke(app, ["auth", "gh", "logout", "--hostname", "github.example.com", "--json"])
        
        assert result.exit_code == 0
        # Verify gh auth logout was called with correct hostname
        call_args = mock_run.call_args_list[0][0][0]
        assert "gh" in call_args
        assert "logout" in call_args
        assert "--hostname" in call_args
