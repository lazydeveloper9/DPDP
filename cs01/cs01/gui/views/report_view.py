"""
CS-01 DPDP Compliance Desktop GUI - Compliance Deliverables Hub (Screen 5).

Renders artifact delivery tiles for all 7 standard CS-01 output files:
  HTML DPO Report | Dataflow Visualizer | RoPA JSON | Remediation Patches
  SARIF 2.1.0     | Markdown Report     | Evidence Bundle ZIP

Each tile shows availability status and launches the appropriate action
(browser open, RoPA dialog, diff viewer, or cryptographic evidence verifier).
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.theme import COLOR_BG_CARD, COLOR_BORDER_SUBTLE
from cs01.gui.widgets.diff_viewer import DiffViewerDialog
from cs01.gui.widgets.ropa_table_dialog import RopaTableDialog
from cs01.pipeline.stage6_report.evidence_locker import verify_evidence_bundle


def _open_file(path: Path) -> None:
    """Open a file with the OS default handler (cross-platform)."""
    try:
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))
    except Exception:
        try:
            if sys.platform == "win32":
                os.startfile(str(path))  # type: ignore[attr-defined]
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                subprocess.Popen(["xdg-open", str(path)])
        except Exception:
            pass

_ARTIFACTS: list[tuple[str, str, str]] = [
    ("pdf",       "Executive PDF Report (cs01-report.pdf)",                     "Open PDF"),
    ("markdown",  "Executive Markdown Report (cs01-report.md)",                "View Markdown"),
    ("html",      "Executive DPO HTML Report (cs01-dpo-report.html)",          "View in Browser"),
    ("dataflow",  "Interactive 2D/3D Dataflow Visualizer (cs01-dataflow.html)", "Open Visualizer"),
    ("ropa",      "Technical RoPA Table (ropa_map.json)",                       "Open RoPA Table"),
    ("patch",     "Deterministic Remediation Patches (*.patch)",                "View Diff Viewer"),
    ("sarif",     "Developer SARIF 2.1.0 (cs01-findings.sarif)",               "Copy Path"),
    ("evidence",  "Rule 13 Evidence Bundle ZIP (cs01-evidence-bundle.zip)",    "Verify Integrity"),
]


class ReportView(QWidget):
    """
    Deliverables Hub with artifact tiles, RoPA dialog launch, and evidence verifier.

    Attributes:
        tiles: Dict mapping artifact key → styled QFrame tile.
        evidence_verification_banner: Banner showing Rule 13 verification result.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.report_files: dict[str, Path] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 24)
        layout.setSpacing(14)

        header_vbox = QVBoxLayout()
        header_vbox.setSpacing(3)

        title = QLabel("Compliance Deliverables & Evidence Locker")
        title.setStyleSheet("font-size: 19px; font-weight: 700; color: #f8fafc;")
        header_vbox.addWidget(title)

        subtitle = QLabel("Access executive PDF compliance audits, RoPA schemas, SARIF feeds, and Rule 13 tamper-evident evidence packages.")
        subtitle.setStyleSheet("font-size: 9.5pt; color: #a6b4c8;")
        header_vbox.addWidget(subtitle)
        layout.addLayout(header_vbox)

        self.tiles_container = QWidget()
        tiles_layout = QVBoxLayout(self.tiles_container)
        tiles_layout.setContentsMargins(0, 0, 0, 0)
        tiles_layout.setSpacing(8)

        self.tiles: dict[str, QFrame] = {}
        for key, name, action_text in _ARTIFACTS:
            frame = QFrame()
            frame.setStyleSheet(
                f"QFrame {{ background-color: {COLOR_BG_CARD}; "
                f"border: 1px solid {COLOR_BORDER_SUBTLE}; "
                "border-radius: 8px; padding: 12px; } "
                "QFrame:hover { border-color: #3b4d68; }"
            )
            f_layout = QHBoxLayout(frame)
            f_layout.setContentsMargins(12, 8, 12, 8)
            f_layout.setSpacing(12)

            lbl = QLabel(name)
            lbl.setStyleSheet("font-size: 10pt; font-weight: 600; color: #f1f5f9;")
            f_layout.addWidget(lbl)
            f_layout.addStretch()

            status_lbl = QLabel("Not Generated")
            status_lbl.setStyleSheet("color: #71829b; font-size: 9pt;")
            f_layout.addWidget(status_lbl)

            btn = QPushButton(action_text)
            btn.setProperty("class", "primary")
            btn.setEnabled(False)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda _checked=False, k=key: self._on_tile_action(k))
            f_layout.addWidget(btn)

            # Optional secondary action for exportable documents
            if key in ("pdf", "markdown"):
                save_btn = QPushButton("Save As...")
                save_btn.setProperty("class", "secondary")
                save_btn.setEnabled(False)
                save_btn.setCursor(Qt.PointingHandCursor)
                save_btn.clicked.connect(lambda _checked=False, k=key: self._on_save_as(k))
                f_layout.addWidget(save_btn)
                frame.save_btn = save_btn  # type: ignore[attr-defined]

            # Attach dynamic attributes for later updates
            frame.status_lbl = status_lbl   # type: ignore[attr-defined]
            frame.btn = btn                  # type: ignore[attr-defined]
            self.tiles[key] = frame
            tiles_layout.addWidget(frame)

        layout.addWidget(self.tiles_container)
        layout.addStretch()

        # Evidence verification status banner
        self.evidence_verification_banner = QLabel("")
        self.evidence_verification_banner.setStyleSheet(
            "font-size: 10pt; font-weight: bold; padding: 10px 14px; border-radius: 6px;"
        )
        layout.addWidget(self.evidence_verification_banner)

    # -------------------------------------------------------------------------
    # Slots
    # -------------------------------------------------------------------------

    def _on_tile_action(self, key: str) -> None:
        """Handle button click on an artifact tile."""
        if key == "pdf":
            pdf_path = self.report_files.get("cs01-report.pdf")
            if pdf_path and Path(pdf_path).exists():
                _open_file(Path(pdf_path))

        elif key == "html":
            html_path = self.report_files.get("cs01-dpo-report.html")
            if html_path and Path(html_path).exists():
                _open_file(Path(html_path))

        elif key == "dataflow":
            html_path = self.report_files.get("cs01-dataflow.html")
            if html_path and Path(html_path).exists():
                _open_file(Path(html_path))

        elif key == "markdown":
            md_path = self.report_files.get("cs01-report.md")
            if md_path and Path(md_path).exists():
                _open_file(Path(md_path))

        elif key == "sarif":
            sarif_path = self.report_files.get("cs01-findings.sarif")
            if sarif_path and Path(sarif_path).exists():
                # Copy path to clipboard and open the file
                from PySide6.QtWidgets import QApplication
                clipboard = QApplication.clipboard()
                clipboard.setText(str(Path(sarif_path).resolve()))
                _open_file(Path(sarif_path))

        elif key == "ropa":
            ropa_path = self.report_files.get("ropa_map.json")
            data: list[dict] = []
            if ropa_path and Path(ropa_path).exists():
                try:
                    data = json.loads(Path(ropa_path).read_text(encoding="utf-8"))
                except Exception:
                    pass
            dialog = RopaTableDialog(data, parent=self)
            dialog.show()

        elif key == "patch":
            diff_text = ""
            for k, p in self.report_files.items():
                if k.endswith(".patch") and Path(p).exists():
                    diff_text = Path(p).read_text(encoding="utf-8")
                    break
            dialog = DiffViewerDialog(diff_text, parent=self)
            dialog.show()

        elif key == "evidence":
            bundle_zip = self.report_files.get("cs01-evidence-bundle.zip")
            if bundle_zip and Path(bundle_zip).exists():
                is_valid, _logs = verify_evidence_bundle(bundle_zip)
                if is_valid:
                    self.evidence_verification_banner.setText(
                        "✓ VERIFIED (Rule 13 Compliant: Cryptographic Hash Match)"
                    )
                    self.evidence_verification_banner.setStyleSheet(
                        "color: #10b981; font-weight: bold;"
                    )
                else:
                    self.evidence_verification_banner.setText(
                        "❌ TAMPERING DETECTED: Evidence hash verification failed!"
                    )
                    self.evidence_verification_banner.setStyleSheet(
                        "color: #ef4444; font-weight: bold;"
                    )

    def _on_save_as(self, key: str) -> None:
        """Handle save as action for exportable documents."""
        if key == "pdf":
            self._on_export_file("cs01-report.pdf", "cs01-report.pdf", "PDF Documents (*.pdf)")
        elif key == "markdown":
            self._on_export_file("cs01-report.md", "cs01-report.md", "Markdown Documents (*.md)")

    def _on_export_file(self, filename: str, default_name: str, file_filter: str) -> None:
        source_path = self.report_files.get(filename)
        if not source_path or not Path(source_path).exists():
            return
        dest_path, _ = QFileDialog.getSaveFileName(self, f"Export {filename}", default_name, file_filter)
        if dest_path:
            try:
                shutil.copyfile(str(source_path), dest_path)
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Public API
    # -------------------------------------------------------------------------

    def bind_reports(self, report_files: dict[str, Path]) -> None:
        """Update tile states based on the set of generated report files."""
        self.report_files = report_files
        for key, frame in self.tiles.items():
            file_match: Path | None = None
            if key == "pdf":
                file_match = report_files.get("cs01-report.pdf")
            elif key == "html":
                file_match = report_files.get("cs01-dpo-report.html")
            elif key == "dataflow":
                file_match = report_files.get("cs01-dataflow.html")
            elif key == "ropa":
                file_match = report_files.get("ropa_map.json")
            elif key == "sarif":
                file_match = report_files.get("cs01-findings.sarif")
            elif key == "markdown":
                file_match = report_files.get("cs01-report.md")
            elif key == "evidence":
                file_match = report_files.get("cs01-evidence-bundle.zip")
            elif key == "patch":
                for k, p in report_files.items():
                    if k.endswith(".patch") or "remediation" in k:
                        file_match = Path(p)
                        break

            if file_match and Path(file_match).exists():
                frame.status_lbl.setText("✓ Available")
                frame.status_lbl.setStyleSheet("color: #10b981; font-size: 11px;")
                frame.btn.setEnabled(True)
                if hasattr(frame, "save_btn"):
                    frame.save_btn.setEnabled(True)
            else:
                frame.status_lbl.setText("Not Generated / Scan Required")
                frame.status_lbl.setStyleSheet("color: #64748b; font-size: 11px;")
                frame.btn.setEnabled(False)
                if hasattr(frame, "save_btn"):
                    frame.save_btn.setEnabled(False)
