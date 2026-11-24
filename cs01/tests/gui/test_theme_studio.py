"""
Test Suite: Theme Customization Studio & Neo-Brutalist Theme Engine.

Verifies the 19 comprehensive requirements from the Master Implementation Prompt:
1. Global background propagation
2. Page-level isolation (Dashboard KPI vs Findings)
3. Sidebar active navigation customization
4. Primary button styling
5. Table header and row styling
6. Statutory severity risk colors
7. Input and dropdown styling
8. Typography metrics
9. Built-in preset application
10. Custom preset saving and retrieval
11. Disk persistence across restarts
12. Safe JSON import/export
13. Component reset-to-inherited
14. Page category reset
15. Reset entire theme
16. WCAG AA contrast validation
17. Runtime updates without interrupting scan workers
18. Settings view navigation and layout
19. Core compliance audit functionality preservation
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from cs01.gui.main_window import MainWindow
from cs01.gui.qss_builder import build_qss
from cs01.gui.theme_engine.contrast_checker import ContrastChecker
from cs01.gui.theme_engine.theme_config import ThemeConfig
from cs01.gui.theme_engine.theme_manager import ThemeManager
from cs01.gui.theme_engine.theme_repository import ThemeRepository
from cs01.gui.views.settings_view import SettingsView


@pytest.fixture(autouse=True)
def reset_theme_manager():
    """Ensure ThemeManager is reset to clean state before each test."""
    tm = ThemeManager.instance()
    tm.reset_all(live_apply=False)
    yield
    tm.reset_all(live_apply=False)


# ----------------------------------------------------------------------------
# 1. Global Background Updates Inheriting Pages
# ----------------------------------------------------------------------------
def test_change_global_background_updates_inheriting_pages(qapp: QApplication) -> None:
    tm = ThemeManager.instance()
    new_bg = "#E0F7FA"
    tm.set_token("global.bg.main", new_bg, live_apply=True)

    assert tm.get_token("global.bg.main") == new_bg
    # page.dashboard.bg has parent_key="global.bg.main", should inherit
    assert tm.get_token("page.dashboard.bg") == new_bg
    assert tm.get_token("page.scan_setup.bg") == new_bg
    assert tm.get_token("page.execution.workspace_bg") == new_bg
    assert tm.get_token("page.findings.workspace_bg") == new_bg

    qss = build_qss()
    assert new_bg in qss


# ----------------------------------------------------------------------------
# 2. Page-level Isolation: Dashboard KPI vs Findings
# ----------------------------------------------------------------------------
def test_change_dashboard_kpi_bg_isolation() -> None:
    tm = ThemeManager.instance()
    tm.set_token("page.dashboard.kpi_card_bg", "#FF00FF")
    
    assert tm.get_token("page.dashboard.kpi_card_bg") == "#FF00FF"
    # Findings summary cards should remain default white
    assert tm.get_token("page.findings.card_bg") == "#FFFFFF"
    assert tm.get_token("global.bg.card") == "#FFFFFF"


# ----------------------------------------------------------------------------
# 3. Sidebar Active Navigation Customization
# ----------------------------------------------------------------------------
def test_change_sidebar_active_nav_color() -> None:
    tm = ThemeManager.instance()
    tm.set_token("component.sidebar.active_bg", "#00E5FF", live_apply=True)
    tm.set_token("component.sidebar.active_text", "#000000", live_apply=True)

    assert tm.get_token("component.sidebar.active_bg") == "#00E5FF"
    assert tm.get_token("component.sidebar.active_text") == "#000000"

    qss = build_qss()
    assert "#00E5FF" in qss


# ----------------------------------------------------------------------------
# 4. Primary Button Styling
# ----------------------------------------------------------------------------
def test_change_primary_button_bg_and_text() -> None:
    tm = ThemeManager.instance()
    tm.set_token("component.button.primary.bg", "#FF1493")
    tm.set_token("component.button.primary.text", "#FFFFFF")

    assert tm.get_token("component.button.primary.bg") == "#FF1493"
    assert tm.get_token("component.button.primary.text") == "#FFFFFF"

    qss = build_qss()
    assert "#FF1493" in qss


# ----------------------------------------------------------------------------
# 5. Table Header and Row Styling
# ----------------------------------------------------------------------------
def test_change_findings_table_header_and_row_bgs() -> None:
    tm = ThemeManager.instance()
    tm.set_token("component.table.header_bg", "#1E3A8A")
    tm.set_token("component.table.row_bg", "#F8FAFC")
    tm.set_token("component.table.row_alt_bg", "#F1F5F9")

    assert tm.get_token("component.table.header_bg") == "#1E3A8A"
    assert tm.get_token("component.table.row_bg") == "#F8FAFC"
    assert tm.get_token("component.table.row_alt_bg") == "#F1F5F9"

    qss = build_qss()
    assert "#1E3A8A" in qss
    assert "#F8FAFC" in qss


# ----------------------------------------------------------------------------
# 6. Statutory Severity Risk Colors
# ----------------------------------------------------------------------------
def test_change_individual_severity_colors() -> None:
    tm = ThemeManager.instance()
    tm.set_token("status.critical", "#DC2626")
    tm.set_token("status.high", "#EA580C")
    tm.set_token("status.medium", "#CA8A04")
    tm.set_token("status.low", "#2563EB")
    tm.set_token("status.success", "#16A34A")

    assert tm.get_token("status.critical") == "#DC2626"
    assert tm.get_token("status.high") == "#EA580C"
    assert tm.get_token("status.medium") == "#CA8A04"
    assert tm.get_token("status.low") == "#2563EB"
    assert tm.get_token("status.success") == "#16A34A"


# ----------------------------------------------------------------------------
# 7. Input and Dropdown Styling
# ----------------------------------------------------------------------------
def test_change_input_and_dropdown_colors() -> None:
    tm = ThemeManager.instance()
    tm.set_token("component.input.bg", "#FEF08A")
    tm.set_token("component.input.text", "#854D0E")
    tm.set_token("component.input.border", "#A16207")

    assert tm.get_token("component.input.bg") == "#FEF08A"
    assert tm.get_token("component.input.text") == "#854D0E"

    qss = build_qss()
    assert "#FEF08A" in qss


# ----------------------------------------------------------------------------
# 8. Typography Metrics
# ----------------------------------------------------------------------------
def test_change_typography() -> None:
    tm = ThemeManager.instance()
    tm.set_token("typography.font_sans", '"Comic Sans MS", cursive')
    tm.set_token("typography.size_h1", 22)
    tm.set_token("typography.size_body", 11)

    assert tm.get_token("typography.font_sans") == '"Comic Sans MS", cursive'
    assert tm.get_token("typography.size_h1") == 22
    assert tm.get_token("typography.size_body") == 11

    qss = build_qss()
    assert "Comic Sans MS" in qss


# ----------------------------------------------------------------------------
# 9. Built-in Preset Application
# ----------------------------------------------------------------------------
def test_apply_preset() -> None:
    tm = ThemeManager.instance()
    assert tm.apply_preset("Cobalt Brutalist")
    assert tm.active_preset_name == "Cobalt Brutalist"
    assert tm.get_token("global.bg.main") == "#E8EEF9"
    assert tm.get_token("global.accent.primary") == "#3155FF"

    assert tm.apply_preset("Yellow Industrial")
    assert tm.active_preset_name == "Yellow Industrial"
    assert tm.get_token("global.bg.main") == "#FCEB80"


# ----------------------------------------------------------------------------
# 10. Custom Preset Saving and Retrieval
# ----------------------------------------------------------------------------
def test_save_custom_theme() -> None:
    tm = ThemeManager.instance()
    tm.set_token("global.bg.main", "#123456")
    assert tm.save_current_as_preset("My Custom Test Preset")

    presets = tm.get_all_presets()
    assert "My Custom Test Preset" in presets
    assert presets["My Custom Test Preset"]["overrides"]["global.bg.main"] == "#123456"

    # Clean up
    tm.delete_preset("My Custom Test Preset")


# ----------------------------------------------------------------------------
# 11. Persistence Across Restarts
# ----------------------------------------------------------------------------
def test_restart_persistence(tmp_path: Path, monkeypatch) -> None:
    fake_config = tmp_path / "theme.json"
    monkeypatch.setattr(ThemeRepository, "get_theme_file_path", classmethod(lambda cls: fake_config))

    cfg = ThemeConfig(name="Saved Theme", overrides={"global.bg.main": "#AABBCC"})
    assert ThemeRepository.save_theme_config(cfg)
    assert fake_config.exists()

    loaded = ThemeRepository.load_theme_config()
    assert loaded.name == "Saved Theme"
    assert loaded.overrides.get("global.bg.main") == "#AABBCC"


# ----------------------------------------------------------------------------
# 12. Safe JSON Import and Export
# ----------------------------------------------------------------------------
def test_import_and_export_themes(tmp_path: Path) -> None:
    tm = ThemeManager.instance()
    tm.set_token("global.accent.primary", "#990000")
    export_file = str(tmp_path / "exported_theme.json")

    ok, msg = tm.export_theme(export_file)
    assert ok
    assert Path(export_file).exists()

    # Reset
    tm.reset_all(live_apply=False)
    assert tm.get_token("global.accent.primary") != "#990000"

    # Import back
    ok_imp, msg_imp = tm.import_theme(export_file, live_apply=False)
    assert ok_imp
    assert tm.get_token("global.accent.primary") == "#990000"

    # Test rejection of invalid payload
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text('{"bad_structure": 123}', encoding="utf-8")
    ok_bad, bad_cfg, _ = ThemeRepository.import_theme(str(corrupt_file))
    assert not ok_bad


# ----------------------------------------------------------------------------
# 13. Component Reset-to-Inherited
# ----------------------------------------------------------------------------
def test_reset_component_to_inherited() -> None:
    tm = ThemeManager.instance()
    token_key = "component.button.primary.bg"

    assert not tm.is_overridden(token_key)
    assert "Inherited" in tm.get_inheritance_status(token_key)

    tm.set_token(token_key, "#112233")
    assert tm.is_overridden(token_key)
    assert tm.get_inheritance_status(token_key) == "Component Override"

    tm.reset_token(token_key)
    assert not tm.is_overridden(token_key)
    assert "Inherited" in tm.get_inheritance_status(token_key)


# ----------------------------------------------------------------------------
# 14. Page Category Reset
# ----------------------------------------------------------------------------
def test_reset_individual_page() -> None:
    tm = ThemeManager.instance()
    tm.set_token("page.dashboard.bg", "#111111")
    tm.set_token("page.dashboard.heading", "#222222")

    assert tm.is_overridden("page.dashboard.bg")
    assert tm.is_overridden("page.dashboard.heading")

    tm.reset_category("Page: Dashboard")
    assert not tm.is_overridden("page.dashboard.bg")
    assert not tm.is_overridden("page.dashboard.heading")


# ----------------------------------------------------------------------------
# 15. Reset Entire Theme
# ----------------------------------------------------------------------------
def test_reset_entire_theme() -> None:
    tm = ThemeManager.instance()
    tm.set_token("global.bg.main", "#000000")
    tm.set_token("global.text.primary", "#FFFFFF")
    tm.set_token("design.border.width", 5)

    tm.reset_all()
    assert not tm.is_overridden("global.bg.main")
    assert not tm.is_overridden("global.text.primary")
    assert tm.get_token("design.border.width") == 2


# ----------------------------------------------------------------------------
# 16. WCAG AA Contrast Validation Warnings
# ----------------------------------------------------------------------------
def test_contrast_validation_warnings() -> None:
    # Yellow background with white text has terrible contrast (~1.1:1)
    passed, ratio, msg = ContrastChecker.check_wcag_aa("#FFFFFF", "#FFE500")
    assert not passed
    assert ratio < 3.0
    assert "WARNING" in msg

    # Deep black on pure white has maximum contrast (21:1)
    passed_high, ratio_high, msg_high = ContrastChecker.check_wcag_aa("#111111", "#FFFFFF")
    assert passed_high
    assert ratio_high > 15.0


# ----------------------------------------------------------------------------
# 17. Runtime Updates While Scan Execution is Active
# ----------------------------------------------------------------------------
def test_change_colors_while_scan_active(qtbot, qapp: QApplication) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Simulate scan started state
    window.scan_execution_view.on_scan_started()
    window.scan_execution_view.on_progress_updated(50, "Analyzing statutory pillars...")

    # Apply live theme changes while scan is ostensibly executing
    tm = ThemeManager.instance()
    tm.set_token("global.accent.primary", "#00FFAA", live_apply=True)
    tm.apply_theme()

    # Verify execution view progress bar and state remain unaffected
    assert window.scan_execution_view.progress_bar.value() == 50
    assert window.stacked_widget.currentIndex() == 0  # not interrupted


# ----------------------------------------------------------------------------
# 18. Settings View Navigation and Layout
# ----------------------------------------------------------------------------
def test_settings_page_and_navigation(qtbot, qapp: QApplication) -> None:
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Settings is mounted at index 6 (stacked widget contains at least 7 pages)
    assert window.stacked_widget.count() >= 7
    window.navigate_to(6)
    assert window.stacked_widget.currentIndex() == 6

    settings_view: SettingsView = window.settings_view
    assert isinstance(settings_view, SettingsView)
    assert settings_view.category_list.count() == len(SettingsView.CATEGORIES)

    # Click on "Neo-Brutalist Geometry" category
    settings_view.category_list.setCurrentRow(4)
    assert len(settings_view._token_rows) > 0


# ----------------------------------------------------------------------------
# 19. Core Audit Functionality Remains 100% Intact
# ----------------------------------------------------------------------------
def test_core_audit_functionality_intact() -> None:
    from cs01.pipeline.stage4_evaluate.rule_loader import load_all_rules
    from cs01.models import PiiType
    from cs01.pipeline.stage3_detect.validators import validate_aadhaar, validate_pan

    # 1. Active statutory rules loaded (39 rules across pass_a and pass_b)
    rules = load_all_rules()
    assert len(rules) == 39

    # 2. PII Types taxonomy
    assert PiiType.AADHAAR in list(PiiType)
    assert PiiType.PAN in list(PiiType)

    # 3. Mathematical Verhoeff and Regex validators intact
    is_valid_aadhaar, reason = validate_aadhaar("9999-8888-7777")
    assert is_valid_aadhaar is False
    assert "verhoeff" in reason

    is_valid_pan, entity_desc = validate_pan("ABCPE1234F")
    assert is_valid_pan is True
    assert "Individual" in entity_desc

    from cs01.utils import redact_pii_in_snippet
    redacted = redact_pii_in_snippet("Target: 9999-8888-7777", ["9999-8888-7777"])
    assert "[PII_" in redacted
    assert "9999-8888-7777" not in redacted
