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
        status_message(str):            Emitted with current progress status description.
        log_emitted(str, str):          Emitted with (level, message) for log console streaming.
        finding_emitted(object):        Emitted incrementally when raw findings are evaluated.
        scan_completed(object, dict):   Emitted with (ScoredFindingBundle, report_files).
        audit_completed(object, dict):  Alias for scan_completed.
        scan_failed(str):               Emitted with error message on unrecoverable exception.
        audit_failed(str):              Alias for scan_failed.
        scan_cancelled():               Emitted when cooperative cancellation completes.
        audit_finished():               Guaranteed lifecycle completion signal (emitted in finally:).
    """

    stage_started = Signal(int, str)
    stage_completed = Signal(int, str, float)
    progress_updated = Signal(int, str)
    status_message = Signal(str)
    log_emitted = Signal(str, str)
    finding_emitted = Signal(object)
    scan_completed = Signal(object, dict)
    audit_completed = Signal(object, dict)
    scan_failed = Signal(str)
    audit_failed = Signal(str)
    scan_cancelled = Signal()
    audit_finished = Signal()
