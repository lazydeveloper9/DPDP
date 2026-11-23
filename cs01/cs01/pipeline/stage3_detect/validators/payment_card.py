import re

def luhn_checksum(card_number: str) -> bool:
    """Validate payment card number using Luhn mod-10 algorithm."""
    digits = [int(d) for d in card_number if d.isdigit()]
    if not digits:
        return False
    checksum = 0
    odd = True
    for d in reversed(digits):
        if not odd:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
        odd = not odd
    return checksum % 10 == 0

def validate_payment_card(candidate: str) -> tuple[bool, str]:
    """
    Validate major payment cards (Visa, MasterCard, Amex, RuPay).
    Requires valid length (13-19 digits) and Luhn check pass.
    Returns (is_valid, reason).
    """
    cleaned = re.sub(r"[\s\-]", "", candidate.strip())
    if not cleaned.isdigit() or len(cleaned) < 13 or len(cleaned) > 19:
        return False, "invalid_card_length"

    if len(set(cleaned)) == 1:
        return False, "dummy_card_repeated_digits"

    if not luhn_checksum(cleaned):
        return False, "luhn_checksum_failed"

    scheme = "generic"
    if cleaned.startswith("4"):
        scheme = "visa"
    elif cleaned.startswith(("51", "52", "53", "54", "55")) or (
        len(cleaned) >= 4 and cleaned[:4].isdigit() and 2221 <= int(cleaned[:4]) <= 2720
    ):
        scheme = "mastercard"
    elif cleaned.startswith(("34", "37")):
        scheme = "amex"
    elif cleaned.startswith(("60", "65", "81", "82")):
        scheme = "rupay"

    return True, f"valid_card_{scheme}"
