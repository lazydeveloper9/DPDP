"""
CS-01 DPDP Compliance Desktop GUI - Central Observable GUI State.

GuiScanState is a QObject-backed, signal-emitting state container
holding the active scan bundle, deliverable paths, and PII hit inventory.
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Signal

from cs01.models.flow_graph import PiiHit
from cs01.models.scored_finding import ScoredFindingBundle


class GuiScanState(QObject):
    """
    Central observable state holding current scan results, artifacts, and metrics.

    Signals:
        state_changed(): Emitted whenever any state field is updated.
    """

    state_changed = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.bundle: ScoredFindingBundle | None = None
        self.report_files: dict[str, Path] = {}
        self.pii_hits: list[PiiHit] = []
        self.readiness_score: float = 100.0
        self.max_penalty_ceiling: str = "None Engaged"
        self.target_path: str = ""

    def update_state(
        self,
        bundle: ScoredFindingBundle | None = None,
        report_files: dict[str, Path] | None = None,
        pii_hits: list[PiiHit] | None = None,
    ) -> None:
        """Update any subset of state fields and emit state_changed."""
        if bundle is not None:
            self.bundle = bundle
            self.readiness_score = bundle.readiness.overall
            self.max_penalty_ceiling = bundle.readiness.max_statutory_ceiling_engaged or "None Engaged"
        if report_files is not None:
            self.report_files = report_files
        if pii_hits is not None:
            self.pii_hits = pii_hits
        self.state_changed.emit()
