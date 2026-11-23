"""
Stage 5 DPDP Readiness Scorer
==============================
Computes repository-wide DPDP Readiness Score (0–100) across 8 statutory pillars:
  1. Notice & Consent (§5, §6, Rule 3)
  2. Security Safeguards (§8(5), Rule 6(1)(a))
  3. Breach Readiness (§8(6), Rule 7)
  4. Retention & Erasure (Rule 6(1)(e), Rule 8)
  5. Children & PwD Protection (§9, Rule 10)
  6. SDF Duties (§10, Rule 12, Rule 13)
  7. Data Principal Rights (Rule 14, §11, §12, §13)
  8. Cross-Border & CERT-In Controls (Rule 15, CERT-In)

Dynamically caps the overall score when unresolved CRITICAL findings exist.
"""

from __future__ import annotations
from typing import Any
from cs01.models import (
    ScoredFinding, DpdpReadinessScore, PillarScore, Severity,
)

PILLARS_METADATA = [
    {
        "id": "notice_consent",
        "label": "Notice & Consent",
        "rule_prefixes": ["CODE-DPDP-002", "ARCH-DPDP-001", "SQL-DPDP-005"],
        "sections": ["§5", "§6", "§7"],
    },
    {
        "id": "security_safeguards",
        "label": "Security Safeguards",
        "rule_prefixes": [
            "CODE-DPDP-001", "CODE-DPDP-003", "SQL-DPDP-001", "IAC-DPDP-001", "ENV-DPDP-001",
            "IAC-DPDP-003", "IAC-DPDP-004", "IAC-DPDP-006",
        ],
        "sections": ["§8(5)"],
    },
    {
        "id": "breach_readiness",
        "label": "Breach Readiness",
        "rule_prefixes": ["CODE-DPDP-005"],
        "sections": ["§8(6)"],
    },
    {
        "id": "retention_erasure",
        "label": "Retention & Erasure",
        "rule_prefixes": ["SQL-DPDP-002", "SQL-DPDP-003", "ARCH-DPDP-002"],
        "sections": ["Rule 6(1)(e)", "Rule 8"],
    },
    {
        "id": "children_protection",
        "label": "Children & PwD Protection",
        "rule_prefixes": ["ARCH-DPDP-003"],
        "sections": ["§9"],
    },
    {
        "id": "sdf_duties",
        "label": "SDF Duties",
        "rule_prefixes": ["ARCH-DPDP-008"],
        "sections": ["§10"],
    },
    {
        "id": "data_principal_rights",
        "label": "Data Principal Rights",
        "rule_prefixes": ["ARCH-DPDP-001"],
        "sections": ["Rule 14", "§11", "§12", "§13"],
    },
    {
        "id": "cross_border_cert_in",
        "label": "Cross-Border & CERT-In Controls",
        "rule_prefixes": ["IAC-DPDP-002", "IAC-DPDP-005", "IAC-DPDP-007", "SQL-DPDP-004", "ARCH-DPDP-004"],
        "sections": ["Rule 15", "CERT-In 2022"],
    },
]

BAND_HIERARCHY = ["250_crore", "200_crore_children", "200_crore_breach", "150_crore", "50_crore"]
BAND_DISPLAY = {
    "250_crore": "₹250 Crore (§8(5) Security Safeguards)",
    "200_crore_children": "₹200 Crore (§9 Children Protection)",
    "200_crore_breach": "₹200 Crore (§8(6) Breach Notification)",
    "150_crore": "₹150 Crore (§10 Significant Data Fiduciary)",
    "50_crore": "₹50 Crore (Residual / Procedural)",
}

def calculate_readiness_score(findings: list[ScoredFinding]) -> DpdpReadinessScore:
    """Calculate the 8-pillar compliance scorecard and apply dynamic penalty capping."""
    critical_count = sum(1 for f in findings if f.severity == Severity.CRITICAL)
    high_count = sum(1 for f in findings if f.severity == Severity.HIGH)

    max_band: str | None = None
    for band in BAND_HIERARCHY:
        if any(f.penalty_band == band for f in findings):
            max_band = band
            break

    max_ceiling_display = BAND_DISPLAY.get(max_band) if max_band else "None Engaged"

    pillar_scores: list[PillarScore] = []
    pillar_pcts: list[float] = []

    for pillar in PILLARS_METADATA:
        matching_findings = [
            f for f in findings
            if any(f.rule_id.startswith(p) for p in pillar["rule_prefixes"])
            or any(sec in f.dpdp_section for sec in pillar["sections"])
        ]
        
        deductions = 0.0
        failing_rules: list[str] = []
        for f in matching_findings:
            failing_rules.append(f.rule_id)
            if f.severity == Severity.CRITICAL:
                deductions += 40.0
            elif f.severity == Severity.HIGH:
                deductions += 25.0
            elif f.severity == Severity.MEDIUM:
                deductions += 15.0
            elif f.severity == Severity.LOW:
                deductions += 5.0

        p_score = max(0.0, round(100.0 - deductions, 1))
        pillar_pcts.append(p_score)

        pillar_scores.append(
            PillarScore(
                pillar_id=pillar["id"],
                label=pillar["label"],
                score=p_score,
                total_rules=len(pillar["rule_prefixes"]),
                passing_rules=max(0, len(pillar["rule_prefixes"]) - len(set(failing_rules))),
                failing_rule_ids=list(set(failing_rules)),
            )
        )

    unweighted_overall = sum(pillar_pcts) / len(pillar_pcts) if pillar_pcts else 100.0

    is_capped = False
    cap_reason = None
    final_score = unweighted_overall

    critical_in_high_band = any(
        f.severity == Severity.CRITICAL and f.penalty_band in ("250_crore", "200_crore_children", "200_crore_breach")
        for f in findings
    )

    if critical_in_high_band and final_score > 60.0:
        is_capped = True
        cap_reason = (
            f"Overall score capped at 60.0 due to {critical_count} unresolved CRITICAL finding(s) "
            f"in the {max_ceiling_display} penalty band."
        )
        final_score = 60.0

    return DpdpReadinessScore(
        overall=round(final_score, 1),
        is_capped=is_capped,
        cap_reason=cap_reason,
        pillars=pillar_scores,
        max_statutory_ceiling_engaged=max_ceiling_display,
        open_critical_count=critical_count,
        open_high_count=high_count,
    )
