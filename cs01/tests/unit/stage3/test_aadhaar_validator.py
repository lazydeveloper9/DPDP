import pytest
from cs01.pipeline.stage3_detect.validators.aadhaar import (
    validate_aadhaar, verhoeff_check, generate_verhoeff_check_digit,
)

def test_verhoeff_known_vectors():
    prefix = "23456789012"
    check_digit = generate_verhoeff_check_digit(prefix)
    full_aadhaar = prefix + str(check_digit)
    assert verhoeff_check(full_aadhaar) is True

def test_validate_aadhaar_success():
    prefix = "36728901234"
    c_digit = generate_verhoeff_check_digit(prefix)
    valid_no = f"{prefix[:4]} {prefix[4:8]} {prefix[8:]}{c_digit}"
    
    is_valid, reason = validate_aadhaar(valid_no)
    assert is_valid is True
    assert reason == "valid"

def test_validate_aadhaar_failures():
    assert validate_aadhaar("012345678912")[0] is False
    assert validate_aadhaar("123456789012")[0] is False
    assert validate_aadhaar("2345678901")[0] is False
    assert validate_aadhaar("2345ABCD0123")[0] is False
    assert validate_aadhaar("222222222222")[0] is False
    assert validate_aadhaar("234567890129")[0] is False
