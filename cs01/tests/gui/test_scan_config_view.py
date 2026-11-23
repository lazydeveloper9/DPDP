"""
Test Suite: Scan Configuration View, Ingestion Form & Target Validators
Verifies R2 (Input forms, target paths, remote Git URLs, validation),
F01, F02, F03, F04, F05, F06, F16, F25.
"""

from __future__ import annotations

import io
import tarfile
import zipfile
from pathlib import Path

from cs01.gui.views.scan_config_view import ScanConfigView
from PySide6.QtCore import Qt

from cs01.models.scan_config import ScanConfig

# ============================================================================
# Tier 1: Nominal Configuration & Validation Tests
# ============================================================================

def test_form_initial_defaults(qtbot) -> None:
    """Verify default field values on initial view presentation (F01, F05, F06)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    assert view.target_input.text() == ""
    assert view.engine_tree_sitter_radio.isChecked() is True
    assert view.engine_opengrep_radio.isChecked() is False
    assert view.fail_on_combo.currentText() == "high"
    assert view.dast_checkbox.isChecked() is False
    assert view.dast_disclaimer_checkbox.isEnabled() is False


def test_local_directory_valid_selection(qtbot, tmp_path: Path) -> None:
    """Verify entering an existing local directory passes path validation (F01)."""
    valid_dir = tmp_path / "valid_codebase"
    valid_dir.mkdir()

    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(valid_dir))
    is_valid, msg = view.validate_target()

    assert is_valid is True
    assert "Valid local directory" in msg
    assert "✓" in view.validation_label.text()


def test_valid_zip_archive_selection(qtbot, tmp_path: Path) -> None:
    """Verify entering a valid benign .zip archive passes archive validation (F02)."""
    zip_path = tmp_path / "app_source.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("index.js", "console.log('clean');")

    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(zip_path))
    is_valid, msg = view.validate_target()

    assert is_valid is True
    assert "Valid archive file" in msg
    assert "✓" in view.validation_label.text()


def test_valid_tar_gz_archive_selection(qtbot, tmp_path: Path) -> None:
    """Verify entering a valid .tar.gz archive passes archive validation (F02)."""
    tar_path = tmp_path / "app_source.tar.gz"
    with tarfile.open(tar_path, "w:gz"):
        pass

    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(tar_path))
    is_valid, msg = view.validate_target()

    assert is_valid is True
    assert "Valid archive file" in msg
    assert "✓" in view.validation_label.text()


def test_remote_git_https_url_parsing(qtbot) -> None:
    """Verify standard remote HTTPS Git URL format is recognized and parsed (F03, F04)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText("https://github.com/my-org/core-banking.git")
    is_valid, msg = view.validate_target()

    assert is_valid is True
    assert "Valid Git repository URL" in msg
    assert "✓" in view.validation_label.text()


def test_remote_git_tree_url_parsing(qtbot) -> None:
    """Verify GitHub tree URL parses clean clone URL and auto-populates branch field (F04)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText("https://github.com/my-org/core-banking/tree/feature-dpdp")
    is_valid, _msg = view.validate_target()

    assert is_valid is True
    assert view.branch_input.text() == "feature-dpdp"


def test_policy_gate_selection(qtbot) -> None:
    """Verify changing policy gate threshold updates ScanConfig fail_on attribute (F05)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    for threshold in ["critical", "high", "medium", "never"]:
        view.fail_on_combo.setCurrentText(threshold)
        config = view.get_scan_config()
        assert config.fail_on == threshold


def test_engine_selection_switch(qtbot) -> None:
    """Verify switching between Tree-Sitter and Opengrep radio buttons updates engine config (F06)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    # Switch to Opengrep
    qtbot.mouseClick(view.engine_opengrep_radio, Qt.MouseButton.LeftButton)
    assert view.engine_opengrep_radio.isChecked() is True
    assert view.engine_tree_sitter_radio.isChecked() is False
    config = view.get_scan_config()
    assert config.engine.opengrep is True
    assert config.engine.tree_sitter is False

    # Switch back to Tree-Sitter
    qtbot.mouseClick(view.engine_tree_sitter_radio, Qt.MouseButton.LeftButton)
    assert view.engine_tree_sitter_radio.isChecked() is True
    config2 = view.get_scan_config()
    assert config2.engine.tree_sitter is True
    assert config2.engine.opengrep is False


def test_start_scan_signal_emission(qtbot, dummy_clean_repo: Path) -> None:
    """Verify clicking Start Scan emits start_scan_requested signal with populated ScanConfig (F01)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(dummy_clean_repo))
    view.fail_on_combo.setCurrentText("critical")

    with qtbot.waitSignal(view.start_scan_requested, timeout=1000) as blocker:
        qtbot.mouseClick(view.start_scan_btn, Qt.MouseButton.LeftButton)

    emitted_config: ScanConfig = blocker.args[0]
    assert emitted_config.scan_root == str(dummy_clean_repo)
    assert emitted_config.fail_on == "critical"


# ============================================================================
# Tier 2: Boundary, Malformed Inputs & Security Defense Tests
# ============================================================================

def test_empty_target_path_validation(qtbot) -> None:
    """Verify empty path generates validation error and prevents signal emission (F01)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText("")
    is_valid, msg = view.validate_target()

    assert is_valid is False
    assert "Target path cannot be empty" in msg
    assert "❌" in view.validation_label.text()


def test_nonexistent_directory_validation(qtbot) -> None:
    """Verify nonexistent path is flagged with an error (F01)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText("C:\\nonexistent_dpdp_dir_xyz_123")
    is_valid, msg = view.validate_target()

    assert is_valid is False
    assert "does not exist" in msg
    assert "❌" in view.validation_label.text()


def test_corrupted_archive_validation(qtbot, tmp_path: Path) -> None:
    """Verify corrupted 0-byte .zip file is caught by archive validator (F02)."""
    corrupt_zip = tmp_path / "corrupted.zip"
    corrupt_zip.write_bytes(b"NOT_A_VALID_ZIP_HEADER")

    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(corrupt_zip))
    is_valid, msg = view.validate_target()

    assert is_valid is False
    assert "Corrupted archive" in msg


def test_zip_slip_malicious_archive_rejection(qtbot, zip_slip_archive: Path) -> None:
    """
    Verify Zip-Slip directory traversal archive (../../evil.txt) is detected and rejected (F02).
    """
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(zip_slip_archive))
    is_valid, msg = view.validate_target()

    assert is_valid is False
    assert "Zip Slip detected" in msg
    assert "❌" in view.validation_label.text()


def test_tar_slip_malicious_archive_rejection(qtbot, tmp_path: Path) -> None:
    """
    Verify Tar-Slip directory traversal archive (../../evil.txt) in .tar.gz is detected and rejected (F02).
    """
    tar_path = tmp_path / "slip.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        ti = tarfile.TarInfo(name="../../evil.txt")
        ti.size = 9
        tf.addfile(ti, io.BytesIO(b"malicious"))

    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(tar_path))
    is_valid, msg = view.validate_target()

    assert is_valid is False
    assert "Zip Slip detected" in msg
    assert "❌" in view.validation_label.text()


def test_windows_drive_path_archive_rejection(qtbot, tmp_path: Path) -> None:
    """
    Verify archive containing Windows absolute drive path (C:\\Windows\\cmd.exe) is detected and rejected (F02).
    """
    # 1. Zip archive with Windows absolute drive path
    zip_path = tmp_path / "absolute_windows.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("C:\\Windows\\cmd.exe", b"malicious")

    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(zip_path))
    is_valid, msg = view.validate_target()

    assert is_valid is False
    assert "Zip Slip detected" in msg
    assert "❌" in view.validation_label.text()

    # 2. Tar archive with Windows absolute drive path
    tar_path = tmp_path / "absolute_windows.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tf:
        ti = tarfile.TarInfo(name="C:/Windows/cmd.exe")
        ti.size = 9
        tf.addfile(ti, io.BytesIO(b"malicious"))

    view.target_input.setText(str(tar_path))
    is_valid_tar, msg_tar = view.validate_target()

    assert is_valid_tar is False
    assert "Zip Slip detected" in msg_tar
    assert "❌" in view.validation_label.text()


def test_invalid_git_url_protocol(qtbot) -> None:
    """Verify unsupported protocols like ftp:// are rejected (F04)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText("ftp://github.com/owner/repo.git")
    is_valid, msg = view.validate_target()

    assert is_valid is False
    assert "Unsupported protocol" in msg


def test_dast_prober_opt_in_disclaimer(qtbot) -> None:
    """Verify live HTTP DAST prober requires explicit statutory disclaimer opt-in (F25)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    # DAST checkbox unchecked initially
    assert view.dast_disclaimer_checkbox.isEnabled() is False
    assert view.get_scan_config().bonus.dast_probe is False

    # Check DAST checkbox -> disclaimer becomes enabled
    view.dast_checkbox.setChecked(True)
    assert view.dast_disclaimer_checkbox.isEnabled() is True
    # Without confirming disclaimer, bonus.dast_probe remains False
    assert view.get_scan_config().bonus.dast_probe is False

    # Check statutory disclaimer -> bonus.dast_probe becomes True
    view.dast_disclaimer_checkbox.setChecked(True)
    assert view.get_scan_config().bonus.dast_probe is True


# ============================================================================
# Tier 3: Pairwise Combinations
# ============================================================================

def test_git_url_with_fail_on_critical_and_opengrep(qtbot) -> None:
    """Pairwise combination: Remote Git URL + fail_on critical + Opengrep engine (F03, F05, F06)."""
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText("https://github.com/fintech/payments.git")
    view.fail_on_combo.setCurrentText("critical")
    qtbot.mouseClick(view.engine_opengrep_radio, Qt.MouseButton.LeftButton)

    config = view.get_scan_config()
    assert config.scan_root == "https://github.com/fintech/payments.git"
    assert config.fail_on == "critical"
    assert config.engine.opengrep is True
    assert config.engine.tree_sitter is False


def test_archive_with_baseline_path_and_dast_opt_in(qtbot, tmp_path: Path) -> None:
    """Pairwise combination: Valid archive + baseline path + DAST prober confirmation (F02, F16, F25)."""
    archive_file = tmp_path / "repo.zip"
    with zipfile.ZipFile(archive_file, "w") as zf:
        zf.writestr("app.py", "pass")
    baseline_file = tmp_path / ".cs01-baseline.json"
    baseline_file.write_text("{}", encoding="utf-8")

    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    view.target_input.setText(str(archive_file))
    view.baseline_input.setText(str(baseline_file))
    view.dast_checkbox.setChecked(True)
    view.dast_disclaimer_checkbox.setChecked(True)

    config = view.get_scan_config()
    assert config.scan_root == str(archive_file)
    assert config.baseline_path == str(baseline_file)
    assert config.bonus.dast_probe is True


# ============================================================================
# Tier 4: Real-World Workflow — Remote Git Shallow Scan & Branch Selection
# ============================================================================

def test_tier4_remote_git_shallow_scan_and_branch_selection(qtbot) -> None:
    """
    Tier 4 Scenario 3: Remote Git Shallow Scan & Branch Selection.
    Verifies inputting GitHub tree URL, auto-extracting branch ref,
    selecting engine, and emitting valid ScanConfig.
    """
    view = ScanConfigView()
    qtbot.addWidget(view)
    view.show()

    tree_url = "https://github.com/org/payment-service/tree/dpdp-compliance"
    view.target_input.setText(tree_url)

    is_valid, _msg = view.validate_target()
    assert is_valid is True
    assert view.branch_input.text() == "dpdp-compliance"

    with qtbot.waitSignal(view.start_scan_requested, timeout=1000) as blocker:
        qtbot.mouseClick(view.start_scan_btn, Qt.MouseButton.LeftButton)

    emitted_config: ScanConfig = blocker.args[0]
    assert emitted_config.scan_root == "https://github.com/org/payment-service/tree/dpdp-compliance"
    assert emitted_config.git_ref == "dpdp-compliance"
    assert emitted_config.fail_on == "high"
