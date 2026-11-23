"""
CS-01 DPDP Compliance Desktop GUI - Scan Execution View (Screen 3).

Provides the live 6-stage pipeline progress stepper, determinate progress bar,
real-time log console, and cooperative cancel button for running audit scans.
"""
from __future__ import annotations

import time
from typing import Final

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import (
    COLOR_BG_CARD,
    COLOR_BORDER_SUBTLE,
    COLOR_STATUS_SUCCESS,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
)
from cs01.gui.widgets.log_console import LogConsoleWidget

STAGES_INFO: Final[list[tuple[int, str, str]]] = [
    (1, "Ingest & AST", "Parse target source & models"),
    (2, "Call Graph", "Resolve interprocedural flows"),
    (3, "Indian PII", "Detect Aadhaar, PAN & personal data"),
    (4, "Evaluate Rules", "Execute statutory DPDP rules"),
    (5, "Risk & Evidence", "Classify risk & hash evidence"),
    (6, "Reports & RoPA", "Generate executive deliverables"),
]


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
        self._start_time: float = 0.0
        self._stage_widgets: dict[int, dict[str, QLabel | QFrame]] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        # 1. Header
        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(3)

        title = QLabel("Pipeline Audit Execution")
        title.setStyleSheet(f"font-size: 19px; font-weight: 700; color: {COLOR_TEXT_PRIMARY};")
        header_vbox.addWidget(title)

        subtitle = QLabel("Live real-time monitoring of local multi-stage AST analysis, PII scanning, and rule evaluation.")
        subtitle.setStyleSheet(f"font-size: 9.5pt; color: {COLOR_TEXT_SECONDARY};")
        header_vbox.addWidget(subtitle)
        layout.addLayout(header_vbox)

        # 2. 6-Stage Visual Stepper Grid
        stepper_frame = QFrame()
        stepper_frame.setStyleSheet(
            f"QFrame {{ background-color: {COLOR_BG_CARD}; "
            f"border: 1px solid {COLOR_BORDER_SUBTLE}; border-radius: 8px; padding: 10px; }}"
        )
        stepper_layout = QGridLayout(stepper_frame)
        stepper_layout.setContentsMargins(10, 10, 10, 10)
        stepper_layout.setSpacing(10)

        for idx, (num, name, desc) in enumerate(STAGES_INFO):
            node_box = QFrame()
            node_box.setStyleSheet(
                "QFrame { background-color: #0b1120; border: 1px solid #2b3b52; border-radius: 6px; padding: 6px; }"
            )
            node_layout = QVBoxLayout(node_box)
            node_layout.setContentsMargins(8, 6, 8, 6)
            node_layout.setSpacing(2)

            top_h = QHBoxLayout()
            num_lbl = QLabel(f"Stage {num}")
            num_lbl.setStyleSheet("font-size: 8pt; font-weight: bold; color: #71829b;")
            status_pill = QLabel("Pending")
            status_pill.setStyleSheet(
                "font-size: 7.5pt; color: #64748b; background-color: rgba(100, 116, 139, 0.15); "
                "padding: 1px 4px; border-radius: 3px;"
            )
            top_h.addWidget(num_lbl)
            top_h.addStretch()
            top_h.addWidget(status_pill)
            node_layout.addLayout(top_h)

            name_lbl = QLabel(name)
            name_lbl.setStyleSheet(f"font-size: 9.5pt; font-weight: 600; color: {COLOR_TEXT_PRIMARY};")
            node_layout.addWidget(name_lbl)

            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("font-size: 8pt; color: #94a3b8;")
            desc_lbl.setWordWrap(True)
            node_layout.addWidget(desc_lbl)

            col = idx % 3
            row = idx // 3
            stepper_layout.addWidget(node_box, row, col)

            self._stage_widgets[num] = {
                "box": node_box,
                "status": status_pill,
                "num": num_lbl,
                "name": name_lbl,
            }

        layout.addWidget(stepper_frame)

        # 3. Overall Progress & Status description
        progress_vbox = QVBoxLayout()
        progress_vbox.setSpacing(6)

        status_row = QHBoxLayout()
        self.status_label = QLabel("Ready to initiate audit pipeline.")
        self.status_label.setStyleSheet(f"color: {COLOR_TEXT_PRIMARY}; font-size: 10pt; font-weight: 500;")
        status_row.addWidget(self.status_label, stretch=1)

        self.elapsed_label = QLabel("")
        self.elapsed_label.setStyleSheet("color: #a6b4c8; font-size: 9pt;")
        status_row.addWidget(self.elapsed_label)
        progress_vbox.addLayout(status_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFixedHeight(10)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: #0b1120; border: 1px solid {COLOR_BORDER_SUBTLE}; border-radius: 5px; }}"
            f"QProgressBar::chunk {{ background-color: #38bdf8; border-radius: 4px; }}"
        )
        progress_vbox.addWidget(self.progress_bar)
        layout.addLayout(progress_vbox)

        # 4. Live log console
        console_header = QHBoxLayout()
        console_lbl = QLabel("DIAGNOSTIC LOG STREAM")
        console_lbl.setStyleSheet("font-size: 8.5pt; font-weight: bold; color: #71829b; letter-spacing: 0.5px;")
        console_header.addWidget(console_lbl)
        console_header.addStretch()
        layout.addLayout(console_header)

        self.log_console = LogConsoleWidget()
        layout.addWidget(self.log_console, stretch=1)

        # 5. Cancel button bar
        btn_layout = QHBoxLayout()
        self.cancel_btn = QPushButton("Cancel Audit")
        self.cancel_btn.setProperty("class", "danger")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.setCursor(Qt.PointingHandCursor)
        btn_layout.addWidget(self.cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    # -------------------------------------------------------------------------
    # Public API — called by MainWindow pipeline signal slots
    # -------------------------------------------------------------------------

    def on_stage_started(self, stage_num: int, stage_name: str) -> None:
        """Update status label and visual stepper when a pipeline stage begins."""
        self.status_label.setText(f"Stage {stage_num}: {stage_name}")

        # Update previous stages to Completed
        for num in range(1, stage_num):
            if num in self._stage_widgets:
                w = self._stage_widgets[num]
                w["status"].setText("Completed")
                w["status"].setStyleSheet(
                    "font-size: 7.5pt; color: #22c55e; background-color: rgba(34, 197, 94, 0.15); "
                    "padding: 1px 4px; border-radius: 3px;"
                )
                w["box"].setStyleSheet(
                    "QFrame { background-color: #0b1120; border: 1px solid rgba(34, 197, 94, 0.4); "
                    "border-radius: 6px; padding: 6px; }"
                )

        # Update active stage
        if stage_num in self._stage_widgets:
            curr = self._stage_widgets[stage_num]
            curr["status"].setText("Running")
            curr["status"].setStyleSheet(
                "font-size: 7.5pt; color: #38bdf8; background-color: rgba(56, 189, 248, 0.15); "
                "padding: 1px 4px; border-radius: 3px; font-weight: bold;"
            )
            curr["box"].setStyleSheet(
                "QFrame { background-color: #141f32; border: 1.5px solid #38bdf8; "
                "border-radius: 6px; padding: 6px; }"
            )

    def on_progress_updated(self, pct: int, description: str) -> None:
        """Drive progress bar and status label from worker signal."""
        self.progress_bar.setValue(pct)
        self.status_label.setText(description)

    def on_scan_started(self) -> None:
        """Reset the view for a new scan run."""
        self._start_time = time.time()
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet(
            f"QProgressBar {{ background-color: #0b1120; border: 1px solid {COLOR_BORDER_SUBTLE}; border-radius: 5px; }}"
            f"QProgressBar::chunk {{ background-color: #38bdf8; border-radius: 4px; }}"
        )
        self.log_console.clear()
        self.status_label.setText("Audit pipeline starting…")
        self.cancel_btn.setEnabled(True)

        for num, w in self._stage_widgets.items():
            w["status"].setText("Pending")
            w["status"].setStyleSheet(
                "font-size: 7.5pt; color: #64748b; background-color: rgba(100, 116, 139, 0.15); "
                "padding: 1px 4px; border-radius: 3px;"
            )
            w["box"].setStyleSheet(
                "QFrame { background-color: #0b1120; border: 1px solid #2b3b52; border-radius: 6px; padding: 6px; }"
            )

    def on_scan_finished(self) -> None:
        """Mark the view as complete."""
        self.progress_bar.setValue(100)
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Audit pipeline completed successfully.")

        for num in range(1, 7):
            if num in self._stage_widgets:
                w = self._stage_widgets[num]
                w["status"].setText("Completed")
                w["status"].setStyleSheet(
                    "font-size: 7.5pt; color: #22c55e; background-color: rgba(34, 197, 94, 0.15); "
                    "padding: 1px 4px; border-radius: 3px;"
                )
                w["box"].setStyleSheet(
                    "QFrame { background-color: #0b1120; border: 1px solid rgba(34, 197, 94, 0.4); "
                    "border-radius: 6px; padding: 6px; }"
                )

    def on_scan_failed(self, error: str) -> None:
        """Mark the view as failed."""
        self.cancel_btn.setEnabled(False)
        self.progress_bar.setStyleSheet(
            "QProgressBar { background-color: #0b1120; border: 1px solid #ef4444; border-radius: 5px; }"
            "QProgressBar::chunk { background-color: #ef4444; border-radius: 4px; }"
        )
        self.status_label.setText(f"Scan failed: {error}")

    def on_scan_cancelled(self) -> None:
        """Mark the view as cancelled."""
        self.cancel_btn.setEnabled(False)
        self.status_label.setText("Audit cancelled by user.")
