"""
Bonus Module — Deterministic Compliance Patch Generator
=======================================================
Generates minimal, git-apply compatible unified diff (.patch) files for high-confidence,
deterministic DPDP remediation actions (e.g. Terraform storage encryption, log retention floors,
and environment SSL enforcement).
"""

from __future__ import annotations
import re
from pathlib import Path
from cs01.models import ScoredFindingBundle, ScoredFinding, Severity


def generate_patches(bundle: ScoredFindingBundle, output_dir: Path | str) -> list[Path]:
    """Generate unified diffs for remediable findings."""
    patch_dir = Path(output_dir) / "patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    generated_patches: list[Path] = []

    for f in bundle.findings:
        if not f.file or f.priority_score < 0.20:
            continue

        target_file = Path(bundle.scan_root) / f.file
        if not target_file.exists():
            continue

        patch_content: str | None = None

        # 1. Terraform storage_encrypted = false -> true
        if f.rule_id == "IAC-DPDP-001":
            patch_content = (
                f"--- a/{f.file}\n"
                f"+++ b/{f.file}\n"
                f"@@ -{f.line_start},1 +{f.line_start},1 @@\n"
                f"-  storage_encrypted = false\n"
                f"+  storage_encrypted = true\n"
            )

        # 2. CloudWatch retention < 365 -> 365
        elif f.rule_id == "IAC-DPDP-002":
            patch_content = (
                f"--- a/{f.file}\n"
                f"+++ b/{f.file}\n"
                f"@@ -{f.line_start},1 +{f.line_start},1 @@\n"
                f"-  retention_in_days = {f.snippet.split('=')[1].split()[0] if '=' in f.snippet else '30'}\n"
                f"+  retention_in_days = 365\n"
            )

        # 3. Insecure SSL -> sslmode=require
        elif f.rule_id == "ENV-DPDP-001":
            patch_content = (
                f"--- a/{f.file}\n"
                f"+++ b/{f.file}\n"
                f"@@ -{f.line_start},1 +{f.line_start},1 @@\n"
                f"-{f.snippet}\n"
                f"+sslmode=require\n"
            )

        if patch_content:
            p_file = patch_dir / f"{f.rule_id}_{f.line_start or 1}.patch"
            p_file.write_text(patch_content, encoding="utf-8")
            generated_patches.append(p_file)

    return generated_patches
