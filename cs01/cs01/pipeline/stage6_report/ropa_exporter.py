"""
Stage 6 RoPA (Record of Processing Activities) Exporter
=======================================================
Drafts an automated RoPA map mapping personal data items to collection sources,
storage repositories, encryption safeguards, and retention limits under DPDP Act §8.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from cs01.models import ScoredFindingBundle


def export_ropa_draft(bundle: ScoredFindingBundle, output_path: Path | str) -> dict[str, Any]:
    """Generate an automated draft Record of Processing Activities from findings."""
    ropa_entries: list[dict[str, Any]] = []

    # Aggregate by matched personal data entities
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
