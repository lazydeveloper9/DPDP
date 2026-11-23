"""
Aadhaar Validator (12-digit Indian National Identity)
=====================================================
Uses the Verhoeff dihedral D5 checksum algorithm.
Aadhaar numbers are 12 digits: 11 data digits + 1 Verhoeff check digit.
First digit is never 0 or 1.
"""

from __future__ import annotations
import re

_D_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_P_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_INV_TABLE = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

def verhoeff_check(number_str: str) -> bool:
    """Validate a numeric string against the Verhoeff algorithm."""
    c = 0
    reversed_digits = [int(ch) for ch in reversed(number_str)]
    for i, digit in enumerate(reversed_digits):
        c = _D_TABLE[c][_P_TABLE[i % 8][digit]]
    return c == 0

def generate_verhoeff_check_digit(number_str: str) -> int:
    """Generate the Verhoeff check digit for an 11-digit prefix."""
    c = 0
    reversed_digits = [int(ch) for ch in reversed(number_str)]
    for i, digit in enumerate(reversed_digits):
        c = _D_TABLE[c][_P_TABLE[(i + 1) % 8][digit]]
    return _INV_TABLE[c]

def validate_aadhaar(candidate: str) -> tuple[bool, str]:
    """
    Validate a potential Aadhaar number candidate string.
    Returns (is_valid, reason).
    """
    cleaned = re.sub(r"[\s\-]", "", candidate)

    if not cleaned.isdigit():
        return False, "contains_non_digits"

    if len(cleaned) != 12:
        return False, "invalid_length"

    if cleaned[0] in ("0", "1"):
        return False, "invalid_starting_digit"

    if len(set(cleaned)) == 1:
        return False, "repetitive_digits"

    if not verhoeff_check(cleaned):
        return False, "verhoeff_checksum_failed"

    return True, "valid"
