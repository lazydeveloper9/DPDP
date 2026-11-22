"""
General Indian Identifiers Validator
====================================
Validators for Passport, Voter ID (EPIC), IFSC, Mobile, Email, and IP Address.
"""

from __future__ import annotations
import ipaddress
import re

# Indian Mobile: 10 digits starting with 6, 7, 8, or 9
# Accepts optional prefixes: +91, 91, or 0
MOBILE_REGEX = re.compile(r"^(?:(?:\+91|91|0)[\s\-]?)?([6-9]\d{9})$")

# Indian Passport: 1 uppercase letter followed by 7 digits
PASSPORT_REGEX = re.compile(r"^[A-Z][1-9][0-9]{6}$")

# Indian Voter ID (EPIC): 3 uppercase letters followed by 7 digits
VOTER_ID_REGEX = re.compile(r"^[A-Z]{3}[0-9]{7}$")

# Indian Financial System Code (IFSC): 4 alpha, '0', 6 alphanumeric
IFSC_REGEX = re.compile(r"^[A-Z]{4}0[A-Z0-9]{6}$")

# Email regex RFC 5322 simplified
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")


def validate_mobile(candidate: str) -> tuple[bool, str]:
    """Validate 10-digit Indian mobile number."""
    cleaned = re.sub(r"[\s\-]", "", candidate)
    match = MOBILE_REGEX.match(cleaned)
    if match:
        standardized = match.group(1)
        # Avoid trivial repeating numbers like 9999999999
        if len(set(standardized)) == 1:
            return False, "repetitive_digits"
        return True, standardized
    return False, "invalid_indian_mobile"


def validate_passport(candidate: str) -> tuple[bool, str]:
    """Validate Indian Passport number."""
    cleaned = candidate.strip().upper()
    if PASSPORT_REGEX.match(cleaned):
        return True, "valid_passport"
    return False, "invalid_passport"


def validate_voter_id(candidate: str) -> tuple[bool, str]:
    """Validate Indian Voter ID (EPIC) number."""
    cleaned = candidate.strip().upper()
    if VOTER_ID_REGEX.match(cleaned):
        return True, "valid_voter_id"
    return False, "invalid_voter_id"


def validate_ifsc(candidate: str) -> tuple[bool, str]:
    """Validate Indian Bank IFSC code."""
    cleaned = candidate.strip().upper()
    if IFSC_REGEX.match(cleaned):
        return True, "valid_ifsc"
    return False, "invalid_ifsc"


def validate_email(candidate: str) -> tuple[bool, str]:
    """Validate email address format."""
    cleaned = candidate.strip()
    if EMAIL_REGEX.match(cleaned) and len(cleaned) <= 254:
        return True, "valid_email"
    return False, "invalid_email"


def validate_ip_address(candidate: str) -> tuple[bool, str]:
    """Validate IPv4 or IPv6 address."""
    cleaned = candidate.strip()
    try:
        ip = ipaddress.ip_address(cleaned)
        # Filter out loopback or private defaults if needed
        return True, f"valid_ipv{ip.version}"
    except ValueError:
        return False, "invalid_ip"
