"""
Script to capture offscreen screenshots of all 6 screens in CS-01 DPDP Compliance Auditor.
Saves rendered PNGs directly into the conversation artifact directory.
"""
import os
import sys
from pathlib import Path

# Headless offscreen
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QSize, Qt
from PySide6.QtGui import QColor, QFontDatabase, QImage, QPainter
from PySide6.QtWidgets import QApplication

from cs01.gui.main_window import MainWindow
from cs01.gui.qss_builder import build_qss
from cs01.gui.theme import DEFAULT_THEME
from cs01.models.flow_graph import FileRole, PiiHit, PiiType
from cs01.models.raw_finding import PassType, Severity
from cs01.models.scored_finding import (
    DpdpReadinessScore,
    ExposureContext,
    PillarScore,
    ScoredFinding,
    ScoredFindingBundle,
)

ARTIFACT_DIR = Path(r"C:\Users\ykn\.gemini\antigravity\brain\fe414285-3ea0-4dc6-bed1-0e21a4a225a1")

def make_sample_bundle() -> tuple[ScoredFindingBundle, list[PiiHit], dict[str, Path]]:
    findings = [
        ScoredFinding(
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
        ),
        ScoredFinding(
            id="finding-high-002",
            rule_id="CONSENT-001",
            pass_type=PassType.A,
            file="src/routes/auth.py",
            line_start=112,
            line_end=120,
            snippet="def register():\n    db.save(user, consent=True)  # No explicit affirmative consent check",
            dpdp_section="§6(1)",
            dpdp_rule="Rule 3(2)",
            penalty_band="50_crore",
            severity=Severity.HIGH,
            message="Missing verifiable affirmative consent mechanism before data ingestion (§6(1))",
            remediation="Present bilingual plain-language notice and require explicit opt-in checkbox before collection.",
            priority_score=78.5,
            confidence=0.95,
            exposure=ExposureContext.PRODUCTION,
            statutory_ceiling_display="₹50 Crore (§6(1) Notice & Consent)",
        ),
        ScoredFinding(
            id="finding-med-003",
            rule_id="LOG-PII-002",
            pass_type=PassType.B,
            file="src/middleware/request_logger.go",
            line_start=78,
            line_end=84,
            snippet="log.Infof(\"Processing KYC request for PAN: %s\", req.PAN)",
            dpdp_section="§8(5)",
            dpdp_rule="Rule 6(3)",
            penalty_band="250_crore",
            severity=Severity.MEDIUM,
            message="Raw PAN leakage to persistent application stdout/stderr logs (§8(5))",
            remediation="Apply statutory SHA-256 masking or redact with ABCDE****F pattern prior to logging.",
            priority_score=62.0,
            confidence=0.92,
            exposure=ExposureContext.INTERNAL,
            statutory_ceiling_display="₹250 Crore (§8(5) Security Safeguards)",
        ),
    ]

    pillar_ids = [
        ("notice_consent", "Notice & Consent (§5, §6)", 75.0, ["CONSENT-001"]),
        ("security_safeguards", "Security Safeguards (§8(5))", 38.0, ["CODE-DPDP-001", "LOG-PII-002"]),
        ("breach_readiness", "Breach Readiness (§8(6))", 85.0, []),
        ("retention_erasure", "Retention & Erasure (Rule 6)", 80.0, []),
        ("children_protection", "Children & PwD (§9)", 100.0, []),
        ("sdf_duties", "SDF Duties (§10, Rule 13)", 90.0, []),
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
        overall=58.5,
        is_capped=True,
        cap_reason="Unresolved CRITICAL finding in 250_crore band: CODE-DPDP-001 (§8(5))",
        pillars=pillars,
        max_statutory_ceiling_engaged="₹250 Crore (§8(5) Security Safeguards)",
        open_critical_count=1,
        open_high_count=1,
    )
    bundle = ScoredFindingBundle(
        scan_id="scan-demo-2026",
        scan_timestamp="2026-11-24T07:00:00Z",
        scan_root="/workspace/enterprise_banking_suite",
        findings=findings,
        readiness=readiness,
        total_files_scanned=142,
    )

    pii_hits = [
        PiiHit(
            id="pii-01",
            pii_type=PiiType.AADHAAR,
            file="src/models/user_vault.py",
            line=48,
            col=12,
            confidence=0.99,
            file_role=FileRole.PRODUCTION,
            value_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            validator_result="valid_verhoeff",
            line_snippet="aadhaar = 'XXXX-XXXX-9012'",
        ),
        PiiHit(
            id="pii-02",
            pii_type=PiiType.PAN,
            file="src/middleware/request_logger.go",
            line=80,
            col=10,
            confidence=0.98,
            file_role=FileRole.PRODUCTION,
            value_sha256="f2ca1bb6c7e907d06dafe4687e579fce76b37e4e93b7605022da52e6ccc26fd2",
            validator_result="valid_pan_individual",
            line_snippet="pan = 'ABCDE****F'",
        ),
        PiiHit(
            id="pii-03",
            pii_type=PiiType.MOBILE,
            file="src/services/sms_dispatcher.py",
            line=35,
            col=8,
            confidence=0.95,
            file_role=FileRole.PRODUCTION,
            value_sha256="7a38e032f3f465223f538e1e45da0c265c43d73a0330b60da5f81f0f4781749f",
            validator_result="valid_trai_series",
            line_snippet="mobile = '+91-98765-*****'",
        ),
        PiiHit(
            id="pii-04",
            pii_type=PiiType.GSTIN,
            file="src/billing/tax_engine.ts",
            line=64,
            col=15,
            confidence=0.97,
            file_role=FileRole.PRODUCTION,
            value_sha256="a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
            validator_result="valid_gstin_mh",
            line_snippet="gstin = '27AAAAA****1Z5'",
        ),
    ]

    # Create dummy report files in tmp
    tmp_reports = Path("./cs01-reports-dist")
    tmp_reports.mkdir(exist_ok=True)
    report_files = {
        "cs01-report.pdf": tmp_reports / "cs01-report.pdf",
        "cs01-report.md": tmp_reports / "cs01-report.md",
        "cs01-dpo-report.html": tmp_reports / "cs01-dpo-report.html",
        "cs01-dataflow.html": tmp_reports / "cs01-dataflow.html",
        "ropa_map.json": tmp_reports / "ropa_map.json",
        "cs01-findings.sarif": tmp_reports / "cs01-findings.sarif",
        "cs01-evidence-bundle.zip": tmp_reports / "cs01-evidence-bundle.zip",
        "fix_CODE_DPDP_001.patch": tmp_reports / "fix_CODE_DPDP_001.patch",
    }
    for p in report_files.values():
        p.write_text("ok", encoding="utf-8")

    return bundle, pii_hits, report_files


def main():
    app = QApplication.instance() or QApplication(sys.argv)

    # Load Windows system fonts into Qt font database for headless offscreen rendering
    font_paths = [
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\CascadiaCode.ttf",
        r"C:\Windows\Fonts\consola.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            QFontDatabase.addApplicationFont(fp)

    app.setStyleSheet(build_qss(DEFAULT_THEME))

    window = MainWindow()
    bundle, pii_hits, report_files = make_sample_bundle()

    # Populate bundle into window
    window.dashboard_view.bind_bundle(bundle)
    window.results_view.bind_bundle(bundle, pii_hits)
    window.pii_inventory_view.bind_pii_hits(pii_hits)
    window.report_view.bind_reports(report_files)
    window.scan_config_view.target_input.setText("C:/DPDP/sample_codebase")
    window.scan_config_view.validate_target()

    # In scan_execution_view, set a running simulation state
    window.scan_execution_view.on_scan_started()
    window.scan_execution_view.on_stage_started(3, "Indian PII Scanner")
    window.scan_execution_view.on_progress_updated(45, "Scanning 142 files for Indian PII identifiers...")
    window.scan_execution_view.log_console.append_log("INFO", "Stage 1: AST Parser parsed 142 source files.")
    window.scan_execution_view.log_console.append_log("INFO", "Stage 2: Interprocedural Call Graph generated 318 edges.")
    window.scan_execution_view.log_console.append_log("WARNING", "Stage 3: Detected unmasked Aadhaar pattern in src/models/user_vault.py:48.")
    window.scan_execution_view.log_console.append_log("INFO", "Stage 3: Verified PAN checksum with Verhoeff & Luhn engines.")

    window.resize(1440, 900)
    window.sidebar.set_collapsed(False)
    window.show()

    screens = [
        (0, "screenshot_dashboard.png"),
        (1, "screenshot_scan_setup.png"),
        (2, "screenshot_execution.png"),
        (3, "screenshot_findings.png"),
        (4, "screenshot_pii_inventory.png"),
        (5, "screenshot_reports.png"),
    ]

    for index, filename in screens:
        window.navigate_to(index)
        app.processEvents()

        # Capture window content
        pixmap = window.grab()
        out_path = ARTIFACT_DIR / filename
        pixmap.save(str(out_path), "PNG")
        print(f"Captured screen {index} -> {out_path} ({out_path.stat().st_size} bytes)")

    print("ALL SCREENSHOTS CAPTURED SUCCESSFULLY!")

if __name__ == "__main__":
    main()
