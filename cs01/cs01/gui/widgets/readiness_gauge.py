"""
CS-01 DPDP Compliance Desktop GUI - DPDP Readiness Gauge Widget.

Neo-Brutalist custom-painted arc gauge rendering a 0–100 score with
2px solid black border, 5px hard offset shadow, and dynamic capping badge.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import QWidget

from cs01.gui.theme import (
    BRUTALIST_BG_SECONDARY,
    BRUTALIST_BLACK,
    BRUTALIST_BORDER,
    BRUTALIST_GREEN,
    BRUTALIST_MUTED,
    BRUTALIST_ORANGE,
    BRUTALIST_RED,
    BRUTALIST_SURFACE,
    BRUTALIST_YELLOW,
)


class ReadinessGaugeWidget(QWidget):
    """
    Neo-Brutalist DPDP Readiness Gauge (0.0 – 100.0).
    Renders a 270° sweeping arc on a white card with 2px black border and 5px shadow.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.score: float = 100.0
        self.is_capped: bool = False
        self.cap_reason: str | None = None
        self.setMinimumSize(200, 200)

        try:
            from cs01.gui.theme_engine.theme_manager import ThemeManager
            ThemeManager.instance().theme_changed.connect(self.update)
        except Exception:
            pass

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
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        try:
            from cs01.gui.theme_engine.theme_manager import ThemeManager
            tm = ThemeManager.instance()
            shadow_c = QColor(str(tm.get_token("page.dashboard.kpi_card_shadow", BRUTALIST_BLACK)))
            card_c = QColor(str(tm.get_token("page.dashboard.kpi_card_bg", BRUTALIST_SURFACE)))
            border_c = QColor(str(tm.get_token("page.dashboard.kpi_card_border", BRUTALIST_BORDER)))
            b_width = int(tm.get_token("design.border.width", 2))
            sx = int(tm.get_token("design.shadow.x", 5))
            sy = int(tm.get_token("design.shadow.y", 5))
            shadow_enabled = bool(tm.get_token("design.shadow.enabled", True))
            custom_gauge_color = tm.get_token("page.dashboard.gauge_color")
        except Exception:
            shadow_c = QColor(BRUTALIST_BLACK)
            card_c = QColor(BRUTALIST_SURFACE)
            border_c = QColor(BRUTALIST_BORDER)
            b_width = 2
            sx, sy = (5, 5)
            shadow_enabled = True
            custom_gauge_color = None

        w, h = self.width(), self.height()
        if not shadow_enabled:
            sx, sy = (0, 0)

        # 1. Hard Offset Solid Shadow
        if shadow_enabled and (sx > 0 or sy > 0):
            shadow_rect = QRect(sx, sy, w - sx, h - sy)
            painter.fillRect(shadow_rect, shadow_c)

        # 2. Main Card Body
        body_rect = QRect(0, 0, w - sx, h - sy)
        painter.fillRect(body_rect, card_c)

        # 3. Solid Border
        if b_width > 0:
            pen = QPen(border_c, b_width)
            pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
            painter.setPen(pen)
            painter.drawRect(body_rect.adjusted(1, 1, -1, -1))

        # 4. Gauge Arc
        gauge_size = min(body_rect.width(), body_rect.height()) - 48
        gx = body_rect.x() + (body_rect.width() - gauge_size) / 2
        gy = body_rect.y() + (body_rect.height() - gauge_size) / 2
        arc_rect = QRectF(gx, gy, gauge_size, gauge_size)

        # Track arc
        track_pen = QPen(QColor(BRUTALIST_BG_SECONDARY), 14)
        track_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(track_pen)
        painter.drawArc(arc_rect, 225 * 16, -270 * 16)

        # Value arc
        if custom_gauge_color and custom_gauge_color != "#FFE500":
            arc_color = QColor(str(custom_gauge_color))
        elif self.score >= 80.0:
            arc_color = QColor(BRUTALIST_GREEN)
        elif self.score >= 60.0:
            arc_color = QColor(BRUTALIST_ORANGE)
        else:
            arc_color = QColor(BRUTALIST_RED)

        val_pen = QPen(arc_color, 14)
        val_pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        painter.setPen(val_pen)
        span_angle = -int(270 * (self.score / 100.0) * 16)
        painter.drawArc(arc_rect, 225 * 16, span_angle)

        # Central numeric score
        painter.setPen(QColor(BRUTALIST_BLACK))
        font = QFont("Space Grotesk", 24, QFont.Weight.Bold)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(arc_rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.score)}")

        # "DPDP READINESS" subtitle
        sub_font = QFont("Space Grotesk", 8, QFont.Weight.Bold)
        sub_font.setBold(True)
        painter.setFont(sub_font)
        painter.setPen(QColor(BRUTALIST_MUTED))
        sub_rect = QRectF(arc_rect.x(), arc_rect.y() + 44, arc_rect.width(), arc_rect.height())
        painter.drawText(sub_rect, Qt.AlignmentFlag.AlignCenter, "DPDP READINESS")

        # CAPPED Badge
        if self.is_capped:
            badge_w, badge_h = 76, 20
            bx = int(body_rect.x() + (body_rect.width() - badge_w) / 2)
            by = int(body_rect.y() + body_rect.height() - badge_h - 10)
            badge_rect = QRect(bx, by, badge_w, badge_h)
            painter.fillRect(badge_rect, QColor(BRUTALIST_RED))
            pen_b = QPen(QColor(BRUTALIST_BORDER), 1.5)
            painter.setPen(pen_b)
            painter.drawRect(badge_rect)
            painter.setPen(QColor("#FFFFFF"))
            b_font = QFont("Space Grotesk", 7, QFont.Weight.Bold)
            b_font.setBold(True)
            painter.setFont(b_font)
            painter.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, "CAPPED")
