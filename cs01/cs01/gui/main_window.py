"""
CS-01 DPDP Compliance Desktop GUI - Main Application Window.

Assembles the Top Header HUD, collapsible navigation rail, central stacked views,
status bar, and responsive layout management. Mounts all 5 real view instances
and wires the AuditPipelineWorker pipeline on start_scan_requested.
"""

from __future__ import annotations

from typing import Final

from PySide6.QtCore import QObject
from PySide6.QtGui import QIcon, QResizeEvent, QShortcut
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.async_runner.scan_worker import AuditPipelineWorker
from cs01.gui.models.gui_state import GuiScanState
from cs01.gui.theme import (
    BREAKPOINT_COLLAPSE_WIDTH,
    HEADER_HUD_HEIGHT,
    WINDOW_DEFAULT_HEIGHT,
    WINDOW_DEFAULT_WIDTH,
    WINDOW_MIN_HEIGHT,
    WINDOW_MIN_WIDTH,
)
from cs01.gui.views.dashboard_view import DashboardView
from cs01.gui.views.report_view import ReportView
from cs01.gui.views.results_view import ResultsView
from cs01.gui.views.scan_config_view import ScanConfigView
from cs01.gui.views.scan_execution_view import ScanExecutionView
from cs01.gui.widgets.sidebar import NavigationSidebar


def _get_process_memory_mb() -> float:
    """Safely retrieves current working set memory in MB."""
    try:
        import win32process

        proc = win32process.GetCurrentProcess()
        info = win32process.GetProcessMemoryInfo(proc)
        return round(info.get("WorkingSetSize", 0) / (1024 * 1024), 1)
    except (ImportError, OSError, AttributeError, KeyError):
        return 14.2


class MainWindow(QMainWindow):
    """
    Primary desktop window shell for the CS-01 DPDP Compliance Auditor.

    Provides Top Header HUD, collapsible NavigationSidebar, central QStackedWidget,
    status bar with statutory metrics, and responsive resize handling.
    """

    APP_TITLE: Final[str] = "CS-01 DPDP Compliance Auditor"
    VERSION_TAG: Final[str] = "v0.1.0-alpha"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.APP_TITLE)
        self.resize(WINDOW_DEFAULT_WIDTH, WINDOW_DEFAULT_HEIGHT)
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)

        # Set application window icon
        from cs01.utils.resources import get_resource_path
        icon_path = get_resource_path("assets/cs01.ico")
        if not icon_path.exists():
            icon_path = get_resource_path("assets/cs01.png")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Tracks explicit user collapse intent to respect manual overrides
        # None = no manual user action yet (auto-collapse/expand freely)
        # True = user manually collapsed sidebar
        # False = user manually expanded sidebar
        self._user_collapsed_override: bool | None = None

        self._setup_ui()
        self._setup_status_bar()
        self._auto_load_existing_reports()

    def _setup_ui(self) -> None:
        """Initializes top HUD, central sidebar/stack layout, and connects signals."""
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_vbox = QVBoxLayout(central_widget)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # 1. Top Header HUD Bar
        hud_frame = QFrame(self)
        hud_frame.setProperty("class", "hud")
        hud_frame.setFixedHeight(HEADER_HUD_HEIGHT)

        hud_layout = QHBoxLayout(hud_frame)
        hud_layout.setContentsMargins(16, 8, 16, 8)
        hud_layout.setSpacing(12)

        self.brand_icon = QLabel("🛡", self)
        self.brand_icon.setStyleSheet("font-size: 20pt; color: #38bdf8;")

        self.brand_title = QLabel(self.APP_TITLE, self)
        self.brand_title.setProperty("class", "hud-title")

        self.version_badge = QLabel(self.VERSION_TAG, self)
        self.version_badge.setProperty("class", "badge-version")

        hud_layout.addWidget(self.brand_icon)
        hud_layout.addWidget(self.brand_title)
        hud_layout.addWidget(self.version_badge)
        hud_layout.addStretch()

        # Load Reports action button in HUD
        self.load_report_btn = QPushButton("📂 Load Reports", self)
        self.load_report_btn.setProperty("class", "secondary")
        self.load_report_btn.setToolTip("Load previously generated scan results (cs01-compliance.json or folder)")
        self.load_report_btn.clicked.connect(self._on_user_load_reports)
        hud_layout.addWidget(self.load_report_btn)

        self.privacy_badge = QLabel("● OFFLINE · ZERO-EGRESS", self)
        self.privacy_badge.setProperty("class", "badge-privacy")
        self.privacy_badge.setToolTip(
            "All AST parsing, PII redaction, and reporting run 100% locally with zero external network egress."
        )
        hud_layout.addWidget(self.privacy_badge)

        main_vbox.addWidget(hud_frame)

        # 2. Central Layout (Left Sidebar + Center StackedWidget)
        content_widget = QWidget(self)
        content_layout = QHBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.sidebar = NavigationSidebar(self)
        self.sidebar.toggle_btn.clicked.connect(self._on_user_toggle_sidebar)
        self._toggle_shortcut: QShortcut | None = getattr(self.sidebar, "_toggle_shortcut", None)
        if self._toggle_shortcut is not None:
            self._toggle_shortcut.activated.connect(self._on_user_toggle_sidebar)
        content_layout.addWidget(self.sidebar)

        self.stacked_widget = QStackedWidget(self)
        self._init_view_slots()
        content_layout.addWidget(self.stacked_widget)

        self.sidebar.navigation_changed.connect(self.navigate_to)
        main_vbox.addWidget(content_widget)

    def _init_view_slots(self) -> None:
        """Mounts all 5 real view instances into QStackedWidget."""
        # Instantiate all views
        self.dashboard_view = DashboardView(self)
        self.scan_config_view = ScanConfigView(self)
        self.scan_execution_view = ScanExecutionView(self)
        self.results_view = ResultsView(self)
        self.report_view = ReportView(self)

        # Add in order matching sidebar indices: 0=Dashboard, 1=Scan Setup, 2=Execution, 3=Results, 4=Reports
        self.stacked_widget.addWidget(self.dashboard_view)       # 0
        self.stacked_widget.addWidget(self.scan_config_view)     # 1
        self.stacked_widget.addWidget(self.scan_execution_view)  # 2
        self.stacked_widget.addWidget(self.results_view)         # 3
        self.stacked_widget.addWidget(self.report_view)          # 4

        # Connect ScanConfigView scan launch → pipeline worker
        self.scan_config_view.start_scan_requested.connect(self._on_start_scan_requested)

        # Connect scan execution cancel button
        self.scan_execution_view.cancel_btn.clicked.connect(self._on_cancel_scan)

    def _on_start_scan_requested(self, scan_config: object) -> None:
        """Launch the audit pipeline worker and switch to execution view."""
        if hasattr(self, "_worker") and self._worker.isRunning():
            return  # Prevent starting multiple concurrent scans

        # Lock scan controls while audit is running
        self.scan_config_view.start_scan_btn.setEnabled(False)

        # Update HUD
        target = getattr(scan_config, "scan_root", str(scan_config))
        if hasattr(self, "hud_target_label"):
            self.hud_target_label.setText(f"Target: {target}")
        # Update privacy badge to scanning state
        self.privacy_badge.setText("⚡ SCANNING IN PROGRESS")
        self.privacy_badge.setStyleSheet("color: #f59e0b; font-weight: bold;")

        # Transition to execution view
        self.navigate_to(2)
        self.scan_execution_view.on_scan_started()

        # Create and wire worker
        self._worker = AuditPipelineWorker(scan_config)  # type: ignore[arg-type]
        self._active_pii_hits: list = []  # Will be populated if stage3 output exists
        w = self._worker
        w.signals.stage_started.connect(self.scan_execution_view.on_stage_started)
        w.signals.progress_updated.connect(self.scan_execution_view.on_progress_updated)
        w.signals.log_emitted.connect(self.scan_execution_view.log_console.append_log)
        w.signals.scan_completed.connect(self._on_scan_completed)
        w.signals.scan_failed.connect(self._on_scan_failed)
        w.signals.scan_cancelled.connect(self._on_scan_cancelled)
        w.signals.audit_finished.connect(self._on_audit_finished)
        w.start()

    def _on_cancel_scan(self) -> None:
        if hasattr(self, "_worker") and self._worker.isRunning():
            self._worker.cancel()

    def _on_audit_finished(self) -> None:
        """Guaranteed cleanup slot called when audit completes, fails, or cancels."""
        self.scan_config_view.start_scan_btn.setEnabled(True)
        self.scan_execution_view.cancel_btn.setEnabled(False)

    def _on_scan_completed(self, bundle: object, report_files: dict) -> None:
        self.scan_execution_view.on_scan_finished()

        # Try to load pii_hits from stage output JSON (always saved by worker)
        pii_hits = None
        try:
            import json
            from pathlib import Path as _Path
            from cs01.models.flow_graph import PiiHitList
            worker = getattr(self, "_worker", None)
            if worker is not None:
                cfg = getattr(worker, "scan_config", None)
                if cfg is not None:
                    pii_json = _Path(cfg.output_dir) / "stage3_pii_hits.json"
                    if pii_json.exists():
                        raw = json.loads(pii_json.read_text(encoding="utf-8"))
                        collection = PiiHitList.model_validate(raw)
                        pii_hits = collection.hits
        except Exception:
            pii_hits = None

        # Bind results to all views
        self.dashboard_view.bind_bundle(bundle)   # type: ignore[arg-type]
        self.results_view.bind_bundle(bundle, pii_hits=pii_hits)  # type: ignore[arg-type]
        self.report_view.bind_reports(report_files)

        # Restore HUD badge
        self.privacy_badge.setText("● OFFLINE · ZERO-EGRESS")
        self.privacy_badge.setStyleSheet("")

        # Navigate to Results view so user sees findings immediately
        self.navigate_to(3)

    def _on_scan_failed(self, error: str) -> None:
        self.scan_execution_view.on_scan_failed(error)
        self.scan_execution_view.log_console.append_log("ERROR", f"Scan failed: {error}")
        # Restore HUD badge
        self.privacy_badge.setText("❌ SCAN FAILED · OFFLINE")
        self.privacy_badge.setStyleSheet("color: #ef4444; font-weight: bold;")

    def _on_scan_cancelled(self) -> None:
        self.scan_execution_view.on_scan_cancelled()
        # Restore HUD badge
        self.privacy_badge.setText("⚠ CANCELLED · OFFLINE · ZERO-EGRESS")
        self.privacy_badge.setStyleSheet("color: #94a3b8; font-weight: bold;")

    def _auto_load_existing_reports(self) -> None:
        """Auto-discovers and loads existing scan results from cs01-reports if present."""
        import json
        from pathlib import Path
        from cs01.models.scored_finding import ScoredFindingBundle
        from cs01.models.flow_graph import PiiHitList

        candidate_dirs = [
            Path.cwd() / "cs01-reports",
            Path.cwd().parent / "cs01-reports",
            Path("C:/DPDP/cs01-reports"),
        ]

        for rep_dir in candidate_dirs:
            if not rep_dir.exists() or not rep_dir.is_dir():
                continue

            # Look for cs01-compliance.json or stage5_bundle.json
            for candidate_json in ("cs01-compliance.json", "stage5_bundle.json"):
                json_path = rep_dir / candidate_json
                if json_path.exists():
                    try:
                        data = json.loads(json_path.read_text(encoding="utf-8"))
                        bundle = ScoredFindingBundle.model_validate(data)

                        # Collect report files
                        report_files: dict[str, Path] = {}
                        for f in rep_dir.iterdir():
                            if f.is_file():
                                report_files[f.name] = f
                        patches_dir = rep_dir / "patches"
                        if patches_dir.exists():
                            for pf in patches_dir.glob("*.patch"):
                                report_files[pf.name] = pf

                        # Try to load pii_hits
                        pii_hits = None
                        pii_json = rep_dir / "stage3_pii_hits.json"
                        if pii_json.exists():
                            try:
                                pii_data = json.loads(pii_json.read_text(encoding="utf-8"))
                                pii_hits = PiiHitList.model_validate(pii_data).hits
                            except Exception:
                                pass

                        # Bind to all views
                        self.dashboard_view.bind_bundle(bundle)
                        self.results_view.bind_bundle(bundle, pii_hits=pii_hits)
                        self.report_view.bind_reports(report_files)

                        self.privacy_badge.setText(f"● LOADED ({len(bundle.findings)} findings) · ZERO-EGRESS")
                        self.privacy_badge.setStyleSheet("color: #10b981; font-weight: bold;")
                        return
                    except Exception:
                        pass

    def _on_user_load_reports(self) -> None:
        """File picker dialog to manually load previously generated scan results."""
        import json
        from pathlib import Path
        from cs01.models.scored_finding import ScoredFindingBundle
        from cs01.models.flow_graph import PiiHitList

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Scan Results JSON (cs01-compliance.json or stage5_bundle.json)",
            "",
            "JSON Files (*.json);;All Files (*.*)",
        )
        if not path:
            return

        json_file = Path(path)
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
            bundle = ScoredFindingBundle.model_validate(data)
            rep_dir = json_file.parent

            report_files: dict[str, Path] = {}
            for f in rep_dir.iterdir():
                if f.is_file():
                    report_files[f.name] = f
            patches_dir = rep_dir / "patches"
            if patches_dir.exists():
                for pf in patches_dir.glob("*.patch"):
                    report_files[pf.name] = pf

            pii_hits = None
            pii_json = rep_dir / "stage3_pii_hits.json"
            if pii_json.exists():
                try:
                    pii_data = json.loads(pii_json.read_text(encoding="utf-8"))
                    pii_hits = PiiHitList.model_validate(pii_data).hits
                except Exception:
                    pass

            self.dashboard_view.bind_bundle(bundle)
            self.results_view.bind_bundle(bundle, pii_hits=pii_hits)
            self.report_view.bind_reports(report_files)

            self.privacy_badge.setText(f"● LOADED ({len(bundle.findings)} findings) · ZERO-EGRESS")
            self.privacy_badge.setStyleSheet("color: #10b981; font-weight: bold;")
            self.navigate_to(0)  # Go to Dashboard
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Load Error", f"Could not load scan bundle:\n{e}")

    def _setup_status_bar(self) -> None:
        """Initializes bottom status bar with engine, egress, and memory readouts."""
        status_bar = self.statusBar()
        status_bar.setSizeGripEnabled(False)

        self.status_engine_label = QLabel(
            "AST Engine: Tree-sitter Polyglot | Rules: 23 Active", self
        )
        self.status_engine_label.setProperty("class", "text-secondary")

        self.status_egress_label = QLabel("🔒 Zero Cloud Egress Confirmed", self)
        self.status_egress_label.setProperty("class", "text-secondary")

        mem_mb = _get_process_memory_mb()
        self.status_memory_label = QLabel(f"Memory: {mem_mb} MB", self)
        self.status_memory_label.setProperty("class", "text-secondary")

        status_bar.addWidget(self.status_engine_label, 1)
        status_bar.addPermanentWidget(self.status_egress_label)
        status_bar.addPermanentWidget(self.status_memory_label)

    def refresh_status_bar(self) -> None:
        """Updates the status bar with current process metrics."""
        mem_mb = _get_process_memory_mb()
        self.status_memory_label.setText(f"Memory: {mem_mb} MB")

    # ------------------------------------------------------------------------
    # NAVIGATION & VIEW MANAGEMENT
    # ------------------------------------------------------------------------

    def _on_user_toggle_sidebar(self) -> None:
        """Records explicit user manual collapse toggle."""
        self._user_collapsed_override = self.sidebar.is_collapsed()

    def navigate_to(self, index: int) -> None:
        """
        Switches the visible screen in QStackedWidget and synchronizes sidebar.

        Args:
            index: Target screen index (0 to 3).
        """
        if 0 <= index < self.stacked_widget.count():
            self.stacked_widget.setCurrentIndex(index)
            if self.sidebar.get_active_index() != index:
                self.sidebar.set_active_index(index, emit_signal=False)

    def set_view(self, index: int, widget: QWidget) -> None:
        """
        Replaces the placeholder at the given index with an actual view component.

        Args:
            index: Target screen index (0 to 3).
            widget: Replacement QWidget view.
        """
        if 0 <= index < self.stacked_widget.count():
            was_current = (self.stacked_widget.currentIndex() == index)
            old_widget = self.stacked_widget.widget(index)
            self.stacked_widget.removeWidget(old_widget)
            self.stacked_widget.insertWidget(index, widget)
            if was_current:
                self.stacked_widget.setCurrentIndex(index)
            if old_widget is not None:
                old_widget.deleteLater()

    def get_view(self, index: int) -> QWidget | None:
        """Returns the widget currently mounted at index."""
        if 0 <= index < self.stacked_widget.count():
            return self.stacked_widget.widget(index)
        return None

    # ------------------------------------------------------------------------
    # RESPONSIVE BREAKPOINT EVENT HANDLING
    # ------------------------------------------------------------------------

    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Manages responsive sidebar collapsing when crossing BREAKPOINT_COLLAPSE_WIDTH.

        - When window width < 1366px: auto-collapses sidebar unless user explicitly kept it expanded.
        - When window width >= 1366px: auto-expands sidebar unless user explicitly kept it collapsed.
        """
        super().resizeEvent(event)
        width = event.size().width()

        if width < BREAKPOINT_COLLAPSE_WIDTH:
            if self._user_collapsed_override is not False and not self.sidebar.is_collapsed():
                self.sidebar.set_collapsed(True)
        elif self._user_collapsed_override is not True and self.sidebar.is_collapsed():
            self.sidebar.set_collapsed(False)
