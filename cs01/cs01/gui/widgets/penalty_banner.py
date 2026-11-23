"""
CS-01 DPDP Compliance Desktop GUI - Section 33 Penalty Ceiling Banner.

Renders the maximum statutory penalty ceiling from the DPDP Act 2023 Schedule,
with a legal disclaimer tooltip clarifying CS-01 is a technical tool, not counsel.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    COLOR_BG_CARD,
    COLOR_BORDER_SUBTLE,
    COLOR_RISK_CRITICAL,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_SECONDARY,
)

_AMBER = "#f59e0b"


class PenaltyCeilingBanner(QFrame):
    """
    Section 33 statutory maximum penalty ceiling display with legal disclaimer.

    Colour-codes the ceiling label:
    - Red for ₹200–₹250 Crore ceilings (CRITICAL tier)
    - Amber for ₹50–₹150 Crore ceilings (HIGH/MEDIUM tier)
    - Green for no engaged ceiling (compliant)
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"background-color: {COLOR_BG_CARD}; "
            f"border: 1px solid {COLOR_BORDER_SUBTLE}; "
            "border-radius: 6px; padding: 10px;"
        )

        layout = QHBoxLayout(self)

        self.icon_label = QLabel("")
        self.icon_label.setVisible(False)

        v_layout = QVBoxLayout()
        self.title_label = QLabel("Section 33 Maximum Statutory Penalty Exposure:")
        self.title_label.setStyleSheet(f"font-size: 11px; color: {COLOR_TEXT_SECONDARY};")
        v_layout.addWidget(self.title_label)

        self.ceiling_label = QLabel("None Engaged (₹0)")
        self.ceiling_label.setStyleSheet(
            f"font-size: 16px; font-weight: bold; color: {COLOR_STATUS_SUCCESS};"
        )
        v_layout.addWidget(self.ceiling_label)
        layout.addLayout(v_layout)

        layout.addStretch()

        self.disclaimer_icon = QLabel("Legal Disclaimer")
        self.disclaimer_icon.setToolTip(
            "Penalty is a statutory maximum ceiling. Actual penalty is discretionary "
            "and determined by the DPBI after formal inquiry under §33(2). "
            "CS-01 is a technical auditing tool, not legal counsel."
        )
        self.disclaimer_icon.setStyleSheet("color: #38bdf8; text-decoration: underline;")
        layout.addWidget(self.disclaimer_icon)

    def set_ceiling(self, ceiling_text: str) -> None:
        """Update the ceiling label text and re-colour based on the band."""
        self.ceiling_label.setText(ceiling_text)
        if "250" in ceiling_text or "200" in ceiling_text:
            self.ceiling_label.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {COLOR_RISK_CRITICAL};"
            )
        elif "150" in ceiling_text or "50" in ceiling_text:
            self.ceiling_label.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {_AMBER};"
            )
        else:
            self.ceiling_label.setStyleSheet(
                f"font-size: 16px; font-weight: bold; color: {COLOR_STATUS_SUCCESS};"
            )
