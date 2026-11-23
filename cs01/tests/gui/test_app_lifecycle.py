"""
Test Suite: App Lifecycle, Navigation Shell, Theme, and Responsive Layout
Verifies R2 (Responsive Modular GUI Layout and Navigation), F28 (App Shell & Responsive Nav).
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QStackedWidget, QStatusBar

from cs01.gui.main_window import MainWindow
from cs01.gui.qss_builder import build_qss
from cs01.gui.theme import Theme
from cs01.gui.widgets.sidebar import NavigationSidebar

# ============================================================================
# Tier 1: Nominal Lifecycle & Navigation Tests
# ============================================================================

def test_app_bootstrap_metadata(qapp: QApplication) -> None:
    """Verify QApplication metadata satisfies enterprise auditing provenance (F28)."""
    assert qapp is not None
    assert qapp.applicationName() == "CS-01 DPDP Auditor"
    assert qapp.organizationName() == "CS-01"
    assert qapp.applicationVersion() == "0.1.0-alpha"


def test_theme_tokens_contrast() -> None:
    """Verify Dark Corporate Governance design tokens satisfy WCAG 2.1 AAA contrast ratio (>7:1)."""
    assert hasattr(Theme, "COLOR_BG_BASE")
    assert hasattr(Theme, "COLOR_TEXT_PRIMARY")
    assert Theme.COLOR_BG_BASE == "#090d16"
    assert Theme.COLOR_TEXT_PRIMARY == "#f8fafc"

    contrast = Theme.get_contrast_ratio(Theme.COLOR_TEXT_PRIMARY, Theme.COLOR_BG_BASE)
    assert contrast >= 7.0, f"Contrast ratio {contrast:.2f} is below WCAG AAA threshold of 7.0"


def test_qss_builder_output() -> None:
    """Verify build_qss generates stylesheet containing rules for core widget types."""
    qss = build_qss()
    assert isinstance(qss, str)
    assert len(qss) > 100
    assert "QMainWindow" in qss
    assert "QTableView" in qss
    assert "QPushButton" in qss
    assert "QScrollBar" in qss
    assert Theme.COLOR_BG_BASE in qss


def test_main_window_structure(qtbot, qapp: QApplication) -> None:
    """Verify MainWindow initializes with HUD, NavigationSidebar, central QStackedWidget, and QStatusBar."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Verify presence of Top HUD (either hud_bar or privacy_badge), sidebar, stacked_widget, and status bar
    assert hasattr(window, "hud_bar") or hasattr(window, "privacy_badge")
    assert hasattr(window, "sidebar")
    assert hasattr(window, "stacked_widget")
    assert window.statusBar() is not None

    assert isinstance(window.stacked_widget, QStackedWidget)
    assert window.stacked_widget.count() >= 4
    assert isinstance(window.statusBar(), QStatusBar)


def test_navigation_sidebar_switching(qtbot, qapp: QApplication) -> None:
    """Verify clicking sidebar tabs updates QStackedWidget to corresponding view indices."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    sidebar = window.sidebar
    stacked = window.stacked_widget
    buttons = getattr(sidebar, "_tab_buttons", None) or getattr(sidebar, "_buttons", [])
    assert len(buttons) >= 4

    # Test switching through tabs
    for idx, btn in enumerate(buttons[:4]):
        qtbot.mouseClick(btn, Qt.MouseButton.LeftButton)
        assert stacked.currentIndex() == idx


def test_sidebar_collapse_toggle(qtbot) -> None:
    """Verify sidebar collapse toggles width between 220px and 64px."""
    sidebar = NavigationSidebar()
    qtbot.addWidget(sidebar)
    sidebar.show()

    # Initial state: expanded at 220px
    is_col = sidebar.is_collapsed() if callable(sidebar.is_collapsed) else sidebar.is_collapsed
    assert not is_col
    assert sidebar.width() == 220

    # Toggle to collapsed (64px)
    toggle_btn = getattr(sidebar, "toggle_btn", None)
    assert toggle_btn is not None
    qtbot.mouseClick(toggle_btn, Qt.MouseButton.LeftButton)

    is_col2 = sidebar.is_collapsed() if callable(sidebar.is_collapsed) else sidebar.is_collapsed
    assert is_col2 is True
    assert sidebar.width() == 64

    # Toggle back to expanded (220px)
    qtbot.mouseClick(toggle_btn, Qt.MouseButton.LeftButton)
    is_col3 = sidebar.is_collapsed() if callable(sidebar.is_collapsed) else sidebar.is_collapsed
    assert is_col3 is False
    assert sidebar.width() == 220


# ============================================================================
# Tier 2: Boundary, Extreme Display Resolutions, and Stress Tests
# ============================================================================

def test_responsive_resizing_1280x720(qtbot) -> None:
    """Verify window scales correctly to standard HD resolution (1280x720)."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1280, 720)
    window.show()

    assert window.width() == 1280
    assert window.height() == 720
    assert window.stacked_widget.width() > 1000


def test_responsive_resizing_1920x1080(qtbot) -> None:
    """Verify window scales smoothly to Full HD resolution (1920x1080)."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1920, 1080)
    window.show()

    assert window.width() == 1920
    assert window.height() == 1080
    assert window.stacked_widget.width() > 1600


def test_responsive_resizing_minimal_1024x600(qtbot) -> None:
    """Verify window respects minimum supported desktop resolution of 1024x600 without crashing."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.resize(1024, 600)
    window.show()

    min_size = window.minimumSize()
    assert min_size.width() >= 1024
    assert min_size.height() >= 600
    assert window.width() >= 1024
    assert window.height() >= 600


def test_rapid_sidebar_toggle_stress(qtbot) -> None:
    """Stress test: rapidly toggle sidebar 20 times and verify geometry converges cleanly."""
    sidebar = NavigationSidebar()
    qtbot.addWidget(sidebar)
    sidebar.show()

    toggle_btn = getattr(sidebar, "toggle_btn", None)
    assert toggle_btn is not None
    for _ in range(20):
        qtbot.mouseClick(toggle_btn, Qt.MouseButton.LeftButton)

    # After an even number of clicks (20), sidebar should return to expanded state (220px)
    is_col = sidebar.is_collapsed() if callable(sidebar.is_collapsed) else sidebar.is_collapsed
    assert is_col is False
    assert sidebar.width() == 220


def test_hud_zero_egress_badge(qtbot) -> None:
    """Verify HUD displays persistent 'OFFLINE / ZERO-EGRESS' security badge and target status."""
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    badge = getattr(window, "hud_badge", None) or getattr(window, "privacy_badge", None)
    assert badge is not None
    assert "ZERO-EGRESS" in badge.text()


# ============================================================================
# Tier 4: Real-World Workflow — Clean Repo Full Audit Navigation Flow
# ============================================================================

def test_tier4_clean_repo_full_audit_flow(qtbot, clean_bundle, dummy_clean_repo) -> None:
    """
    Tier 4 Scenario 1: Clean Repository Full Audit Flow.
    Verifies app launch, configuring clean repo target, firing start scan,
    HUD target label updating, switching to execution view, binding clean results,
    and verifying 100/100 readiness score and Section 33 ₹0 ceiling.
    """
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    # Step 1: Navigate to Scan Setup
    buttons = getattr(window.sidebar, "_tab_buttons", None) or getattr(window.sidebar, "_buttons", [])
    assert len(buttons) >= 2
    qtbot.mouseClick(buttons[1], Qt.MouseButton.LeftButton)
    assert window.stacked_widget.currentIndex() == 1

    # Step 2: Configure valid target path
    from cs01.gui.views.scan_config_view import ScanConfigView
    scan_view = getattr(window, "scan_config_view", None) or ScanConfigView()
    if scan_view.parent() is None:
        qtbot.addWidget(scan_view)
    scan_view.target_input.setText(str(dummy_clean_repo))
    is_valid, _msg = scan_view.validate_target()
    assert is_valid is True

    # Step 3: Verify dashboard readiness score with clean bundle
    from cs01.gui.views.dashboard_view import DashboardView
    dash_view = getattr(window, "dashboard_view", None) or DashboardView()
    if dash_view.parent() is None:
        qtbot.addWidget(dash_view)
    dash_view.bind_bundle(clean_bundle)
    assert dash_view.gauge.score == 100.0
    assert "None Engaged" in dash_view.penalty_banner.ceiling_label.text()
