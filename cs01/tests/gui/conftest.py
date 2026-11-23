"""
Pytest configuration and central fixtures for CS-01 DPDP Compliance Desktop GUI tests.
Configures headless offscreen Qt execution and provides deterministic test fixtures.
"""

from __future__ import annotations

import json
import os
import zipfile
from collections.abc import Generator
from pathlib import Path

import pytest
from PySide6.QtWidgets import QApplication

# Ensure headless offscreen platform before any Qt import
os.environ["QT_QPA_PLATFORM"] = "offscreen"

# Install fallback modules if genuine cs01.gui is not yet present on disk
from .gui_fallbacks import (
    GuiScanState,
    create_app,
    install_fallbacks,
)

install_fallbacks()

from cs01.models.flow_graph import FileRole, PiiHit, PiiType
from cs01.models.raw_finding import PassType, Severity
from cs01.models.scored_finding import (
    DpdpReadinessScore,
    ExposureContext,
    PillarScore,
    ScoredFinding,
    ScoredFindingBundle,
)
from cs01.pipeline.stage6_report.evidence_locker import create_evidence_bundle


@pytest.fixture(scope="session")
def qapp() -> Generator[QApplication, None, None]:
    """Provide a session-level QApplication initialized for headless offscreen testing."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    app = QApplication.instance()
    if app is None:
        app = create_app([])
    yield app


@pytest.fixture
def clean_bundle() -> ScoredFindingBundle:
    """Return a ScoredFindingBundle representing a perfectly compliant audit (100.0 score)."""
    pillar_ids = [
        ("notice_consent", "Notice & Consent (§5, §6)"),
        ("security_safeguards", "Security Safeguards (§8(5))"),
        ("breach_readiness", "Breach Readiness (§8(6))"),
        ("retention_erasure", "Retention & Erasure (Rule 6)"),
        ("children_protection", "Children & PwD (§9)"),
        ("sdf_duties", "SDF Duties (§10, Rule 13)"),
        ("data_principal_rights", "Principal Rights (Rule 14)"),
        ("cross_border_cert_in", "Cross-Border & CERT-In"),
    ]
    pillars = [
        PillarScore(
            pillar_id=pid,
            label=lbl,
            score=100.0,
            total_rules=10,
            passing_rules=10,
            failing_rule_ids=[],
        )
        for pid, lbl in pillar_ids
    ]
    readiness = DpdpReadinessScore(
        overall=100.0,
        is_capped=False,
        cap_reason=None,
        pillars=pillars,
        max_statutory_ceiling_engaged="None Engaged (₹0)",
        open_critical_count=0,
        open_high_count=0,
    )
    return ScoredFindingBundle(
        scan_id="scan-clean-001",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="/workspace/clean_repo",
        findings=[],
        readiness=readiness,
        total_files_scanned=25,
    )


@pytest.fixture
def capped_critical_bundle() -> ScoredFindingBundle:
    """
    Return a ScoredFindingBundle with an unresolved CRITICAL finding triggering
    Section 33(1) maximum ₹250 Crore penalty and dynamic score capping at 60.0.
    """
    critical_finding = ScoredFinding(
        id="finding-crit-001",
        rule_id="CODE-DPDP-001",
        pass_type=PassType.A,
        file="src/models/user_vault.py",
        line_start=45,
        line_end=52,
        snippet="cursor.execute(f'SELECT * FROM users WHERE aadhaar = {aadhaar}')",
        dpdp_section="§8(5)",
        dpdp_rule="Rule 6(1)(a)",
        penalty_band="250_crore",
        severity=Severity.CRITICAL,
        message="Plaintext SQL concatenation of Aadhaar violates reasonable security safeguards (§8(5))",
        remediation="Use parameterized queries and encrypt Aadhaar data at rest via AES-256-GCM.",
        priority_score=95.0,
        confidence=0.98,
        exposure=ExposureContext.PRODUCTION,
        statutory_ceiling_display="₹250 Crore (§8(5) Security Safeguards)",
    )

    pillar_ids = [
        ("notice_consent", "Notice & Consent (§5, §6)", 90.0, ["NOTICE-001"]),
        ("security_safeguards", "Security Safeguards (§8(5))", 40.0, ["CODE-DPDP-001"]),
        ("breach_readiness", "Breach Readiness (§8(6))", 85.0, []),
        ("retention_erasure", "Retention & Erasure (Rule 6)", 80.0, []),
        ("children_protection", "Children & PwD (§9)", 100.0, []),
        ("sdf_duties", "SDF Duties (§10, Rule 13)", 85.0, []),
        ("data_principal_rights", "Principal Rights (Rule 14)", 95.0, []),
        ("cross_border_cert_in", "Cross-Border & CERT-In", 100.0, []),
    ]
    pillars = [
        PillarScore(
            pillar_id=pid,
            label=lbl,
            score=sc,
            total_rules=10,
            passing_rules=10 - len(failing),
            failing_rule_ids=failing,
        )
        for pid, lbl, sc, failing in pillar_ids
    ]
    readiness = DpdpReadinessScore(
        overall=60.0,  # Capped at 60.0
        is_capped=True,
        cap_reason="Unresolved CRITICAL finding in 250_crore band: CODE-DPDP-001 (§8(5))",
        pillars=pillars,
        max_statutory_ceiling_engaged="₹250 Crore (§8(5) Security Safeguards)",
        open_critical_count=1,
        open_high_count=0,
    )
    return ScoredFindingBundle(
        scan_id="scan-capped-002",
        scan_timestamp="2026-11-23T12:15:00Z",
        scan_root="/workspace/fintech_repo",
        findings=[critical_finding],
        readiness=readiness,
        total_files_scanned=48,
    )


@pytest.fixture
def multi_pii_hits() -> list[PiiHit]:
    """Return realistic Indian PII detections satisfying zero plaintext in-memory contract."""
    return [
        PiiHit(
            id="pii-aadhaar-001",
            pii_type=PiiType.AADHAAR,
            file="src/models/user.py",
            line=42,
            col=10,
            confidence=0.99,
            file_role=FileRole.PRODUCTION,
            value_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            validator_result="valid_verhoeff",
            line_snippet="aadhaar = 'XXXX-XXXX-9012'",
        ),
        PiiHit(
            id="pii-pan-001",
            pii_type=PiiType.PAN,
            file="src/billing.py",
            line=15,
            col=8,
            confidence=0.95,
            file_role=FileRole.PRODUCTION,
            value_sha256="f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
            validator_result="valid_pan_individual",
            line_snippet="pan = 'ABCDE****F'",
        ),
        PiiHit(
            id="pii-gstin-001",
            pii_type=PiiType.GSTIN,
            file="src/invoice.py",
            line=30,
            col=12,
            confidence=0.98,
            file_role=FileRole.PRODUCTION,
            value_sha256="5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
            validator_result="valid_gstin_mh",
            line_snippet="gstin = '27AAAAA****1Z5'",
        ),
        PiiHit(
            id="pii-upi-001",
            pii_type=PiiType.UPI_HANDLE,
            file="src/payments.py",
            line=55,
            col=5,
            confidence=0.92,
            file_role=FileRole.PRODUCTION,
            value_sha256="4b227777d4dd1fc61c6f884f48641d02b4d121d3fd328cb08b5531fcacdabf8a",
            validator_result="valid_npci_handle",
            line_snippet="vpa = 'user****@upi'",
        ),
        PiiHit(
            id="pii-mob-001",
            pii_type=PiiType.MOBILE,
            file="src/auth.py",
            line=102,
            col=9,
            confidence=0.90,
            file_role=FileRole.PRODUCTION,
            value_sha256="ef2d127de37b942baad06145e54b0c619a1f22327b2ebbcfbec78f5564afe39d",
            validator_result="valid_mobile_in",
            line_snippet="mobile = '+91-98****3210'",
        ),
        PiiHit(
            id="pii-abha-001",
            pii_type=PiiType.ABHA_HEALTH_ID,
            file="src/health.py",
            line=77,
            col=4,
            confidence=0.94,
            file_role=FileRole.PRODUCTION,
            value_sha256="8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",
            validator_result="valid_abha_14",
            line_snippet="abha = '12-****-****-1234'",
        ),
    ]


@pytest.fixture
def multi_findings_bundle(multi_pii_hits: list[PiiHit]) -> ScoredFindingBundle:
    """Return a diverse ScoredFindingBundle with findings spanning all severity levels."""
    findings = [
        ScoredFinding(
            id="f-crit-01",
            rule_id="CODE-DPDP-001",
            pass_type=PassType.A,
            file="src/vault.py",
            line_start=20,
            line_end=22,
            snippet="logger.info(f'Processing Aadhaar: {aadhaar}')",
            dpdp_section="§8(5)",
            dpdp_rule="Rule 6(1)(a)",
            penalty_band="250_crore",
            severity=Severity.CRITICAL,
            message="Unmasked Aadhaar logged to system stdout",
            remediation="Enforce PII masking and zero plaintext logging.",
            priority_score=92.0,
            statutory_ceiling_display="₹250 Crore (§8(5) Security Safeguards)",
        ),
        ScoredFinding(
            id="f-high-01",
            rule_id="CONSENT-001",
            pass_type=PassType.A,
            file="src/routes/auth.py",
            line_start=85,
            line_end=90,
            snippet="def register(): db.save(user, consent=True)",
            dpdp_section="§6",
            dpdp_rule="Rule 3(1)",
            penalty_band="50_crore",
            severity=Severity.HIGH,
            message="Pre-ticked or assumed consent during user onboarding",
            remediation="Require explicit affirmative notice and unbundled consent checkbox.",
            priority_score=78.0,
            statutory_ceiling_display="₹50 Crore (Residual / Procedural)",
        ),
        ScoredFinding(
            id="f-med-01",
            rule_id="RETENTION-002",
            pass_type=PassType.B,
            file="src/cron/cleanup.py",
            line_start=12,
            line_end=15,
            snippet="RETENTION_DAYS = 3650",
            dpdp_section="§8(7)",
            dpdp_rule="Rule 8",
            penalty_band="50_crore",
            severity=Severity.MEDIUM,
            message="Indefinite data retention period exceeding business purpose",
            remediation="Implement automated deletion or anonymization routines.",
            priority_score=55.0,
            statutory_ceiling_display="₹50 Crore (Residual / Procedural)",
        ),
        ScoredFinding(
            id="f-low-01",
            rule_id="DOCS-001",
            pass_type=PassType.B,
            file="README.md",
            line_start=1,
            line_end=5,
            snippet="# API Documentation",
            dpdp_section="§11",
            dpdp_rule="Rule 14",
            penalty_band="50_crore",
            severity=Severity.LOW,
            message="DPO contact email missing from developer documentation",
            remediation="Publish DPO contact info and grievance redressal mechanism.",
            priority_score=25.0,
            statutory_ceiling_display="₹50 Crore (Residual / Procedural)",
        ),
    ]

    readiness = DpdpReadinessScore(
        overall=60.0,
        is_capped=True,
        cap_reason="Unresolved CRITICAL finding in 250_crore band: CODE-DPDP-001",
        pillars=[
            PillarScore(pillar_id="notice_consent", label="Notice & Consent (§5, §6)", score=70.0, total_rules=5, passing_rules=4, failing_rule_ids=["CONSENT-001"]),
            PillarScore(pillar_id="security_safeguards", label="Security Safeguards (§8(5))", score=45.0, total_rules=10, passing_rules=9, failing_rule_ids=["CODE-DPDP-001"]),
            PillarScore(pillar_id="breach_readiness", label="Breach Readiness (§8(6))", score=100.0, total_rules=5, passing_rules=5, failing_rule_ids=[]),
            PillarScore(pillar_id="retention_erasure", label="Retention & Erasure (Rule 6)", score=80.0, total_rules=5, passing_rules=4, failing_rule_ids=["RETENTION-002"]),
            PillarScore(pillar_id="children_protection", label="Children & PwD (§9)", score=100.0, total_rules=5, passing_rules=5, failing_rule_ids=[]),
            PillarScore(pillar_id="sdf_duties", label="SDF Duties (§10, Rule 13)", score=100.0, total_rules=5, passing_rules=5, failing_rule_ids=[]),
            PillarScore(pillar_id="data_principal_rights", label="Principal Rights (Rule 14)", score=90.0, total_rules=5, passing_rules=4, failing_rule_ids=["DOCS-001"]),
            PillarScore(pillar_id="cross_border_cert_in", label="Cross-Border & CERT-In", score=100.0, total_rules=5, passing_rules=5, failing_rule_ids=[]),
        ],
        max_statutory_ceiling_engaged="₹250 Crore (§8(5) Security Safeguards)",
        open_critical_count=1,
        open_high_count=1,
    )

    return ScoredFindingBundle(
        scan_id="scan-multi-003",
        scan_timestamp="2026-11-23T12:20:00Z",
        scan_root="/workspace/multi_app",
        findings=findings,
        readiness=readiness,
        total_files_scanned=30,
    )


@pytest.fixture
def sample_report_files(tmp_path: Path) -> dict[str, Path]:
    """Generate authentic mock artifact files and a Rule 13 cryptographic evidence bundle."""
    report_dir = tmp_path / "cs01-reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    # 1. HTML DPO report
    html_path = report_dir / "cs01-dpo-report.html"
    html_path.write_text("<!DOCTYPE html><html><body><h1>CS-01 DPO Report</h1></body></html>", encoding="utf-8")

    # 2. Dataflow visualizer HTML
    dataflow_path = report_dir / "cs01-dataflow.html"
    dataflow_path.write_text("<!DOCTYPE html><html><body><div id='cytoscape'></div></body></html>", encoding="utf-8")

    # 3. Markdown report
    md_path = report_dir / "cs01-report.md"
    md_path.write_text("# CS-01 DPDP Compliance Executive Brief\n\nOverall Score: 60.0", encoding="utf-8")

    # 3b. Executive PDF report
    pdf_path = report_dir / "cs01-report.pdf"
    pdf_path.write_bytes(b"%PDF-1.4\n%dummy pdf content\n%%EOF")

    # 4. SARIF 2.1.0
    sarif_path = report_dir / "cs01-findings.sarif"
    sarif_data = {
        "version": "2.1.0",
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "runs": [{"tool": {"driver": {"name": "CS-01"}}, "results": []}],
    }
    sarif_path.write_text(json.dumps(sarif_data), encoding="utf-8")

    # 5. Technical RoPA JSON
    ropa_path = report_dir / "ropa_map.json"
    ropa_data = [
        {
            "system": "User Billing Service",
            "purpose": "Payment collection & tax compliance",
            "lawful_basis": "Statutory Duty under GST Act (§6)",
            "categories": "PAN, GSTIN, Financial",
            "retention": "8 Years (Income Tax Act)",
        },
        {
            "system": "Auth Gateway",
            "purpose": "Identity authentication & session security",
            "lawful_basis": "Affirmative Consent (§6(1))",
            "categories": "Mobile, Email, Session Token",
            "retention": "Active User Session + 180 Days",
        },
    ]
    ropa_path.write_text(json.dumps(ropa_data), encoding="utf-8")

    # 6. Consent Audit JSON
    consent_path = report_dir / "consent_audit.json"
    consent_path.write_text(json.dumps({"consent_notices_audited": 3, "failing": 1}), encoding="utf-8")

    # 7. Remediation Unified Diff Patch
    patch_dir = report_dir / "remediation_patches"
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch_path = patch_dir / "IAC-DPDP-001.patch"
    diff_content = (
        "--- a/terraform/s3.tf\n"
        "+++ b/terraform/s3.tf\n"
        "@@ -10,3 +10,4 @@\n"
        "-  acl = \"public-read\"\n"
        "+  acl = \"private\"\n"
        "+  server_side_encryption_configuration { rule { apply_server_side_encryption_by_default { sse_algorithm = \"aws:kms\" } } }\n"
    )
    patch_path.write_text(diff_content, encoding="utf-8")

    report_map: dict[str, Path] = {
        "cs01-dpo-report.html": html_path,
        "cs01-report.pdf": pdf_path,
        "cs01-dataflow.html": dataflow_path,
        "cs01-report.md": md_path,
        "cs01-findings.sarif": sarif_path,
        "ropa_map.json": ropa_path,
        "consent_audit.json": consent_path,
        "IAC-DPDP-001.patch": patch_path,
    }

    # 8. Cryptographic Rule 13 Evidence Bundle ZIP
    evidence_zip_path = report_dir / "cs01-evidence-bundle.zip"
    created_zip = create_evidence_bundle(
        report_files=report_map,
        scan_id="scan-fixture-001",
        scan_timestamp="2026-11-23T12:00:00Z",
        cs01_version="0.1.0-alpha",
        output_zip_path=evidence_zip_path,
    )
    report_map["cs01-evidence-bundle.zip"] = created_zip

    return report_map


@pytest.fixture
def mock_gui_state(
    capped_critical_bundle: ScoredFindingBundle,
    sample_report_files: dict[str, Path],
    multi_pii_hits: list[PiiHit],
) -> GuiScanState:
    """Return an initialized GuiScanState holding active audit data."""
    state = GuiScanState()
    state.update_state(
        bundle=capped_critical_bundle,
        report_files=sample_report_files,
        pii_hits=multi_pii_hits,
    )
    state.target_path = capped_critical_bundle.scan_root
    return state


@pytest.fixture
def dummy_clean_repo(tmp_path: Path) -> Path:
    """Generate a clean Python repository directory without personal data leaks."""
    repo = tmp_path / "clean_repo"
    repo.mkdir(parents=True, exist_ok=True)
    src = repo / "src"
    src.mkdir()
    (src / "main.py").write_text(
        "def compute_hash(val: str) -> str:\n"
        "    import hashlib\n"
        "    return hashlib.sha256(val.encode()).hexdigest()\n",
        encoding="utf-8",
    )
    return repo


@pytest.fixture
def dummy_leaky_repo(tmp_path: Path) -> Path:
    """Generate a Python repository with explicit PII leaks."""
    repo = tmp_path / "leaky_repo"
    repo.mkdir(parents=True, exist_ok=True)
    src = repo / "src"
    src.mkdir()
    (src / "service.py").write_text(
        "def process_kyc(aadhaar, pan):\n"
        "    print(f'Storing Aadhaar: {aadhaar}')\n"
        "    with open('/tmp/pan.txt', 'w') as f:\n"
        "        f.write(pan)\n",
        encoding="utf-8",
    )
    return repo


@pytest.fixture
def zip_slip_archive(tmp_path: Path) -> Path:
    """Create a malicious ZIP archive containing path traversal to test Zip-Slip defenses."""
    bad_zip = tmp_path / "malicious_zipslip.zip"
    with zipfile.ZipFile(bad_zip, "w") as zf:
        zf.writestr("../../evil.txt", "MALICIOUS PAYLOAD")
        zf.writestr("normal.txt", "NORMAL PAYLOAD")
    return bad_zip
