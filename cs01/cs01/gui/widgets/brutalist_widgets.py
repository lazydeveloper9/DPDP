"""
CS-01 DPDP Compliance Desktop GUI - Neo-Brutalist Component Library.
===================================================================
Provides authentic Neo-Brutalist UI primitives engineered with PySide6 QPainter:
- Thick 2px/3px solid black (#111111) borders
- Hard offset shadows (4px-6px solid black, zero blur)
- Flat saturated color blocks (#FFE500 yellow, #B8F044 green, #FF4444 red, #3155FF cobalt)
- Tactile hover and pressed states (interactive components shift into their shadow)
- Strict geometric zero-radius corners
"""
from __future__ import annotations

from typing import Final
from PySide6.QtCore import QPoint, QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter, QPen
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    BRUTALIST_BG_MAIN,
    BRUTALIST_BLACK,
    BRUTALIST_BLACK_SEC,
    BRUTALIST_BORDER,
    BRUTALIST_GREEN,
    BRUTALIST_MUTED,
    BRUTALIST_ORANGE,
    BRUTALIST_RED,
    BRUTALIST_SURFACE,
    BRUTALIST_SURFACE_ALT,
    BRUTALIST_YELLOW,
)


class BrutalistCard(QFrame):
    """
    Core Neo-Brutalist Card Container.
    Renders a hard solid black offset shadow with 2px solid black border.
    """

    def __init__(
        self,
        bg_color: str | None = None,
        shadow_offset: tuple[int, int] | int = (4, 4),
        border_width: int = 2,
        bg: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        actual_bg = bg or bg_color or BRUTALIST_SURFACE
        self._bg_color = QColor(actual_bg)
        self._shadow_color = QColor(BRUTALIST_BLACK)
        self._border_color = QColor(BRUTALIST_BORDER)
        if isinstance(shadow_offset, int):
            self._shadow_offset = (shadow_offset, shadow_offset)
        else:
            self._shadow_offset = shadow_offset
        self._border_width = border_width
        self._is_hovered: bool = False
        self._inner_layout: QVBoxLayout | None = None

    @property
    def layout_container(self) -> QVBoxLayout:
        if self._inner_layout is None:
            sx, sy = self._shadow_offset
            self._inner_layout = QVBoxLayout(self)
            self._inner_layout.setContentsMargins(12, 12, 12 + sx, 12 + sy)
            self._inner_layout.setSpacing(8)
        return self._inner_layout

    def set_bg_color(self, color_hex: str) -> None:
        self._bg_color = QColor(color_hex)
        self.update()

    def enterEvent(self, event) -> None:  # noqa: N802
        super().enterEvent(event)
        self._is_hovered = True
        self.update()

    def leaveEvent(self, event) -> None:  # noqa: N802
        super().leaveEvent(event)
        self._is_hovered = False
        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w, h = self.width(), self.height()
        sx, sy = self._shadow_offset

        # 1. Hard Offset Solid Shadow (Bottom-Right)
        shadow_rect = QRect(sx, sy, w - sx, h - sy)
        painter.fillRect(shadow_rect, self._shadow_color)

        # 2. Main Card Body
        body_rect = QRect(0, 0, w - sx, h - sy)
        painter.fillRect(body_rect, self._bg_color)

        # 3. Solid Black Border (2px)
        pen = QPen(self._border_color, self._border_width)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.drawRect(body_rect.adjusted(1, 1, -1, -1))


class BrutalistMetricCard(BrutalistCard):
    """
    Neo-Brutalist Executive KPI Card.
    Displays an uppercase category header, large bold metric, and supporting label.
    """

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str,
        bg_color: str = BRUTALIST_SURFACE,
        val_color: str = BRUTALIST_BLACK,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(bg_color=bg_color, shadow_offset=(5, 5), border_width=2, parent=parent)

        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet(
            f"font-size: 8.5pt; font-weight: 800; color: {BRUTALIST_BLACK}; "
            "letter-spacing: 0.8px; background: transparent;"
        )
        self.layout_container.addWidget(self.title_label)

        self.value_label = QLabel(value)
        self.value_label.setStyleSheet(
            f"font-size: 26pt; font-weight: 900; color: {val_color}; "
            "letter-spacing: -0.5px; background: transparent;"
        )
        self.layout_container.addWidget(self.value_label)

        self.subtitle_label = QLabel(subtitle)
        self.subtitle_label.setStyleSheet(
            f"font-size: 8.5pt; font-weight: 600; color: {BRUTALIST_BLACK_SEC}; "
            "background: transparent;"
        )
        self.subtitle_label.setWordWrap(True)
        self.layout_container.addWidget(self.subtitle_label)

    def set_values(self, value: str, subtitle: str | None = None, val_color: str | None = None) -> None:
        self.value_label.setText(value)
        if subtitle is not None:
            self.subtitle_label.setText(subtitle)
        if val_color is not None:
            self.value_label.setStyleSheet(
                f"font-size: 26pt; font-weight: 900; color: {val_color}; "
                "letter-spacing: -0.5px; background: transparent;"
            )
        self.update()


class BrutalistButton(QPushButton):
    """
    Tactile Neo-Brutalist PushButton.
    Paints a crisp 2px black border and 4px hard black offset shadow.
    On mousePress, the button physically translates into its shadow.
    """

    def __init__(
        self,
        text: str,
        variant: str = "primary",  # "primary" (yellow), "secondary" (white), "danger" (red), "dark" (black)
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self._variant = variant
        self._is_pressed: bool = False
        self._is_hovered: bool = False
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(36)
        self.setMinimumWidth(80)

        # Configure colors by variant
        if variant == "primary":
            self._fill_color = QColor(BRUTALIST_YELLOW)
            self._text_color = QColor(BRUTALIST_BLACK)
        elif variant == "danger":
            self._fill_color = QColor(BRUTALIST_RED)
            self._text_color = QColor("#FFFFFF")
        elif variant == "dark":
            self._fill_color = QColor(BRUTALIST_BLACK)
            self._text_color = QColor(BRUTALIST_YELLOW)
        else:  # secondary / default
            self._fill_color = QColor(BRUTALIST_SURFACE)
            self._text_color = QColor(BRUTALIST_BLACK)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self._is_pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        self._is_pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def enterEvent(self, event) -> None:  # noqa: N802
        self._is_hovered = True
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        self._is_hovered = False
        self._is_pressed = False
        self.update()
        super().leaveEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        w, h = self.width(), self.height()
        sx, sy = (4, 4)

        if not self.isEnabled():
            # Disabled button appearance
            body = QRect(0, 0, w - sx, h - sy)
            painter.fillRect(body, QColor("#E0E0E0"))
            pen = QPen(QColor("#888888"), 2)
            painter.setPen(pen)
            painter.drawRect(body.adjusted(1, 1, -1, -1))
            painter.setPen(QColor("#888888"))
            painter.setFont(QFont("Space Grotesk", 9, QFont.Weight.Bold))
            painter.drawText(body, Qt.AlignmentFlag.AlignCenter, self.text())
            return

        # 1. Hard Offset Shadow (unless pressed)
        if not self._is_pressed:
            shadow_rect = QRect(sx, sy, w - sx, h - sy)
            painter.fillRect(shadow_rect, QColor(BRUTALIST_BLACK))

        # 2. Main Button Body (moves into shadow when pressed)
        offset = (2, 2) if self._is_pressed else (0, 0)
        body = QRect(offset[0], offset[1], w - sx, h - sy)

        fill = self._fill_color
        if self._is_hovered and not self._is_pressed:
            if self._variant == "primary":
                fill = QColor("#FFD400")
            elif self._variant == "secondary":
                fill = QColor(BRUTALIST_SURFACE_ALT)

        painter.fillRect(body, fill)

        # 3. 2px Solid Black Border
        pen = QPen(QColor(BRUTALIST_BORDER), 2)
        pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
        painter.setPen(pen)
        painter.drawRect(body.adjusted(1, 1, -1, -1))

        # 4. Button Text
        painter.setPen(self._text_color)
        font = QFont("Space Grotesk", 9, QFont.Weight.Bold)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(body, Qt.AlignmentFlag.AlignCenter, self.text())


class BrutalistBadge(QLabel):
    """
    Rectangular Neo-Brutalist Status Badge with 1.5px/2px solid black border.
    """

    def __init__(
        self,
        text: str,
        bg_color: str = BRUTALIST_YELLOW,
        text_color: str = BRUTALIST_BLACK,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(text, parent)
        self.set_badge_style(bg_color, text_color)

    def set_badge_style(self, bg_color: str, text_color: str = BRUTALIST_BLACK) -> None:
        self.setStyleSheet(
            f"background-color: {bg_color}; color: {text_color}; "
            f"border: 1.5px solid {BRUTALIST_BLACK}; "
            "font-size: 8pt; font-weight: 800; padding: 3px 8px; border-radius: 0px;"
        )
