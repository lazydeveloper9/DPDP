"""
CS-01 DPDP Compliance Desktop GUI - Typed Qt Signal Definitions.

Provides the PipelineSignals QObject carrying the 7 typed inter-thread
signals connecting AuditPipelineWorker to all UI views.
"""
from __future__ import annotations

from PySide6.QtCore import QObject, Signal


class PipelineSignals(QObject):
    """
    Typed Qt signals connecting the background worker to UI views.

    Signals:
        stage_started(int, str):        Emitted at the beginning of each pipeline stage.
        stage_completed(int, str, float): Emitted when a stage finishes with elapsed time.
        progress_updated(int, str):     Emitted with percentage (0-100) and status message.
        log_emitted(str, str):          Emitted with (level, message) for log console streaming.
        scan_completed(object, dict):   Emitted with (ScoredFindingBundle, report_files).
        scan_failed(str):               Emitted with error message on unrecoverable exception.
        scan_cancelled():               Emitted when cooperative cancellation completes.
    """

    stage_started = Signal(int, str)
    stage_completed = Signal(int, str, float)
    progress_updated = Signal(int, str)
    log_emitted = Signal(str, str)
    scan_completed = Signal(object, dict)
    scan_failed = Signal(str)
    scan_cancelled = Signal()
