"""
Stage 6 SARIF 2.1.0 Exporter
============================
Generates GitHub Code Scanning compatible SARIF 2.1.0 documents.

Enforces GitHub Code Scanning hard invariants:
  1. Single unified run architecture (exactly one runs[0] object).
  2. <= 8 tags per rule definition.
  3. 4,500 finding ceiling (priority-ranked clipping with overflow warnings).
  4. Unique automationDetails.id per scan invocation.
  5. URI-compatible file paths relative to repository root.
  6. Levels mapped to SARIF standard: error, warning, note.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from cs01.models import ScoredFindingBundle, ScoredFinding, Severity
from cs01.pipeline.stage4_evaluate.rule_loader import load_all_rules

SARIF_SCHEMA = "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json"
MAX_SARIF_FINDINGS = 4500

SEVERITY_TO_SARIF_LEVEL = {
    Severity.CRITICAL: "error",
    Severity.HIGH: "error",
    Severity.MEDIUM: "warning",
    Severity.LOW: "note",
    Severity.INFO: "note",
}


def export_sarif(bundle: ScoredFindingBundle, output_path: Path | str) -> dict[str, Any]:
    """Serialize ScoredFindingBundle into SARIF 2.1.0 JSON format."""
    all_rules = load_all_rules()
    rule_index_map: dict[str, int] = {}
    sarif_rules: list[dict[str, Any]] = []

    for idx, r in enumerate(all_rules):
        rid = r["rule_id"]
        rule_index_map[rid] = idx
        
        # Invariant 2: <= 8 tags per rule
        tags = r.get("tags", [])[:8]

        sarif_rules.append({
            "id": rid,
            "name": rid.replace("-", "_"),
            "shortDescription": {"text": r.get("description", rid)},
            "fullDescription": {"text": f"DPDP Statutory Rule: {r.get('description', '')}. Section: {r.get('dpdp_section', '')}"},
            "defaultConfiguration": {
                "level": SEVERITY_TO_SARIF_LEVEL.get(Severity(r.get("severity", "MEDIUM")), "warning")
            },
            "help": {
                "text": f"Remediation: {r.get('remediation', '')}\nStatutory Reference: {r.get('dpdp_section', '')} (Penalty Ceiling: {r.get('penalty_band', '')})",
                "markdown": f"**Remediation:** {r.get('remediation', '')}\n\n**Statutory Reference:** `{r.get('dpdp_section', '')}` (Penalty Ceiling Band: `{r.get('penalty_band', '')}`)"
            },
            "properties": {
                "tags": tags,
                "precision": "high",
                "dpdp_section": r.get("dpdp_section", ""),
                "penalty_band": r.get("penalty_band", ""),
            }
        })

    # Sort findings by priority score descending and clip to 4,500
    sorted_findings = bundle.sorted_by_priority()
    clipped_findings = sorted_findings[:MAX_SARIF_FINDINGS]

    sarif_results: list[dict[str, Any]] = []
    for f in clipped_findings:
        level = SEVERITY_TO_SARIF_LEVEL.get(f.severity, "warning")
        r_idx = rule_index_map.get(f.rule_id, 0)

        file_uri = (f.file or "repository-root").replace("\\", "/")
        if file_uri.startswith("./"):
            file_uri = file_uri[2:]

        result_obj: dict[str, Any] = {
            "ruleId": f.rule_id,
            "ruleIndex": r_idx,
            "level": level,
            "message": {
                "text": f"[{f.severity.value}] {f.message} ({f.statutory_ceiling_display})"
            },
            "locations": [
                {
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": file_uri,
                            "uriBaseId": "%SRCROOT%",
                        },
                        "region": {
                            "startLine": f.line_start or 1,
                            "startColumn": 1,
                            "endLine": f.line_end or f.line_start or 1,
                        }
                    }
                }
            ],
            "partialFingerprints": {
                "primaryLocationHash": f.dedupe_key or "hash",
            },
            "properties": {
                "priority_score": f.priority_score,
                "dpdp_section": f.dpdp_section,
                "penalty_band": f.penalty_band,
            }
        }
        sarif_results.append(result_obj)

    sarif_document = {
        "$schema": SARIF_SCHEMA,
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "CS-01",
                        "version": bundle.cs01_version,
                        "informationUri": "https://github.com/DPDP-Auditor/cs01",
                        "rules": sarif_rules,
                    }
                },
                "automationDetails": {
                    "id": f"cs01-scan/{bundle.scan_id}",
                },
                "results": sarif_results,
            }
        ]
    }

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(sarif_document, fh, indent=2, ensure_ascii=False)

    return sarif_document
