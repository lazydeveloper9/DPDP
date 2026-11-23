"""
Resource Path Resolution for Development & PyInstaller Frozen Environments.

Ensures declarative YAML rules, Jinja2 report templates, and graphic assets
resolve cleanly both during development (local directory tree) and when running
from a compiled PyInstaller executable (via sys._MEIPASS).
"""
from __future__ import annotations

import sys
from pathlib import Path


def get_project_root() -> Path:
    """Returns root directory of the CS-01 project or the PyInstaller bundle directory."""
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS).resolve()
    # In source mode: this file is at cs01/cs01/utils/resources.py
    # Project root (containing rules/ and assets/) is 3 levels up: cs01/
    return Path(__file__).resolve().parent.parent.parent


def get_resource_path(relative_path: str | Path) -> Path:
    """
    Resolves a relative resource path against the project root or PyInstaller _MEIPASS bundle.

    Args:
        relative_path: Path relative to repository root (e.g. 'rules/pass_a/rules_01_to_23.yaml')

    Returns:
        Absolute resolved Path to the resource.
    """
    root = get_project_root()
    p = (root / relative_path).resolve()
    if p.exists():
        return p

    # Fallback check adjacent to executable when running frozen
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        fallback = (exe_dir / relative_path).resolve()
        if fallback.exists():
            return fallback

    return p
