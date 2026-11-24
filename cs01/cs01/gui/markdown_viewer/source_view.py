"""
CS-01 DPDP Compliance Desktop GUI - Markdown Source Code Viewer with Line Numbers.

Provides a read-only monospaced editor for inspecting raw Markdown source text,
complete with an integrated line-number gutter, search highlighting, and selection.
"""
from __future__ import annotations

from PySide6.QtCore import QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QPaintEvent, QPainter, QTextFormat
from PySide6.QtWidgets import (
    QPlainTextEdit,
    QTextEdit,
    QWidget,
)


class LineNumberArea(QWidget):
    """Gutter widget displaying line numbers synchronized with the source editor."""

    def __init__(self, editor: MarkdownSourceView) -> None:
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:  # noqa: N802
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802
        self.code_editor.line_number_area_paint_event(event)


class MarkdownSourceView(QPlainTextEdit):
    """
    Read-only source view for inspecting raw Markdown documents with line numbers.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.line_number_area = LineNumberArea(self)

        # Typography: Cascadia Code with fallbacks
        font = QFont("Cascadia Code", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self.setStyleSheet(
            "QPlainTextEdit { background-color: #FFFFFF; color: #111111; "
            "border: 2px solid #111111; border-radius: 0px; padding: 6px; } "
            "QPlainTextEdit:focus { border: 2px solid #111111; }"
        )

        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)

        self._update_line_number_area_width(0)

    def line_number_area_width(self) -> int:
        """Calculates gutter width based on total block/line count."""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 16 + self.fontMetrics().horizontalAdvance("9") * digits
        return max(42, space)

    def _update_line_number_area_width(self, _: int) -> None:
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int) -> None:
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())

        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, event) -> None:  # noqa: N802
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event: QPaintEvent) -> None:
        """Paints line numbers and gutter boundary."""
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#EAE6DA"))

        # Gutter right border (Neo-Brutalist 1.5px solid black)
        painter.setPen(QColor("#111111"))
        painter.drawLine(
            self.line_number_area.width() - 1,
            event.rect().top(),
            self.line_number_area.width() - 1,
            event.rect().bottom(),
        )

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + int(self.blockBoundingRect(block).height())

        painter.setFont(self.font())
        painter.setPen(QColor("#595959"))

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight,
                    number,
                )

            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1
