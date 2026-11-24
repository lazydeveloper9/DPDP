"""
CS-01 DPDP Compliance Desktop GUI - Unified Diff Patch Viewer Dialog.

Modal QDialog rendering a unified diff patch with syntax highlighting:
  - Green  (+) addition lines
  - Red    (-) deletion lines
  - Cyan   (@) hunk headers
  - Default colour for context lines
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import FONT_FAMILY_MONO


class DiffViewerDialog(QDialog):
    """
    Modal dialog displaying a unified diff patch with syntax colouring.

    Args:
        diff_content: Raw unified diff text to render.
        patch_id:     Human-readable identifier shown in the window title.
    """

    def __init__(
        self,
        diff_content: str = "",
        patch_id: str = "Patch",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"Remediation Patch — {patch_id}")
        self.resize(700, 500)
        self.diff_content = diff_content

        layout = QVBoxLayout(self)

        self.setStyleSheet("background-color: #F6F3EA;")

        self.editor = QPlainTextEdit()
        self.editor.setReadOnly(True)
        self.editor.setStyleSheet(
            "background-color: #FFFFFF; "
            "color: #111111; "
            "font-family: 'Cascadia Code', 'Consolas', monospace; "
            "font-size: 10pt; "
            "border: 2px solid #111111; "
            "padding: 8px;"
        )
        layout.addWidget(self.editor)

        self._render_diff()

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        buttons.setStyleSheet(
            "QPushButton { background-color: #EAE6DA; color: #111111; font-weight: 800; "
            "border: 2px solid #111111; padding: 6px 16px; text-transform: uppercase; } "
            "QPushButton:hover { background-color: #FFE500; }"
        )
        buttons.rejected.connect(self.close)
        layout.addWidget(buttons)

    def _render_diff(self) -> None:
        """Parse and render the unified diff with per-line syntax colouring."""
        if not self.diff_content.strip():
            self.editor.setPlainText("No remediation diff available.")
            return

        for line in self.diff_content.splitlines():
            line_esc = (
                line
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )
            if line.startswith("+"):
                self.editor.appendHtml(f"<span style='color: #15803d; font-weight: bold; background-color: #dcfce7;'>{line_esc}</span>")
            elif line.startswith("-"):
                self.editor.appendHtml(f"<span style='color: #b91c1c; font-weight: bold; background-color: #fee2e2;'>{line_esc}</span>")
            elif line.startswith("@@"):
                self.editor.appendHtml(f"<span style='color: #1d4ed8; font-weight: bold; background-color: #dbeafe;'>{line_esc}</span>")
            else:
                self.editor.appendPlainText(line)
