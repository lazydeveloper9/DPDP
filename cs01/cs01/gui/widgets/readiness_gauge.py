"""
CS-01 DPDP Compliance Desktop GUI - DPDP Readiness Gauge Widget.

Custom-painted arc gauge rendering a 0–100 score with dynamic colour
coding (green ≥80, amber ≥60, red <60) and an optional "CAPPED" badge
for Section 33 critical violation dynamic capping.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPaintEvent, QPen
from PySide6.QtWidgets import QWidget

from cs01.gui.theme import (
    COLOR_BG_CARD,
    COLOR_RISK_CRITICAL,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)

_AMBER = "#f59e0b"


class ReadinessGaugeWidget(QWidget):
    """
    Custom-painted DPDP Readiness Gauge arc (0.0 – 100.0).

    Renders a 270° sweeping arc with:
    - Green arc for scores ≥ 80 (compliant)
    - Amber arc for scores ≥ 60 (moderate risk)
    - Red arc for scores < 60 (non-compliant)
    Central text shows integer score; subtitle reads "DPDP READINESS".
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.score: float = 100.0
        self.is_capped: bool = False
        self.cap_reason: str | None = None
        self.setMinimumSize(180, 180)

    def set_score(
        self,
        score: float,
        is_capped: bool = False,
        cap_reason: str | None = None,
    ) -> None:
        """Update the displayed score and trigger a repaint."""
        self.score = max(0.0, min(100.0, float(score)))
        self.is_capped = is_capped
        self.cap_reason = cap_reason
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        from PySide6.QtCore import QRectF

        rect = self.rect()
        side = min(rect.width(), rect.height()) - 20
        gauge_rect = QRectF(10, 10, side, side)

        # Background track
        bg_pen = QPen(QColor(COLOR_BG_CARD), 12)
        bg_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(bg_pen)
        painter.drawArc(gauge_rect, 225 * 16, -270 * 16)

        # Determine arc colour based on score
        if self.score >= 80.0:
            arc_color = QColor(COLOR_STATUS_SUCCESS)
        elif self.score >= 60.0:
            arc_color = QColor(_AMBER)
        else:
            arc_color = QColor(COLOR_RISK_CRITICAL)

        val_pen = QPen(arc_color, 12)
        val_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(val_pen)
        span_angle = -int(270 * (self.score / 100.0) * 16)
        painter.drawArc(gauge_rect, 225 * 16, span_angle)

        # Central numeric score
        painter.setPen(QColor(COLOR_TEXT_PRIMARY))
        font = QFont("Arial", 24, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(gauge_rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.score)}")

        # "DPDP READINESS" subtitle
        from PySide6.QtCore import QRectF as _QRectF
        sub_font = QFont("Arial", 9)
        painter.setFont(sub_font)
        painter.setPen(QColor(COLOR_TEXT_SECONDARY))
        sub_rect = _QRectF(gauge_rect.x(), gauge_rect.y() + 40, gauge_rect.width(), gauge_rect.height())
        painter.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, "DPDP READINESS")

        # Optional CAPPED badge
        if self.is_capped:
            capped_font = QFont("Cascadia Code", 8, QFont.Weight.Bold)
            painter.setFont(capped_font)
            painter.setPen(QColor(COLOR_RISK_CRITICAL))
            cap_rect = _QRectF(gauge_rect.x(), gauge_rect.y() + 60, gauge_rect.width(), gauge_rect.height())
            painter.drawText(cap_rect, Qt.AlignmentFlag.AlignCenter, "CAPPED")
