"""
GSTIN Validator (Goods and Services Tax Identification Number)
==============================================================
Structure: 15 alphanumeric characters
  - Chars 1-2: 2-digit State Code (01-38, 97, 99)
  - Chars 3-12: 10-char PAN of the entity
  - Char 13: Entity number of the same PAN holder (1-9, A-Z)
  - Char 14: Default character 'Z'
  - Char 15: Check digit using Luhn mod-36 algorithm
"""

from __future__ import annotations
import re
from .pan import validate_pan

GST_STATE_CODES: set[str] = {
    "01", "02", "03", "04", "05", "06", "07", "08", "09", "10",
    "11", "12", "13", "14", "15", "16", "17", "18", "19", "20",
    "21", "22", "23", "24", "25", "26", "27", "28", "29", "30",
    "31", "32", "33", "34", "35", "36", "37", "38", "97", "99",
}

CHARS_MOD36 = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"

def gstin_luhn_check(gstin: str) -> bool:
    """Compute and verify Luhn mod-36 check character for GSTIN."""
    factor = 2
    total = 0
    mod = len(CHARS_MOD36)

    for ch in reversed(gstin[:14]):
        if ch not in CHARS_MOD36:
            return False
        val = CHARS_MOD36.index(ch)
        product = val * factor
        total += (product // mod) + (product % mod)
        factor = 1 if factor == 2 else 2

    remainder = total % mod
    check_code = (mod - remainder) % mod
    expected_check_char = CHARS_MOD36[check_code]

    return gstin[14] == expected_check_char

def validate_gstin(candidate: str) -> tuple[bool, str]:
    """
    Validate a potential GSTIN string.
    Returns (is_valid, reason).
    """
    cleaned = candidate.strip().upper()

    if len(cleaned) != 15:
        return False, "invalid_length"

    state_code = cleaned[:2]
    if state_code not in GST_STATE_CODES:
        return False, "invalid_state_code"

    pan_part = cleaned[2:12]
    is_pan_valid, _ = validate_pan(pan_part)
    if not is_pan_valid:
        return False, "invalid_embedded_pan"

    if cleaned[13] != "Z":
        return False, "missing_default_z"

    if not gstin_luhn_check(cleaned):
        return False, "gstin_checksum_failed"

    return True, "valid"
