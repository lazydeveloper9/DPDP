"""
CS-01 DPDP Compliance Desktop GUI - Navigation Sidebar.

Provides the collapsible navigation rail (220px expanded to 64px collapsed)
managing view transitions across all 4 primary audit modules.
"""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    NAV_ITEM_HEIGHT,
    SIDEBAR_WIDTH_COLLAPSED,
    SIDEBAR_WIDTH_EXPANDED,
)


class NavigationSidebar(QFrame):
    """
    Collapsible left navigation sidebar for the CS-01 DPDP Auditor.

    Signals:
        navigation_changed(int): Emitted when a navigation item is selected,
                                 carrying the screen index (0 to 3).
    """

    navigation_changed = Signal(int)
    tab_selected = Signal(int)

    # Statutory Navigation Items: (Index, Display Title, Short Code)
    NAV_ITEMS: Final[list[tuple[int, str, str]]] = [
        (0, "Dashboard", "DSH"),
        (1, "Scan Setup", "SET"),
        (2, "Execution", "RUN"),
        (3, "Findings", "FND"),
        (4, "PII Inventory", "PII"),
        (5, "Reports", "REP"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("class", "sidebar")
        self._collapsed: bool = False
        self._current_index: int = 0
        self._buttons: list[QPushButton] = []

        self._button_group = QButtonGroup(self)
        self._button_group.setExclusive(True)

        self._setup_ui()
        self._tab_buttons = self._buttons
        self.setFixedWidth(SIDEBAR_WIDTH_EXPANDED)

    def _setup_ui(self) -> None:
        """Initializes the sidebar layout, header toggle, buttons, and footer."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 12, 8, 12)
        layout.setSpacing(6)

        # 1. Header with Collapse Toggle & Label
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(4, 0, 4, 8)
        header_layout.setSpacing(8)

        self.toggle_btn = QPushButton("<")
        self.toggle_btn.setProperty("class", "icon-only")
        self.toggle_btn.setToolTip("Toggle sidebar expansion (Ctrl+B)")
        self.toggle_btn.setCursor(Qt.PointingHandCursor)
        self.toggle_btn.clicked.connect(self.toggle_collapsed)

        # Register Ctrl+B keyboard shortcut to toggle sidebar
        self._toggle_shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        self._toggle_shortcut.activated.connect(self.toggle_collapsed)

        self.nav_title_label = QLabel("NAVIGATION")
        self.nav_title_label.setProperty("class", "text-muted")
        font = self.nav_title_label.font()
        font.setPointSize(8)
        font.setBold(True)
        self.nav_title_label.setFont(font)

        header_layout.addWidget(self.toggle_btn)
        header_layout.addWidget(self.nav_title_label)
        header_layout.addStretch()
        layout.addLayout(header_layout)

        # 2. Navigation Item Buttons
        for idx, title, icon in self.NAV_ITEMS:
            btn = QPushButton(title)
            btn.setProperty("class", "nav-btn")
            btn.setCheckable(True)
            btn.setFixedHeight(NAV_ITEM_HEIGHT)
            btn.setCursor(Qt.PointingHandCursor)

            # Persist metadata for collapse/expand rendering
            btn.setProperty("item_index", idx)
            btn.setProperty("item_title", title)
            btn.setProperty("item_icon", icon)
            btn.setAccessibleName(f"Navigate to {title}")

            if idx == 0:
                btn.setChecked(True)

            self._button_group.addButton(btn, idx)
            self._buttons.append(btn)
            layout.addWidget(btn)

        layout.addStretch()

        # 3. Footer Regulatory Stamp
        self.footer_label = QLabel("DPDP Act 2023\nZero-Egress Mode")
        self.footer_label.setProperty("class", "text-muted")
        self.footer_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.footer_label)

        # Connect button group click event
        self._button_group.idClicked.connect(self._on_item_clicked)

    def _on_item_clicked(self, item_id: int) -> None:
        """Handles internal button click and notifies external listeners."""
        if self._current_index != item_id:
            self._current_index = item_id
            self.navigation_changed.emit(item_id)
            self.tab_selected.emit(item_id)

    # ------------------------------------------------------------------------
    # PUBLIC API
    # ------------------------------------------------------------------------

    def set_active_index(self, index: int, emit_signal: bool = True) -> None:
        """
        Programmatically switches the selected navigation item.

        Args:
            index: Target screen index (0 to 5).
            emit_signal: Whether to emit navigation_changed signal.
        """
        if not (0 <= index < len(self.NAV_ITEMS)):
            return

        btn = self._button_group.button(index)
        if btn:
            btn.setChecked(True)
        changed = (self._current_index != index)
        self._current_index = index
        if emit_signal and changed:
            self.navigation_changed.emit(index)

    def set_current_index(self, index: int, emit_signal: bool = True) -> None:
        """Alias for set_active_index."""
        self.set_active_index(index, emit_signal=emit_signal)

    def get_active_index(self) -> int:
        """Returns the currently active screen index."""
        return self._current_index

    def is_collapsed(self) -> bool:
        """Returns True if the sidebar is in compact 64px rail mode."""
        return self._collapsed

    def set_collapsed(self, collapsed: bool, animate: bool = False) -> None:
        """
        Sets the collapsed/expanded state of the sidebar.

        Args:
            collapsed: True for 64px icon rail; False for 220px expanded.
            animate: Whether to animate width change (default False for instant updates).
        """
        if self._collapsed == collapsed:
            return
        self._collapsed = collapsed

        if collapsed:
            self.setFixedWidth(SIDEBAR_WIDTH_COLLAPSED)
            self.nav_title_label.hide()
            self.footer_label.hide()
            self.toggle_btn.setText(">")
            for btn in self._buttons:
                icon = btn.property("item_icon")
                title = btn.property("item_title")
                btn.setText(icon)
                btn.setToolTip(title)
        else:
            self.setFixedWidth(SIDEBAR_WIDTH_EXPANDED)
            self.nav_title_label.show()
            self.footer_label.show()
            self.toggle_btn.setText("<")
            for btn in self._buttons:
                title = btn.property("item_title")
                btn.setText(title)
                btn.setToolTip("")

    def toggle_collapsed(self) -> None:
        """Toggles sidebar between 220px expanded and 64px collapsed mode."""
        self.set_collapsed(not self._collapsed)

    @property
    def collapsed(self) -> bool:
        """Property returning whether the sidebar is collapsed."""
        return self._collapsed

    @collapsed.setter
    def collapsed(self, value: bool) -> None:
        self.set_collapsed(value)

    @property
    def current_index(self) -> int:
        """Property returning the current navigation index."""
        return self._current_index

    @current_index.setter
    def current_index(self, value: int) -> None:
        self.set_active_index(value)
