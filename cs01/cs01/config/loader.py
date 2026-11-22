"""
Config loader: reads cs01.yaml and validates it into a ScanConfig.
Also handles .dpdpignore loading and policy_profiles/*.yaml hot-loading.
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

from ruamel.yaml import YAML

from cs01.models.scan_config import (
    ScanConfig, ThirdScheduleFlags, ApprovedProcessor,
    EngineConfig, BonusConfig,
)

yaml = YAML()
yaml.preserve_quotes = True

# --- Hard-coded default exclusions (always applied, regardless of .dpdpignore) ---
DEFAULT_EXCLUSIONS = [
    "node_modules/", ".venv/", "venv/", "env/",
    "dist/", "build/", "__pycache__/",
    ".git/", ".hg/", ".svn/",
    ".pytest_cache/", ".mypy_cache/", ".ruff_cache/",
    "*.min.js", "*.min.css", "*.lock", "*.map", "*.pyc",
    "*.whl", "*.egg-info/",
]


def load_config(
    config_path: Optional[str] = None,
    overrides: Optional[dict] = None,
) -> ScanConfig:
    """
    Load and validate cs01.yaml into a ScanConfig.

    Args:
        config_path: Path to cs01.yaml. If None, looks for cs01.yaml in cwd.
        overrides:   Dict of values to override after loading (from CLI flags).

    Returns:
        Validated ScanConfig instance.

    Raises:
        SystemExit(2): on validation error (exit code 2 = config error).
    """
    raw: dict = {}

    # Locate config file
    if config_path:
        cfg_file = Path(config_path)
    else:
        cfg_file = Path.cwd() / "cs01.yaml"

    if cfg_file.exists():
        with open(cfg_file, "r", encoding="utf-8") as fh:
            raw = dict(yaml.load(fh) or {})

    # Apply CLI overrides
    if overrides:
        raw.update({k: v for k, v in overrides.items() if v is not None})

    # Build nested models manually (keeps validation errors explicit)
    try:
        cfg = ScanConfig(
            org_name=raw.get("org_name", "Unknown Org"),
            entity_type=raw.get("entity_type", "data_fiduciary"),
            is_sdf=raw.get("is_sdf", False),
            third_schedule=ThirdScheduleFlags(**raw.get("third_schedule", {})),
            approved_processors=[
                ApprovedProcessor(**p) for p in raw.get("approved_processors", [])
            ],
            allowed_cross_border_regions=raw.get("allowed_cross_border_regions", []),
            scan_root=raw.get("scan_root", "."),
            scan_layers=raw.get("scan_layers", ["code", "schema", "iac", "secrets"]),
            fail_on=raw.get("fail_on", "high"),
            output_formats=raw.get("output_formats", ["sarif", "json", "html"]),
            output_dir=raw.get("output_dir", "./cs01-reports"),
            dpdpignore_path=raw.get("dpdpignore_path"),
            baseline_path=raw.get("baseline_path"),
            diff_base=raw.get("diff_base"),
            engine=EngineConfig(**raw.get("engine", {})),
            bonus=BonusConfig(**raw.get("bonus", {})),
            policy_profiles_dir=raw.get("policy_profiles_dir", "./policy_profiles"),
            save_stage_output=raw.get("save_stage_output", False),
            debug=raw.get("debug", False),
            strict_test_scanning=raw.get("strict_test_scanning", False),
        )
    except Exception as exc:
        print(f"[CS-01] CONFIG ERROR: {exc}", file=sys.stderr)
        sys.exit(2)

    return cfg


def load_dpdpignore(scan_root: str, custom_path: Optional[str] = None) -> list[str]:
    """
    Load .dpdpignore patterns from the scan root (or custom path).
    Returns combined list: DEFAULT_EXCLUSIONS + user patterns.
    """
    patterns = list(DEFAULT_EXCLUSIONS)

    # Try custom path first, then scan_root/.dpdpignore
    candidates = []
    if custom_path:
        candidates.append(Path(custom_path))
    candidates.append(Path(scan_root) / ".dpdpignore")

    for path in candidates:
        if path.exists():
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        patterns.append(line)
            break  # only load the first found

    return patterns
