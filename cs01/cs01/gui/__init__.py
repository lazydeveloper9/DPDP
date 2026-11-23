"""
CS-01 DPDP Compliance Desktop GUI Package.

Provides the production PySide6 graphical interface for India's Digital Personal
Data Protection (DPDP) Act 2023 compliance auditing engine.
"""

from __future__ import annotations

from cs01.gui.app import create_app
from cs01.gui.main_window import MainWindow
from cs01.gui.qss_builder import build_qss, polish_widget
from cs01.gui.theme import DEFAULT_THEME, Theme
from cs01.gui.widgets.sidebar import NavigationSidebar


def run_gui(argv: list[str] | None = None) -> int:
    """
    Launches the CS-01 DPDP Compliance Desktop GUI.

    Initializes the Qt event loop, creates the application window,
    and blocks until the user exits.

    Args:
        argv: Optional command line arguments.

    Returns:
        Process exit code from Qt event loop.
    """
    app = create_app(argv)
    window = MainWindow()
    window.show()
    return app.exec()


__all__ = [
    "DEFAULT_THEME",
    "MainWindow",
    "NavigationSidebar",
    "Theme",
    "build_qss",
    "create_app",
    "polish_widget",
    "run_gui",
]
