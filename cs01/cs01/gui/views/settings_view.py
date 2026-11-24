"""
CS-01 DPDP Compliance Desktop GUI - Appearance & Theme Studio (Settings View).

Provides the complete 3-panel Theme Customization Studio:
- Left: Category Navigation List (19 comprehensive categories)
- Center: Dynamic Token Editors with color pickers, RGB readout, inheritance badges, reset buttons
- Right: Real-time Live Preview Engine (interactive cards, tables, buttons, inputs)
- Bottom: Action Bar with Live Preview toggle, Apply, Save Theme, Presets, and Reset controls
"""
from __future__ import annotations

import copy
from typing import Any

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme_engine.contrast_checker import ContrastChecker
from cs01.gui.theme_engine.theme_config import TOKEN_DEFINITIONS, TokenMeta
from cs01.gui.theme_engine.theme_manager import ThemeManager
from cs01.gui.widgets.color_picker_widget import TokenEditorRow
from cs01.gui.widgets.theme_preview_widget import ThemePreviewWidget


class SettingsView(QWidget):
    """
    Primary Appearance & Theme Customization Studio View.
    Mounted at index 6 in MainWindow's QStackedWidget.
    """

    CATEGORIES = [
        ("Theme Presets", "Presets"),
        ("Global Surfaces", "Global Surfaces"),
        ("Global Typography", "Global Typography"),
        ("Global Design Elements", "Global Design"),
        ("Neo-Brutalist Geometry", "Brutalist Geometry"),
        ("Typography Metrics", "Typography Metrics"),
        ("Status & Severity Indicators", "Status Indicators"),
        ("Sidebar Navigation", "Sidebar"),
        ("HUD Toolbar", "HUD Toolbar"),
        ("Buttons & Controls", "Buttons"),
        ("Cards & Panels", "Cards"),
        ("Inputs & Dropdowns", "Inputs"),
        ("Tables & Data Grids", "Tables"),
        ("Page: Dashboard", "Page: Dashboard"),
        ("Page: Scan Setup", "Page: Scan Setup"),
        ("Page: Execution", "Page: Execution"),
        ("Page: Findings", "Page: Findings"),
        ("Page: PII Inventory", "Page: PII Inventory"),
        ("Page: Reports", "Page: Reports"),
        ("Accessibility & Contrast", "Accessibility"),
        ("Import & Export", "ImportExport"),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.tm = ThemeManager.instance()
        self._token_rows: list[TokenEditorRow] = []
        self._setup_ui()
        self.tm.theme_changed.connect(self._on_theme_changed)

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 12)
        main_layout.setSpacing(12)

        # 1. Header Section
        header_layout = QVBoxLayout()
        header_layout.setSpacing(2)

        title = QLabel("APPEARANCE & THEME STUDIO")
        title.setProperty("class", "h1")
        title.setStyleSheet("font-size: 18pt; font-weight: 800; color: #111111; letter-spacing: -0.5px;")
        header_layout.addWidget(title)

        subtitle = QLabel("Customize every visual detail of your CS-01 workspace with live preview and persistent profiles.")
        subtitle.setStyleSheet("font-size: 9.5pt; color: #595959; font-weight: 600;")
        header_layout.addWidget(subtitle)

        main_layout.addLayout(header_layout)

        # 2. Central 3-Panel Splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.splitter.setChildrenCollapsible(False)

        # Left: Category Navigation Rail
        left_panel = self._build_category_nav()
        left_panel.setMinimumWidth(200)
        self.splitter.addWidget(left_panel)

        # Center: Token Editor Area
        self.center_scroll = QScrollArea(self)
        self.center_scroll.setWidgetResizable(True)
        self.center_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self.center_scroll.setStyleSheet("background: transparent;")
        self.center_container = QWidget()
        self.center_layout = QVBoxLayout(self.center_container)
        self.center_layout.setContentsMargins(8, 4, 8, 4)
        self.center_layout.setSpacing(6)
        self.center_scroll.setWidget(self.center_container)
        self.center_scroll.setMinimumWidth(380)
        self.splitter.addWidget(self.center_scroll)

        # Right: Live Visual Preview
        self.preview_panel = ThemePreviewWidget(self)
        self.preview_panel.setMinimumWidth(340)
        self.splitter.addWidget(self.preview_panel)

        self.splitter.setSizes([220, 520, 380])
        main_layout.addWidget(self.splitter, stretch=1)

        # 3. Bottom Action Bar
        bottom_bar = self._build_bottom_bar()
        main_layout.addWidget(bottom_bar)

        # Select first category initially
        self.category_list.setCurrentRow(0)

    def _build_category_nav(self) -> QWidget:
        panel = QFrame(self)
        panel.setProperty("class", "card")
        panel.setStyleSheet(
            "QFrame { background-color: #EAE6DA; border: 2px solid #111111; border-radius: 0px; }"
        )
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        hdr = QLabel("THEME CATEGORIES")
        hdr.setStyleSheet("font-size: 9pt; font-weight: 800; color: #111111; letter-spacing: 0.5px;")
        layout.addWidget(hdr)

        self.category_list = QListWidget(panel)
        self.category_list.setStyleSheet(
            "QListWidget { background: #FFFFFF; border: 1.5px solid #111111; "
            "font-size: 9.5pt; font-weight: 700; color: #111111; outline: none; } "
            "QListWidget::item { padding: 8px 10px; border-bottom: 1px solid #EAE6DA; } "
            "QListWidget::item:selected { background-color: #FFE500; color: #111111; "
            "border-left: 4px solid #111111; }"
        )
        for display_name, tag in self.CATEGORIES:
            item = QListWidgetItem(display_name)
            item.setData(Qt.ItemDataRole.UserRole, tag)
            self.category_list.addItem(item)

        self.category_list.currentRowChanged.connect(self._on_category_changed)
        layout.addWidget(self.category_list)
        return panel

    def _build_bottom_bar(self) -> QWidget:
        bar = QFrame(self)
        bar.setStyleSheet(
            "QFrame { background-color: #EAE6DA; border: 2px solid #111111; "
            "padding: 6px 12px; border-radius: 0px; }"
        )
        layout = QHBoxLayout(bar)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(10)

        # Unsaved state indicator
        self.status_indicator = QLabel("✓ Synchronized")
        self.status_indicator.setStyleSheet(
            "font-size: 9pt; font-weight: 800; color: #111111; background-color: #B8F044; "
            "border: 1px solid #111111; padding: 4px 8px;"
        )
        layout.addWidget(self.status_indicator)

        # Live Preview toggle
        self.live_toggle = QCheckBox("Live Preview (Instant Apply)")
        self.live_toggle.setChecked(self.tm.live_preview)
        self.live_toggle.stateChanged.connect(self._on_live_preview_toggled)
        layout.addWidget(self.live_toggle)

        layout.addStretch()

        # Apply Changes
        self.apply_btn = QPushButton("Apply Changes")
        self.apply_btn.setProperty("class", "primary")
        self.apply_btn.clicked.connect(self._on_apply_clicked)
        layout.addWidget(self.apply_btn)

        # Save Theme
        self.save_btn = QPushButton("Save Theme")
        self.save_btn.setStyleSheet(
            "font-size: 9.5pt; font-weight: 700; background: #FFFFFF; "
            "border: 2px solid #111111; padding: 6px 14px;"
        )
        self.save_btn.clicked.connect(self._on_save_clicked)
        layout.addWidget(self.save_btn)

        # Save As Preset
        self.save_preset_btn = QPushButton("Save As Preset...")
        self.save_preset_btn.setStyleSheet(
            "font-size: 9.5pt; font-weight: 700; background: #FFFFFF; "
            "border: 2px solid #111111; padding: 6px 14px;"
        )
        self.save_preset_btn.clicked.connect(self._on_save_as_preset_clicked)
        layout.addWidget(self.save_preset_btn)

        # Reset Category
        self.reset_cat_btn = QPushButton("Reset Category")
        self.reset_cat_btn.setStyleSheet(
            "font-size: 9.5pt; font-weight: 700; background: #FFFFFF; "
            "border: 2px solid #111111; padding: 6px 14px;"
        )
        self.reset_cat_btn.clicked.connect(self._on_reset_category_clicked)
        layout.addWidget(self.reset_cat_btn)

        # Reset All
        self.reset_all_btn = QPushButton("Reset All")
        self.reset_all_btn.setProperty("class", "danger")
        self.reset_all_btn.clicked.connect(self._on_reset_all_clicked)
        layout.addWidget(self.reset_all_btn)

        return bar

    def _on_category_changed(self, row: int) -> None:
        if row < 0 or row >= len(self.CATEGORIES):
            return
        _, tag = self.CATEGORIES[row]
        self._populate_category_editors(tag)

    def _populate_category_editors(self, tag: str) -> None:
        # Clear existing rows
        for r in self._token_rows:
            r.setParent(None)
            r.deleteLater()
        self._token_rows.clear()

        # Clear layouts completely
        while self.center_layout.count():
            item = self.center_layout.takeAt(0)
            w = item.widget()
            if w:
                w.setParent(None)
                w.deleteLater()
            l = item.layout()
            if l:
                while l.count():
                    sub = l.takeAt(0)
                    if sub.widget():
                        sub.widget().setParent(None)
                        sub.widget().deleteLater()

        # Special panels: Presets, Accessibility, Import/Export
        if tag == "Presets":
            self._build_presets_panel()
            return
        elif tag == "Accessibility":
            self._build_accessibility_panel()
            return
        elif tag == "ImportExport":
            self._build_import_export_panel()
            return

        # Standard token list for category
        tokens = [t for t in TOKEN_DEFINITIONS if t.category == tag]
        if not tokens:
            empty_lbl = QLabel(f"No editable tokens configured for {tag}")
            empty_lbl.setStyleSheet("color: #595959; font-weight: bold; padding: 20px;")
            self.center_layout.addWidget(empty_lbl)
            return

        cat_title = QLabel(tag.upper())
        cat_title.setStyleSheet("font-size: 12pt; font-weight: 800; color: #111111; padding: 4px 0px;")
        self.center_layout.addWidget(cat_title)

        for meta in tokens:
            row = TokenEditorRow(meta, self.center_container)
            row.value_changed.connect(self._on_token_value_changed)
            row.token_reset.connect(self._on_token_value_changed)
            self.center_layout.addWidget(row)
            self._token_rows.append(row)

        self.center_layout.addStretch()

    def _build_presets_panel(self) -> None:
        title = QLabel("THEME PRESETS")
        title.setStyleSheet("font-size: 13pt; font-weight: 800; color: #111111; padding: 4px 0px;")
        self.center_layout.addWidget(title)

        sub = QLabel("Select from 7 built-in Neo-Brutalist themes or your custom saved presets:")
        sub.setStyleSheet("font-size: 9.5pt; color: #595959; font-weight: 600;")
        self.center_layout.addWidget(sub)

        presets = self.tm.get_all_presets()
        for name, data in presets.items():
            card = QFrame()
            card.setStyleSheet(
                "QFrame { background-color: #FFFFFF; border: 2px solid #111111; "
                "padding: 10px; margin: 4px 0px; border-radius: 0px; }"
            )
            c_layout = QVBoxLayout(card)
            c_layout.setContentsMargins(8, 8, 8, 8)
            c_layout.setSpacing(6)

            top = QHBoxLayout()
            p_name = QLabel(name.upper())
            p_name.setStyleSheet("font-size: 11pt; font-weight: 800; color: #111111;")
            top.addWidget(p_name)
            top.addStretch()

            if name == self.tm.active_preset_name:
                active_badge = QLabel("ACTIVE")
                active_badge.setStyleSheet(
                    "font-size: 8pt; font-weight: 800; background: #FFE500; "
                    "color: #111111; border: 1px solid #111111; padding: 2px 6px;"
                )
                top.addWidget(active_badge)

            apply_btn = QPushButton("Apply Preset")
            apply_btn.setProperty("class", "primary" if name != self.tm.active_preset_name else "secondary")
            apply_btn.clicked.connect(lambda _, n=name: self._apply_preset_named(n))
            top.addWidget(apply_btn)

            # Allow delete if user-created
            if name not in ["Bold Enterprise", "Yellow Industrial", "Cobalt Brutalist", "Minimal Monochrome", "Warm Editorial", "High Contrast", "Custom Theme"]:
                del_btn = QPushButton("Delete")
                del_btn.setProperty("class", "danger")
                del_btn.clicked.connect(lambda _, n=name: self._delete_preset_named(n))
                top.addWidget(del_btn)

            c_layout.addLayout(top)

            desc = QLabel(data.get("description", ""))
            desc.setStyleSheet("font-size: 9pt; color: #595959; font-weight: 500;")
            desc.setWordWrap(True)
            c_layout.addWidget(desc)

            self.center_layout.addWidget(card)

        self.center_layout.addStretch()

    def _build_accessibility_panel(self) -> None:
        title = QLabel("ACCESSIBILITY & WCAG 2.1 CONTRAST AUDITOR")
        title.setStyleSheet("font-size: 13pt; font-weight: 800; color: #111111; padding: 4px 0px;")
        self.center_layout.addWidget(title)

        intro = QLabel("Real-time relative luminance verification targeting WCAG AA (4.5:1 minimum) and AAA (7.0:1):")
        intro.setStyleSheet("font-size: 9.5pt; color: #595959; font-weight: 600;")
        self.center_layout.addWidget(intro)

        pairs = [
            ("Primary Text on Main Card", "global.text.primary", "global.bg.card"),
            ("Heading Text on Main Canvas", "global.text.heading", "global.bg.main"),
            ("Primary Button Text on Button Bg", "component.button.primary.text", "component.button.primary.bg"),
            ("Secondary Button Text on Button Bg", "component.button.secondary.text", "component.button.secondary.bg"),
            ("Destructive Button Text on Button Bg", "component.button.danger.text", "component.button.danger.bg"),
            ("Sidebar Active Nav Text on Nav Bg", "component.sidebar.active_text", "component.sidebar.active_bg"),
            ("Table Cell Text on Table Row Bg", "component.table.cell_text", "component.table.row_bg"),
            ("Table Header Text on Table Header Bg", "component.table.header_text", "component.table.header_bg"),
        ]

        for label, fg_key, bg_key in pairs:
            fg = str(self.tm.get_token(fg_key, "#111111"))
            bg = str(self.tm.get_token(bg_key, "#FFFFFF"))
            passed, ratio, msg = ContrastChecker.check_wcag_aa(fg, bg)
            is_aaa, _, _ = ContrastChecker.check_wcag_aaa(fg, bg)

            card = QFrame()
            card.setStyleSheet(
                f"QFrame {{ background-color: #FFFFFF; border: 2px solid {'#111111' if passed else '#FF4444'}; "
                "padding: 8px; margin: 3px 0px; border-radius: 0px; }"
            )
            c_layout = QHBoxLayout(card)
            c_layout.setContentsMargins(8, 6, 8, 6)
            c_layout.setSpacing(10)

            info = QVBoxLayout()
            n_lbl = QLabel(label)
            n_lbl.setStyleSheet("font-size: 9.5pt; font-weight: 800; color: #111111;")
            info.addWidget(n_lbl)

            detail = QLabel(f"FG: {fg}  |  BG: {bg}")
            detail.setStyleSheet("font-size: 8.5pt; color: #595959; font-family: 'Cascadia Code', monospace;")
            info.addWidget(detail)
            c_layout.addLayout(info, stretch=1)

            # Preview capsule
            capsule = QLabel(" Aa Sample ")
            capsule.setStyleSheet(
                f"background-color: {bg}; color: {fg}; font-size: 9.5pt; font-weight: 800; "
                "border: 1px solid #111111; padding: 4px 10px;"
            )
            c_layout.addWidget(capsule)

            # Ratio badge
            ratio_badge = QLabel(f"{ratio:.2f}:1")
            ratio_badge.setStyleSheet(
                f"font-size: 9pt; font-weight: 900; color: #111111; "
                f"background-color: {'#B8F044' if is_aaa else ('#FFE500' if passed else '#FF4444')}; "
                "border: 1.5px solid #111111; padding: 3px 8px;"
            )
            c_layout.addWidget(ratio_badge)

            status_lbl = QLabel("AAA PASS" if is_aaa else ("AA PASS" if passed else "FAIL"))
            status_lbl.setStyleSheet(
                f"font-size: 8.5pt; font-weight: 800; color: {'#008800' if passed else '#CC0000'};"
            )
            c_layout.addWidget(status_lbl)

            self.center_layout.addWidget(card)

        self.center_layout.addStretch()

    def _build_import_export_panel(self) -> None:
        title = QLabel("THEME IMPORT & EXPORT")
        title.setStyleSheet("font-size: 13pt; font-weight: 800; color: #111111; padding: 4px 0px;")
        self.center_layout.addWidget(title)

        sub = QLabel("Export your customized color profile to a JSON file or import a team compliance theme:")
        sub.setStyleSheet("font-size: 9.5pt; color: #595959; font-weight: 600;")
        self.center_layout.addWidget(sub)

        # Export Box
        exp_box = QFrame()
        exp_box.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 2px solid #111111; "
            "padding: 12px; margin: 6px 0px; border-radius: 0px; }"
        )
        e_layout = QVBoxLayout(exp_box)
        e_title = QLabel("EXPORT ACTIVE THEME")
        e_title.setStyleSheet("font-size: 10.5pt; font-weight: 800; color: #111111;")
        e_layout.addWidget(e_title)
        e_desc = QLabel("Generates a schema-validated JSON theme file containing all active global, page, and component overrides.")
        e_desc.setStyleSheet("font-size: 9pt; color: #595959;")
        e_layout.addWidget(e_desc)

        exp_btn = QPushButton("Export Theme JSON...")
        exp_btn.setProperty("class", "primary")
        exp_btn.clicked.connect(self._on_export_file_dialog)
        e_layout.addWidget(exp_btn)
        self.center_layout.addWidget(exp_box)

        # Import Box
        imp_box = QFrame()
        imp_box.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 2px solid #111111; "
            "padding: 12px; margin: 6px 0px; border-radius: 0px; }"
        )
        i_layout = QVBoxLayout(imp_box)
        i_title = QLabel("IMPORT EXTERNAL THEME")
        i_title.setStyleSheet("font-size: 10.5pt; font-weight: 800; color: #111111;")
        i_layout.addWidget(i_title)
        i_desc = QLabel("Loads an external JSON theme configuration file with safety checks and strict type verification.")
        i_desc.setStyleSheet("font-size: 9pt; color: #595959;")
        i_layout.addWidget(i_desc)

        imp_btn = QPushButton("Import Theme JSON...")
        imp_btn.setStyleSheet(
            "font-size: 9.5pt; font-weight: 700; background: #FFFFFF; "
            "border: 2px solid #111111; padding: 6px 14px;"
        )
        imp_btn.clicked.connect(self._on_import_file_dialog)
        i_layout.addWidget(imp_btn)
        self.center_layout.addWidget(imp_box)

        self.center_layout.addStretch()

    def _on_export_file_dialog(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Export CS-01 Theme", "cs01-theme.json", "JSON Files (*.json)"
        )
        if path:
            ok, msg = self.tm.export_theme(path)
            if ok:
                QMessageBox.information(self, "Theme Exported", msg)
            else:
                QMessageBox.critical(self, "Export Failed", msg)

    def _on_import_file_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Import CS-01 Theme", "", "JSON Files (*.json)"
        )
        if path:
            # Confirm replacement
            reply = QMessageBox.question(
                self,
                "Confirm Theme Replacement",
                "Importing this theme will replace your current workspace styling customizations. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                ok, msg = self.tm.import_theme(path, live_apply=True)
                if ok:
                    QMessageBox.information(self, "Theme Imported", msg)
                    self._on_theme_changed()
                else:
                    QMessageBox.critical(self, "Import Failed", msg)

    def _apply_preset_named(self, name: str) -> None:
        self.tm.apply_preset(name, live_apply=True)
        self._on_theme_changed()

    def _delete_preset_named(self, name: str) -> None:
        reply = QMessageBox.question(
            self,
            "Confirm Delete Preset",
            f"Are you sure you want to delete preset '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tm.delete_preset(name)
            self._populate_category_editors("Presets")

    def _on_token_value_changed(self, key: str, val: Any = None) -> None:
        self.status_indicator.setText("● Unsaved Edits")
        self.status_indicator.setStyleSheet(
            "font-size: 9pt; font-weight: 800; color: #111111; background-color: #FFE500; "
            "border: 1.5px solid #111111; padding: 4px 8px;"
        )
        self.preview_panel.refresh_preview()

    def _on_live_preview_toggled(self, state: int) -> None:
        self.tm.live_preview = bool(state)

    def _on_apply_clicked(self) -> None:
        self.tm.apply_theme()
        self.status_indicator.setText("✓ Applied")
        self.status_indicator.setStyleSheet(
            "font-size: 9pt; font-weight: 800; color: #111111; background-color: #B8F044; "
            "border: 1px solid #111111; padding: 4px 8px;"
        )

    def _on_save_clicked(self) -> None:
        self.tm.save_theme()
        self.status_indicator.setText("✓ Saved to Disk")
        self.status_indicator.setStyleSheet(
            "font-size: 9pt; font-weight: 800; color: #111111; background-color: #B8F044; "
            "border: 1px solid #111111; padding: 4px 8px;"
        )
        QMessageBox.information(self, "Theme Saved", "Theme configuration has been saved successfully to your user profile.")

    def _on_save_as_preset_clicked(self) -> None:
        name, ok = QInputDialog.getText(
            self, "Save Theme Preset", "Enter a name for your custom theme preset:"
        )
        if ok and name.strip():
            self.tm.save_current_as_preset(name.strip())
            QMessageBox.information(self, "Preset Saved", f"Preset '{name.strip()}' saved successfully!")
            if self.category_list.currentItem() and self.category_list.currentItem().data(Qt.ItemDataRole.UserRole) == "Presets":
                self._populate_category_editors("Presets")

    def _on_reset_category_clicked(self) -> None:
        curr = self.category_list.currentItem()
        if not curr:
            return
        tag = curr.data(Qt.ItemDataRole.UserRole)
        self.tm.reset_category(tag, live_apply=True)
        self._populate_category_editors(tag)

    def _on_reset_all_clicked(self) -> None:
        reply = QMessageBox.question(
            self,
            "Reset Entire Theme",
            "Are you sure you want to reset ALL theme customizations to factory default Bold Enterprise?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.tm.reset_all(live_apply=True)
            self._on_theme_changed()

    def _on_theme_changed(self) -> None:
        """Refreshes all currently visible token rows."""
        for row in self._token_rows:
            row.sync_from_manager()
        self.preview_panel.refresh_preview()
