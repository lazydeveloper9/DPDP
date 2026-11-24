"""
CS-01 DPDP Compliance Desktop GUI - Theme Repository & Persistence.

Manages saving and loading theme configurations and custom presets from JSON,
importing and exporting external theme files safely with schema validation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import QStandardPaths

from cs01.gui.theme_engine.theme_config import ThemeConfig, TOKEN_MAP
from cs01.gui.theme_engine.theme_presets import BUILTIN_PRESETS


class ThemeRepository:
    """Handles JSON disk persistence, user presets, and safe import/export."""

    SCHEMA_VERSION = 1

    @classmethod
    def get_config_dir(cls) -> Path:
        """Determines the application configuration directory path."""
        try:
            base = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.AppConfigLocation
            )
            if base:
                p = Path(base) / "CS-01"
                p.mkdir(parents=True, exist_ok=True)
                return p
        except Exception:
            pass

        # Fallback to user home
        p = Path.home() / ".cs01"
        p.mkdir(parents=True, exist_ok=True)
        return p

    @classmethod
    def get_theme_file_path(cls) -> Path:
        """Returns the full path to the active theme.json file."""
        return cls.get_config_dir() / "theme.json"

    @classmethod
    def get_presets_file_path(cls) -> Path:
        """Returns the full path to user_presets.json."""
        return cls.get_config_dir() / "user_presets.json"

    @classmethod
    def load_theme_config(cls) -> ThemeConfig:
        """
        Loads the active theme configuration from disk.
        Returns default ThemeConfig if file is missing, empty, or corrupt.
        """
        path = cls.get_theme_file_path()
        if not path.exists():
            return ThemeConfig(name="Bold Enterprise")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return ThemeConfig(name="Bold Enterprise")
            return ThemeConfig.from_dict(data)
        except Exception:
            return ThemeConfig(name="Bold Enterprise")

    @classmethod
    def save_theme_config(cls, config: ThemeConfig) -> bool:
        """Saves the active theme configuration to disk atomically."""
        path = cls.get_theme_file_path()
        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(config.to_dict(), f, indent=2)
            if path.exists():
                path.unlink()
            tmp_path.rename(path)
            return True
        except Exception:
            if tmp_path.exists():
                tmp_path.unlink()
            return False

    @classmethod
    def load_user_presets(cls) -> dict[str, dict[str, Any]]:
        """Loads user-created custom presets."""
        path = cls.get_presets_file_path()
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
            return {}
        except Exception:
            return {}

    @classmethod
    def save_user_preset(cls, name: str, config: ThemeConfig) -> bool:
        """Saves current theme overrides as a named custom preset."""
        presets = cls.load_user_presets()
        presets[name] = {
            "name": name,
            "description": f"User custom preset: {name}",
            "schema_version": cls.SCHEMA_VERSION,
            "overrides": dict(config.overrides),
        }
        path = cls.get_presets_file_path()
        tmp_path = path.with_suffix(".tmp")
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(presets, f, indent=2)
            if path.exists():
                path.unlink()
            tmp_path.rename(path)
            return True
        except Exception:
            return False

    @classmethod
    def delete_user_preset(cls, name: str) -> bool:
        """Deletes a user custom preset (built-ins cannot be deleted)."""
        if name in BUILTIN_PRESETS:
            return False
        presets = cls.load_user_presets()
        if name in presets:
            del presets[name]
            path = cls.get_presets_file_path()
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(presets, f, indent=2)
                return True
            except Exception:
                return False
        return False

    @classmethod
    def export_theme(cls, file_path: str, config: ThemeConfig) -> tuple[bool, str]:
        """Exports the active theme configuration to a specified JSON file."""
        try:
            target = Path(file_path)
            payload = {
                "format": "cs01_theme",
                "schema_version": cls.SCHEMA_VERSION,
                "name": config.name,
                "description": config.description,
                "overrides": config.overrides,
            }
            with open(target, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            return True, f"Theme exported successfully to {target.name}"
        except Exception as e:
            return False, f"Failed to export theme: {e}"

    @classmethod
    def import_theme(cls, file_path: str) -> tuple[bool, ThemeConfig | None, str]:
        """
        Safely validates and imports an external JSON theme configuration.
        Rejects non-JSON, invalid schemas, or malicious payloads without code execution.
        """
        try:
            target = Path(file_path)
            if not target.exists():
                return False, None, "File does not exist"

            with open(target, "r", encoding="utf-8") as f:
                data = json.load(f)

            if not isinstance(data, dict):
                return False, None, "Invalid theme file format: root must be a JSON object"

            # Validate overrides dictionary
            if "overrides" not in data or not isinstance(data["overrides"], dict):
                return False, None, "Invalid theme file: 'overrides' must be an object"
            raw_overrides = data["overrides"]

            clean_overrides: dict[str, Any] = {}
            for k, v in raw_overrides.items():
                if not isinstance(k, str):
                    continue
                # Sanitize value types to primitive literals only
                if isinstance(v, (str, int, float, bool)):
                    clean_overrides[k] = v

            config = ThemeConfig(
                name=str(data.get("name", target.stem)),
                description=str(data.get("description", "Imported theme")),
                schema_version=int(data.get("schema_version", cls.SCHEMA_VERSION)),
                overrides=clean_overrides,
            )
            return True, config, f"Theme '{config.name}' imported successfully"
        except Exception as e:
            return False, None, f"Failed to import theme: {e}"
