"""
CS-01 DPDP Compliance Desktop GUI - Dynamic QSS Builder.

Generates a comprehensive Dark Corporate Governance stylesheet adhering to
WCAG AAA contrast standards, crisp slate borders, active focus indicators,
and sleek modern desktop ergonomics.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cs01.gui.theme import DEFAULT_THEME, Theme

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def build_qss(theme: Theme | None = None) -> str:
    """
    Compiles and returns the authoritative Qt Stylesheet (QSS).

    Args:
        theme: Optional custom Theme instance. Defaults to DEFAULT_THEME.

    Returns:
        Full CSS/QSS string for QApplication.setStyleSheet().
    """
    t = theme or DEFAULT_THEME

    return f"""
    /* =========================================================================
       1. GLOBAL APPLICATION & BASE CANVAS
       ========================================================================= */
    QMainWindow {{
        background-color: {t.bg_base};
        border: none;
    }}

    QWidget {{
        background-color: {t.bg_base};
        color: {t.text_primary};
        font-family: {t.font_sans};
        font-size: 10pt;
        selection-background-color: {t.accent_royal};
        selection-color: {t.text_white};
    }}

    /* Container Frames & Panels */
    QFrame {{
        border: none;
        background-color: transparent;
    }}

    QFrame[class="card"] {{
        background-color: {t.bg_card};
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_lg}px;
    }}

    QFrame[class="card-interactive"] {{
        background-color: {t.bg_card};
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_lg}px;
    }}
    QFrame[class="card-interactive"]:hover {{
        background-color: {t.bg_card_hover};
        border-color: {t.border_strong};
    }}

    QFrame[class="hud"] {{
        background-color: {t.bg_surface};
        border-bottom: 1px solid {t.border_subtle};
    }}

    QFrame[class="sidebar"] {{
        background-color: {t.bg_surface};
        border-right: 1px solid {t.border_subtle};
    }}

    /* =========================================================================
       2. TYPOGRAPHY & LABELS
       ========================================================================= */
    QLabel {{
        color: {t.text_primary};
        background-color: transparent;
        font-size: 10pt;
    }}

    QLabel[class="hud-title"] {{
        font-size: 12pt;
        font-weight: 700;
        color: {t.text_primary};
    }}

    QLabel[class="h1"] {{
        font-size: 16pt;
        font-weight: 700;
        color: {t.text_primary};
    }}

    QLabel[class="h2"] {{
        font-size: 13pt;
        font-weight: 600;
        color: {t.text_primary};
    }}

    QLabel[class="h3"] {{
        font-size: 11pt;
        font-weight: 600;
        color: {t.text_primary};
    }}

    QLabel[class="text-secondary"] {{
        color: {t.text_secondary};
        font-size: 9.5pt;
    }}

    QLabel[class="text-muted"] {{
        color: {t.text_muted};
        font-size: 8.5pt;
    }}

    QLabel[class="code-text"] {{
        font-family: {t.font_mono};
        font-size: 9.5pt;
        color: {t.accent_blue};
    }}

    /* Badges */
    QLabel[class="badge-version"] {{
        background-color: {t.bg_card};
        color: {t.text_secondary};
        font-size: 8.5pt;
        font-weight: 600;
        padding: 2px 8px;
        border-radius: {t.radius_sm}px;
        border: 1px solid {t.border_subtle};
    }}

    QLabel[class="badge-privacy"] {{
        background-color: {t.status_success_bg};
        color: {t.status_success};
        font-size: 8.5pt;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: {t.radius_sm}px;
        border: 1px solid {t.status_success};
    }}

    QLabel[class="badge-critical"] {{
        background-color: {t.risk_critical_bg};
        color: {t.risk_critical};
        font-size: 8.5pt;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: {t.radius_sm}px;
        border: 1px solid {t.risk_critical};
    }}

    QLabel[class="badge-high"] {{
        background-color: {t.risk_high_bg};
        color: {t.risk_high};
        font-size: 8.5pt;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: {t.radius_sm}px;
        border: 1px solid {t.risk_high};
    }}

    QLabel[class="badge-medium"] {{
        background-color: {t.risk_medium_bg};
        color: {t.risk_medium};
        font-size: 8.5pt;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: {t.radius_sm}px;
        border: 1px solid {t.risk_medium};
    }}

    QLabel[class="badge-low"] {{
        background-color: {t.risk_low_bg};
        color: {t.risk_low};
        font-size: 8.5pt;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: {t.radius_sm}px;
        border: 1px solid {t.risk_low};
    }}

    QLabel[class="badge-clean"] {{
        background-color: {t.status_success_bg};
        color: {t.status_success};
        font-size: 8.5pt;
        font-weight: 700;
        padding: 2px 8px;
        border-radius: {t.radius_sm}px;
        border: 1px solid {t.status_success};
    }}

    /* =========================================================================
       3. BUTTON HIERARCHY
       ========================================================================= */
    /* Secondary (Default) Button */
    QPushButton {{
        background-color: {t.bg_card};
        color: {t.text_primary};
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_md}px;
        padding: 6px 14px;
        font-size: 9.5pt;
        font-weight: 600;
        min-height: 22px;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {t.bg_card_hover};
        border-color: {t.border_strong};
    }}
    QPushButton:pressed {{
        background-color: #16202e;
        border-color: {t.border_subtle};
    }}
    QPushButton:focus {{
        border: 1.5px solid {t.border_focus};
    }}
    QPushButton:disabled {{
        background-color: #131c2a;
        color: {t.text_muted};
        border-color: #1e293b;
    }}

    /* Primary Action Button (Call-to-Action) */
    QPushButton[class="primary"] {{
        background-color: {t.accent_royal};
        color: {t.text_white};
        border: 1px solid {t.accent_royal_hover};
        font-weight: 600;
        padding: 6px 16px;
    }}
    QPushButton[class="primary"]:hover {{
        background-color: {t.accent_royal_hover};
        border-color: {t.accent_royal_pressed};
    }}
    QPushButton[class="primary"]:pressed {{
        background-color: {t.accent_royal_pressed};
    }}
    QPushButton[class="primary"]:focus {{
        border: 2px solid {t.border_focus};
    }}
    QPushButton[class="primary"]:disabled {{
        background-color: {t.bg_card};
        color: {t.text_muted};
        border: 1px solid {t.border_subtle};
    }}

    /* Danger / Terminate Button */
    QPushButton[class="danger"] {{
        background-color: {t.risk_critical_btn};
        color: {t.text_white};
        border: 1px solid {t.risk_critical_hover};
        font-weight: 600;
        padding: 6px 14px;
    }}
    QPushButton[class="danger"]:hover {{
        background-color: {t.risk_critical_hover};
    }}
    QPushButton[class="danger"]:pressed {{
        background-color: #991b1b;
    }}
    QPushButton[class="danger"]:focus {{
        border: 2px solid {t.risk_critical};
    }}

    /* Icon-Only Buttons */
    QPushButton[class="icon-only"] {{
        background-color: transparent;
        color: {t.text_secondary};
        border: none;
        border-radius: {t.radius_md}px;
        padding: 4px;
        min-width: 32px;
        max-width: 36px;
        min-height: 32px;
        max-height: 36px;
        font-size: 11pt;
    }}
    QPushButton[class="icon-only"]:hover {{
        background-color: {t.bg_card};
        color: {t.text_primary};
    }}
    QPushButton[class="icon-only"]:pressed {{
        background-color: {t.bg_surface};
    }}

    /* Sidebar Navigation Button */
    QPushButton[class="nav-btn"] {{
        background-color: transparent;
        color: {t.text_secondary};
        border: none;
        border-left: 3px solid transparent;
        border-radius: 0px {t.radius_md}px {t.radius_md}px 0px;
        padding: 8px 12px;
        font-size: 10pt;
        font-weight: 500;
        text-align: left;
        min-height: 24px;
    }}
    QPushButton[class="nav-btn"]:hover {{
        background-color: rgba(30, 41, 59, 0.7);
        color: {t.text_primary};
    }}
    QPushButton[class="nav-btn"]:checked {{
        background-color: {t.bg_card};
        color: {t.accent_blue};
        font-weight: 600;
        border-left: 3px solid {t.accent_blue};
    }}
    QPushButton[class="nav-btn"]:focus {{
        outline: none;
    }}

    /* =========================================================================
       4. FORM CONTROLS & INPUT WELLS
       ========================================================================= */
    QLineEdit {{
        background-color: {t.bg_input};
        color: {t.text_primary};
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_md}px;
        padding: 6px 10px;
        font-size: 9.5pt;
        min-height: 22px;
    }}
    QLineEdit:hover {{
        border-color: {t.border_strong};
    }}
    QLineEdit:focus {{
        border: 1.5px solid {t.border_focus};
    }}
    QLineEdit:disabled {{
        background-color: {t.bg_surface};
        color: {t.text_muted};
        border-color: {t.border_subtle};
    }}
    QLineEdit[class="error"] {{
        border: 1.5px solid {t.border_error};
    }}
    QLineEdit[class="success"] {{
        border: 1.5px solid {t.status_success};
    }}

    QComboBox {{
        background-color: {t.bg_input};
        color: {t.text_primary};
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_md}px;
        padding: 6px 12px;
        font-size: 9.5pt;
        min-height: 22px;
    }}
    QComboBox:hover {{
        border-color: {t.border_strong};
    }}
    QComboBox:focus {{
        border: 1.5px solid {t.border_focus};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 26px;
        border-left: 1px solid {t.border_subtle};
        border-top-right-radius: {t.radius_md}px;
        border-bottom-right-radius: {t.radius_md}px;
    }}
    QComboBox QAbstractItemView {{
        background-color: {t.bg_surface};
        color: {t.text_primary};
        border: 1px solid {t.border_strong};
        border-radius: {t.radius_md}px;
        selection-background-color: {t.accent_royal};
        selection-color: {t.text_white};
        padding: 4px;
        outline: none;
    }}

    /* =========================================================================
       5. STACKED WIDGET & CONTAINERS
       ========================================================================= */
    QStackedWidget {{
        background-color: transparent;
        border: none;
    }}

    /* =========================================================================
       6. SLEEK CUSTOM SCROLLBARS (8px Width)
       ========================================================================= */
    QScrollBar:vertical {{
        background-color: {t.bg_base};
        width: 8px;
        margin: 0px;
        border-radius: {t.radius_sm}px;
    }}
    QScrollBar::handle:vertical {{
        background-color: {t.border_subtle};
        min-height: 24px;
        border-radius: {t.radius_sm}px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {t.border_strong};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
        subcontrol-origin: margin;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background-color: {t.bg_base};
        height: 8px;
        margin: 0px;
        border-radius: {t.radius_sm}px;
    }}
    QScrollBar::handle:horizontal {{
        background-color: {t.border_subtle};
        min-width: 24px;
        border-radius: {t.radius_sm}px;
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {t.border_strong};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
        subcontrol-origin: margin;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* =========================================================================
       7. STATUS BAR & TOOLTIPS
       ========================================================================= */
    QStatusBar {{
        background-color: {t.bg_surface};
        color: {t.text_secondary};
        border-top: 1px solid {t.border_subtle};
        font-size: 8.5pt;
        padding: 2px 10px;
        min-height: 24px;
    }}
    QStatusBar::item {{
        border: none;
        padding: 0 4px;
    }}

    QToolTip {{
        background-color: {t.bg_card};
        color: {t.text_primary};
        border: 1px solid {t.border_strong};
        border-radius: {t.radius_sm}px;
        padding: 6px 10px;
        font-size: 8.5pt;
    }}

    /* =========================================================================
       8. DATA TABLES & PROGRESS METRICS
       ========================================================================= */
    QTableView {{
        background-color: {t.bg_surface};
        gridline-color: {t.bg_card};
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_md}px;
        color: {t.text_primary};
        selection-background-color: #1e3a5f;
        selection-color: {t.text_primary};
    }}
    QHeaderView::section {{
        background-color: {t.bg_card};
        color: {t.text_secondary};
        font-weight: 600;
        font-size: 9pt;
        padding: 6px 10px;
        border: none;
        border-bottom: 1px solid {t.border_subtle};
        border-right: 1px solid {t.border_subtle};
    }}

    QProgressBar {{
        background-color: {t.bg_card};
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_sm}px;
        height: 8px;
        text-align: center;
        color: transparent;
    }}
    QProgressBar::chunk {{
        background-color: {t.accent_royal};
        border-radius: 3px;
    }}

    /* =========================================================================
       9. TABS
       ========================================================================= */
    QTabWidget::pane {{
        border: 1px solid {t.border_subtle};
        border-radius: {t.radius_md}px;
        background-color: {t.bg_surface};
    }}
    QTabBar::tab {{
        background-color: {t.bg_base};
        color: {t.text_secondary};
        border: 1px solid {t.border_subtle};
        padding: 6px 14px;
        margin-right: 2px;
        border-top-left-radius: {t.radius_sm}px;
        border-top-right-radius: {t.radius_sm}px;
    }}
    QTabBar::tab:selected {{
        background-color: {t.bg_card};
        color: {t.accent_blue};
        border-bottom-color: {t.bg_card};
        font-weight: 600;
    }}
    QTabBar::tab:hover:!selected {{
        background-color: {t.bg_card_hover};
        color: {t.text_primary};
    }}
    """


def polish_widget(widget: QWidget, class_name: str | None = None) -> None:
    """
    Forces Qt style re-evaluation on dynamic property changes.

    Args:
        widget: Target QWidget.
        class_name: Optional class string (e.g. "error", "success", "card") to set before re-polishing.
    """
    if class_name is not None:
        widget.setProperty("class", class_name)
    style = widget.style()
    if style:
        style.unpolish(widget)
        style.polish(widget)
