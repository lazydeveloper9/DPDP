"""
CS-01 DPDP Compliance Desktop GUI - Theme Manager Singleton.

Orchestrates the active ThemeConfig, token resolution, QSS stylesheet compilation,
QApplication stylesheet re-application, and dynamic UI updates across all views.
"""
from __future__ import annotations

import copy
from typing import Any

from PySide6.QtCore import QObject, QSettings, Signal
from PySide6.QtWidgets import QApplication

from cs01.gui.theme_engine.contrast_checker import ContrastChecker
from cs01.gui.theme_engine.theme_config import ThemeConfig, TOKEN_DEFINITIONS, TOKEN_MAP
from cs01.gui.theme_engine.theme_presets import BUILTIN_PRESETS
from cs01.gui.theme_engine.theme_repository import ThemeRepository


class ThemeManager(QObject):
    """
    Central theme management singleton for the CS-01 PySide6 GUI.

    Signals:
        theme_changed(): Emitted when theme styling is updated or re-applied.
        live_preview_changed(bool): Emitted when live preview toggle changes.
    """

    theme_changed = Signal()
    live_preview_changed = Signal(bool)

    _instance: ThemeManager | None = None

    def __init__(self) -> None:
        super().__init__()
        self._settings = QSettings("CS-01", "ThemeStudio")
        self._live_preview: bool = self._settings.value("live_preview", True, type=bool)
        self._config: ThemeConfig = ThemeRepository.load_theme_config()
        self._active_preset_name: str = self._settings.value(
            "active_preset", self._config.name, type=str
        )

    @classmethod
    def instance(cls) -> ThemeManager:
        """Returns the singleton ThemeManager instance."""
        if cls._instance is None:
            cls._instance = ThemeManager()
        return cls._instance

    @property
    def live_preview(self) -> bool:
        """Whether edits immediately apply to running application."""
        return self._live_preview

    @live_preview.setter
    def live_preview(self, enabled: bool) -> None:
        self._live_preview = bool(enabled)
        self._settings.setValue("live_preview", self._live_preview)
        self.live_preview_changed.emit(self._live_preview)

    @property
    def active_preset_name(self) -> str:
        """Returns the name of currently active preset."""
        return self._active_preset_name

    @property
    def config(self) -> ThemeConfig:
        """Returns the active ThemeConfig."""
        return self._config

    def get_token(self, key: str, default: Any = None) -> Any:
        """Resolves token according to the inheritance chain."""
        val = self._config.resolve(key)
        if val is not None:
            return val
        if default is not None:
            return default
        return TOKEN_MAP[key].default_value if key in TOKEN_MAP else ""

    def set_token(self, key: str, value: Any, live_apply: bool | None = None) -> None:
        """
        Sets a token override. If live_apply is True (or live_preview is enabled),
        the application stylesheet and widgets update immediately.
        """
        self._config.set(key, value)
        do_apply = live_apply if live_apply is not None else self._live_preview
        if do_apply:
            self.apply_theme()

    def reset_token(self, key: str, live_apply: bool | None = None) -> None:
        """Clears an override for a token so it inherits."""
        self._config.reset(key)
        do_apply = live_apply if live_apply is not None else self._live_preview
        if do_apply:
            self.apply_theme()

    def reset_category(self, category_name: str, live_apply: bool | None = None) -> None:
        """Resets all overrides belonging to a specific category."""
        for token in TOKEN_DEFINITIONS:
            if token.category == category_name:
                self._config.reset(token.key)
        do_apply = live_apply if live_apply is not None else self._live_preview
        if do_apply:
            self.apply_theme()

    def reset_all(self, live_apply: bool | None = None) -> None:
        """Resets all overrides back to factory defaults."""
        self._config.overrides.clear()
        self._config.name = "Bold Enterprise"
        self._active_preset_name = "Bold Enterprise"
        self._settings.setValue("active_preset", "Bold Enterprise")
        do_apply = live_apply if live_apply is not None else self._live_preview
        if do_apply:
            self.apply_theme()

    def is_overridden(self, key: str) -> bool:
        """Checks if a key has an explicit override."""
        return self._config.is_overridden(key)

    def get_inheritance_status(self, key: str) -> str:
        """Returns inheritance label."""
        return self._config.get_inheritance_status(key)

    def get_all_presets(self) -> dict[str, dict[str, Any]]:
        """Returns dictionary of all presets (built-in + user custom)."""
        all_presets = copy.deepcopy(BUILTIN_PRESETS)
        all_presets.update(ThemeRepository.load_user_presets())
        return all_presets

    def apply_preset(self, preset_name: str, live_apply: bool | None = None) -> bool:
        """Applies a built-in or custom preset."""
        presets = self.get_all_presets()
        if preset_name not in presets:
            return False

        preset = presets[preset_name]
        self._config.name = preset.get("name", preset_name)
        self._config.description = preset.get("description", "")
        self._config.overrides = copy.deepcopy(preset.get("overrides", {}))
        self._active_preset_name = preset_name
        self._settings.setValue("active_preset", preset_name)

        do_apply = live_apply if live_apply is not None else self._live_preview
        if do_apply:
            self.apply_theme()
        return True

    def save_current_as_preset(self, name: str) -> bool:
        """Saves current overrides as a custom user preset."""
        success = ThemeRepository.save_user_preset(name, self._config)
        if success:
            self._active_preset_name = name
            self._settings.setValue("active_preset", name)
        return success

    def delete_preset(self, name: str) -> bool:
        """Deletes a custom user preset."""
        return ThemeRepository.delete_user_preset(name)

    def save_theme(self) -> bool:
        """Persists current configuration to user theme.json file."""
        return ThemeRepository.save_theme_config(self._config)

    def export_theme(self, file_path: str) -> tuple[bool, str]:
        """Exports theme to JSON."""
        return ThemeRepository.export_theme(file_path, self._config)

    def import_theme(self, file_path: str, live_apply: bool = True) -> tuple[bool, str]:
        """Imports theme from JSON and optionally applies it."""
        ok, config, msg = ThemeRepository.import_theme(file_path)
        if ok and config:
            self._config = config
            self._active_preset_name = config.name
            if live_apply:
                self.apply_theme()
            return True, msg
        return False, msg

    def check_contrast(
        self, fg_key: str, bg_key: str, large_text: bool = False
    ) -> tuple[bool, float, str]:
        """Calculates contrast ratio between two token colors."""
        fg = str(self.get_token(fg_key))
        bg = str(self.get_token(bg_key))
        return ContrastChecker.check_wcag_aa(fg, bg, large_text=large_text)

    def apply_theme(self) -> None:
        """
        Compiles QSS from current token overrides, reapplies to QApplication,
        and emits theme_changed() to trigger custom repaints.
        """
        from cs01.gui.qss_builder import build_qss

        app = QApplication.instance()
        if app is not None:
            new_qss = build_qss()
            app.setStyleSheet(new_qss)

        # Notify all views and custom-painted widgets
        self.theme_changed.emit()
