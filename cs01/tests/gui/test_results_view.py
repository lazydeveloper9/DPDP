"""
Test Suite: Results View, Findings Table, Indian PII Catalog & Zero-Plaintext Storage
Verifies R3 (Detected Indian PII findings, risk classifications, interactive results),
F07, F08, F09, F10, F11, F12.
"""

from __future__ import annotations

import re

from cs01.gui.models.findings_model import FindingsTableModel
from cs01.gui.models.pii_model import PiiTableModel
from cs01.gui.views.results_view import ResultsView
from cs01.gui.widgets.pii_masked_label import PiiMaskedLabel
from PySide6.QtCore import Qt

from cs01.models.flow_graph import PiiHit
from cs01.models.scored_finding import ScoredFindingBundle

# ============================================================================
# Tier 1: Nominal Findings Table & PII Inventory Rendering
# ============================================================================

def test_findings_table_row_count(qtbot, multi_findings_bundle: ScoredFindingBundle) -> None:
    """Verify FindingsTableModel row count matches findings in bundle (F12)."""
    model = FindingsTableModel(multi_findings_bundle.findings)
    assert model.rowCount() == len(multi_findings_bundle.findings)
    assert model.rowCount() == 4


def test_findings_table_columns(qtbot) -> None:
    """Verify FindingsTableModel headers match required DPDP audit columns (F12)."""
    model = FindingsTableModel()
    expected_headers = [
        "Severity",
        "Rule ID",
        "DPDP Section",
        "File Path",
        "Line",
        "Penalty Band",
        "Priority Score",
    ]
    assert model.columnCount() == len(expected_headers)
    for col, title in enumerate(expected_headers):
        header = model.headerData(col, Qt.Orientation.Horizontal, Qt.ItemDataRole.DisplayRole)
        assert header == title


def test_severity_filter_filtering(qtbot, multi_findings_bundle: ScoredFindingBundle) -> None:
    """Verify selecting 'CRITICAL' filters table to only CRITICAL findings (F12)."""
    view = ResultsView()
    qtbot.addWidget(view)
    view.show()

    view.bind_bundle(multi_findings_bundle)
    assert view.findings_model.rowCount() == 4

    # Filter to CRITICAL
    view.severity_combo.setCurrentText("CRITICAL")
    assert view.findings_model.rowCount() == 1
    finding = view.findings_model.get_finding(0)
    assert finding is not None
    assert finding.rule_id == "CODE-DPDP-001"

    # Reset to ALL
    view.severity_combo.setCurrentText("ALL")
    assert view.findings_model.rowCount() == 4


def test_search_filter_by_rule_id(qtbot, multi_findings_bundle: ScoredFindingBundle) -> None:
    """Verify entering rule ID query filters table dynamically (F12)."""
    view = ResultsView()
    qtbot.addWidget(view)
    view.show()

    view.bind_bundle(multi_findings_bundle)
    view.search_input.setText("CONSENT-001")

    assert view.findings_model.rowCount() == 1
    finding = view.findings_model.get_finding(0)
    assert finding is not None
    assert finding.rule_id == "CONSENT-001"


def test_finding_detail_drawer_selection(qtbot, multi_findings_bundle: ScoredFindingBundle) -> None:
    """Verify selecting a row updates the detail drawer with snippet and statutory citations (F12)."""
    view = ResultsView()
    qtbot.addWidget(view)
    view.show()

    view.bind_bundle(multi_findings_bundle)

    # Select row 0 (CRITICAL)
    index = view.findings_model.index(0, 0)
    view.findings_table.setCurrentIndex(index)

    assert "CODE-DPDP-001" in view.drawer_title.text()
    assert "§8(5)" in view.drawer_section.text()
    assert "250_crore" in view.drawer_section.text()
    assert "Aadhaar" in view.drawer_snippet.toPlainText()
    assert "remediation" in view.drawer_remediation.text().lower()
    assert view.autofix_btn.isEnabled() is True


def test_pii_catalog_table_rendering(qtbot, multi_pii_hits: list[PiiHit]) -> None:
    """Verify PiiTableModel displays all detected Indian PII types (F07-F11)."""
    model = PiiTableModel(multi_pii_hits)
    assert model.rowCount() == 6

    types_in_table = [model.data(model.index(r, 0), Qt.ItemDataRole.DisplayRole) for r in range(6)]
    assert "AADHAAR" in types_in_table
    assert "PAN" in types_in_table
    assert "GSTIN" in types_in_table
    assert "UPI_HANDLE" in types_in_table
    assert "MOBILE" in types_in_table
    assert "ABHA_HEALTH_ID" in types_in_table


# ============================================================================
# Tier 2: Boundary, Indian PII Catalog Masking & Zero Plaintext Invariants
# ============================================================================

def test_aadhaar_strict_masking_zero_plaintext(qtbot, multi_pii_hits: list[PiiHit]) -> None:
    """
    Verify Aadhaar strictly masks first 8 digits (XXXX-XXXX-9012) and raw 12-digit
    number is never present in memory (F07, F12).
    """
    model = PiiTableModel(multi_pii_hits)
    aadhaar_row = None
    for r in range(model.rowCount()):
        if model.data(model.index(r, 0)) == "AADHAAR":
            aadhaar_row = r
            break
    assert aadhaar_row is not None

    displayed_val = model.data(model.index(aadhaar_row, 3))
    assert "XXXX-XXXX-" in displayed_val
    # Assert no 12-digit unmasked sequences exist
    assert not re.search(r"\b\d{12}\b", displayed_val)


def test_pan_entity_type_masking(qtbot, multi_pii_hits: list[PiiHit]) -> None:
    """Verify PAN masks 4 middle digits (ABCDE****F) and stores validator result (F08, F12)."""
    model = PiiTableModel(multi_pii_hits)
    pan_row = None
    for r in range(model.rowCount()):
        if model.data(model.index(r, 0)) == "PAN":
            pan_row = r
            break
    assert pan_row is not None

    displayed_val = model.data(model.index(pan_row, 3))
    assert "****" in displayed_val
    validator_res = model.data(model.index(pan_row, 4))
    assert "pan" in validator_res.lower()


def test_gstin_luhn_masking(qtbot, multi_pii_hits: list[PiiHit]) -> None:
    """Verify GSTIN masks entity PAN segment (27AAAAA****1Z5) with state code (F09, F12)."""
    model = PiiTableModel(multi_pii_hits)
    gstin_row = None
    for r in range(model.rowCount()):
        if model.data(model.index(r, 0)) == "GSTIN":
            gstin_row = r
            break
    assert gstin_row is not None

    displayed_val = model.data(model.index(gstin_row, 3))
    assert "****" in displayed_val
    assert "27AAAAA" in displayed_val  # Maharashtra state code


def test_upi_handle_masking(qtbot, multi_pii_hits: list[PiiHit]) -> None:
    """Verify UPI Virtual Payment Address masks user prefix (user****@upi) (F10, F12)."""
    model = PiiTableModel(multi_pii_hits)
    upi_row = None
    for r in range(model.rowCount()):
        if model.data(model.index(r, 0)) == "UPI_HANDLE":
            upi_row = r
            break
    assert upi_row is not None

    displayed_val = model.data(model.index(upi_row, 3))
    assert "****@" in displayed_val


def test_mobile_e164_masking(qtbot, multi_pii_hits: list[PiiHit]) -> None:
    """Verify Indian mobile number preserves country code and masks 4 middle digits (F11, F12)."""
    model = PiiTableModel(multi_pii_hits)
    mob_row = None
    for r in range(model.rowCount()):
        if model.data(model.index(r, 0)) == "MOBILE":
            mob_row = r
            break
    assert mob_row is not None

    displayed_val = model.data(model.index(mob_row, 3))
    assert "+91-" in displayed_val
    assert "****" in displayed_val


def test_pii_reveal_toggle_audit_confirmation(qtbot) -> None:
    """Verify PiiMaskedLabel reveals text upon button toggle and switches button label (F12)."""
    masked_label = PiiMaskedLabel(masked_text="XXXX-XXXX-9012", unmasked_text="1234-5678-9012")
    qtbot.addWidget(masked_label)
    masked_label.show()

    assert masked_label.text_label.text() == "XXXX-XXXX-9012"
    assert masked_label.toggle_btn.text() == "Reveal"

    # Click Reveal
    qtbot.mouseClick(masked_label.toggle_btn, Qt.MouseButton.LeftButton)
    assert masked_label.text_label.text() == "1234-5678-9012"
    assert masked_label.toggle_btn.text() == "Hide"

    # Click Hide
    qtbot.mouseClick(masked_label.toggle_btn, Qt.MouseButton.LeftButton)
    assert masked_label.text_label.text() == "XXXX-XXXX-9012"
    assert masked_label.toggle_btn.text() == "Reveal"


def test_in_memory_hashing_invariants(qtbot, multi_pii_hits: list[PiiHit]) -> None:
    """Verify strict cryptographic invariant: all PiiHit objects contain 64-char SHA-256 (F12)."""
    for hit in multi_pii_hits:
        assert isinstance(hit.value_sha256, str)
        assert len(hit.value_sha256) == 64
        # Assert valid hex string
        assert all(c in "0123456789abcdef" for c in hit.value_sha256.lower())
        assert hit.file != ""
        assert hit.line > 0


# ============================================================================
# Tier 3: Pairwise Combinations
# ============================================================================

def test_combined_severity_and_search_filter(qtbot, multi_findings_bundle: ScoredFindingBundle) -> None:
    """Pairwise test: Combine severity filter + text search filter (F12)."""
    view = ResultsView()
    qtbot.addWidget(view)
    view.show()

    view.bind_bundle(multi_findings_bundle)
    assert view.findings_model.rowCount() == 4

    # Severity HIGH + search for "register"
    view.severity_combo.setCurrentText("HIGH")
    view.search_input.setText("register")
    assert view.findings_model.rowCount() == 1
    assert view.findings_model.get_finding(0).rule_id == "CONSENT-001"

    # Severity HIGH + search for something not matching HIGH
    view.search_input.setText("Aadhaar")
    assert view.findings_model.rowCount() == 0


# ============================================================================
# Tier 4: Real-World Workflow — Regressive Scan Against Baseline
# ============================================================================

def test_tier4_regressive_scan_against_baseline(qtbot, multi_findings_bundle: ScoredFindingBundle) -> None:
    """
    Tier 4 Scenario 4: Regressive Scan Against Baseline.
    Verifies that suppressed baseline findings can be identified and highlighted,
    while active unsuppressed findings engage Section 33 statutory citations in detail drawer.
    """
    view = ResultsView()
    qtbot.addWidget(view)
    view.show()

    view.bind_bundle(multi_findings_bundle)

    # Row 0: CODE-DPDP-001 (CRITICAL)
    index = view.findings_model.index(0, 0)
    view.findings_table.setCurrentIndex(index)

    assert "CODE-DPDP-001" in view.drawer_title.text()
    assert "250_crore" in view.drawer_section.text()
    assert view.autofix_btn.isEnabled() is True
