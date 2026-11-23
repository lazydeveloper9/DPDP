"""
CS-01 DPDP Compliance Desktop GUI - Scan Execution View (Screen 3).

Provides the live 6-stage pipeline progress stepper, determinate progress bar,
real-time log console, and cooperative cancel button for running audit scans.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.widgets.log_console import LogConsoleWidget


class ScanExecutionView(QWidget):
    """
    Execution screen with 6-stage stepper, progress bar, and live log console.

    Attributes:
        status_label: Short one-line status message above the progress bar.
        progress_bar: Determinate 0–100 progress bar for the audit pipeline.
        log_console:  Real-time coloured log stream from the pipeline worker.
        cancel_btn:   Cooperative cancellation button (enabled only while running).
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        title = QLabel("Pipeline Audit Execution")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #f8fafc;")
        layout.addWidget(title)

        # Stage stepper labels
        stages_label = QLabel(
            "Stages: 1·Ingest AST  2·Call Graph  3·Detect PII  4·Evaluate Rules  5·Risk & Evidence  6·Reports"
        )
        stages_label.setStyleSheet("color: #94a3b8; font-size: 11px;")
        layout.addWidget(stages_label)

        # Status description
        self.status_label = QLabel("Ready to initiate audit pipeline.")
        self.status_label.setStyleSheet("color: #f8fafc; font-size: 13px;")
        layout.addWidget(self.status_label)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(14)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; text-align: center; }"
            "QProgressBar::chunk { background-color: #2563eb; border-radius: 6px; }"
        )
        layout.addWidget(self.progress_bar)

        # Live log console
        self.log_console = LogConsoleWidget()
        layout.addWidget(self.log_console, stretch=1)

        # Cancel button
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("⛔ Cancel Audit")
        self.cancel_btn.setStyleSheet(
            "background-color: #ef4444; color: white; font-weight: bold; padding: 6px 16px;"
        )
        self.cancel_btn.setEnabled(False)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # -------------------------------------------------------------------------
    # Public API — called by MainWindow pipeline signal slots
    # -------------------------------------------------------------------------

    def on_stage_started(self, stage_num: int, stage_name: str) -> None:
        """Update status label when a pipeline stage begins."""
        self.status_label.setText(f"▶  Stage {stage_num}: {stage_name}")

    def on_progress_updated(self, pct: int, description: str) -> None:
        """Drive progress bar and status label from worker signal."""
        self.progress_bar.setValue(pct)
        self.status_label.setText(description)

    def on_scan_started(self) -> None:
        """Reset the view for a new scan run."""
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #1e293b; border: 1px solid #334155; border-radius: 6px; text-align: center; }"
            "QProgressBar::chunk { background-color: #2563eb; border-radius: 6px; }"
        )
        self.log_console.clear()
        self.status_label.setText("Audit pipeline starting…")
        self.cancel_btn.setEnabled(True)

    def on_scan_finished(self) -> None:
        """Mark the view as complete."""
        self.progress_bar.setValue(100)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("✓ Audit pipeline completed successfully.")

    def on_scan_failed(self, error: str) -> None:
        """Mark the view as failed."""
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #1e293b; border: 1px solid #ef4444; border-radius: 6px; text-align: center; }"
            "QProgressBar::chunk { background-color: #ef4444; border-radius: 6px; }"
        )
        self.status_label.setText(f"❌ Scan failed: {error}")

    def on_scan_cancelled(self) -> None:
        """Mark the view as cancelled."""
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("⚠ Audit cancelled by user.")
