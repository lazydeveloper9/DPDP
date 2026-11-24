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
    Integrates dynamic theme tokens from ThemeManager while preserving full backward
    compatibility with Theme dataclass overrides.
    """
    t = theme or DEFAULT_THEME

    # Dynamic token resolution via ThemeManager if available
    try:
        from cs01.gui.theme_engine.theme_manager import ThemeManager
        tm = ThemeManager.instance()
        bg_main = str(tm.get_token("global.bg.main", t.bg_base))
        bg_sec = str(tm.get_token("global.bg.secondary", t.bg_surface))
        card_bg = str(tm.get_token("component.card.bg", BRUTALIST_SURFACE))
        card_alt_bg = str(tm.get_token("global.bg.card_secondary", BRUTALIST_SURFACE_ALT))
        card_hover_bg = str(tm.get_token("component.card.hover_bg", BRUTALIST_SURFACE_ALT))
        text_primary = str(tm.get_token("global.text.primary", t.text_primary))
        text_sec = str(tm.get_token("global.text.secondary", BRUTALIST_BLACK_SEC))
        text_muted = str(tm.get_token("global.text.muted", BRUTALIST_MUTED))
        text_inverse = str(tm.get_token("global.text.inverse", "#FFFFFF"))
        border_col = str(tm.get_token("design.border.color", BRUTALIST_BORDER))
        border_width = int(tm.get_token("design.border.width", 2))
        corner_radius = int(tm.get_token("design.corner.radius", 0))
        accent_yellow = str(tm.get_token("global.accent.primary", BRUTALIST_YELLOW))
        accent_cobalt = str(tm.get_token("global.accent.secondary", BRUTALIST_COBALT))
        selection_bg = str(tm.get_token("global.selection.bg", BRUTALIST_YELLOW))
        selection_text = str(tm.get_token("global.selection.text", BRUTALIST_BLACK))
        
        btn_pri_bg = str(tm.get_token("component.button.primary.bg", BRUTALIST_YELLOW))
        btn_pri_text = str(tm.get_token("component.button.primary.text", BRUTALIST_BLACK))
        btn_pri_hover = str(tm.get_token("component.button.primary.hover_bg", BRUTALIST_YELLOW_BRIGHT))
        btn_sec_bg = str(tm.get_token("component.button.secondary.bg", BRUTALIST_SURFACE))
        btn_sec_text = str(tm.get_token("component.button.secondary.text", BRUTALIST_BLACK))
        btn_sec_hover = str(tm.get_token("component.button.secondary.hover_bg", BRUTALIST_SURFACE_ALT))
        btn_dan_bg = str(tm.get_token("component.button.danger.bg", BRUTALIST_RED))
        btn_dan_text = str(tm.get_token("component.button.danger.text", "#FFFFFF"))
        btn_dan_hover = str(tm.get_token("component.button.danger.hover_bg", "#E02E2E"))

        sidebar_bg = str(tm.get_token("component.sidebar.bg", t.bg_surface))
        sidebar_active_bg = str(tm.get_token("component.sidebar.active_bg", BRUTALIST_YELLOW))
        sidebar_active_text = str(tm.get_token("component.sidebar.active_text", BRUTALIST_BLACK))
        sidebar_hover_bg = str(tm.get_token("component.sidebar.hover_bg", BRUTALIST_SURFACE))

        table_hdr_bg = str(tm.get_token("component.table.header_bg", BRUTALIST_YELLOW))
        table_hdr_text = str(tm.get_token("component.table.header_text", BRUTALIST_BLACK))
        table_row_bg = str(tm.get_token("component.table.row_bg", BRUTALIST_SURFACE))
        table_row_alt = str(tm.get_token("component.table.row_alt_bg", BRUTALIST_SURFACE_ALT))
        table_sel_bg = str(tm.get_token("component.table.selected_row_bg", BRUTALIST_YELLOW))
        table_cell_text = str(tm.get_token("component.table.cell_text", BRUTALIST_BLACK))

        input_bg = str(tm.get_token("component.input.bg", BRUTALIST_SURFACE))
        input_text = str(tm.get_token("component.input.text", BRUTALIST_BLACK))
        input_border = str(tm.get_token("component.input.border", border_col))
        input_focus = str(tm.get_token("component.input.focus_border", BRUTALIST_BLACK))

        status_crit = str(tm.get_token("status.critical", BRUTALIST_RED))
        status_high = str(tm.get_token("status.high", BRUTALIST_ORANGE))
        status_med = str(tm.get_token("status.medium", BRUTALIST_YELLOW))
        status_low = str(tm.get_token("status.low", BRUTALIST_COBALT))
        status_succ = str(tm.get_token("status.success", BRUTALIST_GREEN))

        font_sans = str(tm.get_token("typography.font_sans", t.font_sans))
        font_mono = str(tm.get_token("typography.font_mono", t.font_mono))
        size_h1 = int(tm.get_token("typography.size_h1", 18))
        size_h2 = int(tm.get_token("typography.size_h2", 13))
        size_h3 = int(tm.get_token("typography.size_h3", 11))
        size_body = int(tm.get_token("typography.size_body", 10))
    except Exception:
        bg_main = t.bg_base
        bg_sec = t.bg_surface
        card_bg = BRUTALIST_SURFACE
        card_alt_bg = BRUTALIST_SURFACE_ALT
        card_hover_bg = BRUTALIST_SURFACE_ALT
        text_primary = t.text_primary
        text_sec = BRUTALIST_BLACK_SEC
        text_muted = BRUTALIST_MUTED
        text_inverse = "#FFFFFF"
        border_col = BRUTALIST_BORDER
        border_width = 2
        corner_radius = 0
        accent_yellow = BRUTALIST_YELLOW
        accent_cobalt = BRUTALIST_COBALT
        selection_bg = BRUTALIST_YELLOW
        selection_text = BRUTALIST_BLACK
        btn_pri_bg = BRUTALIST_YELLOW
        btn_pri_text = BRUTALIST_BLACK
        btn_pri_hover = BRUTALIST_YELLOW_BRIGHT
        btn_sec_bg = BRUTALIST_SURFACE
        btn_sec_text = BRUTALIST_BLACK
        btn_sec_hover = BRUTALIST_SURFACE_ALT
        btn_dan_bg = BRUTALIST_RED
        btn_dan_text = "#FFFFFF"
        btn_dan_hover = "#E02E2E"
        sidebar_bg = t.bg_surface
        sidebar_active_bg = BRUTALIST_YELLOW
        sidebar_active_text = BRUTALIST_BLACK
        sidebar_hover_bg = BRUTALIST_SURFACE
        table_hdr_bg = BRUTALIST_YELLOW
        table_hdr_text = BRUTALIST_BLACK
        table_row_bg = BRUTALIST_SURFACE
        table_row_alt = BRUTALIST_SURFACE_ALT
        table_sel_bg = BRUTALIST_YELLOW
        table_cell_text = BRUTALIST_BLACK
        input_bg = BRUTALIST_SURFACE
        input_text = BRUTALIST_BLACK
        input_border = BRUTALIST_BORDER
        input_focus = BRUTALIST_BLACK
        status_crit = BRUTALIST_RED
        status_high = BRUTALIST_ORANGE
        status_med = BRUTALIST_YELLOW
        status_low = BRUTALIST_COBALT
        status_succ = BRUTALIST_GREEN
        font_sans = t.font_sans
        font_mono = t.font_mono
        size_h1 = 18
        size_h2 = 13
        size_h3 = 11
        size_body = 10

    return f"""
    /* =========================================================================
       1. GLOBAL APPLICATION CANVAS & BASE WIDGETS
       /* Fallback/Legacy Dark Canvas: #090d16 */
       ========================================================================= */
    QMainWindow {{
        background-color: {bg_main};
        border: none;
    }}

    QWidget {{
        background-color: {bg_main};
        color: {text_primary};
        font-family: {font_sans};
        font-size: {size_body}pt;
        selection-background-color: {selection_bg};
        selection-color: {selection_text};
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
        background-color: {card_bg};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
    }}

    QFrame[class="card-interactive"] {{
        background-color: {card_bg};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
    }}
    QFrame[class="card-interactive"]:hover {{
        background-color: {card_hover_bg};
        border: {border_width}px solid {border_col};
    }}

    QFrame[class="card-alt"] {{
        background-color: {card_alt_bg};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
    }}

    QFrame[class="hud"] {{
        background-color: {bg_sec};
        border-bottom: {border_width}px solid {border_col};
    }}

    QFrame[class="sidebar"] {{
        background-color: {sidebar_bg};
        border-right: {border_width}px solid {sidebar_hover_bg or border_col};
    }}

    /* =========================================================================
       2. TYPOGRAPHY & LABELS
       ========================================================================= */
    QLabel {{
        color: {text_primary};
        background-color: transparent;
        font-size: {size_body}pt;
    }}

    QLabel[class="hud-title"] {{
        font-size: {size_h2}pt;
        font-weight: 800;
        color: {text_primary};
        letter-spacing: -0.3px;
    }}

    QLabel[class="h1"] {{
        font-size: {size_h1}pt;
        font-weight: 800;
        color: {text_primary};
        letter-spacing: -0.5px;
    }}

    QLabel[class="h2"] {{
        font-size: {size_h2}pt;
        font-weight: 700;
        color: {text_primary};
    }}

    QLabel[class="h3"] {{
        font-size: {size_h3}pt;
        font-weight: 700;
        color: {text_primary};
    }}

    QLabel[class="text-secondary"] {{
        color: {text_sec};
        font-size: 9.5pt;
        font-weight: 500;
    }}

    QLabel[class="text-muted"] {{
        color: {text_muted};
        font-size: 8.5pt;
        font-weight: 600;
    }}

    QLabel[class="code-text"] {{
        font-family: {font_mono};
        font-size: 9.5pt;
        font-weight: 600;
        color: {text_primary};
        background-color: {card_alt_bg};
        border: 1px solid {border_col};
        padding: 2px 4px;
    }}

    /* Badges */
    QLabel[class="badge-version"] {{
        background-color: {accent_yellow};
        color: {text_primary};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 3px 8px;
        border-radius: {corner_radius}px;
        border: 1.5px solid {border_col};
    }}

    QLabel[class="badge-privacy"] {{
        background-color: {status_succ};
        color: {text_primary};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 4px 10px;
        border-radius: {corner_radius}px;
        border: {border_width}px solid {border_col};
    }}

    QLabel[class="badge-critical"] {{
        background-color: {status_crit};
        color: {text_inverse};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: {corner_radius}px;
        border: 1.5px solid {border_col};
    }}

    QLabel[class="badge-high"] {{
        background-color: {status_high};
        color: {text_primary};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: {corner_radius}px;
        border: 1.5px solid {border_col};
    }}

    QLabel[class="badge-medium"] {{
        background-color: {status_med};
        color: {text_primary};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: {corner_radius}px;
        border: 1.5px solid {border_col};
    }}

    QLabel[class="badge-low"] {{
        background-color: {status_low};
        color: {text_inverse};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: {corner_radius}px;
        border: 1.5px solid {border_col};
    }}

    QLabel[class="badge-clean"] {{
        background-color: {status_succ};
        color: {text_primary};
        font-size: 8.5pt;
        font-weight: 800;
        padding: 2px 8px;
        border-radius: {corner_radius}px;
        border: 1.5px solid {border_col};
    }}

    /* =========================================================================
       3. BUTTON HIERARCHY (NEO-BRUTALIST)
       ========================================================================= */
    /* Secondary (Default) Button */
    QPushButton {{
        background-color: {btn_sec_bg};
        color: {btn_sec_text};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        padding: 6px 14px;
        font-size: 9.5pt;
        font-weight: 700;
        min-height: 24px;
        outline: none;
    }}
    QPushButton:hover {{
        background-color: {btn_sec_hover};
        border-color: {border_col};
    }}
    QPushButton:pressed {{
        background-color: {bg_sec};
        border-color: {border_col};
    }}
    QPushButton:focus {{
        border: {border_width}px solid {border_col};
    }}
    QPushButton:disabled {{
        background-color: #E2DFD6;
        color: #8C887E;
        border-color: #8C887E;
    }}

    /* Primary Action Button (Signature Accent) */
    QPushButton[class="primary"] {{
        background-color: {btn_pri_bg};
        color: {btn_pri_text};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        font-weight: 800;
        padding: 6px 16px;
    }}
    QPushButton[class="primary"]:hover {{
        background-color: {btn_pri_hover};
        border-color: {border_col};
    }}
    QPushButton[class="primary"]:pressed {{
        background-color: #E6CE00;
        border-color: {border_col};
    }}
    QPushButton[class="primary"]:focus {{
        border: 2.5px solid {border_col};
    }}
    QPushButton[class="primary"]:disabled {{
        background-color: #E2DFD6;
        color: #8C887E;
        border-color: #8C887E;
    }}

    /* Danger / Terminate Button */
    QPushButton[class="danger"] {{
        background-color: {btn_dan_bg};
        color: {btn_dan_text};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        font-weight: 800;
        padding: 6px 14px;
    }}
    QPushButton[class="danger"]:hover {{
        background-color: {btn_dan_hover};
    }}
    QPushButton[class="danger"]:pressed {{
        background-color: #C01B1B;
    }}
    QPushButton[class="danger"]:focus {{
        border: 2.5px solid {border_col};
    }}

    /* Icon-Only Buttons */
    QPushButton[class="icon-only"] {{
        background-color: {btn_sec_bg};
        color: {btn_sec_text};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        padding: 4px;
        min-width: 32px;
        max-width: 36px;
        min-height: 32px;
        max-height: 36px;
        font-size: 11pt;
        font-weight: bold;
    }}
    QPushButton[class="icon-only"]:hover {{
        background-color: {accent_yellow};
        color: {btn_sec_text};
    }}
    QPushButton[class="icon-only"]:pressed {{
        background-color: {card_alt_bg};
    }}

    /* Sidebar Navigation Button */
    QPushButton[class="nav-btn"] {{
        background-color: transparent;
        color: {text_primary};
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
        background-color: {sidebar_hover_bg};
        color: {text_primary};
        border-left: 4px solid {border_col};
    }}
    QPushButton[class="nav-btn"]:checked {{
        background-color: {sidebar_active_bg};
        color: {sidebar_active_text};
        font-weight: 800;
        border: {border_width}px solid {border_col};
        border-left: 6px solid {border_col};
    }}
    QPushButton[class="nav-btn"]:focus {{
        outline: none;
    }}

    /* =========================================================================
       4. FORM CONTROLS & INPUT WELLS
       ========================================================================= */
    QLineEdit {{
        background-color: {input_bg};
        color: {input_text};
        border: {border_width}px solid {input_border};
        border-radius: {corner_radius}px;
        padding: 6px 10px;
        font-size: 9.5pt;
        min-height: 24px;
    }}
    QLineEdit:hover {{
        border-color: {input_border};
        background-color: #FFFFFA;
    }}
    QLineEdit:focus {{
        border: 2.5px solid {input_focus};
        background-color: {input_bg};
    }}
    QLineEdit:disabled {{
        background-color: #E2DFD6;
        color: #8C887E;
        border-color: #8C887E;
    }}
    QLineEdit[class="error"] {{
        border: 2.5px solid {status_crit};
        background-color: #FFF0F0;
    }}
    QLineEdit[class="success"] {{
        border: 2.5px solid {status_succ};
    }}

    QComboBox {{
        background-color: {input_bg};
        color: {input_text};
        border: {border_width}px solid {input_border};
        border-radius: {corner_radius}px;
        padding: 6px 12px;
        font-size: 9.5pt;
        font-weight: 600;
        min-height: 24px;
    }}
    QComboBox:hover {{
        border-color: {input_border};
        background-color: {card_alt_bg};
    }}
    QComboBox:focus {{
        border: 2.5px solid {input_focus};
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 26px;
        border-left: {border_width}px solid {input_border};
    }}
    QComboBox QAbstractItemView {{
        background-color: {input_bg};
        color: {input_text};
        border: {border_width}px solid {input_border};
        border-radius: {corner_radius}px;
        selection-background-color: {selection_bg};
        selection-color: {selection_text};
        padding: 4px;
        outline: none;
    }}

    QSpinBox {{
        background-color: {input_bg};
        color: {input_text};
        border: {border_width}px solid {input_border};
        border-radius: {corner_radius}px;
        padding: 6px 10px;
        font-size: 9.5pt;
        font-weight: 600;
        min-height: 24px;
    }}

    QCheckBox {{
        color: {text_primary};
        font-size: 9.5pt;
        font-weight: 600;
        spacing: 8px;
    }}
    QCheckBox::indicator {{
        width: 18px;
        height: 18px;
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        background-color: {input_bg};
    }}
    QCheckBox::indicator:hover {{
        background-color: {card_alt_bg};
    }}
    QCheckBox::indicator:checked {{
        background-color: {accent_yellow};
        image: none;
    }}

    QRadioButton {{
        color: {text_primary};
        font-size: 9.5pt;
        font-weight: 600;
        spacing: 8px;
    }}
    QRadioButton::indicator {{
        width: 18px;
        height: 18px;
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        background-color: {input_bg};
    }}
    QRadioButton::indicator:checked {{
        background-color: {accent_yellow};
    }}

    /* =========================================================================
       5. STACKED WIDGET & CONTAINERS
       ========================================================================= */
    QStackedWidget {{
        background-color: {bg_main};
        border: none;
    }}

    QSplitter::handle {{
        background-color: {border_col};
        width: 4px;
    }}

    /* =========================================================================
       6. NEO-BRUTALIST SCROLLBARS (10px Width with Black Border)
       ========================================================================= */
    QScrollBar:vertical {{
        background-color: {bg_main};
        width: 12px;
        margin: 0px;
        border-left: {border_width}px solid {border_col};
    }}
    QScrollBar::handle:vertical {{
        background-color: {accent_yellow};
        min-height: 30px;
        border: 1px solid {border_col};
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {border_col};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
    }}

    QScrollBar:horizontal {{
        background-color: {bg_main};
        height: 12px;
        margin: 0px;
        border-top: {border_width}px solid {border_col};
    }}
    QScrollBar::handle:horizontal {{
        background-color: {accent_yellow};
        min-width: 30px;
        border: 1px solid {border_col};
    }}
    QScrollBar::handle:horizontal:hover {{
        background-color: {border_col};
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
        background-color: {bg_sec};
        color: {text_primary};
        border-top: {border_width}px solid {border_col};
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
        background-color: {card_alt_bg};
        color: {text_primary};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        padding: 6px 10px;
        font-size: 8.5pt;
        font-weight: 600;
    }}

    /* =========================================================================
       8. DATA TABLES & PROGRESS METRICS
       ========================================================================= */
    QTableView {{
        background-color: {table_row_bg};
        alternate-background-color: {table_row_alt};
        gridline-color: {border_col};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        color: {table_cell_text};
        selection-background-color: {table_sel_bg};
        selection-color: {selection_text};
        font-size: 9.5pt;
    }}
    QHeaderView::section {{
        background-color: {table_hdr_bg};
        color: {table_hdr_text};
        font-weight: 800;
        font-size: 9pt;
        padding: 6px 10px;
        border: 1px solid {border_col};
        border-bottom: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
    }}

    QProgressBar {{
        background-color: {bg_sec};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        height: 14px;
        text-align: center;
        color: {text_primary};
        font-weight: bold;
        font-size: 8pt;
    }}
    QProgressBar::chunk {{
        background-color: {accent_yellow};
        border-right: {border_width}px solid {border_col};
    }}

    /* =========================================================================
       9. DIALOGS & POPUPS
       ========================================================================= */
    QDialog {{
        background-color: {bg_main};
        border: {border_width}px solid {border_col};
    }}

    QMessageBox {{
        background-color: {bg_main};
        border: {border_width}px solid {border_col};
    }}

    QMenu {{
        background-color: {card_bg};
        color: {text_primary};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        padding: 4px;
    }}
    QMenu::item {{
        padding: 6px 20px;
        font-weight: 600;
    }}
    QMenu::item:selected {{
        background-color: {selection_bg};
        color: {selection_text};
    }}

    QPlainTextEdit, QTextEdit {{
        background-color: {card_bg};
        color: {text_primary};
        border: {border_width}px solid {border_col};
        border-radius: {corner_radius}px;
        font-family: {font_mono};
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
