"""
PAN Validator (Permanent Account Number - 10-char Indian Tax ID)
=================================================================
Structure:
  - Characters 1-3: Alphabetic series (AAA to ZZZ)
  - Character 4: Status/Entity type of the holder:
      P: Individual
      C: Company
      H: Hindu Undivided Family (HUF)
      A: Association of Persons (AOP)
      T: Trust
      B: Body of Individuals (BOI)
      L: Local Authority
      J: Artificial Juridical Person
      G: Government Agency
      F: Firm / Limited Liability Partnership
  - Character 5: First letter of PAN holder's last name/surname
  - Characters 6-9: Sequential numeric series (0001 to 9999)
  - Character 10: Alphabetic check digit
"""

from __future__ import annotations
import re

PAN_REGEX = re.compile(r"^[A-Z]{3}([PCHATBLJGF])[A-Z][0-9]{4}[A-Z]$")

ENTITY_TYPES: dict[str, str] = {
    "P": "Individual",
    "C": "Company",
    "H": "Hindu Undivided Family",
    "A": "Association of Persons",
    "T": "Trust",
    "B": "Body of Individuals",
    "L": "Local Authority",
    "J": "Artificial Juridical Person",
    "G": "Government Agency",
    "F": "Firm / LLP",
}


def validate_pan(candidate: str) -> tuple[bool, str]:
    """
    Validate a potential PAN number string.
    Returns (is_valid, entity_type_or_reason).
    """
    cleaned = candidate.strip().upper()

    if len(cleaned) != 10:
        return False, "invalid_length"

    match = PAN_REGEX.match(cleaned)
    if not match:
        return False, "invalid_pan_format"

    entity_code = match.group(1)
    # Check that sequential digits are not 0000
    if cleaned[5:9] == "0000":
        return False, "invalid_numeric_series"

    entity_desc = ENTITY_TYPES.get(entity_code, "Unknown")
    return True, f"valid ({entity_desc})"
