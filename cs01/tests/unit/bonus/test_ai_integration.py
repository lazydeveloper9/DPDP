"""
Unit tests for Qwen 2.5 Coder local AI client and DPO briefing generators.
"""

import pytest
from cs01.ai import LocalLLMClient, generate_executive_dpo_brief, explain_finding_in_depth
from cs01.models import (
    ScoredFindingBundle, ScoredFinding, DpdpReadinessScore, PillarScore,
    PassType, Severity,
)


def test_ai_client_rejects_external_endpoints():
    """Verify that cloud/external endpoints are rejected to enforce zero cloud egress."""
    with pytest.raises(ValueError, match="Security Guardrail"):
        LocalLLMClient(endpoint="https://api.openai.com/v1")


def test_ai_client_accepts_local_endpoints():
    """Verify local hostnames are allowed."""
    client_local = LocalLLMClient(endpoint="http://localhost:11434")
    assert client_local.endpoint == "http://localhost:11434"

    client_ip = LocalLLMClient(endpoint="http://127.0.0.1:8000")
    assert client_ip.endpoint == "http://127.0.0.1:8000"


class MockLLMClient:
    def __init__(self):
        self.last_prompt = ""
        self.last_system = ""

    def generate(self, prompt: str, system_prompt: str = "", on_token=None, **kwargs) -> str:
        self.last_prompt = prompt
        self.last_system = system_prompt
        return "# Executive DPDP Brief\n\nCompliance posture is acceptable."


def test_generate_executive_dpo_brief():
    mock_client = MockLLMClient()
    pillar = PillarScore(
        pillar_id="p1",
        label="Security Safeguards",
        score=75.0,
        total_rules=4,
        passing_rules=3,
        failing_rule_ids=["CODE-DPDP-001"],
    )
    readiness = DpdpReadinessScore(
        overall=75.0,
        is_capped=False,
        pillars=[pillar],
        open_critical_count=0,
        open_high_count=1,
    )
    finding = ScoredFinding(
        id="f1",
        rule_id="CODE-DPDP-001",
        pass_type=PassType.A,
        file="app.py",
        line_start=12,
        snippet="logger.info(aadhaar)",
        matched_entity="logger.info",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.HIGH,
        message="Logging unguarded PII",
        remediation="Mask data before logging",
    )
    bundle = ScoredFindingBundle(
        scan_id="test_scan",
        scan_timestamp="2026-11-23T00:00:00Z",
        scan_root="./myapp",
        total_files_scanned=10,
        findings=[finding],
        readiness=readiness,
    )

    result = generate_executive_dpo_brief(bundle, mock_client)  # type: ignore[arg-type]
    assert "Executive DPDP Brief" in result
    assert "CODE-DPDP-001" in mock_client.last_prompt
    assert "§8(5)" in mock_client.last_prompt
    assert "Security Safeguards" in mock_client.last_prompt


def test_explain_finding_in_depth():
    mock_client = MockLLMClient()
    finding = ScoredFinding(
        id="f1",
        rule_id="CODE-DPDP-001",
        pass_type=PassType.A,
        file="app.py",
        line_start=12,
        snippet="logger.info(aadhaar)",
        matched_entity="logger.info",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.HIGH,
        message="Logging unguarded PII",
        remediation="Mask data before logging",
        statutory_ceiling_display="§8(5) up to ₹250 Crore",
    )

    result = explain_finding_in_depth(finding, mock_client)  # type: ignore[arg-type]
    assert "Executive DPDP Brief" in result
    assert "CODE-DPDP-001" in mock_client.last_prompt
    assert "logger.info(aadhaar)" in mock_client.last_prompt
