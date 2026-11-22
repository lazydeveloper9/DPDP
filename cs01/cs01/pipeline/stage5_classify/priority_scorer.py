"""
Stage 5 Priority Scorer
=======================
Implements the statutory penalty-weighted risk scoring model:
  Priority Score = Severity_Weight × Confidence × Penalty_Band_Weight × Exposure_Multiplier
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML
from cs01.models import RawFinding, Severity, ExposureContext

yaml = YAML()

# Default scoring weights (overridden by policy_profiles/penalty_bands.yaml if present)
DEFAULT_SEVERITY_WEIGHTS: dict[Severity, float] = {
    Severity.CRITICAL: 1.00,
    Severity.HIGH: 0.75,
    Severity.MEDIUM: 0.45,
    Severity.LOW: 0.20,
    Severity.INFO: 0.05,
}

DEFAULT_BAND_WEIGHTS: dict[str, float] = {
    "250_crore": 1.00,
    "200_crore_breach": 0.85,
    "200_crore_children": 0.85,
    "150_crore": 0.70,
    "50_crore": 0.40,
}

DEFAULT_EXPOSURE_MULTIPLIERS: dict[str, float] = {
    ExposureContext.EXTERNAL_LIVE: 1.25,
    ExposureContext.PRODUCTION: 1.00,
    ExposureContext.INTERNAL: 0.50,
}


class PriorityScorer:
    """Computes statutory priority scores for findings."""

    def __init__(self, policy_profiles_dir: Path | str | None = None):
        self.severity_weights = dict(DEFAULT_SEVERITY_WEIGHTS)
        self.band_weights = dict(DEFAULT_BAND_WEIGHTS)
        self.exposure_multipliers = dict(DEFAULT_EXPOSURE_MULTIPLIERS)

        if policy_profiles_dir:
            p = Path(policy_profiles_dir) / "penalty_bands.yaml"
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as fh:
                        data = yaml.load(fh)
                    sw = data.get("scoring_weights", {})
                    if "severity_weights" in sw:
                        for k, v in sw["severity_weights"].items():
                            try:
                                self.severity_weights[Severity(k)] = float(v)
                            except ValueError:
                                pass
                    if "band_weights" in sw:
                        for k, v in sw["band_weights"].items():
                            self.band_weights[k] = float(v)
                except Exception:
                    pass

    def compute_score(
        self,
        severity: Severity,
        penalty_band: str,
        confidence: float = 0.90,
        exposure: str = ExposureContext.PRODUCTION,
    ) -> tuple[float, float, float, float]:
        """
        Returns (priority_score, severity_weight, band_weight, exposure_multiplier).
        """
        s_weight = self.severity_weights.get(severity, 0.45)
        b_weight = self.band_weights.get(penalty_band, 0.40)
        e_mult = self.exposure_multipliers.get(exposure, 1.00)

        raw_score = s_weight * confidence * b_weight * e_mult
        priority_score = round(min(1.0, max(0.0, raw_score)), 4)

        return priority_score, s_weight, b_weight, e_mult
