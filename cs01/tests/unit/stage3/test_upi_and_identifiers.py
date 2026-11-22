import pytest
from cs01.pipeline.stage3_detect.validators.upi import validate_upi_id
from cs01.pipeline.stage3_detect.validators.identifiers import (
    validate_mobile, validate_passport, validate_voter_id, validate_ifsc, validate_email,
)


def test_validate_upi():
    assert validate_upi_id("john.doe@okaxis")[0] is True
    assert validate_upi_id("vendor_pay@paytm")[0] is True
    assert validate_upi_id("test@okhdfcbank")[0] is True
    # Unregistered handle
    assert validate_upi_id("test@unknownfakehandle")[0] is False


def test_validate_mobile():
    assert validate_mobile("9876543210")[0] is True
    assert validate_mobile("+91 9876543210")[0] is True
    assert validate_mobile("09123456789")[0] is True
    # Repetitive digits
    assert validate_mobile("9999999999")[0] is False
    # Starts with 5 (invalid Indian mobile start)
    assert validate_mobile("5123456789")[0] is False


def test_validate_passport_and_voter_id():
    assert validate_passport("A1234567")[0] is True
    assert validate_passport("12345678")[0] is False

    assert validate_voter_id("XYZ1234567")[0] is True
    assert validate_voter_id("XY12345678")[0] is False


def test_validate_ifsc():
    assert validate_ifsc("HDFC0001234")[0] is True
    assert validate_ifsc("SBIN0000456")[0] is True
    # 5th char not '0'
    assert validate_ifsc("HDFC1001234")[0] is False


def test_validate_email():
    assert validate_email("user@example.com")[0] is True
    assert validate_email("invalid-email-str")[0] is False
