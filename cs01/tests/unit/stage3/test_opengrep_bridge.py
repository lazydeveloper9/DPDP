"""
Unit Tests for Opengrep / Semgrep Subprocess Bridge
===================================================
Tests binary resolution, zero-egress command construction, JSON parsing,
statutory DPDP rulepack validation, and graceful fallback behavior.
"""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import subprocess
from ruamel.yaml import YAML
import pytest

from cs01.pipeline.stage3_detect.opengrep_bridge import OpengrepBridge
from cs01.models import ScanConfig, EngineConfig, RawFinding, Severity, PassType
from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
from cs01.models import FlowGraph, PiiHitList, RepoModel

def test_default_rules_exist_and_valid():
    """Verify packaged DPDP rules exist and conform to Semgrep YAML specification."""
    rules_path = OpengrepBridge.get_default_rules_path()
    assert rules_path.exists(), f"Rules file missing: {rules_path}"

    with open(rules_path, "r", encoding="utf-8") as f:
        data = YAML(typ="safe").load(f)

    assert "rules" in data, "YAML must have a 'rules' key"
    rules = data["rules"]
    assert len(rules) >= 4, "Must contain at least 4 core DPDP rules"

    rule_ids = [r["id"] for r in rules]
    assert "DPDP-SEC-LOG-001" in rule_ids
    assert "DPDP-SEC-ENV-001" in rule_ids

    for rule in rules:
        assert "message" in rule
        assert "severity" in rule
        assert "metadata" in rule
        meta = rule["metadata"]
        assert "dpdp_section" in meta
        assert "dpdp_rule" in meta
        assert "penalty_band" in meta
        assert "remediation" in meta

def test_build_command_zero_egress():
    """Ensure command formulation includes mandatory zero-egress, local-only flags."""
    cmd = OpengrepBridge.build_command(
        binary="opengrep",
        target_path="/workspace/repo",
        rules_path="/workspace/rules.yaml",
        extra_args=["--verbose"],
    )

    assert cmd[0] == "opengrep"
    assert "scan" in cmd
    assert "--json" in cmd
    assert "--config" in cmd
    assert "--metrics=off" in cmd
    assert "--disable-version-check" in cmd
    assert "--verbose" in cmd
    assert cmd[-1] == "/workspace/repo"

def test_detect_binary_fallback():
    """When no binary is present on the PATH, detect_binary returns (None, None)."""
    with patch("shutil.which", return_value=None), patch("os.path.isfile", return_value=False):
        binary, flavor = OpengrepBridge.detect_binary()
        assert binary is None
        assert flavor is None

def test_detect_binary_opengrep():
    """When opengrep is in PATH, detect_binary returns opengrep path and flavor."""
    with patch("shutil.which", side_effect=lambda x: "/usr/bin/opengrep" if x == "opengrep" else None):
        binary, flavor = OpengrepBridge.detect_binary()
        assert binary == "/usr/bin/opengrep"
        assert flavor == "opengrep"

def test_detect_binary_semgrep():
    """When semgrep is in PATH (and opengrep is not), detect_binary returns semgrep."""
    with patch("shutil.which", side_effect=lambda x: "/usr/bin/semgrep" if x == "semgrep" else None):
        binary, flavor = OpengrepBridge.detect_binary()
        assert binary == "/usr/bin/semgrep"
        assert flavor == "semgrep"

def test_parse_semgrep_json():
    """Verify parsing standard Semgrep / Opengrep JSON output into CS-01 RawFindings."""
    mock_json = {
        "results": [
            {
                "check_id": "DPDP-SEC-LOG-001",
                "path": "src/controllers/auth.py",
                "start": {"line": 42, "col": 5},
                "end": {"line": 42, "col": 55},
                "extra": {
                    "message": "Personal data flows directly into logger",
                    "severity": "ERROR",
                    "lines": "logger.info('Aadhaar submitted: %s', aadhaar)",
                    "metadata": {
                        "cs01_rule_id": "CODE-DPDP-001",
                        "dpdp_section": "§8(5)",
                        "dpdp_rule": "Rule 6(1)(a)",
                        "penalty_band": "250_crore",
                        "remediation": "Mask PII before logging.",
                    },
                },
            },
            {
                "check_id": "DPDP-SEC-ENV-001",
                "path": ".env.production",
                "start": {"line": 10, "col": 1},
                "end": {"line": 10, "col": 30},
                "extra": {
                    "message": "Insecure DB SSL mode",
                    "severity": "ERROR",
                    "lines": "DATABASE_URL=postgres://...sslmode=disable",
                    "metadata": {
                        "cs01_rule_id": "ENV-DPDP-001",
                        "dpdp_section": "§8(5)",
                        "dpdp_rule": "Rule 6(1)(a)",
                        "penalty_band": "250_crore",
                        "remediation": "Set sslmode=require.",
                    },
                },
            },
        ],
        "errors": [],
    }

    findings = OpengrepBridge.parse_semgrep_json(
        mock_json,
        scan_root=".",
        flavor="opengrep",
    )

    assert len(findings) == 2

    f1 = findings[0]
    assert f1.rule_id == "CODE-DPDP-001"
    assert f1.engine == "opengrep"
    assert f1.file == "src/controllers/auth.py"
    assert f1.line_start == 42
    assert f1.dpdp_section == "§8(5)"
    assert f1.dpdp_rule == "Rule 6(1)(a)"
    assert f1.penalty_band == "250_crore"
    assert f1.severity == Severity.CRITICAL
    assert "Aadhaar submitted" in f1.snippet

    f2 = findings[1]
    assert f2.rule_id == "ENV-DPDP-001"
    assert f2.engine == "opengrep"
    assert f2.file == ".env.production"
    assert f2.line_start == 10
    assert f2.severity == Severity.CRITICAL

def test_run_scan_graceful_missing_binary():
    """Verify run_scan returns [] gracefully without error when binary is missing."""
    bridge = OpengrepBridge()
    cfg = ScanConfig(scan_root=".", engine=EngineConfig(opengrep=True))

    with patch.object(OpengrepBridge, "detect_binary", return_value=(None, None)):
        findings = bridge.run_scan(".", cfg)
        assert findings == []

def test_run_scan_timeout_handling():
    """Verify run_scan handles subprocess timeout cleanly."""
    bridge = OpengrepBridge()
    cfg = ScanConfig(scan_root=".", engine=EngineConfig(opengrep=True, timeout_seconds=1.0))

    with patch.object(OpengrepBridge, "detect_binary", return_value=("/bin/opengrep", "opengrep")), \
         patch("subprocess.run", side_effect=subprocess.TimeoutExpired(cmd="opengrep", timeout=1.0)):
        findings = bridge.run_scan(".", cfg)
        assert findings == []

def test_evaluator_integration_with_opengrep():
    """Verify Stage 4 evaluator merges Opengrep findings when engine.opengrep is enabled."""
    cfg = ScanConfig(scan_root=".", engine=EngineConfig(tree_sitter=False, opengrep=True))
    flow_graph = FlowGraph(nodes={}, edges=[])
    pii_hits = PiiHitList(hits=[])
    repo_model = RepoModel(scan_root=".")

    mock_finding = RawFinding(
        id="DPDP-TEST:test.py:1",
        rule_id="DPDP-TEST",
        pass_type=PassType.A,
        engine="opengrep",
        file="test.py",
        line_start=1,
        snippet="mock line",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.HIGH,
        message="Mock Opengrep Finding",
        remediation="Fix it",
    )

    with patch("cs01.pipeline.stage3_detect.opengrep_bridge.OpengrepBridge.run_scan", return_value=[mock_finding]):
        findings = run_evaluate(flow_graph, pii_hits, repo_model, cfg)
        assert len(findings) == 1
        assert findings[0].engine == "opengrep"
        assert findings[0].rule_id == "DPDP-TEST"
