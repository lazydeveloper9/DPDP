"""
Stage 6 GitLab SAST JSON Exporter
=================================
Serializes findings into GitLab's native SAST format (gl-sast-report.json)
for integration with GitLab Security Dashboards and MR widgets.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from cs01.models import ScoredFindingBundle, Severity

GITLAB_SEVERITY_MAP = {
    Severity.CRITICAL: "Critical",
    Severity.HIGH: "High",
    Severity.MEDIUM: "Medium",
    Severity.LOW: "Low",
    Severity.INFO: "Info",
}


def export_gitlab_sast(bundle: ScoredFindingBundle, output_path: Path | str) -> dict[str, Any]:
    """Serialize ScoredFindingBundle into GitLab SAST format."""
    vulnerabilities: list[dict[str, Any]] = []

    for f in bundle.findings:
        gl_severity = GITLAB_SEVERITY_MAP.get(f.severity, "Medium")
        file_path = (f.file or "global").replace("\\", "/")
        if file_path.startswith("./"):
            file_path = file_path[2:]

        vuln = {
            "id": f.dedupe_key,
            "category": "sast",
            "name": f"[{f.rule_id}] {f.message[:80]}",
            "message": f"{f.message} (Statutory: {f.dpdp_section})",
            "description": f"{f.message}\nStatutory Reference: {f.dpdp_section}\nCeiling: {f.statutory_ceiling_display}\nRemediation: {f.remediation}",
            "severity": gl_severity,
            "confidence": "High",
            "scanner": {
                "id": "cs01",
                "name": "CS-01 DPDP Compliance Auditor"
            },
            "location": {
                "file": file_path,
                "start_line": f.line_start or 1,
                "end_line": f.line_end or f.line_start or 1,
            },
            "identifiers": [
                {
                    "type": "cs01_rule_id",
                    "name": f.rule_id,
                    "value": f.rule_id,
                    "url": "https://dpdp.gov.in"
                },
                {
                    "type": "dpdp_act_section",
                    "name": f"DPDP Act {f.dpdp_section}",
                    "value": f.dpdp_section,
                }
            ]
        }
        vulnerabilities.append(vuln)

    report = {
        "version": "15.0.0",
        "vulnerabilities": vulnerabilities,
        "remediations": [],
        "scan": {
            "scanner": {
                "id": "cs01",
                "name": "CS-01",
                "url": "https://github.com/DPDP-Auditor/cs01",
                "version": bundle.cs01_version,
            },
            "type": "sast",
            "start_time": bundle.scan_timestamp,
            "status": "success",
        }
    }

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2, ensure_ascii=False)

    return report
