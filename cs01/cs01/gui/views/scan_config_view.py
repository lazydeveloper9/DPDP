"""
CS-01 DPDP Compliance Desktop GUI - Scan Configuration View (Screen 2).
========================================================================
Provides ingestion of local codebase directories, software archives (.zip, .tar.gz)
with Zip-Slip path traversal defense, and remote Git repository URLs.
Supports policy gate threshold selection, SAST engine switching, deliverable artifact
toggles, statutory DAST prober guardrails, and audit scan dispatching.
"""

from __future__ import annotations

import logging
import os
import re
import tarfile
import zipfile
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from cs01.gui.qss_builder import polish_widget
from cs01.gui.theme import (
    BRUTALIST_BG_MAIN,
    BRUTALIST_BG_SECONDARY,
    BRUTALIST_BLACK,
    BRUTALIST_BORDER,
    BRUTALIST_COBALT,
    BRUTALIST_GREEN,
    BRUTALIST_MUTED,
    BRUTALIST_ORANGE,
    BRUTALIST_RED,
    BRUTALIST_SURFACE,
    BRUTALIST_SURFACE_ALT,
    BRUTALIST_YELLOW,
    DEFAULT_THEME,
    Theme,
)
from cs01.gui.widgets.brutalist_widgets import BrutalistCard
from cs01.models.scan_config import (
    AiConfig,
    BonusConfig,
    EngineConfig,
    ScanConfig,
)
from cs01.utils.archive import is_archive
from cs01.utils.git_ingest import is_git_url, parse_git_url

logger = logging.getLogger("cs01.gui.scan_config_view")


class ScanConfigView(QWidget):
    """
    Scan Configuration View for CS-01 DPDP Compliance Auditor.

    Enables operators to select scan targets (directories, archives, remote Git URLs),
    configure statutory policy gate thresholds, switch SAST analysis engines, select
    compliance deliverables, configure baseline suppression, and initiate audits.
    """

    # Inter-thread signal contracts
    start_scan_requested = Signal(object)  # Emits ScanConfig instance
    scan_requested = Signal(dict)          # Emits normalized configuration dictionary

    def __init__(
        self,
        parent: QWidget | None = None,
        theme: Theme | None = None,
    ) -> None:
        super().__init__(parent)
        self.theme: Theme = theme or DEFAULT_THEME
        self._init_ui()
        self._connect_signals()

    # ------------------------------------------------------------------------
    # UI CONSTRUCTION
    # ------------------------------------------------------------------------

    def _init_ui(self) -> None:
        """Builds responsive layout enclosed in a resizable QScrollArea."""
        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.setSpacing(0)

        # Responsive Scroll Area wrapper for resolutions down to 1024x680
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.content_widget = QWidget(self.scroll_area)
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(24, 20, 24, 20)
        self.content_layout.setSpacing(16)

        # 1. Screen Header
        self._build_header_card()

        # 2. Target Source Selection & Codebase Ingestion Card
        self._build_target_card()

        # 3. Audit Pipeline Parameters Card
        self._build_pipeline_card()

        # 4. Compliance Deliverables Checklist Card
        self._build_deliverables_card()

        # 5. Advanced & Regulatory Options Card
        self._build_advanced_card()

        # 6. Action Footer Bar
        self._build_footer_bar()

        self.scroll_area.setWidget(self.content_widget)
        outer_layout.addWidget(self.scroll_area)

    def _build_header_card(self) -> None:
        """Header presenting screen title and concise statutory purpose."""
        header_frame = QFrame(self.content_widget)
        h_layout = QVBoxLayout(header_frame)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)

        self.title_label = QLabel("SCAN CONFIGURATION & TARGET SETUP", header_frame)
        self.title_label.setStyleSheet(f"font-size: 16pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: -0.5px;")

        self.subtitle_label = QLabel(
            "Configure target codebase, analysis parameters, statutory fail-on thresholds, "
            "and deliverable artifacts for compliance evaluation.",
            header_frame,
        )
        self.subtitle_label.setStyleSheet(f"font-size: 9.5pt; color: {BRUTALIST_MUTED};")

        h_layout.addWidget(self.title_label)
        h_layout.addWidget(self.subtitle_label)
        self.content_layout.addWidget(header_frame)

    def _build_target_card(self) -> None:
        """Target source selection, ingestion input row, and dynamic validation badge."""
        self.target_source_card = BrutalistCard(bg="#FFFFFF", shadow_offset=4, parent=self.content_widget)
        self.target_source_card.setProperty("class", "card")
        card_layout = QVBoxLayout(self.target_source_card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(12)

        # Mode Selection
        mode_header = QLabel("01 // TARGET SOURCE SELECTION & CODEBASE INGESTION", self.target_source_card)
        mode_header.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: 0.5px;")
        card_layout.addWidget(mode_header)

        mode_row = QHBoxLayout()
        mode_row.setSpacing(24)
        self.mode_local_radio = QRadioButton(
            "Local Directory or Archive Package", self.target_source_card
        )
        self.mode_remote_radio = QRadioButton(
            "Remote Git Repository (GitHub / GitLab / Bitbucket / SSH)", self.target_source_card
        )
        self.mode_local_radio.setChecked(True)

        self.mode_group = QButtonGroup(self)
        self.mode_group.addButton(self.mode_local_radio)
        self.mode_group.addButton(self.mode_remote_radio)

        mode_row.addWidget(self.mode_local_radio)
        mode_row.addWidget(self.mode_remote_radio)
        mode_row.addStretch()
        card_layout.addLayout(mode_row)

        # Target Path / URL Input Row
        input_label = QLabel("Source Target Path or Git Clone URL:", self.target_source_card)
        input_label.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700; font-size: 9.5pt;")
        card_layout.addWidget(input_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)

        self.target_input = QLineEdit(self.target_source_card)
        self.target_input.setPlaceholderText(
            "Enter directory path, archive (.zip, .tar.gz), or Git URL..."
        )
        self.target_input.setFixedHeight(36)
        self.target_input.setStyleSheet(
            f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; "
            "padding: 4px 10px; font-weight: 500; font-size: 10pt;"
        )
        input_row.addWidget(self.target_input, 1)

        self.browse_folder_btn = QPushButton("Browse Folder", self.target_source_card)
        self.browse_folder_btn.setFixedHeight(36)
        self.browse_folder_btn.setStyleSheet(
            f"background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; "
            "font-weight: 800; padding: 4px 14px; text-transform: uppercase;"
        )

        self.browse_archive_btn = QPushButton("Select Archive", self.target_source_card)
        self.browse_archive_btn.setFixedHeight(36)
        self.browse_archive_btn.setStyleSheet(
            f"background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; "
            "font-weight: 800; padding: 4px 14px; text-transform: uppercase;"
        )

        self.validate_btn = QPushButton("Validate", self.target_source_card)
        self.validate_btn.setFixedHeight(36)
        self.validate_btn.setStyleSheet(
            f"background-color: {BRUTALIST_YELLOW}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; "
            "font-weight: 800; padding: 4px 18px; text-transform: uppercase;"
        )

        input_row.addWidget(self.browse_folder_btn)
        input_row.addWidget(self.browse_archive_btn)
        input_row.addWidget(self.validate_btn)
        card_layout.addLayout(input_row)

        # Target validation status readout
        self.validation_label = QLabel("", self.target_source_card)
        self.validation_label.setWordWrap(True)
        self.validation_label.setStyleSheet("font-size: 11px;")
        card_layout.addWidget(self.validation_label)

        # Remote Git Options Panel (Branch, Depth, Token)
        self.git_options_frame = QFrame(self.target_source_card)
        self.git_options_frame.setStyleSheet(
            f"background-color: {BRUTALIST_SURFACE_ALT}; border: 1.5px solid {BRUTALIST_BORDER}; padding: 10px;"
        )
        git_layout = QGridLayout(self.git_options_frame)
        git_layout.setContentsMargins(8, 8, 8, 8)
        git_layout.setSpacing(10)

        branch_lbl = QLabel("Git Branch / Ref:", self.git_options_frame)
        branch_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700;")
        self.branch_input = QLineEdit(self.git_options_frame)
        self.branch_input.setPlaceholderText("main")
        self.branch_input.setStyleSheet(f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; padding: 4px;")

        depth_lbl = QLabel("Clone Depth:", self.git_options_frame)
        depth_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700;")
        self.clone_depth_spin = QSpinBox(self.git_options_frame)
        self.clone_depth_spin.setRange(1, 50)
        self.clone_depth_spin.setValue(1)
        self.clone_depth_spin.setStyleSheet(f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; padding: 4px;")

        token_lbl = QLabel("Access Token (Optional for Private Repos):", self.git_options_frame)
        token_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700;")
        self.git_token_input = QLineEdit(self.git_options_frame)
        self.git_token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.git_token_input.setPlaceholderText("Personal Access Token")
        self.git_token_input.setStyleSheet(f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; padding: 4px;")

        git_layout.addWidget(branch_lbl, 0, 0)
        git_layout.addWidget(self.branch_input, 1, 0)
        git_layout.addWidget(depth_lbl, 0, 1)
        git_layout.addWidget(self.clone_depth_spin, 1, 1)
        git_layout.addWidget(token_lbl, 0, 2)
        git_layout.addWidget(self.git_token_input, 1, 2)

        # Visible only when Remote Git mode is active or Git URL entered
        self.git_options_frame.setVisible(False)
        card_layout.addWidget(self.git_options_frame)

        self.content_layout.addWidget(self.target_source_card)

    def _build_pipeline_card(self) -> None:
        """Audit pipeline parameters: fail-on threshold, engine selector, output dir, baseline."""
        self.pipeline_card = BrutalistCard(bg="#FFFFFF", shadow_offset=4, parent=self.content_widget)
        self.pipeline_card.setProperty("class", "card")
        p_layout = QVBoxLayout(self.pipeline_card)
        p_layout.setContentsMargins(18, 16, 18, 16)
        p_layout.setSpacing(12)

        pipeline_header = QLabel("02 // AUDIT PIPELINE & STATUTORY RULE PARAMETERS", self.pipeline_card)
        pipeline_header.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: 0.5px;")
        p_layout.addWidget(pipeline_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(8)

        # 1. Statutory Fail-On Gate Threshold
        fail_on_lbl = QLabel("Statutory Fail-On Gate:", self.pipeline_card)
        fail_on_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700;")
        self.fail_on_combo = QComboBox(self.pipeline_card)
        self.fail_on_combo.addItems(["high", "critical", "medium", "never"])
        self.fail_on_combo.setCurrentText("high")
        self.fail_on_combo.setFixedHeight(34)
        self.fail_on_combo.setStyleSheet(
            f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; font-weight: 700; padding: 4px;"
        )

        grid.addWidget(fail_on_lbl, 0, 0)
        grid.addWidget(self.fail_on_combo, 1, 0)

        # 2. SAST Analysis Engine Radio Buttons
        engine_lbl = QLabel("Static Analysis Engine:", self.pipeline_card)
        engine_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700;")
        engine_box = QHBoxLayout()
        engine_box.setSpacing(12)

        self.engine_tree_sitter_radio = QRadioButton(
            "Tree-Sitter Polyglot AST", self.pipeline_card
        )
        self.engine_tree_sitter_radio.setChecked(True)
        self.engine_opengrep_radio = QRadioButton(
            "Opengrep Engine", self.pipeline_card
        )
        self.engine_opengrep_radio.setChecked(False)

        self.engine_group = QButtonGroup(self)
        self.engine_group.addButton(self.engine_tree_sitter_radio)
        self.engine_group.addButton(self.engine_opengrep_radio)

        engine_box.addWidget(self.engine_tree_sitter_radio)
        engine_box.addWidget(self.engine_opengrep_radio)
        engine_box.addStretch()

        grid.addWidget(engine_lbl, 0, 1)
        grid.addLayout(engine_box, 1, 1)

        # 3. Output Reports Directory
        out_lbl = QLabel("Output Reports Directory:", self.pipeline_card)
        out_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700;")
        out_row = QHBoxLayout()
        out_row.setSpacing(6)
        self.output_dir_input = QLineEdit("./cs01-reports", self.pipeline_card)
        self.output_dir_input.setFixedHeight(34)
        self.output_dir_input.setStyleSheet(f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; padding: 4px 8px;")
        self.browse_output_btn = QPushButton("...", self.pipeline_card)
        self.browse_output_btn.setFixedHeight(34)
        self.browse_output_btn.setFixedWidth(40)
        self.browse_output_btn.setStyleSheet(f"background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; font-weight: 800;")
        out_row.addWidget(self.output_dir_input, 1)
        out_row.addWidget(self.browse_output_btn)

        grid.addWidget(out_lbl, 0, 2)
        grid.addLayout(out_row, 1, 2)

        p_layout.addLayout(grid)

        # 4. CI/CD Baseline Regression Suppression
        baseline_box = QVBoxLayout()
        baseline_box.setSpacing(6)
        self.baseline_checkbox = QCheckBox(
            "Enable Baseline Suppression (.cs01-baseline.json)", self.pipeline_card
        )
        baseline_row = QHBoxLayout()
        baseline_row.setSpacing(8)
        self.baseline_input = QLineEdit(self.pipeline_card)
        self.baseline_input.setPlaceholderText(".cs01-baseline.json (optional)")
        self.baseline_input.setFixedHeight(34)
        self.baseline_input.setStyleSheet(f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; padding: 4px 8px;")
        self.browse_baseline_btn = QPushButton("Browse Baseline...", self.pipeline_card)
        self.browse_baseline_btn.setFixedHeight(34)
        self.browse_baseline_btn.setStyleSheet(f"background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; font-weight: 800; padding: 4px 12px;")
        baseline_row.addWidget(self.baseline_input, 1)
        baseline_row.addWidget(self.browse_baseline_btn)

        baseline_box.addWidget(self.baseline_checkbox)
        baseline_box.addLayout(baseline_row)
        p_layout.addLayout(baseline_box)

        self.content_layout.addWidget(self.pipeline_card)

    def _build_deliverables_card(self) -> None:
        """Statutory compliance deliverables checklist (all 8 checked by default)."""
        self.deliverables_card = BrutalistCard(bg="#FFFFFF", shadow_offset=4, parent=self.content_widget)
        self.deliverables_card.setProperty("class", "card")
        d_layout = QVBoxLayout(self.deliverables_card)
        d_layout.setContentsMargins(18, 16, 18, 16)
        d_layout.setSpacing(12)

        d_header = QLabel("03 // STATUTORY COMPLIANCE DELIVERABLES CHECKLIST", self.deliverables_card)
        d_header.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: 0.5px;")
        d_layout.addWidget(d_header)

        grid = QGridLayout()
        grid.setHorizontalSpacing(24)
        grid.setVerticalSpacing(8)

        self.cb_dpo_html = QCheckBox(
            "Executive DPO HTML Report (cs01-dpo-report.html)", self.deliverables_card
        )
        self.cb_dataflow = QCheckBox(
            "Interactive 2D/3D Dataflow Visualizer (cs01-dataflow.html)", self.deliverables_card
        )
        self.cb_ropa_json = QCheckBox(
            "Technical RoPA Inventory JSON (ropa_map.json)", self.deliverables_card
        )
        self.cb_consent_audit = QCheckBox(
            "Consent Lifecycle Verification Audit (consent_audit.json)", self.deliverables_card
        )
        self.cb_sarif = QCheckBox(
            "Developer SARIF 2.1.0 Report (cs01-findings.sarif)", self.deliverables_card
        )
        self.cb_patches = QCheckBox(
            "Deterministic Remediation Patches (patches/*.patch)", self.deliverables_card
        )
        self.cb_evidence_bundle = QCheckBox(
            "Rule 13 Signed Evidence Bundle (cs01-evidence-bundle.zip)", self.deliverables_card
        )
        self.cb_markdown_brief = QCheckBox(
            "Executive DPO Markdown Brief (dpo_ai_executive_brief.md)", self.deliverables_card
        )

        for cb in (
            self.cb_dpo_html,
            self.cb_dataflow,
            self.cb_ropa_json,
            self.cb_consent_audit,
            self.cb_sarif,
            self.cb_patches,
            self.cb_evidence_bundle,
            self.cb_markdown_brief,
        ):
            cb.setChecked(True)

        grid.addWidget(self.cb_dpo_html, 0, 0)
        grid.addWidget(self.cb_dataflow, 0, 1)
        grid.addWidget(self.cb_ropa_json, 1, 0)
        grid.addWidget(self.cb_consent_audit, 1, 1)
        grid.addWidget(self.cb_sarif, 2, 0)
        grid.addWidget(self.cb_patches, 2, 1)
        grid.addWidget(self.cb_evidence_bundle, 3, 0)
        grid.addWidget(self.cb_markdown_brief, 3, 1)

        d_layout.addLayout(grid)
        self.content_layout.addWidget(self.deliverables_card)

    def _build_advanced_card(self) -> None:
        """Advanced options: stage models, strict test scanning, local AI triage, DAST prober."""
        self.advanced_card = BrutalistCard(bg="#FFFFFF", shadow_offset=4, parent=self.content_widget)
        self.advanced_card.setProperty("class", "card")
        adv_layout = QVBoxLayout(self.advanced_card)
        adv_layout.setContentsMargins(18, 16, 18, 16)
        adv_layout.setSpacing(12)

        header_row = QHBoxLayout()
        adv_header = QLabel("04 // ADVANCED & REGULATORY OPTIONS", self.advanced_card)
        adv_header.setStyleSheet(f"font-size: 11pt; font-weight: 800; color: {BRUTALIST_BLACK}; letter-spacing: 0.5px;")
        self.toggle_advanced_btn = QPushButton("Collapse", self.advanced_card)
        self.toggle_advanced_btn.setFixedWidth(100)
        self.toggle_advanced_btn.setFixedHeight(30)
        self.toggle_advanced_btn.setStyleSheet(f"background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; font-weight: 800; text-transform: uppercase;")
        header_row.addWidget(adv_header)
        header_row.addStretch()
        header_row.addWidget(self.toggle_advanced_btn)
        adv_layout.addLayout(header_row)

        self.advanced_body = QFrame(self.advanced_card)
        body_layout = QVBoxLayout(self.advanced_body)
        body_layout.setContentsMargins(0, 4, 0, 0)
        body_layout.setSpacing(10)

        # Row 1: Intermediate Models & Strict Test Exclusion
        row1 = QHBoxLayout()
        self.save_intermediate_checkbox = QCheckBox(
            "Save Intermediate Stage Models (JSON)", self.advanced_body
        )
        self.save_intermediate_checkbox.setChecked(True)
        self.strict_test_scanning_checkbox = QCheckBox(
            "Include Test & Fixture Directories in Statutory Scoring", self.advanced_body
        )
        self.strict_test_scanning_checkbox.setChecked(False)
        row1.addWidget(self.save_intermediate_checkbox)
        row1.addWidget(self.strict_test_scanning_checkbox)
        row1.addStretch()
        body_layout.addLayout(row1)

        # Row 2: Local AI Triage
        row2 = QHBoxLayout()
        self.ai_triage_checkbox = QCheckBox(
            "Local AI DPO Triage (Qwen 2.5 Coder via Ollama)", self.advanced_body
        )
        self.ai_triage_checkbox.setChecked(False)
        ai_endpoint_lbl = QLabel("Endpoint:", self.advanced_body)
        ai_endpoint_lbl.setStyleSheet(f"color: {BRUTALIST_BLACK}; font-weight: 700;")
        self.ai_endpoint_input = QLineEdit("http://localhost:11434", self.advanced_body)
        self.ai_endpoint_input.setFixedWidth(200)
        self.ai_endpoint_input.setStyleSheet(f"background-color: #FFFFFF; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; padding: 4px;")
        self.test_ai_btn = QPushButton("Test Connection", self.advanced_body)
        self.test_ai_btn.setStyleSheet(f"background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; border: 2px solid {BRUTALIST_BORDER}; font-weight: 800; padding: 4px 10px;")

        row2.addWidget(self.ai_triage_checkbox)
        row2.addWidget(ai_endpoint_lbl)
        row2.addWidget(self.ai_endpoint_input)
        row2.addWidget(self.test_ai_btn)
        row2.addStretch()
        body_layout.addLayout(row2)

        # Row 3: Live DAST Prober & Mandatory Statutory Authorization Disclaimer (§8(5))
        dast_box = QVBoxLayout()
        dast_box.setSpacing(4)
        self.dast_checkbox = QCheckBox(
            "Enable Live HTTP DAST Prober", self.advanced_body
        )
        self.dast_checkbox.setChecked(False)

        self.dast_disclaimer_checkbox = QCheckBox(
            "I confirm statutory authorization for live HTTP probes (§8(5))", self.advanced_body
        )
        self.dast_disclaimer_checkbox.setEnabled(False)
        self.dast_disclaimer_checkbox.setChecked(False)

        dast_box.addWidget(self.dast_checkbox)
        dast_box.addWidget(self.dast_disclaimer_checkbox)
        body_layout.addLayout(dast_box)

        adv_layout.addWidget(self.advanced_body)
        self.content_layout.addWidget(self.advanced_card)

    def _build_footer_bar(self) -> None:
        """Action bar housing Reset Defaults and primary Start Compliance Audit CTA."""
        footer_layout = QHBoxLayout()
        footer_layout.setContentsMargins(0, 10, 0, 4)
        footer_layout.setSpacing(14)
        footer_layout.addStretch()

        self.reset_btn = QPushButton("Reset Defaults", self.content_widget)
        self.reset_btn.setFixedHeight(44)
        self.reset_btn.setStyleSheet(
            f"QPushButton {{ background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_BLACK}; "
            f"font-weight: 800; font-size: 10pt; border: 2px solid {BRUTALIST_BORDER}; padding: 8px 20px; text-transform: uppercase; }} "
            f"QPushButton:hover {{ background-color: {BRUTALIST_YELLOW}; }}"
        )

        self.start_scan_btn = QPushButton("Start Compliance Audit", self.content_widget)
        self.start_scan_btn.setProperty("class", "primary")
        self.start_scan_btn.setFixedHeight(44)
        self.start_scan_btn.setMinimumWidth(260)
        self.start_scan_btn.setEnabled(False)
        self.start_scan_btn.setStyleSheet(
            f"QPushButton {{ background-color: {BRUTALIST_YELLOW}; color: {BRUTALIST_BLACK}; "
            f"font-weight: 900; font-size: 11pt; border: 2px solid {BRUTALIST_BORDER}; padding: 8px 24px; text-transform: uppercase; letter-spacing: 0.5px; }} "
            f"QPushButton:hover {{ background-color: #FFD400; }} "
            f"QPushButton:disabled {{ background-color: {BRUTALIST_BG_SECONDARY}; color: {BRUTALIST_MUTED}; border: 2px solid {BRUTALIST_MUTED}; }}"
        )

        footer_layout.addWidget(self.reset_btn)
        footer_layout.addWidget(self.start_scan_btn)
        self.content_layout.addLayout(footer_layout)

    # ------------------------------------------------------------------------
    # SIGNAL CONNECTIONS & SHORTCUTS
    # ------------------------------------------------------------------------

    def _connect_signals(self) -> None:
        """Connects UI events, mode switching, validation updates, and keyboard shortcuts."""
        # Target input and validation triggers
        self.target_input.textChanged.connect(self._on_target_text_changed)
        self.target_input.returnPressed.connect(self.validate_target)
        self.validate_btn.clicked.connect(self.validate_target)

        # Browse handlers
        self.browse_folder_btn.clicked.connect(self._on_browse_folder)
        self.browse_archive_btn.clicked.connect(self._on_browse_archive)
        self.browse_output_btn.clicked.connect(self._on_browse_output)
        self.browse_baseline_btn.clicked.connect(self._on_browse_baseline)

        # Mode radio switching
        self.mode_local_radio.toggled.connect(self._on_mode_toggled)
        self.mode_remote_radio.toggled.connect(self._on_mode_toggled)

        # DAST guardrail link
        self.dast_checkbox.toggled.connect(self._on_dast_toggled)

        # Baseline checkbox link
        self.baseline_checkbox.toggled.connect(self._on_baseline_checkbox_toggled)
        self.baseline_input.textChanged.connect(self._on_baseline_text_changed)

        # Advanced options toggle
        self.toggle_advanced_btn.clicked.connect(self._on_toggle_advanced)

        # Actions
        self.reset_btn.clicked.connect(self.reset_defaults)
        self.start_scan_btn.clicked.connect(self._on_start_scan_click)

        # Shortcuts (Ctrl+Enter / Ctrl+Return)
        s1 = QShortcut(QKeySequence("Ctrl+Return"), self)
        s1.activated.connect(self._on_start_scan_click)
        s2 = QShortcut(QKeySequence("Ctrl+Enter"), self)
        s2.activated.connect(self._on_start_scan_click)

    # ------------------------------------------------------------------------
    # TARGET VALIDATION & SECURITY CHECKS
    # ------------------------------------------------------------------------

    def validate_target(self) -> tuple[bool, str]:
        """
        Validates the current target path, archive safety, or remote Git URL.

        Checks performed:
        - Non-empty input validation.
        - Remote Git URL protocol verification (http/https/git/ssh; rejects ftp://, etc.).
        - Git URL syntax parsing and auto-population of branch ref.
        - Non-destructive archive inspection (.zip, .tar.gz, .tgz, .tar, .bz2):
          rejection of Zip-Slip path traversal (.., absolute Windows drive C:, leading /).
        - Local directory verification and file count stats badge.

        Returns:
            tuple[bool, str]: (is_valid, validation_message)
        """
        target = self.target_input.text().strip()

        # 1. Empty input check
        if not target:
            msg = "Target path cannot be empty"
            self.validation_label.setText(f"❌ {msg}")
            self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
            polish_widget(self.target_input, "error")
            self.start_scan_btn.setEnabled(False)
            return False, msg

        # 2. Unsupported protocol check
        if "://" in target:
            scheme = target.split("://", 1)[0].lower()
            if scheme not in ("http", "https", "git", "ssh"):
                msg = f"Unsupported protocol: {scheme}"
                self.validation_label.setText(f"❌ {msg}")
                self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
                polish_widget(self.target_input, "error")
                self.start_scan_btn.setEnabled(False)
                return False, msg

        # 3. Remote Git URL validation
        if is_git_url(target):
            clean_url, branch = parse_git_url(target)
            if branch:
                self.branch_input.setText(branch)
            msg = f"Valid Git repository URL ({clean_url})"
            self.validation_label.setText(f"✓ {msg}")
            self.validation_label.setStyleSheet("color: #111111; font-weight: 800; background-color: #B8F044; border: 1.5px solid #111111; padding: 4px 8px;")
            polish_widget(self.target_input, "success")
            self.start_scan_btn.setEnabled(True)
            return True, msg

        # 4. Local filesystem validation
        p = Path(target)
        if not p.exists():
            msg = f"Target path does not exist: {target}"
            self.validation_label.setText(f"❌ {msg}")
            self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
            polish_widget(self.target_input, "error")
            self.start_scan_btn.setEnabled(False)
            return False, msg

        # 5. Archive validation & Zip-Slip defense
        if is_archive(p):
            name_lower = p.name.lower()
            if (
                name_lower.endswith(".zip")
                or (p.suffix.lower() == ".zip")
                or zipfile.is_zipfile(p)
            ):
                try:
                    with zipfile.ZipFile(p, "r") as zf:
                        for member in zf.infolist():
                            m_name = member.filename
                            if (
                                ".." in m_name
                                or m_name.startswith(("/", "\\"))
                                or bool(re.match(r"^[a-zA-Z]:", m_name))
                            ):
                                msg = f"Malicious archive rejected (Zip Slip detected): {m_name}"
                                self.validation_label.setText(f"❌ {msg}")
                                self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
                                polish_widget(self.target_input, "error")
                                self.start_scan_btn.setEnabled(False)
                                return False, msg
                except (zipfile.BadZipFile, EOFError, OSError, ValueError, KeyError) as exc:
                    msg = f"Corrupted archive: {exc}"
                    self.validation_label.setText(f"❌ {msg}")
                    self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
                    polish_widget(self.target_input, "error")
                    self.start_scan_btn.setEnabled(False)
                    return False, msg

            elif (
                name_lower.endswith((".tar.gz", ".tgz", ".tar", ".tar.bz2", ".tar.xz", ".bz2"))
                or (p.exists() and tarfile.is_tarfile(p))
            ):
                try:
                    with tarfile.open(p, "r:*") as tf:
                        for member in tf.getmembers():
                            m_name = member.name
                            if (
                                ".." in m_name
                                or m_name.startswith(("/", "\\"))
                                or bool(re.match(r"^[a-zA-Z]:", m_name))
                            ):
                                msg = f"Malicious archive rejected (Zip Slip detected): {m_name}"
                                self.validation_label.setText(f"❌ {msg}")
                                self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
                                polish_widget(self.target_input, "error")
                                self.start_scan_btn.setEnabled(False)
                                return False, msg
                except (tarfile.TarError, zipfile.BadZipFile, EOFError, OSError, ValueError, KeyError) as exc:
                    msg = f"Corrupted archive: {exc}"
                    self.validation_label.setText(f"❌ {msg}")
                    self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
                    polish_widget(self.target_input, "error")
                    self.start_scan_btn.setEnabled(False)
                    return False, msg

            msg = f"Valid archive file ({p.name})"
            self.validation_label.setText(f"✓ {msg}")
            self.validation_label.setStyleSheet("color: #111111; font-weight: 800; background-color: #B8F044; border: 1.5px solid #111111; padding: 4px 8px;")
            polish_widget(self.target_input, "success")
            self.start_scan_btn.setEnabled(True)
            return True, msg

        # 6. Local directory validation & file counts badge
        if p.is_dir():
            code_count, sql_count, iac_count, size_str = self._count_directory_stats(p)
            msg = (
                f"Valid local directory ({p.name}) - {code_count} code files, "
                f"{sql_count} SQL schemas, {iac_count} IaC configs. Size: {size_str}."
            )
            self.validation_label.setText(f"✓ {msg}")
            self.validation_label.setStyleSheet("color: #111111; font-weight: 800; background-color: #B8F044; border: 1.5px solid #111111; padding: 4px 8px;")
            polish_widget(self.target_input, "success")
            self.start_scan_btn.setEnabled(True)
            return True, msg

        # Exists but neither archive nor directory
        msg = f"Target path is not a recognized directory or archive: {p.name}"
        self.validation_label.setText(f"❌ {msg}")
        self.validation_label.setStyleSheet("color: #FFFFFF; font-weight: 800; background-color: #FF4444; border: 1.5px solid #111111; padding: 4px 8px;")
        polish_widget(self.target_input, "error")
        self.start_scan_btn.setEnabled(False)
        return False, msg

    def _count_directory_stats(self, dir_path: Path) -> tuple[int, int, int, str]:
        """Counts code files, SQL schemas, IaC configs, and total size of a local directory."""
        code_exts = {
            ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".java",
            ".cpp", ".c", ".rs", ".php", ".rb", ".cs",
        }
        sql_exts = {".sql"}
        iac_exts = {".tf", ".yaml", ".yml"}
        iac_names = {"dockerfile"}

        code_count = 0
        sql_count = 0
        iac_count = 0
        total_bytes = 0

        skip_dirs = {".git", ".venv", "venv", "__pycache__", "node_modules", ".pytest_cache"}

        try:
            for root, dirs, files in os.walk(dir_path):
                dirs[:] = [d for d in dirs if d not in skip_dirs]
                for f in files:
                    f_path = Path(root) / f
                    try:
                        total_bytes += f_path.stat().st_size
                    except OSError:
                        pass
                    f_lower = f.lower()
                    suffix = Path(f_lower).suffix
                    if suffix in code_exts:
                        code_count += 1
                    elif suffix in sql_exts:
                        sql_count += 1
                    elif suffix in iac_exts or f_lower in iac_names:
                        iac_count += 1
        except (OSError, UnicodeDecodeError) as exc:
            logger.debug("Directory stats traversal error: %s", exc)

        if total_bytes < 1024:
            size_str = f"{total_bytes} B"
        elif total_bytes < 1024 * 1024:
            size_str = f"{total_bytes / 1024:.1f} KB"
        else:
            size_str = f"{total_bytes / (1024 * 1024):.1f} MB"

        return code_count, sql_count, iac_count, size_str

    # ------------------------------------------------------------------------
    # CONFIGURATION GENERATION
    # ------------------------------------------------------------------------

    def get_scan_config(self) -> ScanConfig:
        """
        Builds and returns a fully populated ScanConfig Pydantic model instance.
        """
        target = self.target_input.text().strip()
        # Normalize local paths to absolute Path.resolve() if not remote git url
        if target and not is_git_url(target) and not target.startswith("/workspace"):
            try:
                target = str(Path(target).resolve())
            except Exception:
                pass

        git_ref = self.branch_input.text().strip() or None
        baseline = self.baseline_input.text().strip() or None
        if baseline and not baseline.startswith("/"):
            try:
                baseline = str(Path(baseline).resolve())
            except Exception:
                pass

        fail_on = self.fail_on_combo.currentText()
        use_tree_sitter = self.engine_tree_sitter_radio.isChecked()
        use_opengrep = self.engine_opengrep_radio.isChecked()
        output_dir = self.output_dir_input.text().strip() or "./cs01-reports"
        try:
            output_dir = str(Path(output_dir).resolve())
        except Exception:
            pass

        # DAST Prober requires BOTH dast_checkbox and statutory authorization disclaimer (§8(5))
        dast_probe = (
            self.dast_checkbox.isChecked() and self.dast_disclaimer_checkbox.isChecked()
        )

        # Baseline suppression path
        baseline_path = (
            baseline if (baseline or self.baseline_checkbox.isChecked()) else None
        )

        # Output formats based on deliverables
        formats: list[str] = []
        if self.cb_sarif.isChecked():
            formats.append("sarif")
        if self.cb_ropa_json.isChecked() or self.cb_consent_audit.isChecked():
            formats.append("json")
        if self.cb_dpo_html.isChecked() or self.cb_dataflow.isChecked():
            formats.append("html")
        if self.cb_markdown_brief.isChecked():
            formats.append("markdown")
        if not formats:
            formats = ["sarif", "json", "html"]

        engine_cfg = EngineConfig(
            tree_sitter=use_tree_sitter,
            opengrep=use_opengrep,
            ai_triage=self.ai_triage_checkbox.isChecked(),
            ai_triage_endpoint=self.ai_endpoint_input.text().strip() or "http://localhost:11434",
        )

        bonus_cfg = BonusConfig(
            consent_audit=self.cb_consent_audit.isChecked(),
            patch_generator=self.cb_patches.isChecked(),
            dast_probe=dast_probe,
        )

        ai_cfg = AiConfig(
            enabled=True,
            endpoint=self.ai_endpoint_input.text().strip() or "http://localhost:11434",
        )

        return ScanConfig(
            scan_root=target,
            git_ref=git_ref,
            baseline_path=baseline_path,
            fail_on=fail_on,
            output_dir=output_dir,
            output_formats=formats,
            engine=engine_cfg,
            bonus=bonus_cfg,
            ai=ai_cfg,
            save_stage_output=self.save_intermediate_checkbox.isChecked(),
            strict_test_scanning=self.strict_test_scanning_checkbox.isChecked(),
        )

    def get_config(self) -> dict:
        """
        Returns a normalized configuration dictionary suitable for worker threads.
        """
        config = self.get_scan_config()
        d = config.model_dump()
        d["git_shallow_depth"] = self.clone_depth_spin.value()
        d["git_token"] = self.git_token_input.text().strip()
        d["deliverables"] = {
            "dpo_html": self.cb_dpo_html.isChecked(),
            "dataflow_visualizer": self.cb_dataflow.isChecked(),
            "ropa_json": self.cb_ropa_json.isChecked(),
            "consent_audit": self.cb_consent_audit.isChecked(),
            "sarif_report": self.cb_sarif.isChecked(),
            "remediation_patches": self.cb_patches.isChecked(),
            "evidence_bundle": self.cb_evidence_bundle.isChecked(),
            "executive_markdown": self.cb_markdown_brief.isChecked(),
        }
        return d

    def reset_defaults(self) -> None:
        """Restores all input fields, checkboxes, radios, and validation status to defaults."""
        self.target_input.blockSignals(True)
        self.target_input.setText("")
        self.target_input.blockSignals(False)

        self.branch_input.setText("")
        self.clone_depth_spin.setValue(1)
        self.git_token_input.setText("")

        self.output_dir_input.setText("./cs01-reports")
        self.baseline_checkbox.setChecked(False)
        self.baseline_input.setText("")

        self.fail_on_combo.setCurrentText("high")
        self.engine_tree_sitter_radio.setChecked(True)
        self.engine_opengrep_radio.setChecked(False)

        for cb in (
            self.cb_dpo_html,
            self.cb_dataflow,
            self.cb_ropa_json,
            self.cb_consent_audit,
            self.cb_sarif,
            self.cb_patches,
            self.cb_evidence_bundle,
            self.cb_markdown_brief,
        ):
            cb.setChecked(True)

        self.save_intermediate_checkbox.setChecked(True)
        self.strict_test_scanning_checkbox.setChecked(False)
        self.ai_triage_checkbox.setChecked(False)
        self.ai_endpoint_input.setText("http://localhost:11434")

        self.dast_checkbox.setChecked(False)
        self.dast_disclaimer_checkbox.setChecked(False)
        self.dast_disclaimer_checkbox.setEnabled(False)

        self.mode_local_radio.setChecked(True)
        self.git_options_frame.setVisible(False)

        self.validation_label.setText("")
        polish_widget(self.target_input, None)
        self.start_scan_btn.setEnabled(False)

    # ------------------------------------------------------------------------
    # EVENT HANDLERS & SLOTS
    # ------------------------------------------------------------------------

    def _on_target_text_changed(self, text: str) -> None:
        """Handles text modification in the target input field."""
        stripped = text.strip()
        if not stripped:
            self.validation_label.setText("")
            polish_widget(self.target_input, None)
            self.start_scan_btn.setEnabled(False)
            return

        # Eagerly enable the start button as soon as non-empty text exists;
        # full validation runs below and may disable again on hard errors.
        self.start_scan_btn.setEnabled(True)

        # Auto-switch to Remote Git mode if remote URL format detected
        if is_git_url(stripped) or ("://" in stripped and not stripped.startswith("file://")):
            if not self.mode_remote_radio.isChecked():
                self.mode_remote_radio.setChecked(True)
            self.git_options_frame.setVisible(True)
        elif Path(stripped).exists() or is_archive(stripped):
            if not self.mode_local_radio.isChecked():
                self.mode_local_radio.setChecked(True)
            self.git_options_frame.setVisible(False)

        # Validate target to update validation label and refine Start button state
        self.validate_target()

    def _on_mode_toggled(self) -> None:
        """Shows or hides Git-specific options depending on the active source mode."""
        is_remote = self.mode_remote_radio.isChecked()
        self.git_options_frame.setVisible(is_remote)

    def _on_dast_toggled(self, checked: bool) -> None:
        """Statutory guardrail: disclaimer is enabled only when DAST prober is opted in."""
        self.dast_disclaimer_checkbox.setEnabled(checked)
        if not checked:
            self.dast_disclaimer_checkbox.setChecked(False)

    def _on_baseline_checkbox_toggled(self, checked: bool) -> None:
        """Enables baseline file path entry when baseline suppression is active."""
        self.baseline_input.setEnabled(checked)

    def _on_baseline_text_changed(self, text: str) -> None:
        """Automatically checks baseline_checkbox when baseline path is provided."""
        if text.strip() and not self.baseline_checkbox.isChecked():
            self.baseline_checkbox.setChecked(True)

    def _on_toggle_advanced(self) -> None:
        """Toggles collapse/expand of the advanced options body frame."""
        is_visible = self.advanced_body.isVisible()
        self.advanced_body.setVisible(not is_visible)
        self.toggle_advanced_btn.setText("Expand" if is_visible else "Collapse")

    def _on_browse_folder(self) -> None:
        """Opens native directory picker dialog for local target folder."""
        path = QFileDialog.getExistingDirectory(self, "Select Local Codebase Directory")
        if path:
            self.target_input.setText(path)
            self.validate_target()

    def _on_browse_archive(self) -> None:
        """Opens native file picker dialog for codebase software archive."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Codebase Software Archive",
            "",
            "Archives (*.zip *.tar.gz *.tgz *.tar *.tar.bz2 *.bz2);;All Files (*.*)",
        )
        if path:
            self.target_input.setText(path)
            self.validate_target()

    def _on_browse_output(self) -> None:
        """Opens native directory picker dialog for output reports destination."""
        path = QFileDialog.getExistingDirectory(self, "Select Output Reports Directory")
        if path:
            self.output_dir_input.setText(path)

    def _on_browse_baseline(self) -> None:
        """Opens native file picker dialog for .cs01-baseline.json file."""
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Baseline Comparison JSON",
            "",
            "Baseline JSON (*.json);;All Files (*.*)",
        )
        if path:
            self.baseline_input.setText(path)
            self.baseline_checkbox.setChecked(True)

    def _on_start_scan_click(self) -> None:
        """Validates target and emits start_scan_requested and scan_requested signals."""
        is_valid, msg = self.validate_target()
        if not is_valid:
            self.validation_label.setText(f"❌ Cannot start audit: {msg}")
            self.validation_label.setStyleSheet("color: #ef4444; font-weight: bold;")
            return

        config = self.get_scan_config()
        self.start_scan_requested.emit(config)
        self.scan_requested.emit(self.get_config())
