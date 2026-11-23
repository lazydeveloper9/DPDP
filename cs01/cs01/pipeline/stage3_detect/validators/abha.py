import re

def validate_abha(candidate: str) -> tuple[bool, str]:
    """
    Validate an Ayushman Bharat Health Account (ABHA / NDHM Health ID) number.
    Format: 14 digits, typically formatted as 12-3456-7890-1234 or 14 consecutive digits.
    Returns (is_valid, reason).
    """
    cleaned = re.sub(r"[\s\-]", "", candidate.strip())
    if len(cleaned) != 14 or not cleaned.isdigit():
        return False, "invalid_abha_length"

    if cleaned[0] == "0":
        return False, "invalid_abha_start"

    if len(set(cleaned)) == 1:
        return False, "dummy_abha"

    return True, "valid_abha"
