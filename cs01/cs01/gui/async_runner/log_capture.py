"""
CS-01 DPDP Compliance Desktop GUI - Qt Log Capture Handler.

Bridges Python's standard logging to PipelineSignals.log_emitted for
real-time streaming to the LogConsoleWidget in ScanExecutionView.
"""
from __future__ import annotations

import logging

from cs01.gui.async_runner.signals import PipelineSignals


class QtLogCaptureHandler(logging.Handler):
    """
    Bridges standard Python logging to PipelineSignals.log_emitted Qt signal.

    Install on the root logger or any named logger to stream all log records
    to the live LogConsoleWidget without blocking the UI thread.
    """

    def __init__(self, signals: PipelineSignals) -> None:
        super().__init__()
        self.signals = signals

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname
            self.signals.log_emitted.emit(level, msg)
        except Exception:
            self.handleError(record)
