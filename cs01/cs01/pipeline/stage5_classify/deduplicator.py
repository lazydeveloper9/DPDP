"""
Stage 5 Deduplicator
====================
Merges duplicate or overlapping RawFinding records sharing the same logical signature
(rule_id, file, line, and matched entity).
"""

from __future__ import annotations
import hashlib
from typing import Any

from cs01.models import RawFinding, Severity

SEVERITY_ORDER = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

def _dedupe_key(finding: RawFinding) -> str:
    """Generate a deterministic deduplication signature for a finding."""
    key_str = f"{finding.rule_id}:{finding.file or 'global'}:{finding.line_start or 0}:{finding.matched_entity or ''}"
    return hashlib.sha256(key_str.encode("utf-8")).hexdigest()[:16]

def deduplicate_findings(raw_findings: list[RawFinding]) -> list[RawFinding]:
    """Group and merge overlapping findings, retaining highest severity."""
    grouped: dict[str, list[RawFinding]] = {}
    for f in raw_findings:
        dk = _dedupe_key(f)
        grouped.setdefault(dk, []).append(f)

    deduped: list[RawFinding] = []
    for dk, group in grouped.items():
        if len(group) == 1:
            deduped.append(group[0])
            continue

        group.sort(key=lambda item: SEVERITY_ORDER.index(item.severity), reverse=True)
        primary = group[0]

        merged_pii_ids: list[str] = []
        merged_flow_ids: list[str] = []
        for g in group:
            merged_pii_ids.extend(g.contributing_pii_hit_ids)
            merged_flow_ids.extend(g.contributing_flow_edge_ids)

        merged_finding = primary.model_copy(
            update={
                "contributing_pii_hit_ids": list(set(merged_pii_ids)),
                "contributing_flow_edge_ids": list(set(merged_flow_ids)),
            }
        )
        deduped.append(merged_finding)

    return deduped
