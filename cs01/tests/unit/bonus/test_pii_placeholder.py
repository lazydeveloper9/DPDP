import pytest
from cs01.ai.pii_placeholder import mask_pii_with_placeholders, unmask_placeholders

def test_pii_placeholder_masking_and_unmasking():
    original = "User 2345 6789 0124 with PAN ABCDE1234F contacted via alice@test.com"
    masked, mapping = mask_pii_with_placeholders(original)

    assert "[AADHAAR_1]" in masked
    assert "[PAN_1]" in masked
    assert "[EMAIL_1]" in masked
    assert "2345 6789 0124" not in masked
    assert "ABCDE1234F" not in masked
    assert "alice@test.com" not in masked

    restored = unmask_placeholders(masked, mapping)
    assert restored == original
