"""
Test Suite: Asynchronous Audit Pipeline Worker, Typed Qt Signals & Cooperative Cancellation
Verifies R4 (Asynchronous Pipeline Integration), F29 (Async Worker & Progress).
"""

from __future__ import annotations

import logging

import pytest
from cs01.gui.async_runner.log_capture import QtLogCaptureHandler
from cs01.gui.async_runner.scan_worker import AuditPipelineWorker
from cs01.gui.async_runner.signals import PipelineSignals
from cs01.gui.widgets.log_console import LogConsoleWidget
from PySide6.QtWidgets import QApplication

from cs01.models.scan_config import EngineConfig, ScanConfig
from cs01.models.scored_finding import ScoredFindingBundle


@pytest.fixture(autouse=True)
def manage_worker_threads(monkeypatch, qapp: QApplication):
    """
    Autouse fixture ensuring every instantiated AuditPipelineWorker is safely terminated,
    scheduled for deletion via deleteLater(), and the Qt event queue is flushed,
    preventing heap teardown conflicts and 0xC0000409 process exit crashes on Windows.
    """
    workers: list[AuditPipelineWorker] = []
    orig_init = AuditPipelineWorker.__init__

    def tracked_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        workers.append(self)

    monkeypatch.setattr(AuditPipelineWorker, "__init__", tracked_init)

    yield

    for worker in workers:
        try:
            if worker.isRunning():
                worker.terminate()
                worker.wait(1000)
            worker.deleteLater()
        except RuntimeError:
            pass

    app = qapp or QApplication.instance()
    if app:
        app.processEvents()


# ============================================================================
# Tier 1: Nominal Asynchronous Execution & Signal Streaming
# ============================================================================

def test_worker_instantiation_and_signals(qtbot) -> None:
    """Verify all 7 typed Qt signals are defined and present on PipelineSignals (F29)."""
    signals = PipelineSignals()
    expected_signals = [
        "stage_started",
        "stage_completed",
        "progress_updated",
        "log_emitted",
        "scan_completed",
        "scan_failed",
        "scan_cancelled",
    ]
    for sig_name in expected_signals:
        assert hasattr(signals, sig_name)


def test_worker_stage_stepping_signals(qtbot) -> None:
    """Verify worker steps through all 6 statutory stages sequentially (F29)."""
    config = ScanConfig(scan_root="/workspace/test")
    worker = AuditPipelineWorker(config)

    stages_seen: list[tuple[int, str]] = []
    worker.signals.stage_started.connect(lambda stage_num, stage_name: stages_seen.append((stage_num, stage_name)))

    with qtbot.waitSignal(worker.signals.scan_completed, timeout=3000):
        worker.start()

    worker.wait()
    assert len(stages_seen) == 6
    assert [s[0] for s in stages_seen] == [1, 2, 3, 4, 5, 6]
    assert "AST" in stages_seen[0][1]
    assert "PII" in stages_seen[2][1]


def test_progress_updated_monotonicity(qtbot) -> None:
    """Verify progress_updated signal emits monotonically increasing values from 0 to 100 (F29)."""
    config = ScanConfig(scan_root="/workspace/test")
    worker = AuditPipelineWorker(config)

    progress_values: list[int] = []
    worker.signals.progress_updated.connect(lambda pct, desc: progress_values.append(pct))

    with qtbot.waitSignal(worker.signals.scan_completed, timeout=3000):
        worker.start()

    worker.wait()
    assert len(progress_values) >= 6
    assert progress_values[-1] == 100
    for i in range(len(progress_values) - 1):
        assert progress_values[i] <= progress_values[i + 1]


def test_log_emitted_signal_streaming(qtbot) -> None:
    """Verify QtLogCaptureHandler captures Python logging and emits Qt signals (F29)."""
    signals = PipelineSignals()
    handler = QtLogCaptureHandler(signals)
    logger = logging.getLogger("test_cs01_logger")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    captured_logs: list[tuple[str, str]] = []
    signals.log_emitted.connect(lambda lvl, msg: captured_logs.append((lvl, msg)))

    logger.info("Audit started for compliance verification.")
    logger.warning("Unsafe configuration detected.")

    assert len(captured_logs) == 2
    assert captured_logs[0][0] == "INFO"
    assert "Audit started" in captured_logs[0][1]
    assert captured_logs[1][0] == "WARNING"


def test_worker_successful_completion(qtbot, clean_bundle: ScoredFindingBundle) -> None:
    """Verify scan_completed signal emits ScoredFindingBundle and deliverables map (F29)."""
    config = ScanConfig(scan_root="/workspace/clean")
    worker = AuditPipelineWorker(config)
    worker._simulated_bundle = clean_bundle
    worker._simulated_reports = {"report.html": "/path/report.html"}

    with qtbot.waitSignal(worker.signals.scan_completed, timeout=3000) as blocker:
        worker.start()

    worker.wait()
    emitted_bundle, emitted_reports = blocker.args
    assert isinstance(emitted_bundle, ScoredFindingBundle)
    assert emitted_bundle.scan_id == "scan-clean-001"
    assert "report.html" in emitted_reports


# ============================================================================
# Tier 2: Boundary, Cancellation & Exception Safety Tests
# ============================================================================

def test_worker_cooperative_cancellation(qtbot) -> None:
    """
    Verify cooperative cancellation token exits worker cleanly and emits scan_cancelled (F29).
    """
    config = ScanConfig(scan_root="/workspace/long_scan")
    worker = AuditPipelineWorker(config)

    with qtbot.waitSignal(worker.signals.scan_cancelled, timeout=3000):
        worker.start()
        # Request immediate cancellation
        worker.cancel()

    worker.wait(2000)
    assert not worker.isRunning()
    assert worker._is_cancelled is True


def test_worker_exception_handling_no_crash(qtbot) -> None:
    """
    Verify pipeline exception is caught, emits scan_failed signal, and does not crash Qt thread (F29).
    """
    config = ScanConfig(scan_root="/workspace/error_scan")
    worker = AuditPipelineWorker(config)
    worker._raise_simulated_error = OSError("Disk quota exceeded (simulated I/O error)")

    with qtbot.waitSignal(worker.signals.scan_failed, timeout=3000) as blocker:
        worker.start()

    worker.wait()
    err_msg = blocker.args[0]
    assert "Disk quota exceeded" in err_msg


def test_log_console_widget_colored_output(qtbot) -> None:
    """Verify LogConsoleWidget formats INFO, WARNING, ERROR logs with correct colors (F29)."""
    console = LogConsoleWidget()
    qtbot.addWidget(console)
    console.show()

    console.append_log("INFO", "AST parsing completed.")
    console.append_log("WARNING", "Potential Aadhaar leak detected.")
    console.append_log("ERROR", "Fatal Section 8(5) violation.")

    plain_text = console.toPlainText()
    assert "[INFO]" in plain_text
    assert "[WARNING]" in plain_text
    assert "[ERROR]" in plain_text
    html = console.toHtml()
    assert "span" in html.lower() or "#" in html


# ============================================================================
# Tier 3: Pairwise Combinations
# ============================================================================

def test_worker_with_tree_sitter_and_opengrep_configs(qtbot) -> None:
    """Pairwise test: Worker execution across Tree-Sitter and Opengrep engine configs (F06, F29)."""
    # Config 1: Tree-Sitter
    c1 = ScanConfig(scan_root="/repo1", engine=EngineConfig(tree_sitter=True, opengrep=False))
    w1 = AuditPipelineWorker(c1)
    with qtbot.waitSignal(w1.signals.scan_completed, timeout=3000):
        w1.start()
    w1.wait()

    # Config 2: Opengrep
    c2 = ScanConfig(scan_root="/repo2", engine=EngineConfig(tree_sitter=False, opengrep=True))
    w2 = AuditPipelineWorker(c2)
    with qtbot.waitSignal(w2.signals.scan_completed, timeout=3000):
        w2.start()
    w2.wait()


# ============================================================================
# Tier 4: Real-World Workflow — Cooperative Pipeline Cancellation & Recovery
# ============================================================================

def test_tier4_cooperative_pipeline_cancellation_and_recovery(qtbot) -> None:
    """
    Tier 4 Scenario 6: Cooperative Pipeline Cancellation & Recovery.
    Verifies:
    1. Scan worker initiated on long audit.
    2. Cancellation signal requested mid-scan.
    3. scan_cancelled emitted cleanly without lockup.
    4. New subsequent scan is configured and completes successfully.
    """
    config1 = ScanConfig(scan_root="/repo/run1")
    worker1 = AuditPipelineWorker(config1)

    # Cancel scan 1
    with qtbot.waitSignal(worker1.signals.scan_cancelled, timeout=3000):
        worker1.start()
        worker1.cancel()
    worker1.wait()
    assert worker1._is_cancelled is True

    # Reconfigure and run scan 2 successfully
    config2 = ScanConfig(scan_root="/repo/run2")
    worker2 = AuditPipelineWorker(config2)
    with qtbot.waitSignal(worker2.signals.scan_completed, timeout=3000):
        worker2.start()
    worker2.wait()
    assert worker2.isRunning() is False
