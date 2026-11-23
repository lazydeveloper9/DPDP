import pytest
from cs01.pipeline.stage4_evaluate.rule_loader import load_all_rules, get_rule_by_id

def test_load_all_rules():
    rules = load_all_rules()
    assert len(rules) >= 10

    for r in rules:
        assert len(r.get("tags", [])) <= 8
        assert "rule_id" in r
        assert "pass" in r
        assert "dpdp_section" in r
        assert "penalty_band" in r

def test_get_rule_by_id():
    rule = get_rule_by_id("CODE-DPDP-001")
    assert rule is not None
    assert rule["severity"] == "CRITICAL"
    assert rule["dpdp_section"] == "§8(5)"
    assert rule["penalty_band"] == "250_crore"

    rule_b = get_rule_by_id("ARCH-DPDP-001")
    assert rule_b is not None
    assert rule_b["pass"] == "B"
