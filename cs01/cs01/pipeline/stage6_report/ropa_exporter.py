"""
Stage 6 RoPA (Record of Processing Activities) Exporter
=======================================================
Drafts an automated RoPA map mapping personal data items to collection sources,
storage repositories, encryption safeguards, and retention limits under DPDP Act §8.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Optional

from cs01.models import ScoredFindingBundle, ProductCapabilityReport

def export_ropa_draft(
    bundle: ScoredFindingBundle,
    output_path: Path | str,
    capability_report: Optional[ProductCapabilityReport] = None,
) -> dict[str, Any]:
    """Generate an automated draft Record of Processing Activities from capabilities & findings."""
    ropa_entries: list[dict[str, Any]] = []

    if capability_report and capability_report.pii_inventory:
        seen = set()
        for item in capability_report.pii_inventory:
            key = f"{item.category}:{item.field_or_param}"
            if key in seen:
                continue
            seen.add(key)
            matching_findings = [f for f in bundle.findings if item.field_or_param in (f.matched_entity or "")]
            rules_triggered = list(set(f.rule_id for f in matching_findings))
            is_non_compliant = any(f.severity.value in ("CRITICAL", "HIGH") for f in matching_findings) or (item.is_stored and not item.is_encrypted)
            
            ropa_entries.append({
                "personal_data_category": item.category,
                "field_or_entity": item.field_or_param,
                "pii_type": item.pii_type,
                "locations_identified": [f"{item.location_file}:{item.location_line}" if item.location_line is not None else item.location_file],
                "is_stored": item.is_stored,
                "is_encrypted": item.is_encrypted,
                "processing_risks_detected": rules_triggered,
                "compliance_posture": "Non-Compliant" if is_non_compliant else "Compliant / Audited",
                "recommended_safeguards": list(set(f.remediation for f in matching_findings)) if matching_findings else ["Maintain verified cryptographic protection"],
                "dpdp_legal_basis": "Consent (§6) or Legitimate Uses (§7)",
            })

    if not ropa_entries:
        entities: dict[str, list] = {}
        for f in bundle.findings:
            ent = f.matched_entity or "Personal Data"
            entities.setdefault(ent, []).append(f)

        for ent, findings in entities.items():
            files_involved = list(set(f.file for f in findings if f.file))
            rules_triggered = list(set(f.rule_id for f in findings))
            highest_sev = findings[0].severity.value

            ropa_entries.append({
                "personal_data_category": ent,
                "locations_identified": files_involved,
                "processing_risks_detected": rules_triggered,
                "compliance_posture": "Non-Compliant" if highest_sev in ("CRITICAL", "HIGH") else "Review Needed",
                "recommended_safeguards": list(set(f.remediation for f in findings)),
                "dpdp_legal_basis": "Consent (§6) or Legitimate Uses (§7)",
            })

    ropa_document = {
        "title": "Automated Record of Processing Activities (RoPA) — Technical Draft",
        "notice": "This draft is automatically generated from static code and schema analysis. Legal counsel must review prior to regulatory submission under DPDP Act §8.",
        "scan_id": bundle.scan_id,
        "scan_root": bundle.scan_root,
        "entries": ropa_entries,
    }

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        json.dump(ropa_document, fh, indent=2, ensure_ascii=False)

    return ropa_document
