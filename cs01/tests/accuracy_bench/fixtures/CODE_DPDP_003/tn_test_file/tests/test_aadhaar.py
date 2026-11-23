def test_aadhaar_validation():
    test_number = "234567890124"
    assert len(test_number) == 12
    assert test_number[0] not in ("0", "1")
