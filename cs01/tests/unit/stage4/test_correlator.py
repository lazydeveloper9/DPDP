import pytest
from cs01.models.raw_finding import RawFinding, PassType, Severity
from cs01.models.flow_graph import FlowGraph, DataGuard, GuardType, PiiHitList
from cs01.models.repo_model import RepoModel
from cs01.models.scan_config import ScanConfig
from cs01.pipeline.stage4_evaluate.correlator import correlate_findings

def test_correlator_escalation():
    f_sql = RawFinding(
        id="SQL-DPDP-001:schema.sql:10",
        rule_id="SQL-DPDP-001",
        pass_type=PassType.A,
        file="schema.sql",
        line_start=10,
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.HIGH,
        message="Unencrypted PII",
        remediation="Encrypt",
        matched_entity="users.aadhaar_number",
    )

    f_iac = RawFinding(
        id="IAC-DPDP-001:main.tf:5",
        rule_id="IAC-DPDP-001",
        pass_type=PassType.A,
        file="main.tf",
        line_start=5,
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.HIGH,
        message="Unencrypted RDS",
        remediation="Enable storage_encrypted",
        matched_entity="users_prod",
    )

    findings = [f_sql, f_iac]
    correlated = correlate_findings(findings, FlowGraph(), PiiHitList(), RepoModel(), ScanConfig())

    assert f_sql.severity == Severity.CRITICAL
    assert len(f_sql.correlation_chain) == 2
    assert f_iac.id in f_sql.related_finding_ids
    assert f_sql.id in f_iac.related_finding_ids

def test_correlator_compensating_controls():
    f_code = RawFinding(
        id="CODE-DPDP-001:src/main.py:12",
        rule_id="CODE-DPDP-001",
        pass_type=PassType.A,
        file="src/main.py",
        line_start=12,
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.CRITICAL,
        message="PII logging",
        remediation="Mask",
    )

    guard = DataGuard(
        id="GUARD:src/main.py:10:mask_pii",
        guard_type=GuardType.MASKING,
        file="src/main.py",
        line=10,
        guard_function_name="mask_pii",
    )

    flow_graph = FlowGraph(guards=[guard])
    correlated = correlate_findings([f_code], flow_graph, PiiHitList(), RepoModel(), ScanConfig())

    assert len(f_code.compensating_controls) == 1
    assert "mask_pii" in f_code.compensating_controls[0]
