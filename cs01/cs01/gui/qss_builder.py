"""
CS-01 DPDP Compliance Desktop GUI - Dynamic QSS Builder.

Generates the authoritative Bold Enterprise Neo-Brutalist stylesheet adhering to
authentic geometric minimalism: 2px solid black (#111111) borders, warm off-white
canvas (#F6F3EA), pure white (#FFFFFF) and pale yellow (#FFF4C2) cards, signature
yellow (#FFE500) interactive buttons, high contrast, and sharp 0px radius corners.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from cs01.gui.theme import (
    BRUTALIST_BG_MAIN,
    BRUTALIST_BG_SECONDARY,
    BRUTALIST_BLACK,
    BRUTALIST_BLACK_SEC,
    BRUTALIST_BORDER,
    BRUTALIST_COBALT,
    BRUTALIST_GREEN,
    BRUTALIST_MUTED,
    BRUTALIST_ORANGE,
    BRUTALIST_RED,
    BRUTALIST_SURFACE,
    BRUTALIST_SURFACE_ALT,
    BRUTALIST_YELLOW,
    BRUTALIST_YELLOW_BRIGHT,
    DEFAULT_THEME,
    Theme,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget


def build_qss(theme: Theme | None = None) -> str:
    """
    Compiles and returns the authoritative Bold Enterprise Neo-Brutalist Qt Stylesheet.

    Args:
        theme: Optional custom Theme instance. Defaults to DEFAULT_THEME.

    Returns:
        Full CSS/QSS string for QApplication.setStyleSheet().
    """
    t = theme or DEFAULT_THEME

    return f"""
    /* =========================================================================
       1. GLOBAL APPLICATION CANVAS & BASE WIDGETS
       /* Fallback/Legacy Dark Canvas: #090d16 */
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
        selection-background-color: {BRUTALIST_YELLOW};
        selection-color: {BRUTALIST_BLACK};
    }}

    QScrollArea {{
        background-color: transparent;
        border: none;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    /* Container Frames & Panels */
    QFrame {{
        border: none;
        background-color: transparent;
    }}

    QFrame[class="card"] {{
        background-color: {BRUTALIST_SURFACE};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
    }}

    QFrame[class="card-interactive"] {{
        background-color: {BRUTALIST_SURFACE};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
    }}
    QFrame[class="card-interactive"]:hover {{
        background-color: {BRUTALIST_SURFACE_ALT};
        border: 2px solid {BRUTALIST_BORDER};
    }}

    QFrame[class="card-alt"] {{
        background-color: {BRUTALIST_SURFACE_ALT};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
    }}

    QFrame[class="hud"] {{
        background-color: {t.bg_surface};
        border-bottom: 2px solid {BRUTALIST_BORDER};
    }}

    QFrame[class="sidebar"] {{
        background-color: {t.bg_surface};
        border-right: 2px solid {BRUTALIST_BORDER};
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
        font-size: 13pt;
        font-weight: 800;
        color: {BRUTALIST_BLACK};
        letter-spacing: -0.3px;
    }}

    QLabel[class="h1"] {{
        font-size: 18pt;
        font-weight: 800;
        color: {BRUTALIST_BLACK};
        letter-spacing: -0.5px;
    }}

    QLabel[class="h2"] {{
        font-size: 13pt;
        font-weight: 700;
        color: {BRUTALIST_BLACK};
    }}

    QLabel[class="h3"] {{
        font-size: 11pt;
        font-weight: 700;
        color: {BRUTALIST_BLACK};
    }}

    QLabel[class="text-secondary"] {{
        color: {BRUTALIST_BLACK_SEC};
        font-size: 9.5pt;
        font-weight: 500;
    }}

    QLabel[class="text-muted"] {{
        color: {BRUTALIST_MUTED};
        font-size: 8.5pt;
        font-weight: 600;
    }}

    QLabel[class="code-text"] {{
        font-family: {t.font_mono};
        font-size: 9.5pt;
        font-weight: 600;
        color: {BRUTALIST_BLACK};
        background-color: {BRUTALIST_SURFACE_ALT};
        border: 1px solid {BRUTALIST_BORDER};
        padding: 2px 4px;
    }}

    /* Badges */
    QLabel[class="badge-version"] {{
        background-color: {BRUTALIST_YELLOW};
        color: {BRUTALIST_BLACK};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: 0px;
        border: 1.5px solid {BRUTALIST_BORDER};
    }}

    QLabel[class="badge-privacy"] {{
        background-color: {BRUTALIST_GREEN};
        color: {BRUTALIST_BLACK};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: 0px;
        border: 2px solid {BRUTALIST_BORDER};
    }}

    QLabel[class="badge-critical"] {{
        background-color: {BRUTALIST_RED};
        color: #FFFFFF;
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 0px;
        border: 1.5px solid {BRUTALIST_BORDER};
    }}

    QLabel[class="badge-high"] {{
        background-color: {BRUTALIST_ORANGE};
        color: {BRUTALIST_BLACK};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 0px;
        border: 1.5px solid {BRUTALIST_BORDER};
    }}

    QLabel[class="badge-medium"] {{
        background-color: {BRUTALIST_YELLOW};
        color: {BRUTALIST_BLACK};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 0px;
        border: 1.5px solid {BRUTALIST_BORDER};
    }}

    QLabel[class="badge-low"] {{
        background-color: {BRUTALIST_COBALT};
        color: #FFFFFF;
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 0px;
        border: 1.5px solid {BRUTALIST_BORDER};
    }}

    QLabel[class="badge-clean"] {{
        background-color: {BRUTALIST_GREEN};
        color: {BRUTALIST_BLACK};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: 0px;
        border: 1.5px solid {BRUTALIST_BORDER};
    }}

    /* =========================================================================
       3. BUTTON HIERARCHY (NEO-BRUTALIST)
       ========================================================================= */
    /* Secondary (Default) Button */
    QPushButton {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        padding: 6px 14px;
        font-size: 9.5pt;
        font-weight: 700;
        min-height: 24px;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {BRUTALIST_SURFACE_ALT};
        border-color: {BRUTALIST_BORDER};
    }}
    QPushButton:pressed {{
        background-color: {BRUTALIST_BG_SECONDARY};
        border-color: {BRUTALIST_BORDER};
    }}
    QPushButton:focus {{
        border: 2px solid {BRUTALIST_BLACK};
    }}
    QPushButton:disabled {{
        background-color: #E2DFD6;
        color: #8C887E;
        border-color: #8C887E;
    }}

    /* Primary Action Button (Signature Yellow) */
    QPushButton[class="primary"] {{
        background-color: {BRUTALIST_YELLOW};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        font-weight: 800;
        padding: 6px 16px;
    }}
    QPushButton[class="primary"]:hover {{
        background-color: {BRUTALIST_YELLOW_BRIGHT};
        border-color: {BRUTALIST_BORDER};
    }}
    QPushButton[class="primary"]:pressed {{
        background-color: #E6CE00;
        border-color: {BRUTALIST_BORDER};
    }}
    QPushButton[class="primary"]:focus {{
        border: 2.5px solid {BRUTALIST_BLACK};
    }}
    QPushButton[class="primary"]:disabled {{
        background-color: #E2DFD6;
        color: #8C887E;
        border-color: #8C887E;
    }}

    /* Danger / Terminate Button */
    QPushButton[class="danger"] {{
        background-color: {BRUTALIST_RED};
        color: #FFFFFF;
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        font-weight: 800;
        padding: 6px 14px;
    }}
    QPushButton[class="danger"]:hover {{
        background-color: #E02E2E;
    }}
    QPushButton[class="danger"]:pressed {{
        background-color: #C01B1B;
    }}
    QPushButton[class="danger"]:focus {{
        border: 2.5px solid {BRUTALIST_BLACK};
    }}

    /* Icon-Only Buttons */
    QPushButton[class="icon-only"] {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        padding: 4px;
        min-width: 32px;
        max-width: 36px;
        min-height: 32px;
        max-height: 36px;
        font-size: 11pt;
        font-weight: bold;
    }}
    QPushButton[class="icon-only"]:hover {{
        background-color: {BRUTALIST_YELLOW};
        color: {BRUTALIST_BLACK};
    }}
    QPushButton[class="icon-only"]:pressed {{
        background-color: {BRUTALIST_SURFACE_ALT};
    }}

    /* Sidebar Navigation Button */
    QPushButton[class="nav-btn"] {{
        background-color: transparent;
        color: {BRUTALIST_BLACK};
        border: none;
        border-left: 4px solid transparent;
        border-radius: 0px;
        padding: 8px 14px;
        font-size: 10pt;
        font-weight: 700;
        text-align: left;
        min-height: 26px;
    }}
    QPushButton[class="nav-btn"]:hover {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border-left: 4px solid {BRUTALIST_BORDER};
    }}
    QPushButton[class="nav-btn"]:checked {{
        background-color: {BRUTALIST_YELLOW};
        color: {BRUTALIST_BLACK};
        font-weight: 800;
        border: 2px solid {BRUTALIST_BORDER};
        border-left: 6px solid {BRUTALIST_BORDER};
    }}
    QPushButton[class="nav-btn"]:focus {{
        outline: none;
    }}

    /* =========================================================================
       4. FORM CONTROLS & INPUT WELLS
       ========================================================================= */
    QLineEdit {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        padding: 6px 10px;
        font-size: 9.5pt;
        min-height: 24px;
    }}
    QLineEdit:hover {{
        border-color: {BRUTALIST_BORDER};
        background-color: #FFFFFA;
    }}
    QLineEdit:focus {{
        border: 2.5px solid {BRUTALIST_BLACK};
        background-color: {BRUTALIST_SURFACE};
    }}
    QLineEdit:disabled {{
        background-color: #E2DFD6;
        color: #8C887E;
        border-color: #8C887E;
    }}
    QLineEdit[class="error"] {{
        border: 2.5px solid {BRUTALIST_RED};
        background-color: #FFF0F0;
    }}
    QLineEdit[class="success"] {{
        border: 2.5px solid {BRUTALIST_GREEN};
    }}

    QComboBox {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        padding: 6px 12px;
        font-size: 9.5pt;
        font-weight: 600;
        min-height: 24px;
    }}
    QComboBox:hover {{
        border-color: {BRUTALIST_BORDER};
        background-color: {BRUTALIST_SURFACE_ALT};
    }}
    QComboBox:focus {{
        border: 2.5px solid {BRUTALIST_BLACK};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 26px;
        border-left: 2px solid {BRUTALIST_BORDER};
    }}
    QComboBox QAbstractItemView {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        selection-background-color: {BRUTALIST_YELLOW};
        selection-color: {BRUTALIST_BLACK};
        padding: 4px;
        outline: none;
    }}

    QSpinBox {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        padding: 6px 10px;
        font-size: 9.5pt;
        font-weight: 600;
        min-height: 24px;
    }}

    QCheckBox {{
        color: {BRUTALIST_BLACK};
        font-size: 9.5pt;
        font-weight: 600;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        background-color: {BRUTALIST_SURFACE};
    }}
    QCheckBox::indicator:hover {{
        background-color: {BRUTALIST_SURFACE_ALT};
    }}
    QCheckBox::indicator:checked {{
        background-color: {BRUTALIST_YELLOW};
        image: none;
    }}

    QRadioButton {{
        color: {BRUTALIST_BLACK};
        font-size: 9.5pt;
        font-weight: 600;
        spacing: 8px;
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        background-color: {BRUTALIST_SURFACE};
    }}
    QRadioButton::indicator:checked {{
        background-color: {BRUTALIST_YELLOW};
    }}

    /* =========================================================================
       5. STACKED WIDGET & CONTAINERS
       ========================================================================= */
    QStackedWidget {{
        background-color: {t.bg_base};
        border: none;
    }}

    QSplitter::handle {{
        background-color: {BRUTALIST_BORDER};
        width: 4px;
    }}

    /* =========================================================================
       6. NEO-BRUTALIST SCROLLBARS (10px Width with Black Border)
       ========================================================================= */
    QScrollBar:vertical {{
        background-color: {t.bg_base};
        width: 12px;
        margin: 0px;
        border-left: 2px solid {BRUTALIST_BORDER};
    }}
    QScrollBar::handle:vertical {{
        background-color: {BRUTALIST_YELLOW};
        min-height: 30px;
        border: 1px solid {BRUTALIST_BORDER};
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {BRUTALIST_BLACK};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background-color: {t.bg_base};
        height: 12px;
        margin: 0px;
        border-top: 2px solid {BRUTALIST_BORDER};
    }}
    QScrollBar::handle:horizontal {{
        background-color: {BRUTALIST_YELLOW};
        min-width: 30px;
        border: 1px solid {BRUTALIST_BORDER};
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {BRUTALIST_BLACK};
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
    }}

    /* =========================================================================
       7. STATUS BAR & TOOLTIPS
       ========================================================================= */
    QStatusBar {{
        background-color: {t.bg_surface};
        color: {BRUTALIST_BLACK};
        border-top: 2px solid {BRUTALIST_BORDER};
        font-size: 9pt;
        font-weight: 700;
        padding: 3px 12px;
        min-height: 26px;
    }}
    QStatusBar::item {{
        border: none;
        padding: 0 6px;
    }}

    QToolTip {{
        background-color: {BRUTALIST_SURFACE_ALT};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        padding: 6px 10px;
        font-size: 8.5pt;
        font-weight: 600;
    }}

    /* =========================================================================
       8. DATA TABLES & PROGRESS METRICS
       ========================================================================= */
    QTableView {{
        background-color: {BRUTALIST_SURFACE};
        alternate-background-color: {BRUTALIST_SURFACE_ALT};
        gridline-color: {BRUTALIST_BORDER};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        color: {BRUTALIST_BLACK};
        selection-background-color: {BRUTALIST_YELLOW};
        selection-color: {BRUTALIST_BLACK};
        font-size: 9.5pt;
    }}
    QHeaderView::section {{
        background-color: {BRUTALIST_YELLOW};
        color: {BRUTALIST_BLACK};
        font-weight: 800;
        font-size: 9pt;
        padding: 6px 10px;
        border: 1px solid {BRUTALIST_BORDER};
        border-bottom: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
    }}

    QProgressBar {{
        background-color: {t.bg_surface};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        height: 14px;
        text-align: center;
        color: {BRUTALIST_BLACK};
        font-weight: bold;
        font-size: 8pt;
    }}
    QProgressBar::chunk {{
        background-color: {BRUTALIST_YELLOW};
        border-right: 2px solid {BRUTALIST_BORDER};
    }}

    /* =========================================================================
       9. DIALOGS & POPUPS
       ========================================================================= */
    QDialog {{
        background-color: {t.bg_base};
        border: 2px solid {BRUTALIST_BORDER};
    }}

    QMessageBox {{
        background-color: {t.bg_base};
        border: 2px solid {BRUTALIST_BORDER};
    }}

    QMenu {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        font-weight: 600;
    }}
    QMenu::item:selected {{
        background-color: {BRUTALIST_YELLOW};
        color: {BRUTALIST_BLACK};
    }}

    QPlainTextEdit, QTextEdit {{
        background-color: {BRUTALIST_SURFACE};
        color: {BRUTALIST_BLACK};
        border: 2px solid {BRUTALIST_BORDER};
        border-radius: 0px;
        font-family: {t.font_mono};
        font-size: 9.5pt;
        padding: 6px;
    }}
    """


def polish_widget(widget: QWidget, class_name: str | None = None) -> None:
    """
    Forces Qt style re-evaluation on dynamic property changes.

    Args:
        widget: Target QWidget.
        class_name: Optional class string to set before re-polishing.
    """
    if class_name is not None:
        widget.setProperty("class", class_name)
    style = widget.style()
    if style:
        style.unpolish(widget)
        style.polish(widget)
