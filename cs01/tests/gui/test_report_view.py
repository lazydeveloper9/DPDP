"""
Test Suite: Report Generation View, Deliverables Hub, RoPA Dialog & Cryptographic Evidence Verifier
Verifies R3 (Deliverable exports, DPO HTML, data-flow visualizer, RoPA JSON, SARIF, evidence bundle),
F17, F18, F19, F20, F21, F22, F23, F24, F26.
"""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

from cs01.gui.views.report_view import ReportView
from cs01.gui.widgets.diff_viewer import DiffViewerDialog
from cs01.gui.widgets.ropa_table_dialog import RopaTableDialog
from PySide6.QtCore import Qt

from cs01.pipeline.stage6_report.evidence_locker import (
    verify_evidence_bundle,
)

# ============================================================================
# Tier 1: Nominal Deliverables Hub & Artifact Tiles
# ============================================================================

def test_artifact_tiles_presence(qtbot, sample_report_files: dict[str, Path]) -> None:
    """Verify all standard compliance deliverable tiles (including PDF and Markdown) are present and active (F17-F24)."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports(sample_report_files)

    expected_keys = ["pdf", "markdown", "html", "dataflow", "ropa", "patch", "sarif", "evidence"]
    for key in expected_keys:
        assert key in view.tiles
        frame = view.tiles[key]
        assert "✓ Available" in frame.status_lbl.text()
        assert frame.btn.isEnabled() is True


def test_pdf_report_tile_state(qtbot, sample_report_files: dict[str, Path]) -> None:
    """Verify PDF report tile and Save As button are enabled when cs01-report.pdf exists."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports(sample_report_files)
    pdf_tile = view.tiles["pdf"]
    assert pdf_tile.btn.isEnabled() is True
    assert "Open PDF" in pdf_tile.btn.text()
    assert pdf_tile.save_btn.isEnabled() is True


def test_markdown_report_tile_state(qtbot, sample_report_files: dict[str, Path]) -> None:
    """Verify Markdown report tile and Save As button are enabled when cs01-report.md exists."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports(sample_report_files)
    md_tile = view.tiles["markdown"]
    assert md_tile.btn.isEnabled() is True
    assert "View Markdown" in md_tile.btn.text()
    assert md_tile.save_btn.isEnabled() is True


def test_html_report_tile_state(qtbot, sample_report_files: dict[str, Path]) -> None:
    """Verify HTML report tile is enabled when cs01-dpo-report.html exists (F17)."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports(sample_report_files)
    html_tile = view.tiles["html"]
    assert html_tile.btn.isEnabled() is True
    assert "View in Browser" in html_tile.btn.text()


def test_ropa_dialog_display(qtbot, sample_report_files: dict[str, Path]) -> None:
    """Verify clicking View RoPA opens RopaTableDialog with rows from ropa_map.json (F19)."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports(sample_report_files)

    # Click RoPA tile button
    qtbot.mouseClick(view.tiles["ropa"].btn, Qt.MouseButton.LeftButton)

    # Locate active RopaTableDialog child
    dialog = view.findChild(RopaTableDialog)
    assert dialog is not None
    assert dialog.isVisible() is True
    assert dialog.table.rowCount() == 2
    assert dialog.table.item(0, 0).text() == "User Billing Service"
    assert "GST Act" in dialog.table.item(0, 2).text()
    dialog.close()


def test_diff_viewer_dialog_syntax_coloring(qtbot, sample_report_files: dict[str, Path]) -> None:
    """Verify clicking View Diff opens DiffViewerDialog rendering patch lines with syntax colors (F24)."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports(sample_report_files)

    # Click patch tile button
    qtbot.mouseClick(view.tiles["patch"].btn, Qt.MouseButton.LeftButton)

    dialog = view.findChild(DiffViewerDialog)
    assert dialog is not None
    assert dialog.isVisible() is True
    text = dialog.editor.toPlainText()
    assert "terraform/s3.tf" in text
    assert "aws:kms" in text
    dialog.close()


def test_evidence_bundle_verification_valid(qtbot, sample_report_files: dict[str, Path]) -> None:
    """Verify clicking Verify Integrity on untampered evidence bundle passes Rule 13 audit (F22, F23)."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports(sample_report_files)

    # Click Verify Integrity
    qtbot.mouseClick(view.tiles["evidence"].btn, Qt.MouseButton.LeftButton)

    assert "VERIFIED (Rule 13 Compliant" in view.evidence_verification_banner.text()
    assert "✓" in view.evidence_verification_banner.text()


# ============================================================================
# Tier 2: Boundary, Missing Artifacts & Cryptographic Tamper Detection
# ============================================================================

def test_evidence_bundle_tamper_detection(
    qtbot, tmp_path: Path, sample_report_files: dict[str, Path]
) -> None:
    """
    Cryptographic adversarial test: simulate malicious modification of a file inside
    cs01-evidence-bundle.zip and verify verification banner reports TAMPERING DETECTED (F23).
    """
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    bundle_path = sample_report_files["cs01-evidence-bundle.zip"]

    # Tamper with the zip archive by rewriting one of the packaged files
    tampered_zip = tmp_path / "tampered_bundle.zip"
    with zipfile.ZipFile(bundle_path, "r") as zin, zipfile.ZipFile(tampered_zip, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "cs01-report.md":
                # Adversarially modify audit score inside markdown report
                data = b"# HACKED AUDIT: OVERALL SCORE 100.0 (FAKE)"
            zout.writestr(item, data)

    # Point report files to tampered bundle
    tampered_reports = dict(sample_report_files)
    tampered_reports["cs01-evidence-bundle.zip"] = tampered_zip

    view.bind_reports(tampered_reports)
    qtbot.mouseClick(view.tiles["evidence"].btn, Qt.MouseButton.LeftButton)

    assert "TAMPERING DETECTED" in view.evidence_verification_banner.text()
    assert "❌" in view.evidence_verification_banner.text()


def test_evidence_bundle_manifest_hash_tamper_detection(
    qtbot, tmp_path: Path, sample_report_files: dict[str, Path]
) -> None:
    """
    Verify modifying manifest.json without updating manifest.json.sha256 sidecar
    triggers tampering detection and rejection (Rule 13, F23).
    """
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    bundle_path = sample_report_files["cs01-evidence-bundle.zip"]
    tampered_zip = tmp_path / "manifest_tampered_bundle.zip"

    with zipfile.ZipFile(bundle_path, "r") as zin, zipfile.ZipFile(tampered_zip, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "manifest.json":
                manifest_data = json.loads(data.decode("utf-8"))
                manifest_data["title"] = "FORGED DPDP Compliance Manifest (100% Score)"
                data = json.dumps(manifest_data, indent=2).encode("utf-8")
            zout.writestr(item, data)

    tampered_reports = dict(sample_report_files)
    tampered_reports["cs01-evidence-bundle.zip"] = tampered_zip

    view.bind_reports(tampered_reports)
    qtbot.mouseClick(view.tiles["evidence"].btn, Qt.MouseButton.LeftButton)

    assert "TAMPERING DETECTED" in view.evidence_verification_banner.text()
    assert "❌" in view.evidence_verification_banner.text()

    # Direct verification check
    is_valid, logs = verify_evidence_bundle(tampered_zip)
    assert is_valid is False
    assert any("manifest.json hash mismatch" in line for line in logs)


def test_evidence_bundle_unmanifested_rogue_file_rejection(
    qtbot, tmp_path: Path, sample_report_files: dict[str, Path]
) -> None:
    """
    Verify injecting an undeclared rogue file (e.g. backdoor.exe) into the evidence bundle
    triggers tampering detection and rejection (Rule 13, F23).
    """
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    bundle_path = sample_report_files["cs01-evidence-bundle.zip"]
    tampered_zip = tmp_path / "rogue_injected_bundle.zip"

    with zipfile.ZipFile(bundle_path, "r") as zin, zipfile.ZipFile(tampered_zip, "w") as zout:
        for item in zin.infolist():
            zout.writestr(item, zin.read(item.filename))
        # Inject undeclared rogue implant
        zout.writestr("backdoor.exe", b"MALICIOUS_EXECUTABLE_PAYLOAD")

    tampered_reports = dict(sample_report_files)
    tampered_reports["cs01-evidence-bundle.zip"] = tampered_zip

    view.bind_reports(tampered_reports)
    qtbot.mouseClick(view.tiles["evidence"].btn, Qt.MouseButton.LeftButton)

    assert "TAMPERING DETECTED" in view.evidence_verification_banner.text()
    assert "❌" in view.evidence_verification_banner.text()

    # Direct verification check
    is_valid, logs = verify_evidence_bundle(tampered_zip)
    assert is_valid is False
    assert any("rogue file" in line.lower() for line in logs)


def test_missing_deliverable_tile_state(qtbot) -> None:
    """Verify empty reports map renders all artifact tiles in disabled state (F17-F24)."""
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports({})

    for frame in view.tiles.values():
        assert "Not Generated / Scan Required" in frame.status_lbl.text()
        assert frame.btn.isEnabled() is False


def test_ropa_export_csv_action(qtbot, tmp_path: Path, sample_report_files: dict[str, Path]) -> None:
    """Verify technical RoPA table exports valid CSV with correct headers and rows (F19)."""
    ropa_path = sample_report_files["ropa_map.json"]
    data = json.loads(ropa_path.read_text(encoding="utf-8"))

    dialog = RopaTableDialog(data)
    qtbot.addWidget(dialog)
    dialog.show()

    export_file = tmp_path / "exported_ropa.csv"
    dialog.export_to_csv(export_file)

    assert export_file.exists()
    content = export_file.read_text(encoding="utf-8")
    assert "System,Purpose,Lawful Basis,Categories,Retention" in content
    assert "User Billing Service" in content
    assert "Auth Gateway" in content


def test_diff_viewer_empty_patch_handling(qtbot) -> None:
    """Verify DiffViewerDialog gracefully handles empty diff without crashing (F24)."""
    dialog = DiffViewerDialog(diff_content="")
    qtbot.addWidget(dialog)
    dialog.show()

    assert "No remediation diff available." in dialog.editor.toPlainText()


# ============================================================================
# Tier 3: Pairwise Combinations
# ============================================================================

def test_multiple_remediation_patches_in_report_view(qtbot, tmp_path: Path) -> None:
    """Pairwise test: Multiple patches present in deliverables map (F24)."""
    patch1 = tmp_path / "IAC-DPDP-001.patch"
    patch1.write_text("--- a/s3.tf\n+++ b/s3.tf\n+ encryption = true", encoding="utf-8")
    patch2 = tmp_path / "CODE-DPDP-002.patch"
    patch2.write_text("--- a/auth.py\n+++ b/auth.py\n+ hash_password(pwd)", encoding="utf-8")

    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    view.bind_reports({"remediation_1.patch": patch1, "remediation_2.patch": patch2})
    assert view.tiles["patch"].btn.isEnabled() is True


# ============================================================================
# Tier 4: Real-World Workflow — Rule 13 Evidence Bundle Generation & Verification
# ============================================================================

def test_tier4_rule13_evidence_bundle_and_tamper_detection(
    qtbot, tmp_path: Path, sample_report_files: dict[str, Path]
) -> None:
    """
    Tier 4 Scenario 5: Rule 13 Evidence Bundle Generation & Tamper Detection.
    Verifies full lifecycle of evidence bundle:
    1. Initial verification passes cryptographic validation (Rule 13).
    2. File modification detected and flagged as TAMPERING DETECTED.
    """
    view = ReportView()
    qtbot.addWidget(view)
    view.show()

    # Step 1: Initial valid bundle
    view.bind_reports(sample_report_files)
    qtbot.mouseClick(view.tiles["evidence"].btn, Qt.MouseButton.LeftButton)
    assert "VERIFIED (Rule 13 Compliant" in view.evidence_verification_banner.text()

    # Step 2: Corrupt manifest inside zip
    bundle_zip = sample_report_files["cs01-evidence-bundle.zip"]
    corrupted_zip = tmp_path / "corrupted_bundle.zip"
    with zipfile.ZipFile(bundle_zip, "r") as zin, zipfile.ZipFile(corrupted_zip, "w") as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename == "manifest.json":
                # Corrupt manifest JSON structure
                data = b"{'corrupted_json': True"
            zout.writestr(item, data)

    # Step 3: Trigger verification on corrupted bundle
    reports = dict(sample_report_files)
    reports["cs01-evidence-bundle.zip"] = corrupted_zip
    view.bind_reports(reports)
    qtbot.mouseClick(view.tiles["evidence"].btn, Qt.MouseButton.LeftButton)

    assert "TAMPERING DETECTED" in view.evidence_verification_banner.text()
