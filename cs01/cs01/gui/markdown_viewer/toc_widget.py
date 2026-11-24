"""
CS-01 DPDP Compliance Desktop GUI - Markdown Table of Contents Widget.

Generates a hierarchical navigation tree from Markdown heading anchors with
real-time section filtering, smooth selection, and collapsible rail toggle.
"""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.markdown_viewer.markdown_parser import HeadingItem


class TableOfContentsWidget(QFrame):
    """
    Collapsible left-side Table of Contents panel.
    Emits heading_selected(anchor: str) when an item is clicked.
    """

    heading_selected = Signal(str)
    collapsed_toggled = Signal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._collapsed: bool = False
        self._headings: list[HeadingItem] = []
        self._items_by_anchor: dict[str, QTreeWidgetItem] = {}

        self._setup_ui()

    def _setup_ui(self) -> None:
        self.setProperty("class", "card")
        self.setStyleSheet(
            "QFrame { background-color: #EAE6DA; border: 2px solid #111111; border-radius: 0px; }"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        # Header with title and collapse toggle
        header_layout = QHBoxLayout()
        header_layout.setSpacing(6)

        self.title_label = QLabel("TABLE OF CONTENTS")
        self.title_label.setStyleSheet("font-size: 8.5pt; font-weight: 800; color: #111111; letter-spacing: 0.8px;")
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()

        self.toggle_btn = QPushButton("◀")
        self.toggle_btn.setFixedSize(24, 24)
        self.toggle_btn.setToolTip("Collapse Table of Contents")
        self.toggle_btn.setStyleSheet(
            "font-size: 9pt; font-weight: 800; background: #FFFFFF; border: 1.5px solid #111111; padding: 0px;"
        )
        self.toggle_btn.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self.toggle_btn)
        layout.addLayout(header_layout)

        # Search filter
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filter headings...")
        self.filter_input.setStyleSheet(
            "background: #FFFFFF; border: 1.5px solid #111111; font-size: 9pt; padding: 4px 6px; font-weight: 600;"
        )
        self.filter_input.textChanged.connect(self._on_filter_changed)
        layout.addWidget(self.filter_input)

        # Tree View
        self.tree = QTreeWidget(self)
        self.tree.setHeaderHidden(True)
        self.tree.setAnimated(True)
        self.tree.setStyleSheet(
            "QTreeWidget { background-color: #FFFFFF; border: 1.5px solid #111111; "
            "font-size: 9pt; font-weight: 600; color: #111111; outline: none; } "
            "QTreeWidget::item { padding: 5px 4px; border-bottom: 1px solid #F0ECE1; } "
            "QTreeWidget::item:hover { background-color: #FFF4C2; } "
            "QTreeWidget::item:selected { background-color: #FFE500; color: #111111; font-weight: 800; }"
        )
        self.tree.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.tree)

    def populate(self, headings: list[HeadingItem]) -> None:
        """Builds hierarchical tree from heading level metadata."""
        self._headings = headings
        self.tree.clear()
        self._items_by_anchor.clear()

        # Stack tracking last item at each level: index = level (1-6)
        level_stack: dict[int, QTreeWidgetItem] = {}

        for h in headings:
            item = QTreeWidgetItem([h.title])
            item.setData(0, Qt.ItemDataRole.UserRole, h.anchor)
            item.setToolTip(0, f"H{h.level}: {h.title}")

            # Determine parent: look for nearest ancestor level < h.level
            parent_item = None
            for lvl in range(h.level - 1, 0, -1):
                if lvl in level_stack:
                    parent_item = level_stack[lvl]
                    break

            if parent_item is not None:
                parent_item.addChild(item)
            else:
                self.tree.addTopLevelItem(item)

            level_stack[h.level] = item
            # Invalidate any deeper levels in stack
            for deeper in range(h.level + 1, 7):
                level_stack.pop(deeper, None)

            self._items_by_anchor[h.anchor] = item

        self.tree.expandAll()

    def select_heading(self, anchor: str) -> None:
        """Programmatically highlights heading corresponding to active anchor."""
        item = self._items_by_anchor.get(anchor)
        if item:
            self.tree.setCurrentItem(item)
            self.tree.scrollToItem(item)

    def toggle_collapse(self) -> None:
        """Toggles width and visibility of TOC elements."""
        self._collapsed = not self._collapsed
        self.filter_input.setVisible(not self._collapsed)
        self.tree.setVisible(not self._collapsed)
        self.title_label.setVisible(not self._collapsed)
        self.toggle_btn.setText("▶" if self._collapsed else "◀")
        self.setFixedWidth(40 if self._collapsed else 240)
        self.collapsed_toggled.emit(self._collapsed)

    def _on_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        anchor = item.data(0, Qt.ItemDataRole.UserRole)
        if anchor:
            self.heading_selected.emit(anchor)

    def _on_filter_changed(self, text: str) -> None:
        query = text.strip().lower()

        def _filter_item(item: QTreeWidgetItem) -> bool:
            title = item.text(0).lower()
            matches = query in title
            child_matches = False
            for i in range(item.childCount()):
                child = item.child(i)
                if _filter_item(child):
                    child_matches = True
            visible = matches or child_matches
            item.setHidden(not visible)
            if visible and query:
                item.setExpanded(True)
            return visible

        for i in range(self.tree.topLevelItemCount()):
            top = self.tree.topLevelItem(i)
            _filter_item(top)
