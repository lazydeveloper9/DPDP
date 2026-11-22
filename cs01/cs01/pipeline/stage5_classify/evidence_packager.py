"""
Stage 5 Evidence Packager
=========================
Attaches statutory disclaimers, formatted penalty ceiling bands,
redacted code snippets, and fingerprinting metadata to convert RawFindings into ScoredFindings.
"""

from __future__ import annotations
import hashlib
from cs01.models import RawFinding, ScoredFinding, ExposureContext
from cs01.utils import redact_pii_in_snippet

CEILING_MAP = {
    "250_crore": "DPDP Act §8(5) — Up to ₹250 Crore (Discretionary Maximum)",
    "200_crore_breach": "DPDP Act §8(6) — Up to ₹200 Crore (Discretionary Maximum)",
    "200_crore_children": "DPDP Act §9 — Up to ₹200 Crore (Discretionary Maximum)",
    "150_crore": "DPDP Act §10 — Up to ₹150 Crore (Discretionary Maximum)",
    "50_crore": "DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum)",
}


def package_evidence(
    raw: RawFinding,
    priority_score: float,
    confidence: float,
    exposure: str,
    s_weight: float,
    b_weight: float,
    e_mult: float,
) -> ScoredFinding:
    """Transform RawFinding into a fully packaged and scored ScoredFinding."""
    ceiling_display = CEILING_MAP.get(
        raw.penalty_band,
        f"DPDP Act — Statutory Ceiling: {raw.penalty_band} (Discretionary Maximum)",
    )

    # Compute a unique fingerprint for baseline diffing
    key_str = f"{raw.rule_id}:{raw.file or 'global'}:{raw.line_start or 0}:{raw.snippet[:60]}"
    fingerprint = hashlib.sha256(key_str.encode("utf-8")).hexdigest()

    # Redact any remaining raw PII literals
    redacted = redact_pii_in_snippet(raw.snippet, [])

    return ScoredFinding(
        id=raw.id,
        rule_id=raw.rule_id,
        pass_type=raw.pass_type,
        file=raw.file,
        line_start=raw.line_start,
        line_end=raw.line_end,
        snippet=raw.snippet,
        matched_entity=raw.matched_entity,
        dpdp_section=raw.dpdp_section,
        dpdp_rule=raw.dpdp_rule,
        penalty_band=raw.penalty_band,
        severity=raw.severity,
        engine=raw.engine,
        message=raw.message,
        remediation=raw.remediation,
        contributing_pii_hit_ids=raw.contributing_pii_hit_ids,
        contributing_flow_edge_ids=raw.contributing_flow_edge_ids,
        priority_score=priority_score,
        confidence=confidence,
        exposure=exposure,
        band_weight=b_weight,
        severity_weight=s_weight,
        exposure_multiplier=e_mult,
        statutory_ceiling_display=ceiling_display,
        redacted_snippet=redacted,
        dedupe_key=fingerprint,
    )
