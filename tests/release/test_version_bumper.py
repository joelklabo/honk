"""Tests for version bumper."""

import pytest
from honk.release.versioning.bumper import Version, VersionBumper
from honk.release.analyzer import ReleaseType


class TestVersion:
    def test_parse_simple_version(self):
        """Test parsing simple version."""
        v = Version.parse("1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
    
    def test_parse_with_v_prefix(self):
        """Test parsing version with v prefix."""
        v = Version.parse("v1.2.3")
        assert v.major == 1
        assert v.minor == 2
        assert v.patch == 3
    
    def test_bump_major(self):
        """Test bumping major version."""
        v = Version(1, 2, 3)
        bumped = v.bump(ReleaseType.MAJOR)
        assert str(bumped) == "2.0.0"
    
    def test_bump_minor(self):
        """Test bumping minor version."""
        v = Version(1, 2, 3)
        bumped = v.bump(ReleaseType.MINOR)
        assert str(bumped) == "1.3.0"
    
    def test_bump_patch(self):
        """Test bumping patch version."""
        v = Version(1, 2, 3)
        bumped = v.bump(ReleaseType.PATCH)
        assert str(bumped) == "1.2.4"
    
    def test_str_representation(self):
        """Test string representation."""
        v = Version(1, 2, 3)
        assert str(v) == "1.2.3"
