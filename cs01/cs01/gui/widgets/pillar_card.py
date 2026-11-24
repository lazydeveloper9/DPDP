"""
CS-01 DPDP Compliance Desktop GUI - Statutory Pillar Card Widget.

Renders an individual DPDP compliance pillar scorecard as an authentic
Neo-Brutalist tile with a 2px solid black border, 4px hard black shadow,
tactile hover, crisp progress indicator, and rectangular status badge.
"""
from __future__ import annotations

from PySide6.QtCore import QPoint, QRect, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    BRUTALIST_BG_SECONDARY,
    BRUTALIST_BLACK,
    BRUTALIST_BORDER,
    BRUTALIST_GREEN,
    BRUTALIST_MUTED,
    BRUTALIST_ORANGE,
    BRUTALIST_RED,
    BRUTALIST_SURFACE,
    BRUTALIST_SURFACE_ALT,
)


class PillarCardWidget(QFrame):
    """
    Neo-Brutalist Statutory DPDP Pillar Card.
    Renders compliance score, progress bar, and failing rule badge with 4px hard shadow.

    Args:
        pillar_id: Unique slug identifier matching DpdpReadinessScore.pillars[].pillar_id.
        label: Human-readable statutory pillar name (e.g. "Notice & Consent (§5, §6)").
    """

    clicked = Signal(str)

    def __init__(self, pillar_id: str, label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.pillar_id = pillar_id
        self._is_hovered: bool = False
        self._bg_color = QColor(BRUTALIST_SURFACE)
        self.setCursor(Qt.PointingHandCursor)

        # 4px shadow offset margins
        sx, sy = (4, 4)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10 + sx, 10 + sy)
        layout.setSpacing(6)

        # Header row: Label + Status Pill
        header_row = QHBoxLayout()
        header_row.setSpacing(6)
        self.label_widget = QLabel(label)
        self.label_widget.setStyleSheet(
            f"font-weight: 800; font-size: 8.5pt; color: {BRUTALIST_BLACK}; background: transparent;"
        )
        self.label_widget.setWordWrap(True)
        header_row.addWidget(self.label_widget, stretch=1)

        self.status_pill = QLabel("Good")
        self.status_pill.setStyleSheet(
            f"background-color: {BRUTALIST_GREEN}; color: {BRUTALIST_BLACK}; "
            f"border: 1.5px solid {BRUTALIST_BORDER}; font-size: 7.5pt; font-weight: 800; "
            "padding: 2px 6px; border-radius: 0px;"
        )
        header_row.addWidget(self.status_pill)
        layout.addLayout(header_row)

        # Score Row
        self.score_label = QLabel("100.0 / 100")
        self.score_label.setStyleSheet(
            f"color: {BRUTALIST_BLACK}; font-weight: 900; font-size: 13pt; background: transparent;"
        )
        layout.addWidget(self.score_label)

        # Progress Bar (Neo-brutalist 2px border)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: {BRUTALIST_BG_SECONDARY}; border: 1.5px solid {BRUTALIST_BORDER}; border-radius: 0px; }}"
            f"QProgressBar::chunk {{ background-color: {BRUTALIST_GREEN}; border-right: 1.5px solid {BRUTALIST_BORDER}; }}"
        )
        layout.addWidget(self.progress_bar)

        # Failing rules count badge
        self.issues_badge = QLabel("0 Failing Rules")
        self.issues_badge.setStyleSheet(
            f"color: {BRUTALIST_MUTED}; font-size: 8.5pt; font-weight: 700; background: transparent;"
        )
        layout.addWidget(self.issues_badge)

    def enterEvent(self, event) -> None:  # noqa: N802
        super().enterEvent(event)
        self._is_hovered = True
        self._bg_color = QColor(BRUTALIST_SURFACE_ALT)
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        super().leaveEvent(event)
        self._is_hovered = False
        self._bg_color = QColor(BRUTALIST_SURFACE)
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w, h = self.width(), self.height()
        sx, sy = (4, 4)

        # 1. Hard Offset Solid Shadow (Bottom-Right)
        shadow_rect = QRect(sx, sy, w - sx, h - sy)
        painter.fillRect(shadow_rect, QColor(BRUTALIST_BLACK))

        # 2. Main Card Body
        body_rect = QRect(0, 0, w - sx, h - sy)
        painter.fillRect(body_rect, self._bg_color)

        # 3. Solid 2px Black Border
        pen = QPen(QColor(BRUTALIST_BORDER), 2)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.drawRect(body_rect.adjusted(1, 1, -1, -1))

    def mousePressEvent(self, event) -> None:  # noqa: N802
        super().mousePressEvent(event)
        self.clicked.emit(self.pillar_id)

    def set_data(self, score: float, failing_count: int = 0) -> None:
        """Update the pillar card with a new score and failing rule count."""
        self.score_label.setText(f"{score:.1f} / 100")
        self.progress_bar.setValue(int(score))
        self.issues_badge.setText(f"{failing_count} Failing Rules")

        if score >= 80:
            status_text = "Good"
            pill_bg = BRUTALIST_GREEN
            pill_text = BRUTALIST_BLACK
            chunk_color = BRUTALIST_GREEN
        elif score >= 60:
            status_text = "Needs Attention"
            pill_bg = BRUTALIST_ORANGE
            pill_text = BRUTALIST_BLACK
            chunk_color = BRUTALIST_ORANGE
        else:
            status_text = "Critical"
            pill_bg = BRUTALIST_RED
            pill_text = "#FFFFFF"
            chunk_color = BRUTALIST_RED

        self.status_pill.setText(status_text)
        self.status_pill.setStyleSheet(
            f"background-color: {pill_bg}; color: {pill_text}; "
            f"border: 1.5px solid {BRUTALIST_BORDER}; font-size: 7.5pt; font-weight: 800; "
            "padding: 2px 6px; border-radius: 0px;"
        )
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: {BRUTALIST_BG_SECONDARY}; border: 1.5px solid {BRUTALIST_BORDER}; border-radius: 0px; }}"
            f"QProgressBar::chunk {{ background-color: {chunk_color}; border-right: 1.5px solid {BRUTALIST_BORDER}; }}"
        )
