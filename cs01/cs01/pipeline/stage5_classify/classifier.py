"""
Pipeline Stage 5 — Classify Risk & Package Evidence
===================================================
Entry point: run_classify(raw_findings, cfg, **kwargs) -> ScoredFindingBundle

Orchestrates:
  1. Finding deduplication
  2. Statutory priority risk scoring
  3. Evidence packaging & PII redaction
  4. 8-Pillar DPDP Readiness Score computation with dynamic capping
"""

from __future__ import annotations
from typing import Any

from cs01.models import (
    RawFinding, ScoredFinding, ScoredFindingBundle, ScanConfig, ExposureContext,
)
from .deduplicator import deduplicate_findings
from .priority_scorer import PriorityScorer
from .readiness_scorer import calculate_readiness_score
from .evidence_packager import package_evidence

def run_classify(
    raw_findings: list[RawFinding],
    cfg: ScanConfig,
    **kwargs: Any,
) -> ScoredFindingBundle:
    """Stage 5 execution: deduplicate, score, and package findings."""
    scorer = PriorityScorer(cfg.policy_profiles_dir)

    deduped_raw = deduplicate_findings(raw_findings)

    scored_list: list[ScoredFinding] = []
    for raw in deduped_raw:
        confidence = 0.90
        exposure = ExposureContext.PRODUCTION
        if raw.file and any(p in raw.file.replace("\\", "/").lower() for p in ("/tests/", "/test/", "/spec/")):
            exposure = ExposureContext.INTERNAL
            confidence = 0.30

        p_score, s_w, b_w, e_m = scorer.compute_score(
            severity=raw.severity,
            penalty_band=raw.penalty_band,
            confidence=confidence,
            exposure=exposure,
        )

        scored = package_evidence(
            raw=raw,
            priority_score=p_score,
            confidence=confidence,
            exposure=exposure,
            s_weight=s_w,
            b_weight=b_w,
            e_mult=e_m,
        )
        scored_list.append(scored)

    if cfg.baseline_path:
        from pathlib import Path
        bpath = Path(cfg.baseline_path)
        if bpath.exists():
            from cs01.utils import load_json
            try:
                bdata = load_json(bpath)
                fingerprints: set[str] = set()
                if isinstance(bdata, dict):
                    if "fingerprints" in bdata:
                        fingerprints = set(bdata["fingerprints"])
                    elif "findings" in bdata:
                        fingerprints = {f.get("dedupe_key") for f in bdata["findings"] if f.get("dedupe_key")}
                elif isinstance(bdata, list):
                    fingerprints = {item if isinstance(item, str) else item.get("dedupe_key", "") for item in bdata}
                
                for s in scored_list:
                    if s.dedupe_key in fingerprints:
                        s.is_baseline_suppressed = True
            except Exception:
                pass

    scored_list.sort(key=lambda s: s.priority_score, reverse=True)

    readiness = calculate_readiness_score(scored_list)

    return ScoredFindingBundle(
        scan_id=kwargs.get("scan_id", "local_scan"),
        scan_timestamp=kwargs.get("scan_timestamp", ""),
        scan_root=kwargs.get("scan_root", cfg.scan_root),
        total_files_scanned=kwargs.get("total_files", 0),
        partial_scan=kwargs.get("partial_scan", False),
        partial_scan_details=kwargs.get("partial_details", []),
        findings=scored_list,
        readiness=readiness,
    )
