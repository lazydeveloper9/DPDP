"""
CS-01 DPDP Compliance Desktop GUI - Live Log Console Widget.

A read-only QPlainTextEdit that streams pipeline stage logs with
level-coloured HTML formatting for real-time DPO audit monitoring.
"""
from __future__ import annotations

from PySide6.QtWidgets import QPlainTextEdit, QWidget

from cs01.gui.theme import COLOR_BORDER_SUBTLE, COLOR_TEXT_PRIMARY, FONT_FAMILY_MONO

_LEVEL_COLORS: dict[str, str] = {
    "INFO": "#94a3b8",
    "WARNING": "#f59e0b",
    "ERROR": "#ef4444",
    "CRITICAL": "#ef4444",
    "SUCCESS": "#10b981",
    "DEBUG": "#64748b",
}


class LogConsoleWidget(QPlainTextEdit):
    """
    Real-time log console widget with HTML level-colour formatting.

    Messages are appended via append_log(level, message) which colour-codes
    the level prefix. The widget is read-only and uses a monospace code font.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setStyleSheet(
            f"background-color: #050811; "
            f"color: {COLOR_TEXT_PRIMARY}; "
            f"font-family: {FONT_FAMILY_MONO}; "
            f"font-size: 11px; "
            f"border: 1px solid {COLOR_BORDER_SUBTLE};"
        )

    def toHtml(self) -> str:  # noqa: N802
        """Return the full HTML content of the console."""
        return self.document().toHtml()

    def append_log(self, level: str, message: str) -> None:
        """Append a formatted log entry with level-dependent colour coding."""
        color = _LEVEL_COLORS.get(level.upper(), COLOR_TEXT_PRIMARY)
        escaped = (
            message
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        self.appendHtml(
            f"<span style='color:{color};'>"
            f"<b>[{level.upper()}]</b> {escaped}"
            f"</span>"
        )
