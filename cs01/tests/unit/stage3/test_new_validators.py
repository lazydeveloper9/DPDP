import pytest
from cs01.pipeline.stage3_detect.validators.driving_licence import validate_driving_licence
from cs01.pipeline.stage3_detect.validators.abha import validate_abha
from cs01.pipeline.stage3_detect.validators.payment_card import validate_payment_card, luhn_checksum

def test_driving_licence_valid():
    is_valid, reason = validate_driving_licence("DL-0420110012345")
    assert is_valid is True
    assert reason == "valid_dl_DL"

    is_valid, reason = validate_driving_licence("MH12 20150001234")
    assert is_valid is True
    assert reason == "valid_dl_MH"

def test_driving_licence_invalid():
    assert validate_driving_licence("XX-0420110012345")[0] is False  # Invalid state
    assert validate_driving_licence("123456789")[0] is False          # Too short
    assert validate_driving_licence("DL-ABC-2011-1234")[0] is False   # Invalid format

def test_abha_valid():
    assert validate_abha("14-1234-5678-9012")[0] is True
    assert validate_abha("91123456789012")[0] is True

def test_abha_invalid():
    assert validate_abha("01123456789012")[0] is False  # Starts with 0
    assert validate_abha("11111111111111")[0] is False  # Repeated dummy digits
    assert validate_abha("12345")[0] is False           # Too short

def test_luhn_checksum():
    assert luhn_checksum("79927398713") is True
    assert luhn_checksum("79927398710") is False

def test_payment_card_valid():
    assert validate_payment_card("4532015112830366")[0] is True  # Visa
    assert "visa" in validate_payment_card("4532015112830366")[1]

def test_payment_card_invalid():
    assert validate_payment_card("4532015112830367")[0] is False  # Bad Luhn
    assert validate_payment_card("1111111111111111")[0] is False  # Dummy
    assert validate_payment_card("1234")[0] is False              # Too short
