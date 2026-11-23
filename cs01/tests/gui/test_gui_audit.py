"""
Automated Test Suite: CS-01 PySide/Qt Desktop GUI End-to-End Audit Integration.

Verifies:
1. AuditWorker nominal execution via Qt signals and moveToThread compatibility.
2. Guaranteed audit_finished signal emission in finally: block.
3. Fail-explicit error surfacing when target path does not exist.
4. UI control locking: start button disabled during audit and re-enabled after audit_finished.
5. Cooperative cancellation exits cleanly and restores UI state.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QThread
from PySide6.QtWidgets import QApplication

from cs01.gui.async_runner.scan_worker import AuditPipelineWorker, AuditWorker
from cs01.gui.main_window import MainWindow
from cs01.models.scan_config import ScanConfig
from cs01.models.scored_finding import ScoredFindingBundle


def test_audit_worker_nominal_signals(qtbot, tmp_path: Path) -> None:
    """AuditWorker runs, emits stage signals, progress, scan_completed, and audit_finished."""
    cfg = ScanConfig(scan_root="/workspace/test_nominal", output_dir=str(tmp_path))
    worker = AuditWorker(cfg)

    stages: list[int] = []
    completed_bundles: list[object] = []
    finished_called: list[bool] = []

    worker.signals.stage_started.connect(lambda num, name: stages.append(num))
    worker.signals.audit_completed.connect(lambda bundle, reps: completed_bundles.append(bundle))
    worker.signals.audit_finished.connect(lambda: finished_called.append(True))

    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.signals.audit_finished.connect(thread.quit)

    with qtbot.waitSignal(worker.signals.audit_finished, timeout=5000):
        thread.start()

    thread.wait(2000)
    assert len(stages) == 6
    assert len(completed_bundles) == 1
    assert len(finished_called) == 1
    assert isinstance(completed_bundles[0], ScoredFindingBundle)


def test_audit_worker_invalid_path_fails_explicitly(qtbot, tmp_path: Path) -> None:
    """Non-existent real path raises FileNotFoundError and emits audit_failed and audit_finished."""
    invalid_path = str(tmp_path / "non_existent_codebase_xyz_999")
    cfg = ScanConfig(scan_root=invalid_path, output_dir=str(tmp_path))
    worker = AuditWorker(cfg)

    failed_errors: list[str] = []
    finished_called: list[bool] = []

    worker.signals.audit_failed.connect(lambda err: failed_errors.append(err))
    worker.signals.audit_finished.connect(lambda: finished_called.append(True))

    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.signals.audit_finished.connect(thread.quit)

    with qtbot.waitSignal(worker.signals.audit_finished, timeout=5000):
        thread.start()

    thread.wait(2000)
    assert len(failed_errors) == 1
    assert "does not exist" in failed_errors[0]
    assert len(finished_called) == 1


def test_audit_worker_cooperative_cancellation(qtbot, tmp_path: Path) -> None:
    """Worker can be cancelled cooperatively, emitting scan_cancelled and audit_finished."""
    cfg = ScanConfig(scan_root="/workspace/long_run", output_dir=str(tmp_path))
    worker = AuditWorker(cfg)

    cancelled: list[bool] = []
    finished: list[bool] = []

    worker.signals.scan_cancelled.connect(lambda: cancelled.append(True))
    worker.signals.audit_finished.connect(lambda: finished.append(True))

    thread = QThread()
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.signals.audit_finished.connect(thread.quit)

    thread.start()
    worker.cancel()

    with qtbot.waitSignal(worker.signals.audit_finished, timeout=5000):
        pass

    thread.wait(2000)
    assert len(cancelled) == 1
    assert len(finished) == 1


def test_main_window_controls_locked_during_audit(qtbot, tmp_path: Path) -> None:
    """MainWindow locks Start button during active scan and restores it on audit_finished."""
    win = MainWindow()
    qtbot.addWidget(win)

    start_btn = win.scan_config_view.start_scan_btn
    cancel_btn = win.scan_execution_view.cancel_btn

    # Initial state: button can be enabled
    win.scan_config_view.target_input.setText("/workspace/sample_target")

    cfg = ScanConfig(scan_root="/workspace/sample_target", output_dir=str(tmp_path))
    win._on_start_scan_requested(cfg)

    # Immediately after request: start button disabled, cancel enabled
    assert not start_btn.isEnabled()
    assert cancel_btn.isEnabled()

    # Wait for completion
    with qtbot.waitSignal(win._worker.signals.audit_finished, timeout=5000):
        pass

    win._worker.wait(2000)
    QApplication.processEvents()

    # After completion: start button re-enabled, cancel disabled
    assert start_btn.isEnabled()
    assert not cancel_btn.isEnabled()
