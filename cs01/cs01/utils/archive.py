"""
cs01.utils.archive — Secure archive decompression and workspace management.
Prevents Zip Slip and tar path traversal vulnerabilities.
"""

from __future__ import annotations
import os
import shutil
import tarfile
import tempfile
import zipfile
from contextlib import contextmanager
from pathlib import Path
from typing import Generator

ARCHIVE_EXTENSIONS = {".zip", ".tar", ".gz", ".tgz", ".bz2", ".tar.gz", ".tar.bz2"}

def is_archive(path: str | Path) -> bool:
    """Check if the given path is an archive file (zip, tar, tgz)."""
    p = Path(path)
    if not p.is_file():
        return False
    name_lower = p.name.lower()
    if any(name_lower.endswith(ext) for ext in ARCHIVE_EXTENSIONS):
        return True
    return zipfile.is_zipfile(p) or tarfile.is_tarfile(p)

def safe_extract_zip(zip_path: Path, dest_dir: Path) -> Path:
    """Extract a ZIP file safely, preventing directory traversal (Zip Slip)."""
    dest_dir = dest_dir.resolve()
    with zipfile.ZipFile(zip_path, "r") as zf:
        for member in zf.infolist():
            member_path = (dest_dir / member.filename).resolve()
            if not member_path.is_relative_to(dest_dir):
                raise ValueError(
                    f"Malicious archive member detected (Zip Slip): {member.filename}"
                )
        zf.extractall(dest_dir)
    return dest_dir

def safe_extract_tar(tar_path: Path, dest_dir: Path) -> Path:
    """Extract a TAR file safely, preventing directory traversal."""
    dest_dir = dest_dir.resolve()
    with tarfile.open(tar_path, "r:*") as tf:
        for member in tf.getmembers():
            member_path = (dest_dir / member.name).resolve()
            if not member_path.is_relative_to(dest_dir):
                raise ValueError(
                    f"Malicious archive member detected (Tar Slip): {member.name}"
                )
        tf.extractall(dest_dir)
    return dest_dir

@contextmanager
def extracted_workspace(
    target_path: str | Path,
    ref: Optional[str] = None,
) -> Generator[Path, None, None]:
    """
    Context manager that provides a directory path to scan.
    - If target_path is a remote Git or GitHub URL, it is shallow-cloned to a temporary workspace.
    - If target_path is an archive (.zip, .tar.gz, etc.), it is extracted safely.
    - If target_path is a local directory, it yields the resolved directory path.
    Temporary workspaces are automatically cleaned up upon exit.
    """
    from .git_ingest import is_git_url, cloned_workspace

    target_str = str(target_path).strip()
    if is_git_url(target_str):
        with cloned_workspace(target_str, ref=ref) as ws:
            yield ws
        return

    p = Path(target_path).resolve()
    if not p.exists():
        raise FileNotFoundError(f"Scan target does not exist: {target_path}")

    if p.is_file() and is_archive(p):
        temp_dir = tempfile.mkdtemp(prefix="cs01_workspace_")
        temp_path = Path(temp_dir).resolve()
        try:
            if zipfile.is_zipfile(p):
                safe_extract_zip(p, temp_path)
            elif tarfile.is_tarfile(p):
                safe_extract_tar(p, temp_path)
            else:
                safe_extract_zip(p, temp_path)
            yield temp_path
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
    elif p.is_dir():
        yield p
    else:
        raise ValueError(f"Scan target must be a directory or supported archive file (.zip, .tar.gz): {target_path}")
