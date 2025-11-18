"""Tests for auth doctor packs."""

from unittest.mock import Mock, patch

from honk.auth.doctor import create_github_auth_pack, create_azure_auth_pack


class TestGitHubAuthDoctorPack:
    """Test GitHub auth doctor pack."""

    @patch("honk.auth.providers.github.subprocess.run")
    def test_pack_passes_when_authenticated(self, mock_run):
        """Test pack passes when user is authenticated."""
        # Mock gh CLI responses
        version_result = Mock()
        version_result.returncode = 0
        version_result.stdout = "gh version 2.0.0"
        
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.com as testuser"
        
        mock_run.side_effect = [version_result, status_result, status_result]
        
        pack = create_github_auth_pack()
        result = pack.run(plan=False)
        checks = result.checks
        
        assert len(checks) >= 1
        assert checks[0].passed
        assert "testuser" in checks[0].message or "Authenticated" in checks[0].message

    @patch("honk.auth.providers.github.subprocess.run")
    def test_pack_fails_when_not_authenticated(self, mock_run):
        """Test pack fails when user is not authenticated."""
        # Mock gh CLI responses
        version_result = Mock()
        version_result.returncode = 0
        
        status_result = Mock()
        status_result.returncode = 1
        status_result.stderr = "Not logged in"
        
        mock_run.side_effect = [version_result, status_result]
        
        pack = create_github_auth_pack()
        result = pack.run(plan=False)
        checks = result.checks
        
        assert len(checks) >= 1
        assert not checks[0].passed
        assert checks[0].remedy is not None
        assert "login" in checks[0].remedy.lower()

    @patch("honk.auth.providers.github.subprocess.run")
    def test_pack_checks_scopes(self, mock_run):
        """Test pack validates required scopes."""
        # Mock gh CLI responses
        version_result = Mock()
        version_result.returncode = 0
        
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.com as testuser\n  - Token scopes: repo, read:org"
        
        mock_run.side_effect = [version_result, status_result, status_result]
        
        # Request scopes that aren't present
        pack = create_github_auth_pack(scopes=["repo", "workflow"])
        result = pack.run(plan=False)
        checks = result.checks
        
        # Should have auth check and scope check
        assert len(checks) >= 2
        # Auth check should pass
        assert checks[0].passed
        # Scope check should fail (missing workflow)
        scope_check = checks[1]
        assert not scope_check.passed
        assert "workflow" in scope_check.message or "Missing" in scope_check.message

    @patch("honk.auth.providers.github.subprocess.run")
    def test_pack_with_custom_hostname(self, mock_run):
        """Test pack works with custom GitHub hostname."""
        # Mock gh CLI responses
        version_result = Mock()
        version_result.returncode = 0
        
        status_result = Mock()
        status_result.returncode = 0
        status_result.stdout = "✓ Logged in to github.example.com as testuser"
        
        mock_run.side_effect = [version_result, status_result, status_result]
        
        pack = create_github_auth_pack(hostname="github.example.com")
        assert "github.example.com" in pack.name
        
        result = pack.run(plan=False)
        checks = result.checks
        assert len(checks) >= 1
        assert checks[0].passed


class TestAzureAuthDoctorPack:
    """Test Azure DevOps auth doctor pack."""

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_pack_passes_when_authenticated(self, mock_run):
        """Test pack passes when user is authenticated."""
        import json
        
        # Mock az CLI responses
        version_result = Mock()
        version_result.returncode = 0
        
        account_result = Mock()
        account_result.returncode = 0
        account_result.stdout = json.dumps({"user": {"name": "user@example.com"}})
        
        project_result = Mock()
        project_result.returncode = 0
        project_result.stdout = json.dumps({"value": [{"name": "TestProject"}]})
        
        mock_run.side_effect = [version_result, account_result, project_result]
        
        pack = create_azure_auth_pack(org="https://dev.azure.com/test-org")
        result = pack.run(plan=False)
        checks = result.checks
        
        assert len(checks) >= 1
        assert checks[0].passed
        assert "test-org" in checks[0].message or "Authenticated" in checks[0].message

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_pack_fails_when_not_authenticated(self, mock_run):
        """Test pack fails when user is not authenticated."""
        # Mock az CLI responses
        version_result = Mock()
        version_result.returncode = 0
        
        account_result = Mock()
        account_result.returncode = 1
        account_result.stderr = "Please run 'az login'"
        
        mock_run.side_effect = [version_result, account_result]
        
        pack = create_azure_auth_pack(org="https://dev.azure.com/test-org")
        result = pack.run(plan=False)
        checks = result.checks
        
        assert len(checks) >= 1
        assert not checks[0].passed
        assert checks[0].remedy is not None
        assert "az login" in checks[0].remedy

    @patch("honk.auth.providers.azure.subprocess.run")
    def test_pack_fails_when_no_pat(self, mock_run):
        """Test pack fails when Azure is authenticated but PAT is missing."""
        import json
        
        # Mock az CLI responses
        version_result = Mock()
        version_result.returncode = 0
        
        account_result = Mock()
        account_result.returncode = 0
        account_result.stdout = json.dumps({"user": {"name": "user@example.com"}})
        
        project_result = Mock()
        project_result.returncode = 1
        project_result.stderr = "PAT required"
        
        mock_run.side_effect = [version_result, account_result, project_result]
        
        pack = create_azure_auth_pack(org="https://dev.azure.com/test-org")
        result = pack.run(plan=False)
        checks = result.checks
        
        assert len(checks) >= 1
        assert not checks[0].passed
        assert "PAT" in checks[0].message or "login" in checks[0].remedy.lower()
