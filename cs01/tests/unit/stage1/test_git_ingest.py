"""
Unit tests for Remote Git & GitHub Repository Ingestion
======================================================
Tests URL recognition, ref parsing, shallow clone command formulation,
error handling, and temporary workspace management.
"""

from pathlib import Path
import subprocess
import tempfile
from unittest.mock import patch, MagicMock
import pytest

from cs01.utils.git_ingest import (
    is_git_url,
    parse_git_url,
    clone_git_repo,
    cloned_workspace,
)
from cs01.utils.archive import extracted_workspace


def test_is_git_url():
    """Verify detection of various Git and GitHub URL formats."""
    # Positive matches
    assert is_git_url("https://github.com/owner/repo")
    assert is_git_url("http://github.com/owner/repo")
    assert is_git_url("https://github.com/owner/repo.git")
    assert is_git_url("https://github.com/owner/repo/tree/main")
    assert is_git_url("https://github.com/owner/repo/tree/feature/consent-flow")
    assert is_git_url("git@github.com:owner/repo.git")
    assert is_git_url("https://gitlab.com/group/project.git")
    assert is_git_url("https://bitbucket.org/team/repo")
    assert is_git_url("git://github.com/owner/repo.git")

    # Negative matches
    assert not is_git_url("")
    assert not is_git_url("   ")
    assert not is_git_url("./local/path")
    assert not is_git_url("C:\\DPDP\\my_project")
    assert not is_git_url("archive.zip")
    assert not is_git_url("https://google.com")


def test_parse_git_url():
    """Verify extracting clean clone URL and branch ref from GitHub URLs."""
    # Standard repository URL
    clean_url, ref = parse_git_url("https://github.com/fastapi/fastapi")
    assert clean_url == "https://github.com/fastapi/fastapi.git"
    assert ref is None

    # Tree branch URL
    clean_url, ref = parse_git_url("https://github.com/fastapi/fastapi/tree/0.110.0")
    assert clean_url == "https://github.com/fastapi/fastapi.git"
    assert ref == "0.110.0"

    # Multi-segment branch URL
    clean_url, ref = parse_git_url("https://github.com/org/repo/tree/feature/dpdp-audit")
    assert clean_url == "https://github.com/org/repo.git"
    assert ref == "feature/dpdp-audit"

    # SSH URL
    clean_url, ref = parse_git_url("git@github.com:org/repo.git")
    assert clean_url == "git@github.com:org/repo.git"
    assert ref is None


def test_clone_git_repo_success(tmp_path):
    """Verify clone executes shallow clone command with ref."""
    target_url = "https://github.com/example/sample-repo"

    with patch("shutil.which", return_value="git"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        dest = clone_git_repo(target_url, tmp_path, ref="v1.0")

        assert dest == tmp_path
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "git"
        assert args[1] == "clone"
        assert "--depth" in args
        assert "1" in args
        assert "-b" in args
        assert "v1.0" in args
        assert "https://github.com/example/sample-repo.git" in args


def test_clone_git_repo_failure(tmp_path):
    """Verify clone raises RuntimeError when git fails."""
    target_url = "https://github.com/example/nonexistent-repo"

    with patch("shutil.which", return_value="git"), \
         patch("subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(returncode=128, stdout="", stderr="Repository not found")

        with pytest.raises(RuntimeError, match="Git clone failed"):
            clone_git_repo(target_url, tmp_path)


def test_clone_git_repo_timeout(tmp_path):
    """Verify clone raises TimeoutError when subprocess exceeds timeout."""
    target_url = "https://github.com/example/repo"

    with patch("shutil.which", return_value="git"), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="git", timeout=5.0)):
        with pytest.raises(TimeoutError, match="timed out"):
            clone_git_repo(target_url, tmp_path, timeout_seconds=5.0)


def test_extracted_workspace_with_git_url():
    """Verify extracted_workspace seamlessly handles GitHub URLs."""
    target_url = "https://github.com/owner/demo"

    with patch("cs01.utils.git_ingest.clone_git_repo") as mock_clone:
        with extracted_workspace(target_url, ref="main") as ws_path:
            assert ws_path.exists()
            assert ws_path.is_dir()
            mock_clone.assert_called_once()
            called_url = mock_clone.call_args[0][0]
            assert called_url == target_url
            called_ref = mock_clone.call_args[1].get("ref")
            assert called_ref == "main"

        # Workspace directory should be cleaned up after context exit
        assert not ws_path.exists()
