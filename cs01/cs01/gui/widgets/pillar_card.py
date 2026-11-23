"""
CS-01 DPDP Compliance Desktop GUI - Statutory Pillar Card Widget.

Renders an individual DPDP compliance pillar scorecard as a styled QFrame
with a progress bar, numeric score, and failing rule count badge.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    COLOR_BG_CARD,
    COLOR_BG_CARD_HOVER,
    COLOR_BORDER_SUBTLE,
    COLOR_RISK_CRITICAL,
    COLOR_RISK_MEDIUM,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_PRIMARY,
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

    clicked = Signal(str)

    def __init__(self, pillar_id: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pillar_id = pillar_id
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_BG_CARD}; "
            f"border: 1px solid {COLOR_BORDER_SUBTLE}; "
            "border-radius: 8px; padding: 10px; }}"
            f"QFrame:hover {{ border-color: #38bdf8; background-color: {COLOR_BG_CARD_HOVER}; }}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # Header row: Label + Status Pill
        header_row = QHBoxLayout()
        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet(f"font-weight: 600; font-size: 11px; color: {COLOR_TEXT_PRIMARY};")
        self.label_widget.setWordWrap(True)
        header_row.addWidget(self.label_widget, stretch=1)

        self.status_pill = QLabel("Good")
        self.status_pill.setStyleSheet(
            f"background-color: rgba(34, 197, 94, 0.15); color: {COLOR_STATUS_SUCCESS}; "
            "font-size: 8pt; font-weight: bold; padding: 2px 6px; border-radius: 4px;"
        )
        header_row.addWidget(self.status_pill)
        layout.addLayout(header_row)

        # Score Row
        self.score_label = QLabel("100.0 / 100")
        self.score_label.setStyleSheet(f"color: {COLOR_STATUS_SUCCESS}; font-weight: bold; font-size: 14px;")
        layout.addWidget(self.score_label)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: #0b1120; border: none; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ background-color: {COLOR_STATUS_SUCCESS}; border-radius: 3px; }}"
        )
        layout.addWidget(self.progress_bar)

        # Failing rules count badge
        self.issues_badge = QLabel("0 Failing Rules")
        self.issues_badge.setStyleSheet(f"color: {COLOR_TEXT_SECONDARY}; font-size: 10.5px;")
        layout.addWidget(self.issues_badge)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        super().mousePressEvent(event)
        self.clicked.emit(self.pillar_id)

    def set_data(self, score: float, failing_count: int = 0) -> None:
        """Update the pillar card with a new score and failing rule count."""
        self.score_label.setText(f"{score:.1f} / 100")
        self.progress_bar.setValue(int(score))
        self.issues_badge.setText(f"{failing_count} Failing Rules")

        if score >= 80:
            color = COLOR_STATUS_SUCCESS
            status_text = "Good"
            bg_color = "rgba(34, 197, 94, 0.15)"
        elif score >= 60:
            color = _AMBER
            status_text = "Needs Attention"
            bg_color = "rgba(245, 158, 11, 0.15)"
        else:
            color = COLOR_RISK_CRITICAL
            status_text = "Critical"
            bg_color = "rgba(239, 68, 68, 0.15)"

        self.status_pill.setText(status_text)
        self.status_pill.setStyleSheet(
            f"background-color: {bg_color}; color: {color}; "
            "font-size: 8pt; font-weight: bold; padding: 2px 6px; border-radius: 4px;"
        )
        self.score_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 14px;")
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: #0b1120; border: none; border-radius: 3px; }}"
            f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}"
        )
