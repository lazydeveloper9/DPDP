import pytest
from cs01.pipeline.stage3_detect.validators.gstin import validate_gstin, gstin_luhn_check


def test_validate_gstin():
    # Example GSTIN structure: 27 (Maharashtra) + AAAAA0001A (valid PAN) + 1 + Z + check char
    prefix_14 = "27AAAAA0001A1Z"
    
    # Calculate expected check char
    from cs01.pipeline.stage3_detect.validators.gstin import CHARS_MOD36
    factor = 2
    total = 0
    mod = len(CHARS_MOD36)
    for ch in reversed(prefix_14):
        val = CHARS_MOD36.index(ch)
        product = val * factor
        total += (product // mod) + (product % mod)
        factor = 1 if factor == 2 else 2
    rem = total % mod
    code = (mod - rem) % mod
    check_char = CHARS_MOD36[code]
    valid_gstin = prefix_14 + check_char

    is_valid, reason = validate_gstin(valid_gstin)
    assert is_valid is True
    assert reason == "valid"

    # Test invalid state code 98
    invalid_state = "98" + valid_gstin[2:]
    assert validate_gstin(invalid_state)[0] is False

    # Test corrupted check character
    corrupted = valid_gstin[:14] + ("0" if valid_gstin[14] != "0" else "1")
    assert validate_gstin(corrupted)[0] is False
