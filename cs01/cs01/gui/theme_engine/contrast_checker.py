"""
CS-01 DPDP Compliance Desktop GUI - WCAG Contrast Checker.

Calculates relative luminance and contrast ratios conforming to WCAG 2.1 AA/AAA specifications.
"""
from __future__ import annotations

import re


class ContrastChecker:
    """WCAG 2.1 Contrast Ratio and Relative Luminance Validator."""

    HEX_REGEX = re.compile(r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})$")

    @classmethod
    def is_valid_hex(cls, hex_str: str) -> bool:
        """Validates if string is a valid #RGB, #RRGGBB, or #RRGGBBAA hex color."""
        if not isinstance(hex_str, str):
            return False
        return bool(cls.HEX_REGEX.match(hex_str.strip()))

    @classmethod
    def parse_rgb(cls, hex_str: str) -> tuple[int, int, int] | None:
        """Extracts RGB integer components (0-255) from hex string."""
        if not cls.is_valid_hex(hex_str):
            return None
        c = hex_str.strip().lstrip("#")
        if len(c) == 3:
            return (
                int(c[0] * 2, 16),
                int(c[1] * 2, 16),
                int(c[2] * 2, 16),
            )
        if len(c) == 6 or len(c) == 8:
            return (
                int(c[0:2], 16),
                int(c[2:4], 16),
                int(c[4:6], 16),
            )
        return None

    @classmethod
    def relative_luminance(cls, hex_str: str) -> float:
        """
        Calculates the relative luminance (0.0 to 1.0) of a color per WCAG 2.1.
        L = 0.2126 * R + 0.7152 * G + 0.0722 * B
        """
        rgb = cls.parse_rgb(hex_str)
        if rgb is None:
            return 0.0
        r, g, b = [val / 255.0 for val in rgb]
        rs = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        gs = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        bs = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs

    @classmethod
    def contrast_ratio(cls, fg_hex: str, bg_hex: str) -> float:
        """
        Calculates contrast ratio (1.0 to 21.0) between foreground and background.
        (L1 + 0.05) / (L2 + 0.05)
        """
        l1 = cls.relative_luminance(fg_hex)
        l2 = cls.relative_luminance(bg_hex)
        lighter = max(l1, l2)
        darker = min(l1, l2)
        return (lighter + 0.05) / (darker + 0.05)

    @classmethod
    def check_wcag_aa(
        cls, fg_hex: str, bg_hex: str, large_text: bool = False
    ) -> tuple[bool, float, str]:
        """
        Evaluates WCAG 2.1 AA compliance.
        Threshold: 4.5:1 for standard text, 3.0:1 for large text (>=18pt or >=14pt bold).
        """
        ratio = cls.contrast_ratio(fg_hex, bg_hex)
        threshold = 3.0 if large_text else 4.5
        passed = ratio >= threshold
        if passed:
            msg = f"Passes WCAG AA ({ratio:.2f}:1 >= {threshold}:1)"
        else:
            msg = f"WARNING: Low contrast ({ratio:.2f}:1 < {threshold}:1 recommended for accessibility)"
        return passed, ratio, msg

    @classmethod
    def check_wcag_aaa(
        cls, fg_hex: str, bg_hex: str, large_text: bool = False
    ) -> tuple[bool, float, str]:
        """
        Evaluates WCAG 2.1 AAA compliance.
        Threshold: 7.0:1 for standard text, 4.5:1 for large text.
        """
        ratio = cls.contrast_ratio(fg_hex, bg_hex)
        threshold = 4.5 if large_text else 7.0
        passed = ratio >= threshold
        if passed:
            msg = f"Passes WCAG AAA ({ratio:.2f}:1 >= {threshold}:1)"
        else:
            msg = f"Fails WCAG AAA ({ratio:.2f}:1 < {threshold}:1)"
        return passed, ratio, msg
