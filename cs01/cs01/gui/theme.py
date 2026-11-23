"""
CS-01 DPDP Compliance Desktop GUI - Design Tokens & Theme Specification.

Defines the Dark Corporate Governance semantic tokens, typography hierarchy,
spacing metrics, and DPDP Act 2023 statutory risk color accents.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

# ============================================================================
# 1. COLOR TOKENS (DARK CORPORATE GOVERNANCE PALETTE)
# ============================================================================

# Canvas & Background Depths
COLOR_BG_BASE: Final[str] = "#090d16"          # Deepest window background
COLOR_BG_SURFACE: Final[str] = "#0f172a"       # Sidebar, Top HUD, Headers
COLOR_BG_CARD: Final[str] = "#1e293b"          # Metric cards, tiles, dialog wells
COLOR_BG_CARD_HOVER: Final[str] = "#273549"    # Interactive card hover state
COLOR_BG_INPUT: Final[str] = "#070a10"         # Text fields, combo boxes, code wells

# Borders & Separators
COLOR_BORDER_SUBTLE: Final[str] = "#334155"     # Standard container borders & grid lines
COLOR_BORDER_STRONG: Final[str] = "#475569"     # Focus outlines, dividers, active tabs
COLOR_BORDER_FOCUS: Final[str] = "#38bdf8"      # Keyboard focus ring (trust cyan)
COLOR_BORDER_ERROR: Final[str] = "#ef4444"      # Input validation error border

# Typography / Foregrounds (WCAG AAA Compliant)
COLOR_TEXT_PRIMARY: Final[str] = "#f8fafc"     # High-contrast headings, values (>17:1)
COLOR_TEXT_SECONDARY: Final[str] = "#94a3b8"   # Field labels, descriptions, captions (>6.9:1)
COLOR_TEXT_MUTED: Final[str] = "#64748b"       # Placeholders, inactive hints, disabled text
COLOR_TEXT_INVERSE: Final[str] = "#090d16"     # Text on bright accent badges
COLOR_TEXT_WHITE: Final[str] = "#ffffff"       # Text on primary & danger buttons

# Brand & Primary Interactive Accents
COLOR_ACCENT_BLUE: Final[str] = "#38bdf8"       # Sky cyan: brand shield, focus rings, highlights
COLOR_ACCENT_ROYAL: Final[str] = "#2563eb"      # Royal blue: primary call-to-action buttons
COLOR_ACCENT_ROYAL_HOVER: Final[str] = "#1d4ed8"# Hover state for primary buttons
COLOR_ACCENT_ROYAL_PRESSED: Final[str] = "#1e40af" # Pressed state for primary buttons

# DPDP Statutory Penalty Ceilings & Risk Accents (Schedule to DPDP Act 2023)
# Band 1: Section 8(5) - Reasonable Security Safeguards (Max ₹250 Crore)
COLOR_RISK_CRITICAL: Final[str] = "#ef4444"
COLOR_RISK_CRITICAL_BG: Final[str] = "rgba(239, 68, 68, 0.15)"
COLOR_RISK_CRITICAL_BTN: Final[str] = "#dc2626"
COLOR_RISK_CRITICAL_HOVER: Final[str] = "#b91c1c"

# Band 2 & 3: Section 9 (Children) & Section 8(6) (Breach Reporting) (Max ₹200 Crore)
COLOR_RISK_HIGH: Final[str] = "#f97316"
COLOR_RISK_HIGH_BG: Final[str] = "rgba(249, 115, 22, 0.15)"

# Band 4: Section 10 - Significant Data Fiduciary Duties (Max ₹150 Crore)
COLOR_RISK_MEDIUM: Final[str] = "#eab308"
COLOR_RISK_MEDIUM_BG: Final[str] = "rgba(234, 179, 8, 0.15)"

# Band 5: Section 33(1) - Residual Statutory Breaches (Max ₹50 Crore)
COLOR_RISK_LOW: Final[str] = "#3b82f6"
COLOR_RISK_LOW_BG: Final[str] = "rgba(59, 130, 246, 0.15)"

# Zero-Egress Status & Clean Compliance Posture
COLOR_STATUS_SUCCESS: Final[str] = "#10b981"
COLOR_STATUS_SUCCESS_BG: Final[str] = "rgba(16, 185, 129, 0.15)"
COLOR_STATUS_INFO: Final[str] = "#38bdf8"
COLOR_STATUS_INFO_BG: Final[str] = "rgba(56, 189, 248, 0.15)"


# ============================================================================
# 2. TYPOGRAPHY HIERARCHY
# ============================================================================

FONT_FAMILY_SANS: Final[str] = (
    '"Segoe UI", "Segoe UI Variable Text", -apple-system, '
    'BlinkMacSystemFont, "Inter", "Helvetica Neue", Arial, sans-serif'
)
FONT_FAMILY_MONO: Final[str] = (
    '"Cascadia Code", "Consolas", "JetBrains Mono", "Courier New", monospace'
)

# Font Size Scale (in points)
FONT_SIZE_DISPLAY: Final[int] = 24    # Readiness Score Ring
FONT_SIZE_H1: Final[int] = 16         # Primary View Titles
FONT_SIZE_H2: Final[int] = 13         # Section Headers, Card Titles
FONT_SIZE_H3: Final[int] = 11         # Group Headers, Subsections
FONT_SIZE_BODY: Final[int] = 10       # Standard UI Labels & Body Copy
FONT_SIZE_CAPTION: Final[float] = 8.5 # Badges, Timestamps, Secondary Meta
FONT_SIZE_CODE: Final[float] = 9.5    # File Paths, Masked PII, JSON

# Font Weights
FONT_WEIGHT_REGULAR: Final[int] = 400
FONT_WEIGHT_MEDIUM: Final[int] = 500
FONT_WEIGHT_SEMIBOLD: Final[int] = 600
FONT_WEIGHT_BOLD: Final[int] = 700


# ============================================================================
# 3. SPACING & GEOMETRY METRICS
# ============================================================================

SPACE_XXS: Final[int] = 2
SPACE_XS: Final[int] = 4
SPACE_SM: Final[int] = 8
SPACE_MD: Final[int] = 12
SPACE_LG: Final[int] = 16
SPACE_XL: Final[int] = 20
SPACE_XXL: Final[int] = 24
SPACE_3XL: Final[int] = 32

RADIUS_NONE: Final[int] = 0
RADIUS_SM: Final[int] = 4
RADIUS_MD: Final[int] = 6
RADIUS_LG: Final[int] = 8
RADIUS_XL: Final[int] = 12
RADIUS_FULL: Final[int] = 9999

# Component Dimensions (in pixels)
HEADER_HUD_HEIGHT: Final[int] = 56
SIDEBAR_WIDTH_EXPANDED: Final[int] = 220
SIDEBAR_WIDTH_COLLAPSED: Final[int] = 64
STATUS_BAR_HEIGHT: Final[int] = 28
NAV_ITEM_HEIGHT: Final[int] = 42
INPUT_CONTROL_HEIGHT: Final[int] = 36
BUTTON_CONTROL_HEIGHT: Final[int] = 36

# Responsive Breakpoints & Window Bounds
BREAKPOINT_COLLAPSE_WIDTH: Final[int] = 1366
WINDOW_MIN_WIDTH: Final[int] = 1024
WINDOW_MIN_HEIGHT: Final[int] = 680
WINDOW_DEFAULT_WIDTH: Final[int] = 1440
WINDOW_DEFAULT_HEIGHT: Final[int] = 900


# ============================================================================
# 4. THEME DATA CLASS
# ============================================================================

@dataclass(frozen=True)
class Theme:
    """Immutable Design Token Specification for CS-01 DPDP Compliance Auditor."""

    # Class-level Constants for WCAG AAA Accessibility & Tests
    COLOR_BG_BASE: Final[str] = COLOR_BG_BASE
    COLOR_BG_SURFACE: Final[str] = COLOR_BG_SURFACE
    COLOR_BG_CARD: Final[str] = COLOR_BG_CARD
    COLOR_TEXT_PRIMARY: Final[str] = COLOR_TEXT_PRIMARY
    COLOR_TEXT_SECONDARY: Final[str] = COLOR_TEXT_SECONDARY
    COLOR_TEXT_MUTED: Final[str] = COLOR_TEXT_MUTED
    COLOR_ACCENT: Final[str] = COLOR_ACCENT_BLUE
    COLOR_SUCCESS: Final[str] = COLOR_STATUS_SUCCESS
    COLOR_WARNING: Final[str] = "#f59e0b"
    COLOR_ERROR: Final[str] = COLOR_RISK_CRITICAL
    COLOR_BORDER: Final[str] = COLOR_BORDER_SUBTLE
    FONT_FAMILY: Final[str] = FONT_FAMILY_SANS
    FONT_MONO: Final[str] = FONT_FAMILY_MONO

    @classmethod
    def get_contrast_ratio(cls, hex1: str = COLOR_TEXT_PRIMARY, hex2: str = COLOR_BG_BASE) -> float:
        """Calculate relative luminance contrast ratio between two hex colors (WCAG 2.1)."""
        def _luminance(hex_str: str) -> float:
            c = hex_str.lstrip("#")
            r, g, b = [int(c[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
            rs = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            gs = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            bs = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs

        l1 = _luminance(hex1)
        l2 = _luminance(hex2)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    # Backgrounds
    bg_base: str = COLOR_BG_BASE
    bg_surface: str = COLOR_BG_SURFACE
    bg_card: str = COLOR_BG_CARD
    bg_card_hover: str = COLOR_BG_CARD_HOVER
    bg_input: str = COLOR_BG_INPUT

    # Borders
    border_subtle: str = COLOR_BORDER_SUBTLE
    border_strong: str = COLOR_BORDER_STRONG
    border_focus: str = COLOR_BORDER_FOCUS
    border_error: str = COLOR_BORDER_ERROR

    # Foregrounds
    text_primary: str = COLOR_TEXT_PRIMARY
    text_secondary: str = COLOR_TEXT_SECONDARY
    text_muted: str = COLOR_TEXT_MUTED
    text_inverse: str = COLOR_TEXT_INVERSE
    text_white: str = COLOR_TEXT_WHITE

    # Accents & Brand
    accent_blue: str = COLOR_ACCENT_BLUE
    accent_royal: str = COLOR_ACCENT_ROYAL
    accent_royal_hover: str = COLOR_ACCENT_ROYAL_HOVER
    accent_royal_pressed: str = COLOR_ACCENT_ROYAL_PRESSED

    # DPDP Statutory Risk Accents
    risk_critical: str = COLOR_RISK_CRITICAL
    risk_critical_bg: str = COLOR_RISK_CRITICAL_BG
    risk_critical_btn: str = COLOR_RISK_CRITICAL_BTN
    risk_critical_hover: str = COLOR_RISK_CRITICAL_HOVER
    risk_high: str = COLOR_RISK_HIGH
    risk_high_bg: str = COLOR_RISK_HIGH_BG
    risk_medium: str = COLOR_RISK_MEDIUM
    risk_medium_bg: str = COLOR_RISK_MEDIUM_BG
    risk_low: str = COLOR_RISK_LOW
    risk_low_bg: str = COLOR_RISK_LOW_BG

    # Status
    status_success: str = COLOR_STATUS_SUCCESS
    status_success_bg: str = COLOR_STATUS_SUCCESS_BG
    status_info: str = COLOR_STATUS_INFO
    status_info_bg: str = COLOR_STATUS_INFO_BG

    # Typography
    font_sans: str = FONT_FAMILY_SANS
    font_mono: str = FONT_FAMILY_MONO

    # Metrics
    sidebar_expanded: int = SIDEBAR_WIDTH_EXPANDED
    sidebar_collapsed: int = SIDEBAR_WIDTH_COLLAPSED
    breakpoint_collapse: int = BREAKPOINT_COLLAPSE_WIDTH
    hud_height: int = HEADER_HUD_HEIGHT
    radius_sm: int = RADIUS_SM
    radius_md: int = RADIUS_MD
    radius_lg: int = RADIUS_LG


DEFAULT_THEME: Final[Theme] = Theme()
