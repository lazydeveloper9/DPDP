"""
CS-01 DPDP Compliance Desktop GUI - Professional Color & Token Picker Widget.

Provides a tactile Neo-Brutalist control for editing individual design tokens:
- Visual color swatch with border
- Clickable QColorDialog trigger
- Hexadecimal QLineEdit with real-time validation (#RGB, #RRGGBB, #AARRGGBB)
- RGB display label
- Inheritance badge ([Inherited], [Override])
- Reset-to-inherited button (↺)
- WCAG AA contrast warning indicator
- Type-aware controls for integers (spinbox), booleans (checkbox), and strings
"""
from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme_engine.contrast_checker import ContrastChecker
from cs01.gui.theme_engine.theme_config import TokenMeta
from cs01.gui.theme_engine.theme_manager import ThemeManager


class ColorSwatchButton(QPushButton):
    """Square color preview button that opens QColorDialog when clicked."""

    def __init__(self, initial_color: str = "#FFFFFF", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(32, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.set_color(initial_color)

    def set_color(self, hex_color: str) -> None:
        self.setStyleSheet(
            f"background-color: {hex_color}; "
            "border: 2px solid #111111; "
            "border-radius: 0px;"
        )


class TokenEditorRow(QFrame):
    """
    Control row for a single theme token.
    Supports colors, integers, booleans, and string inputs.
    """

    value_changed = Signal(str, object)  # (token_key, new_value)
    token_reset = Signal(str)            # (token_key)

    def __init__(self, meta: TokenMeta, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.meta = meta
        self.tm = ThemeManager.instance()
        self._updating: bool = False

        self._setup_ui()
        self.sync_from_manager()

    def _setup_ui(self) -> None:
        self.setProperty("class", "card")
        self.setStyleSheet(
            "QFrame { background-color: #FFFFFF; border: 1.5px solid #111111; "
            "padding: 6px; margin: 2px 0px; border-radius: 0px; }"
        )
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 6, 8, 6)
        main_layout.setSpacing(4)

        # Top line: Title, description, inheritance indicator, reset button
        top_layout = QHBoxLayout()
        top_layout.setSpacing(8)

        self.title_label = QLabel(self.meta.display_name)
        self.title_label.setStyleSheet("font-size: 9.5pt; font-weight: 700; color: #111111;")
        top_layout.addWidget(self.title_label)

        self.status_badge = QLabel("Inherited")
        self.status_badge.setStyleSheet(
            "font-size: 8pt; font-weight: 800; color: #111111; background-color: #FFF4C2; "
            "border: 1px solid #111111; padding: 1px 6px;"
        )
        top_layout.addWidget(self.status_badge)
        top_layout.addStretch()

        self.reset_btn = QPushButton("↺ Reset")
        self.reset_btn.setToolTip("Reset to inherited or default value")
        self.reset_btn.setStyleSheet(
            "font-size: 8pt; font-weight: 700; background-color: #FFFFFF; color: #111111; "
            "border: 1px solid #111111; padding: 2px 8px;"
        )
        self.reset_btn.clicked.connect(self._on_reset_clicked)
        top_layout.addWidget(self.reset_btn)

        main_layout.addLayout(top_layout)

        # Bottom line: Controls (color swatch, hex input, RGB label, etc.)
        bottom_layout = QHBoxLayout()
        bottom_layout.setSpacing(8)

        if self.meta.value_type == "color":
            self.swatch = ColorSwatchButton("#FFFFFF", self)
            self.swatch.clicked.connect(self._open_color_dialog)
            bottom_layout.addWidget(self.swatch)

            self.hex_input = QLineEdit()
            self.hex_input.setFixedWidth(90)
            self.hex_input.setStyleSheet(
                "font-family: 'Cascadia Code', monospace; font-size: 9pt; font-weight: 700; "
                "background: #FFFFFF; border: 1.5px solid #111111; padding: 3px 6px;"
            )
            self.hex_input.textChanged.connect(self._on_hex_text_changed)
            bottom_layout.addWidget(self.hex_input)

            self.choose_btn = QPushButton("Choose...")
            self.choose_btn.setStyleSheet(
                "font-size: 8.5pt; font-weight: 700; background: #FFFFFF; "
                "border: 1.5px solid #111111; padding: 4px 10px;"
            )
            self.choose_btn.clicked.connect(self._open_color_dialog)
            bottom_layout.addWidget(self.choose_btn)

            self.rgb_label = QLabel("rgb(255, 255, 255)")
            self.rgb_label.setStyleSheet("font-size: 8.5pt; color: #595959; font-family: 'Cascadia Code', monospace;")
            bottom_layout.addWidget(self.rgb_label)
            bottom_layout.addStretch()

        elif self.meta.value_type == "int":
            self.spin_box = QSpinBox()
            if "border" in self.meta.key:
                self.spin_box.setRange(0, 5)
            elif "radius" in self.meta.key:
                self.spin_box.setRange(0, 16)
            elif "shadow" in self.meta.key:
                self.spin_box.setRange(0, 12)
            else:
                self.spin_box.setRange(0, 72)
            self.spin_box.valueChanged.connect(self._on_int_changed)
            bottom_layout.addWidget(self.spin_box)
            bottom_layout.addStretch()

        elif self.meta.value_type == "bool":
            self.checkbox = QCheckBox("Enabled")
            self.checkbox.stateChanged.connect(self._on_bool_changed)
            bottom_layout.addWidget(self.checkbox)
            bottom_layout.addStretch()

        elif self.meta.value_type == "str":
            self.str_input = QLineEdit()
            self.str_input.textChanged.connect(self._on_str_changed)
            bottom_layout.addWidget(self.str_input)

        main_layout.addLayout(bottom_layout)

        # Contrast warning label if applicable
        self.contrast_label = QLabel("")
        self.contrast_label.setVisible(False)
        self.contrast_label.setStyleSheet(
            "font-size: 8pt; font-weight: 700; color: #CC0000; background: #FFE8E8; "
            "border: 1px solid #CC0000; padding: 2px 6px;"
        )
        main_layout.addWidget(self.contrast_label)

    def sync_from_manager(self) -> None:
        """Updates UI values from current ThemeManager state."""
        self._updating = True
        try:
            val = self.tm.get_token(self.meta.key)
            is_overridden = self.tm.is_overridden(self.meta.key)
            status_text = self.tm.get_inheritance_status(self.meta.key)

            self.status_badge.setText(status_text)
            if is_overridden:
                self.status_badge.setStyleSheet(
                    "font-size: 8pt; font-weight: 800; color: #111111; background-color: #FFE500; "
                    "border: 1.5px solid #111111; padding: 1px 6px;"
                )
                self.reset_btn.setEnabled(True)
            else:
                self.status_badge.setStyleSheet(
                    "font-size: 8pt; font-weight: 700; color: #595959; background-color: #EAE6DA; "
                    "border: 1px solid #595959; padding: 1px 6px;"
                )
                self.reset_btn.setEnabled(False)

            if self.meta.value_type == "color" and isinstance(val, str):
                self.swatch.set_color(val)
                self.hex_input.setText(val)
                rgb = ContrastChecker.parse_rgb(val)
                if rgb:
                    self.rgb_label.setText(f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})")
                self._update_contrast_warning(val)

            elif self.meta.value_type == "int" and hasattr(self, "spin_box"):
                self.spin_box.setValue(int(val))

            elif self.meta.value_type == "bool" and hasattr(self, "checkbox"):
                self.checkbox.setChecked(bool(val))

            elif self.meta.value_type == "str" and hasattr(self, "str_input"):
                self.str_input.setText(str(val))
        finally:
            self._updating = False

    def _update_contrast_warning(self, fg_hex: str) -> None:
        """Calculates and updates contrast warning label against companion background."""
        if not self.meta.companion_bg_key:
            self.contrast_label.setVisible(False)
            return

        bg_hex = str(self.tm.get_token(self.meta.companion_bg_key, "#FFFFFF"))
        passed, ratio, msg = ContrastChecker.check_wcag_aa(fg_hex, bg_hex)
        if not passed:
            self.contrast_label.setText(f"⚠️ {msg} (against {self.meta.companion_bg_key}: {bg_hex})")
            self.contrast_label.setVisible(True)
        else:
            self.contrast_label.setVisible(False)

    def _open_color_dialog(self) -> None:
        current_hex = str(self.tm.get_token(self.meta.key, "#FFFFFF"))
        qcolor = QColor(current_hex)
        dialog = QColorDialog(qcolor, self)
        dialog.setWindowTitle(f"Choose Color: {self.meta.display_name}")
        if dialog.exec():
            selected = dialog.selectedColor()
            if selected.isValid():
                hex_str = selected.name().upper()
                self._apply_value(hex_str)

    def _on_hex_text_changed(self, text: str) -> None:
        if self._updating:
            return
        clean = text.strip()
        if not clean.startswith("#"):
            clean = "#" + clean
        if ContrastChecker.is_valid_hex(clean):
            self.swatch.set_color(clean)
            rgb = ContrastChecker.parse_rgb(clean)
            if rgb:
                self.rgb_label.setText(f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})")
            self._apply_value(clean)

    def _on_int_changed(self, val: int) -> None:
        if not self._updating:
            self._apply_value(val)

    def _on_bool_changed(self, state: int) -> None:
        if not self._updating:
            self._apply_value(bool(state))

    def _on_str_changed(self, text: str) -> None:
        if not self._updating:
            self._apply_value(text.strip())

    def _on_reset_clicked(self) -> None:
        self.tm.reset_token(self.meta.key)
        self.token_reset.emit(self.meta.key)
        self.sync_from_manager()

    def _apply_value(self, val: Any) -> None:
        self.tm.set_token(self.meta.key, val)
        self.value_changed.emit(self.meta.key, val)
        self.sync_from_manager()
