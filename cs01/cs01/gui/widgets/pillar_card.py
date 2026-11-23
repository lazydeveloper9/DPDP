"""
CS-01 DPDP Compliance Desktop GUI - Statutory Pillar Card Widget.

Renders an individual DPDP compliance pillar scorecard as a styled QFrame
with a progress bar, numeric score, and failing rule count badge.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    COLOR_BG_CARD,
    COLOR_BORDER_SUBTLE,
    COLOR_RISK_CRITICAL,
    COLOR_RISK_MEDIUM,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_SECONDARY,
)

_AMBER = "#f59e0b"


class PillarCardWidget(QFrame):
    """
    Statutory DPDP Pillar Card rendering compliance score and failing rules count.

    Args:
        pillar_id: Unique slug identifier matching DpdpReadinessScore.pillars[].pillar_id.
        label: Human-readable statutory pillar name (e.g. "Notice & Consent (§5, §6)").
    """

    def __init__(self, pillar_id: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pillar_id = pillar_id
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"background-color: {COLOR_BG_CARD}; "
            f"border: 1px solid {COLOR_BORDER_SUBTLE}; "
            "border-radius: 6px; padding: 8px;"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet("font-weight: 600; font-size: 11px;")
        self.label_widget.setWordWrap(True)
        layout.addWidget(self.label_widget)

        self.score_label = QLabel("100.0 / 100")
        self.score_label.setStyleSheet(f"color: {COLOR_STATUS_SUCCESS}; font-weight: bold; font-size: 13px;")
        layout.addWidget(self.score_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {COLOR_STATUS_SUCCESS}; border-radius: 4px; }}"
        )
        layout.addWidget(self.progress_bar)

        self.issues_badge = QLabel("0 Failing Rules")
        self.issues_badge.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 11px;")
        layout.addWidget(self.issues_badge)

    def set_data(self, score: float, failing_count: int = 0) -> None:
        """Update the pillar card with a new score and failing rule count."""
        self.score_label.setText(f"{score:.1f} / 100")
        self.progress_bar.setValue(int(score))
        self.issues_badge.setText(f"{failing_count} Failing Rules")

        if score >= 80:
            color = COLOR_STATUS_SUCCESS
        elif score >= 60:
            color = _AMBER
        else:
            color = COLOR_RISK_CRITICAL

        self.score_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 13px;")
        self.progress_bar.setStyleSheet(
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 4px; }}"
        )
