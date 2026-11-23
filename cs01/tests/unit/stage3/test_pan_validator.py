import pytest
from cs01.pipeline.stage3_detect.validators.pan import validate_pan

def test_validate_pan_success():
    valid_p, desc_p = validate_pan("ABCPE1234F")
    assert valid_p is True
    assert "Individual" in desc_p

    valid_c, desc_c = validate_pan("XYZCA9876K")
    assert valid_c is True
    assert "Company" in desc_c

    valid_t, desc_t = validate_pan("MNOTB5555M")
    assert valid_t is True
    assert "Trust" in desc_t

def test_validate_pan_failures():
    assert validate_pan("ABCZE1234F")[0] is False
    assert validate_pan("ABCDE1234F")[0] is False
    assert validate_pan("ABCPE1234")[0] is False
    assert validate_pan("ABCPE12345F")[0] is False
    assert validate_pan("ABCPE0000F")[0] is False
    assert validate_pan("abcpe1234f")[0] is True
    assert validate_pan("ABC-E1234F")[0] is False
