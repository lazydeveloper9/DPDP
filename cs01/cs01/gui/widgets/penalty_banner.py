"""
CS-01 DPDP Compliance Desktop GUI - Section 33 Penalty Ceiling Banner.

Renders the maximum statutory penalty ceiling from the DPDP Act 2023 Schedule
as an authentic Neo-Brutalist panel with 2px solid black border and 5px hard shadow.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt
from PySide6.QtGui import QColor, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    BRUTALIST_BLACK,
    BRUTALIST_BORDER,
    BRUTALIST_GREEN,
    BRUTALIST_MUTED,
    BRUTALIST_ORANGE,
    BRUTALIST_RED,
    BRUTALIST_SURFACE,
    BRUTALIST_SURFACE_ALT,
)


class PenaltyCeilingBanner(QFrame):
    """
    Neo-Brutalist Section 33 statutory maximum penalty ceiling display with legal disclaimer.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bg_color = QColor(BRUTALIST_SURFACE)

        # 5px shadow offset margins
        sx, sy = (5, 5)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 12, 14 + sx, 12 + sy)
        layout.setSpacing(12)

        self.icon_label = QLabel("")
        self.icon_label.setVisible(False)

        v_layout = QVBoxLayout()
        v_layout.setSpacing(3)
        self.title_label = QLabel("SECTION 33 MAXIMUM STATUTORY PENALTY EXPOSURE:")
        self.title_label.setStyleSheet(
            f"font-size: 8.5pt; font-weight: 800; color: {BRUTALIST_BLACK}; "
            "letter-spacing: 0.8px; background: transparent;"
        )
        v_layout.addWidget(self.title_label)

        self.ceiling_label = QLabel("None Engaged (₹0)")
        self.ceiling_label.setStyleSheet(
            f"font-size: 16pt; font-weight: 900; color: {BRUTALIST_BLACK}; background: transparent;"
        )
        v_layout.addWidget(self.ceiling_label)
        layout.addLayout(v_layout)

        layout.addStretch()

        self.disclaimer_icon = QLabel("LEGAL DISCLAIMER")
        self.disclaimer_icon.setToolTip(
            "Penalty is a statutory maximum ceiling under §33 Schedule. Actual penalty is discretionary "
            "and determined by the DPBI after formal inquiry under §33(2). "
            "CS-01 is a technical auditing tool, not legal counsel."
        )
        self.disclaimer_icon.setStyleSheet(
            f"background-color: {BRUTALIST_SURFACE_ALT}; color: {BRUTALIST_BLACK}; "
            f"border: 1.5px solid {BRUTALIST_BORDER}; font-size: 8pt; font-weight: 800; "
            "padding: 5px 10px; border-radius: 0px;"
        )
        self.disclaimer_icon.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self.disclaimer_icon)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w, h = self.width(), self.height()
        sx, sy = (5, 5)

        # 1. Hard Offset Solid Shadow
        shadow_rect = QRect(sx, sy, w - sx, h - sy)
        painter.fillRect(shadow_rect, QColor(BRUTALIST_BLACK))

        # 2. Main Body
        body_rect = QRect(0, 0, w - sx, h - sy)
        painter.fillRect(body_rect, self._bg_color)

        # 3. 2px Solid Black Border
        pen = QPen(QColor(BRUTALIST_BORDER), 2)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.drawRect(body_rect.adjusted(1, 1, -1, -1))

    def set_ceiling(self, ceiling_text: str) -> None:
        """Update the ceiling label text and re-colour based on the band."""
        self.ceiling_label.setText(ceiling_text)
        if "250" in ceiling_text or "200" in ceiling_text:
            self.ceiling_label.setStyleSheet(
                f"font-size: 16pt; font-weight: 900; color: {BRUTALIST_RED}; background: transparent;"
            )
        elif "150" in ceiling_text or "50" in ceiling_text:
            self.ceiling_label.setStyleSheet(
                f"font-size: 16pt; font-weight: 900; color: {BRUTALIST_ORANGE}; background: transparent;"
            )
        else:
            self.ceiling_label.setStyleSheet(
                f"font-size: 16pt; font-weight: 900; color: {BRUTALIST_BLACK}; background: transparent;"
            )
