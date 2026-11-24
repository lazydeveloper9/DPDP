"""
CS-01 DPDP Compliance Desktop GUI - In-App Report Search Bar Widget.

Provides interactive text search across rendered and source Markdown reports:
- Real-time search query dispatching
- Find Next / Previous navigation
- Match counter ("1 of 8 matches")
- Case-sensitive matching toggle
- Neo-Brutalist yellow highlight styling and keyboard shortcut hooks
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)


class MarkdownSearchBar(QFrame):
    """
    Search toolbar bar placed above document views.
    """

    search_requested = Signal(str, bool, bool)  # (query, forward, case_sensitive)
    search_closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setStyleSheet(
            "QFrame { background-color: #FFF4C2; border: 2px solid #111111; "
            "border-radius: 0px; padding: 4px; }"
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        lbl = QLabel("FIND:")
        lbl.setStyleSheet("font-size: 8.5pt; font-weight: 800; color: #111111;")
        layout.addWidget(lbl)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Find text in report...")
        self.input.setStyleSheet(
            "QLineEdit { background: #FFFFFF; border: 1.5px solid #111111; "
            "font-size: 9pt; font-weight: 600; padding: 3px 8px; min-width: 220px; }"
        )
        self.input.returnPressed.connect(self._on_find_next)
        self.input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self.input)

        self.match_count_label = QLabel("")
        self.match_count_label.setStyleSheet(
            "font-size: 8.5pt; font-weight: 700; color: #595959; font-family: 'Cascadia Code', monospace;"
        )
        layout.addWidget(self.match_count_label)

        self.prev_btn = QPushButton("▲ Prev")
        self.prev_btn.setToolTip("Find Previous (Shift+Enter)")
        self.prev_btn.setStyleSheet(
            "font-size: 8pt; font-weight: 700; background: #FFFFFF; border: 1.5px solid #111111; padding: 3px 8px;"
        )
        self.prev_btn.clicked.connect(self._on_find_prev)
        layout.addWidget(self.prev_btn)

        self.next_btn = QPushButton("▼ Next")
        self.next_btn.setToolTip("Find Next (Enter)")
        self.next_btn.setStyleSheet(
            "font-size: 8pt; font-weight: 700; background: #FFE500; border: 1.5px solid #111111; padding: 3px 8px;"
        )
        self.next_btn.clicked.connect(self._on_find_next)
        layout.addWidget(self.next_btn)

        self.case_box = QCheckBox("Match Case")
        self.case_box.setStyleSheet("font-size: 8.5pt; font-weight: 700; color: #111111;")
        self.case_box.stateChanged.connect(lambda: self._on_find_next())
        layout.addWidget(self.case_box)

        layout.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(22, 22)
        self.close_btn.setToolTip("Close Search (Esc)")
        self.close_btn.setStyleSheet(
            "font-size: 9pt; font-weight: 800; background: #FFFFFF; border: 1.5px solid #111111; padding: 0px;"
        )
        self.close_btn.clicked.connect(self.close_search)
        layout.addWidget(self.close_btn)

    def set_match_status(self, current: int, total: int) -> None:
        """Updates match counter label."""
        if total == 0:
            self.match_count_label.setText("No matches")
            self.match_count_label.setStyleSheet("color: #CC0000; font-weight: 800; font-size: 8.5pt;")
        else:
            self.match_count_label.setText(f"{current} of {total} matches")
            self.match_count_label.setStyleSheet("color: #111111; font-weight: 800; font-size: 8.5pt;")

    def clear_match_status(self) -> None:
        self.match_count_label.setText("")

    def focus_input(self) -> None:
        self.input.selectAll()
        self.input.setFocus()

    def close_search(self) -> None:
        self.clear_match_status()
        self.setVisible(False)
        self.search_closed.emit()

    def _on_text_changed(self, text: str) -> None:
        if text.strip():
            self._on_find_next()
        else:
            self.clear_match_status()

    def _on_find_next(self) -> None:
        text = self.input.text()
        if text:
            self.search_requested.emit(text, True, self.case_box.isChecked())

    def _on_find_prev(self) -> None:
        text = self.input.text()
        if text:
            self.search_requested.emit(text, False, self.case_box.isChecked())
