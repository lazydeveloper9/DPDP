"""
cs01.utils.git_ingest — Remote Git and GitHub Repository Ingestion
=================================================================
Enables direct scanning of remote Git repositories (GitHub, GitLab, Bitbucket, etc.)
via shallow cloning with automatic zip fallback when git CLI is absent.
"""

from __future__ import annotations
from contextlib import contextmanager
import logging
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Generator, Optional
import urllib.parse

from rich.console import Console

logger = logging.getLogger("cs01.git_ingest")
console = Console(stderr=True)

GIT_URL_PATTERNS = [
    re.compile(r"^https?://(www\.)?github\.com/[^/]+/[^/]+", re.IGNORECASE),
    re.compile(r"^https?://(www\.)?gitlab\.com/[^/]+/[^/]+", re.IGNORECASE),
    re.compile(r"^https?://(www\.)?bitbucket\.org/[^/]+/[^/]+", re.IGNORECASE),
    re.compile(r"^https?://(www\.)?codeberg\.org/[^/]+/[^/]+", re.IGNORECASE),
    re.compile(r"^https?://.+/.+\.git$", re.IGNORECASE),
    re.compile(r"^git@[^:]+:.+\.git$", re.IGNORECASE),
    re.compile(r"^(git|ssh)://", re.IGNORECASE),
]

def is_git_url(target: str | Path) -> bool:
    """Check if the given target string is a remote Git/GitHub URL."""
    if isinstance(target, Path):
        target = str(target)
    target = target.strip()
    if not target:
        return False
    if target.startswith(("git@", "git://", "ssh://")):
        return True
    if target.startswith(("http://", "https://")):
        for pattern in GIT_URL_PATTERNS:
            if pattern.search(target):
                return True
        if target.endswith(".git"):
            return True
        try:
            parsed = urllib.parse.urlparse(target)
            host = parsed.netloc.lower()
            if any(h in host for h in ("github.com", "gitlab.com", "bitbucket.org", "codeberg.org")):
                parts = [p for p in parsed.path.split("/") if p]
                if len(parts) >= 2:
                    return True
        except Exception:
            pass
    return False

def parse_git_url(url: str) -> tuple[str, Optional[str]]:
    """
    Parse a Git or GitHub URL into a clean clone URL and an optional branch/ref.
    Supports GitHub tree/blob URLs, e.g.:
      https://github.com/owner/repo/tree/feature-branch
    Returns: (clean_clone_url, branch_ref)
    """
    url = url.strip()
    parsed = urllib.parse.urlparse(url)

    match = re.search(r"github\.com/([^/]+)/([^/]+)/(?:tree|blob)/(.+)", url, re.IGNORECASE)
    if match:
        owner, repo, ref = match.group(1), match.group(2), match.group(3)
        clean_url = f"https://github.com/{owner}/{repo}.git"
        return clean_url, ref

    clean_url = url
    if not clean_url.endswith(".git") and not clean_url.startswith("git@"):
        clean_url = clean_url.rstrip("/")
        if "github.com" in clean_url or "gitlab.com" in clean_url:
            clean_url = f"{clean_url}.git"

    return clean_url, None

def clone_git_repo(
    url: str,
    dest_dir: Path,
    ref: Optional[str] = None,
    depth: int = 1,
    timeout_seconds: float = 180.0,
) -> Path:
    """
    Clone a remote Git repository into dest_dir using shallow clone.
    Falls back to HTTP zip download for public GitHub repositories if git CLI is absent.
    """
    clean_url, url_ref = parse_git_url(url)
    target_ref = ref or url_ref

    git_bin = shutil.which("git")
    if git_bin:
        cmd = [git_bin, "clone", "--depth", str(depth)]
        if target_ref:
            cmd.extend(["-b", target_ref])
        cmd.extend([clean_url, str(dest_dir)])

        ref_display = f" (branch/ref: {target_ref})" if target_ref else ""
        console.print(f"[cyan]📦 Cloning remote repository {clean_url}{ref_display}...[/cyan]")
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
            if res.returncode == 0:
                return dest_dir
            else:
                stderr_msg = res.stderr.strip() or res.stdout.strip()
                raise RuntimeError(
                    f"Git clone failed (exit code {res.returncode}): {stderr_msg}\n"
                    f"Verify that the repository URL is correct and public (or SSH keys are configured)."
                )
        except subprocess.TimeoutExpired:
            raise TimeoutError(f"Git clone timed out after {timeout_seconds} seconds.")

    return _download_github_zip(clean_url, dest_dir, ref=target_ref)

def _download_github_zip(url: str, dest_dir: Path, ref: Optional[str] = None) -> Path:
    """Download public GitHub repository as a ZIP archive when git CLI is unavailable."""
    match = re.search(r"github\.com[:/]([^/]+)/([^/\.]+)", url, re.IGNORECASE)
    if not match:
        raise RuntimeError("git CLI is not installed on PATH and target is not a recognized GitHub URL.")

    owner, repo = match.groups()
    branch = ref or "main"
    zip_url = f"https://codeload.github.com/{owner}/{repo}/zip/refs/heads/{branch}"

    console.print(f"[cyan]📦 Git CLI not found. Downloading public GitHub archive from {zip_url}...[/cyan]")
    import urllib.request
    from cs01.utils.archive import safe_extract_zip

    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as tmp_zip:
        tmp_zip_path = Path(tmp_zip.name)

    try:
        req = urllib.request.Request(zip_url, headers={"User-Agent": "CS01-DPDP-Auditor"})
        with urllib.request.urlopen(req, timeout=60) as resp, open(tmp_zip_path, "wb") as out_file:
            shutil.copyfileobj(resp, out_file)

        extract_tmp = dest_dir / "_unzip_tmp"
        extract_tmp.mkdir(parents=True, exist_ok=True)
        safe_extract_zip(tmp_zip_path, extract_tmp)

        subdirs = [d for d in extract_tmp.iterdir() if d.is_dir()]
        if subdirs:
            root_content = subdirs[0]
            for item in root_content.iterdir():
                shutil.move(str(item), str(dest_dir))
            shutil.rmtree(extract_tmp, ignore_errors=True)
        return dest_dir
    finally:
        if tmp_zip_path.exists():
            try:
                tmp_zip_path.unlink()
            except OSError:
                pass

@contextmanager
def cloned_workspace(url: str, ref: Optional[str] = None) -> Generator[Path, None, None]:
    """
    Context manager that clones a remote git repository into an isolated temporary
    workspace and automatically purges it upon exit.
    """
    temp_dir = tempfile.mkdtemp(prefix="cs01_git_")
    temp_path = Path(temp_dir).resolve()
    try:
        clone_git_repo(url, temp_path, ref=ref)
        yield temp_path
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
