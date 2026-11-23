"""
Unit tests for baseline loading, dedupe matching, and suppression in Stage 5.
"""

import tempfile
from pathlib import Path
from cs01.models import RawFinding, PassType, Severity, ScanConfig
from cs01.pipeline.stage5_classify.classifier import run_classify
from cs01.utils import save_json

def test_baseline_suppresses_known_findings():
    raw1 = RawFinding(
        id="f1",
        rule_id="CODE-DPDP-001",
        pass_type=PassType.A,
        file="app/views.py",
        line_start=15,
        snippet="logger.info(user.pan)",
        matched_entity="logger.info",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.HIGH,
        message="Logging PII",
        remediation="Mask data",
    )
    raw2 = RawFinding(
        id="f2",
        rule_id="CODE-DPDP-002",
        pass_type=PassType.A,
        file="app/config.py",
        line_start=20,
        snippet="api_key = 'secret'",
        matched_entity="api_key",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.CRITICAL,
        message="Hardcoded secret",
        remediation="Use vault",
    )

    with tempfile.TemporaryDirectory() as tmp:
        cfg_init = ScanConfig(policy_profiles_dir="./policy_profiles")
        bundle_init = run_classify([raw1, raw2], cfg_init)

        f1_key = next(f.dedupe_key for f in bundle_init.findings if f.rule_id == "CODE-DPDP-001")

        baseline_file = Path(tmp) / ".cs01-baseline.json"
        save_json({"fingerprints": [f1_key]}, baseline_file)

        cfg_with_base = ScanConfig(
            policy_profiles_dir="./policy_profiles",
            baseline_path=str(baseline_file),
        )
        bundle_second = run_classify([raw1, raw2], cfg_with_base)

        scored_f1 = next(f for f in bundle_second.findings if f.rule_id == "CODE-DPDP-001")
        scored_f2 = next(f for f in bundle_second.findings if f.rule_id == "CODE-DPDP-002")

        assert scored_f1.is_baseline_suppressed is True
        assert scored_f2.is_baseline_suppressed is False
