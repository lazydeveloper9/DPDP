"""
CS-01 Opengrep / Semgrep Isolated Subprocess Bridge
===================================================
Executes optional Opengrep (LGPL-2.1) or Semgrep CLI as an isolated external subprocess.

Strict DPDP & PRD Constraints:
  - 100% Zero-Egress: enforced via `--metrics=off --disable-version-check`.
  - Offline & Isolated: zero runtime Python bindings or dynamic library linking.
  - License Hygiene: executes only Apache-2.0 DPDP rules provided by CS-01.
  - Graceful Fallback: if binary is missing, logs warning and seamlessly falls back
    to internal Tree-sitter engine without interrupting the audit pipeline.
"""

from __future__ import annotations
import json
import logging
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any, Optional

from rich.console import Console

from cs01.models import RawFinding, PassType, Severity, ScanConfig

logger = logging.getLogger("cs01.opengrep_bridge")
console = Console(stderr=True)


class OpengrepBridge:
    """
    Subprocess bridge to Opengrep / Semgrep CLI.
    Runs scans with zero telemetry and converts results into CS-01 RawFinding models.
    """

    def __init__(self, custom_binary: Optional[str] = None):
        self.custom_binary = custom_binary

    @staticmethod
    def detect_binary(custom_path: Optional[str] = None) -> tuple[Optional[str], Optional[str]]:
        """
        Locate the opengrep or semgrep binary and identify its flavor.
        Returns: (binary_path, flavor) e.g. ('/usr/local/bin/opengrep', 'opengrep')
        """
        candidates: list[str] = []
        if custom_path:
            candidates.append(custom_path)
        candidates.extend(["opengrep", "semgrep"])

        for cand in candidates:
            resolved = shutil.which(cand) or (cand if os.path.isfile(cand) and os.access(cand, os.X_OK) else None)
            if resolved:
                # Determine flavor and verify it works
                flavor = "opengrep" if "opengrep" in Path(resolved).name.lower() else "semgrep"
                return str(resolved), flavor

        return None, None

    @staticmethod
    def get_default_rules_path() -> Path:
        """Return the default packaged DPDP rules file for Opengrep / Semgrep."""
        # Check project root rules directory first, then package rules directory
        this_dir = Path(__file__).resolve()
        candidate1 = this_dir.parent.parent.parent.parent / "rules" / "opengrep" / "dpdp_rules.yaml"
        candidate2 = this_dir.parent.parent.parent / "rules" / "opengrep" / "dpdp_rules.yaml"
        if candidate1.exists():
            return candidate1
        if candidate2.exists():
            return candidate2
        return candidate1

    @staticmethod
    def build_command(
        binary: str,
        target_path: str | Path,
        rules_path: str | Path,
        extra_args: Optional[list[str]] = None,
    ) -> list[str]:
        """
        Formulate zero-egress, local-first execution command.
        Strictly disables telemetry, cloud metrics, and version check calls.
        """
        cmd = [
            binary,
            "scan",
            "--json",
            "--config",
            str(rules_path),
            "--metrics=off",
            "--disable-version-check",
            "--quiet",
        ]
        if extra_args:
            cmd.extend(extra_args)
        cmd.append(str(target_path))
        return cmd

    def run_scan(self, target_path: str | Path, cfg: ScanConfig) -> list[RawFinding]:
        """
        Execute Opengrep / Semgrep scan against target directory.
        Returns list of RawFinding. Falls back gracefully if binary not present.
        """
        binary_path, flavor = self.detect_binary(cfg.engine.opengrep_binary or self.custom_binary)
        if not binary_path or not flavor:
            console.print(
                "\n[yellow]⚠ Opengrep / Semgrep binary not found on PATH. "
                "Falling back to native Tree-sitter engine.\n"
                "  To enable, install Opengrep (https://github.com/opengrep/opengrep) "
                "or specify 'opengrep_binary' in cs01.yaml.[/yellow]"
            )
            return []

        rules_path = Path(cfg.engine.rules_dir) if cfg.engine.rules_dir else self.get_default_rules_path()
        if not rules_path.exists():
            console.print(f"[yellow]⚠ Opengrep rules not found at: {rules_path}. Skipping Opengrep pass.[/yellow]")
            return []

        cmd = self.build_command(binary_path, target_path, rules_path)
        timeout_sec = cfg.engine.timeout_seconds or 120.0

        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                check=False,
            )
        except subprocess.TimeoutExpired:
            console.print(f"[yellow]⚠ Opengrep scan timed out after {timeout_sec}s. Proceeding with AST findings.[/yellow]")
            return []
        except Exception as exc:
            console.print(f"[yellow]⚠ Opengrep execution error: {exc}. Proceeding with AST findings.[/yellow]")
            return []

        stdout = res.stdout.strip()
        if not stdout:
            if res.returncode not in (0, 1):
                logger.debug("Opengrep stderr: %s", res.stderr)
            return []

        try:
            data = json.loads(stdout)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse Opengrep JSON output: %s", exc)
            return []

        return self.parse_semgrep_json(data, scan_root=target_path, flavor=flavor)

    @classmethod
    def parse_semgrep_json(
        cls,
        json_data: dict[str, Any] | str,
        scan_root: str | Path,
        flavor: str = "opengrep",
    ) -> list[RawFinding]:
        """
        Convert standard Semgrep / Opengrep JSON output into CS-01 RawFinding objects.
        Handles metadata extraction, severity mapping, and snippet normalization.
        """
        if isinstance(json_data, str):
            json_data = json.loads(json_data)

        results = json_data.get("results", [])
        findings: list[RawFinding] = []
        scan_root_path = Path(scan_root).resolve()

        severity_map = {
            "CRITICAL": Severity.CRITICAL,
            "ERROR": Severity.CRITICAL,
            "HIGH": Severity.HIGH,
            "WARNING": Severity.HIGH,
            "MEDIUM": Severity.MEDIUM,
            "LOW": Severity.LOW,
            "INFO": Severity.INFO,
        }

        for item in results:
            check_id = item.get("check_id", "DPDP-OPENGREP")
            raw_path = item.get("path", "")
            
            # Normalize path relative to scan_root
            try:
                abs_item_path = Path(raw_path).resolve()
                if abs_item_path.is_relative_to(scan_root_path):
                    rel_path = str(abs_item_path.relative_to(scan_root_path)).replace("\\", "/")
                else:
                    rel_path = raw_path.replace("\\", "/")
            except Exception:
                rel_path = raw_path.replace("\\", "/")

            start = item.get("start", {})
            end = item.get("end", {})
            line_start = start.get("line") or 1
            line_end = end.get("line") or line_start

            extra = item.get("extra", {})
            metadata = extra.get("metadata", {})

            # Rule mappings
            cs01_rule_id = metadata.get("cs01_rule_id") or check_id
            dpdp_section = metadata.get("dpdp_section", "§8(5)")
            dpdp_rule = metadata.get("dpdp_rule", "Rule 6(1)(a)")
            penalty_band = metadata.get("penalty_band", "250_crore")
            remediation = metadata.get(
                "remediation",
                "Apply reasonable security safeguards and tokenization pursuant to DPDP Act 2023.",
            )

            # Determine severity
            raw_sev = (metadata.get("severity") or extra.get("severity") or "HIGH").upper()
            severity = severity_map.get(raw_sev, Severity.HIGH)

            snippet = extra.get("lines", "")
            message = extra.get("message", "Opengrep compliance finding")

            fid = f"{cs01_rule_id}:{rel_path}:{line_start}"
            finding = RawFinding(
                id=fid,
                rule_id=cs01_rule_id,
                pass_type=PassType.A,
                engine=flavor,
                file=rel_path,
                line_start=line_start,
                line_end=line_end,
                snippet=snippet.strip() if snippet else "",
                dpdp_section=dpdp_section,
                dpdp_rule=dpdp_rule,
                penalty_band=penalty_band,
                severity=severity,
                message=message,
                remediation=remediation,
            )
            findings.append(finding)

        return findings
