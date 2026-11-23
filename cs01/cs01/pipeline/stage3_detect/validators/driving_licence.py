import re

STATE_CODES = {
    "AN", "AP", "AR", "AS", "BR", "CH", "CG", "DD", "DL", "DN", "GA", "GJ",
    "HP", "HR", "JH", "JK", "KA", "KL", "LA", "LD", "MH", "ML", "MN", "MP",
    "MZ", "NL", "OD", "PB", "PY", "RJ", "SK", "TN", "TR", "TS", "UK", "UP", "WB"
}

def validate_driving_licence(candidate: str) -> tuple[bool, str]:
    """
    Validate an Indian Driving Licence number.
    Standard MoRTH format: SS-RR-YYYY-NNNNNNN or SSRRYYYYNNNNNNN (15 or 16 chars).
    Returns (is_valid, reason).
    """
    cleaned = re.sub(r"[\s\-]", "", candidate.strip().upper())
    if len(cleaned) < 13 or len(cleaned) > 16:
        return False, "invalid_dl_length"

    m = re.match(r"^([A-Z]{2})(\d{2})((?:19|20)\d{2}|\d{2})(\d{7})$", cleaned)
    if not m:
        return False, "invalid_dl_format"

    state, rto, year, num = m.groups()
    if state not in STATE_CODES:
        return False, f"invalid_dl_state_{state}"

    return True, f"valid_dl_{state}"
