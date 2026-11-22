"""
Stage 5 output model: ScoredFinding + ScoredFindingBundle + DpdpReadinessScore
Deduplicated, priority-scored findings ready for report rendering.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field
from .raw_finding import RawFinding, Severity


class ExposureContext(str):
    EXTERNAL_LIVE = "external_live"     # confirmed by DAST probe
    PRODUCTION = "production"
    INTERNAL = "internal"


class ScoredFinding(RawFinding):
    """
    A deduplicated, scored, evidence-enriched finding.
    Extends RawFinding with scoring and report-ready fields.
    """
    # Scoring
    priority_score: float = 0.0           # 0.0–1.0 (Severity x Confidence x Band x Exposure)
    confidence: float = 1.0
    exposure: str = ExposureContext.PRODUCTION
    band_weight: float = 1.0
    severity_weight: float = 1.0
    exposure_multiplier: float = 1.0

    # Statutory display
    statutory_ceiling_display: str = ""   # e.g. "§8(5) — up to ₹250 Cr (discretionary)"
    statutory_disclaimer: str = (
        "Penalty is a statutory maximum ceiling. Actual penalty is discretionary "
        "and determined by the DPBI after formal inquiry under §33(2). "
        "CS-01 is a technical auditing tool, not legal counsel."
    )

    # Evidence
    redacted_snippet: str = ""            # PII replaced with [AADHAAR_1], [PAN_1], etc.
    dedupe_key: str = ""                  # hash used for deduplication

    # Merge history
    merged_from_ids: list[str] = Field(default_factory=list)   # original RawFinding IDs


class PillarScore(BaseModel):
    pillar_id: str
    label: str
    score: float            # 0–100
    total_rules: int
    passing_rules: int
    failing_rule_ids: list[str] = Field(default_factory=list)


class DpdpReadinessScore(BaseModel):
    """
    Aggregate DPDP Readiness Score (0–100) across 8 statutory pillars.
    Dynamically capped when CRITICAL findings exist in high-penalty bands.
    """
    overall: float                                      # 0–100
    is_capped: bool = False
    cap_reason: Optional[str] = None                    # why the score was capped
    pillars: list[PillarScore] = Field(default_factory=list)
    max_statutory_ceiling_engaged: Optional[str] = None  # e.g. "₹250 Cr (§8(5))"
    open_critical_count: int = 0
    open_high_count: int = 0


class ScoredFindingBundle(BaseModel):
    """
    Output of Pipeline Stage 5 — Classify Risk & Package Evidence.
    This is the SOLE input to Stage 6 (Report).
    """
    scan_id: str                    # unique scan invocation ID (UUID)
    scan_timestamp: str             # ISO 8601
    scan_root: str
    cs01_version: str = "0.1.0-alpha"
    policy_profile_version: str = ""

    findings: list[ScoredFinding] = Field(default_factory=list)
    readiness: DpdpReadinessScore = Field(
        default_factory=lambda: DpdpReadinessScore(overall=100.0)
    )

    # Scan metadata
    total_files_scanned: int = 0
    partial_scan: bool = False      # True → exit code 3 (some files unparseable)
    partial_scan_details: list[str] = Field(default_factory=list)

    # Convenience views
    def by_severity(self, severity: Severity) -> list[ScoredFinding]:
        return [f for f in self.findings if f.severity == severity]

    def sorted_by_priority(self) -> list[ScoredFinding]:
        return sorted(self.findings, key=lambda f: f.priority_score, reverse=True)
