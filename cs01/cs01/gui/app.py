"""
CS-01 DPDP Compliance Desktop GUI - Application Bootstrap.

Configures High-DPI scaling policies, initializes the QApplication singleton,
sets corporate application metadata, and applies the dark governance stylesheet.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import QApplication

from cs01.gui.qss_builder import build_qss
from cs01.gui.theme import DEFAULT_THEME, Theme


def create_app(
    argv: list[str] | None = None,
    theme: Theme | None = None,
) -> QApplication:
    """
    Initializes and configures the singleton QApplication instance.

    Inspects QApplication.instance() to prevent duplicate instantiation
    errors (crucial for both pytest-qt and standalone execution).

    Args:
        argv: Command line arguments list. Defaults to sys.argv.
        theme: Optional custom Theme instance. Defaults to DEFAULT_THEME.

    Returns:
        Configured QApplication instance with high-DPI scaling and QSS applied.
    """
    app = QApplication.instance()
    if app is None:
        # Configure High-DPI rounding policy prior to QApplication construction
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        app = QApplication(argv if argv is not None else sys.argv)

    # Configure Application Metadata
    app.setApplicationName("CS-01 DPDP Auditor")
    app.setOrganizationName("CS-01")
    app.setOrganizationDomain("cs01.local")
    app.setApplicationVersion("0.1.0-alpha")

    # Set Default Application Font
    font = QFont("Segoe UI", 10)
    font.setStyleHint(QFont.SansSerif)
    app.setFont(font)

    # Apply Authoritative QSS Theme
    active_theme = theme or DEFAULT_THEME
    app.setStyleSheet(build_qss(active_theme))

    return app
