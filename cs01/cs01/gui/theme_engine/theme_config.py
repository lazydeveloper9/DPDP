"""
CS-01 DPDP Compliance Desktop GUI - Theme Tokens & Configuration Schema.

Defines the comprehensive token schema, default values, inheritance parent keys,
and serialization logic for the CS-01 Theme Customization Studio.
"""
from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any


@dataclass
class TokenMeta:
    """Metadata for a theme token."""
    key: str
    display_name: str
    category: str
    default_value: Any
    parent_key: str | None = None
    value_type: str = "color"  # "color", "int", "float", "str", "bool"
    description: str = ""
    companion_bg_key: str | None = None  # for contrast checking


# ============================================================================
# COMPREHENSIVE TOKEN DEFINITIONS
# ============================================================================

TOKEN_DEFINITIONS: list[TokenMeta] = [
    # ------------------------------------------------------------------------
    # 1. Global Application Surfaces
    # ------------------------------------------------------------------------
    TokenMeta("global.bg.main", "Main Canvas Background", "Global Surfaces", "#FFF6CC", description="App-wide root window background"),
    TokenMeta("global.bg.secondary", "Secondary Background", "Global Surfaces", "#EAE6DA", description="Sidebar, HUD, and footer surface"),
    TokenMeta("global.bg.card", "Primary Card Background", "Global Surfaces", "#FFFFFF", description="Standard white container cards"),
    TokenMeta("global.bg.card_secondary", "Secondary Card Background", "Global Surfaces", "#FFF4C2", description="Subtle warm card background"),
    TokenMeta("global.bg.elevated", "Elevated Surface", "Global Surfaces", "#FFFFFF", description="Modals, dropdowns, floating menus"),
    TokenMeta("global.bg.panel", "Panel Background", "Global Surfaces", "#FFFFFF", description="Workspace panels and sidebars"),
    TokenMeta("global.bg.popup", "Popup Background", "Global Surfaces", "#FFFFFF", description="Popups and tooltips background"),
    TokenMeta("global.bg.dialog", "Dialog Background", "Global Surfaces", "#FFFFFF", description="Modal dialogue window background"),
    TokenMeta("global.bg.footer", "Footer / Status Bar Background", "Global Surfaces", "#EAE6DA", description="Bottom status bar background"),

    # ------------------------------------------------------------------------
    # 2. Global Typography
    # ------------------------------------------------------------------------
    TokenMeta("global.text.primary", "Primary Text", "Global Typography", "#111111", companion_bg_key="global.bg.card", description="Main body text, headings, prominent copy"),
    TokenMeta("global.text.secondary", "Secondary Text", "Global Typography", "#242424", companion_bg_key="global.bg.card", description="Labels, subtitles, secondary metadata"),
    TokenMeta("global.text.muted", "Muted Text", "Global Typography", "#595959", companion_bg_key="global.bg.card", description="De-emphasized timestamps, hints, captions"),
    TokenMeta("global.text.heading", "Main Headings", "Global Typography", "#111111", companion_bg_key="global.bg.main", description="Primary page titles"),
    TokenMeta("global.text.section_heading", "Section Headings", "Global Typography", "#111111", companion_bg_key="global.bg.main", description="Card and panel headers"),
    TokenMeta("global.text.card_heading", "Card Headings", "Global Typography", "#111111", companion_bg_key="global.bg.card", description="Card titles"),
    TokenMeta("global.text.body", "Body Copy", "Global Typography", "#111111", companion_bg_key="global.bg.card", description="Standard text and descriptions"),
    TokenMeta("global.text.link", "Link & Interactive Text", "Global Typography", "#3155FF", companion_bg_key="global.bg.card", description="Hyperlinks and inline actions"),
    TokenMeta("global.text.disabled", "Disabled Text", "Global Typography", "#888888", companion_bg_key="global.bg.card", description="Inactive controls and buttons"),
    TokenMeta("global.text.inverse", "Inverse Text", "Global Typography", "#FFFFFF", companion_bg_key="global.accent.primary", description="Text on dark/saturated backgrounds"),

    # ------------------------------------------------------------------------
    # 3. Global Design Elements & Borders
    # ------------------------------------------------------------------------
    TokenMeta("global.border.primary", "Primary Border", "Global Design", "#111111", description="High-contrast 2px solid boundary"),
    TokenMeta("global.border.secondary", "Secondary Border", "Global Design", "#111111", description="Inner card and divider borders"),
    TokenMeta("global.border.divider", "Divider Lines", "Global Design", "#111111", description="Horizontal rules and section separators"),
    TokenMeta("global.border.focus", "Focus Outline", "Global Design", "#111111", description="Keyboard focus indicator"),
    TokenMeta("global.accent.primary", "Primary Accent (Yellow)", "Global Design", "#FFE500", description="Signature brand action color"),
    TokenMeta("global.accent.secondary", "Secondary Accent (Cobalt)", "Global Design", "#3155FF", description="Electric cobalt secondary accent"),
    TokenMeta("global.selection.bg", "Selection Background", "Global Design", "#FFE500", description="Text and row selection highlight"),
    TokenMeta("global.selection.text", "Selection Text", "Global Design", "#111111", companion_bg_key="global.selection.bg", description="Text color within active selection"),
    TokenMeta("global.hover.surface", "Hover Surface Highlight", "Global Design", "#FFF4C2", description="Hover effect on cards and list items"),
    TokenMeta("global.active.surface", "Active Surface Pressed", "Global Design", "#FFD400", description="Pressed state on buttons and cards"),

    # ------------------------------------------------------------------------
    # 4. Neo-Brutalist Geometry & Shadows
    # ------------------------------------------------------------------------
    TokenMeta("design.border.width", "Border Width (px)", "Brutalist Geometry", 2, value_type="int", description="Width of hard outer borders (0-5px)"),
    TokenMeta("design.border.color", "Border Color", "Brutalist Geometry", "#111111", description="Outer container and card border color"),
    TokenMeta("design.corner.radius", "Corner Radius (px)", "Brutalist Geometry", 0, value_type="int", description="Card and button border radius (0-16px)"),
    TokenMeta("design.shadow.x", "Shadow X Offset (px)", "Brutalist Geometry", 4, value_type="int", description="Horizontal hard shadow offset (0-12px)"),
    TokenMeta("design.shadow.y", "Shadow Y Offset (px)", "Brutalist Geometry", 4, value_type="int", description="Vertical hard shadow offset (0-12px)"),
    TokenMeta("design.shadow.color", "Shadow Color", "Brutalist Geometry", "#111111", description="Color of solid unblurred offset shadow"),
    TokenMeta("design.shadow.enabled", "Hard Shadows Enabled", "Brutalist Geometry", True, value_type="bool", description="Toggle offset shadow rendering"),

    # ------------------------------------------------------------------------
    # 5. Global Typography Metrics
    # ------------------------------------------------------------------------
    TokenMeta("typography.font_sans", "Sans-Serif Font Family", "Typography Metrics", '"Cascadia Code", "Inter", "Arial", sans-serif', value_type="str", description="Main UI font stack"),
    TokenMeta("typography.font_mono", "Monospace Font Family", "Typography Metrics", '"Cascadia Code", "Consolas", monospace', value_type="str", description="Code diffs, hashes, and log console"),
    TokenMeta("typography.size_display", "Display Score Size (pt)", "Typography Metrics", 24, value_type="int", description="Readiness score numbers"),
    TokenMeta("typography.size_h1", "View Heading Size (pt)", "Typography Metrics", 18, value_type="int", description="Primary screen titles"),
    TokenMeta("typography.size_h2", "Section Header Size (pt)", "Typography Metrics", 13, value_type="int", description="Section headers and card titles"),
    TokenMeta("typography.size_h3", "Subsection Header Size (pt)", "Typography Metrics", 11, value_type="int", description="Group headers and sub-metrics"),
    TokenMeta("typography.size_body", "Body Font Size (pt)", "Typography Metrics", 10, value_type="int", description="Standard UI labels and copy"),
    TokenMeta("typography.size_caption", "Caption Font Size (pt)", "Typography Metrics", 8.5, value_type="float", description="Badges, tags, secondary metadata"),
    TokenMeta("typography.size_code", "Code Diff Size (pt)", "Typography Metrics", 9.5, value_type="float", description="Code viewer, hashes, logs"),

    # ------------------------------------------------------------------------
    # 6. Status & Statutory Risk Indicators
    # ------------------------------------------------------------------------
    TokenMeta("status.critical", "Critical Severity Color", "Status Indicators", "#FF4444", description="Critical compliance violation color"),
    TokenMeta("status.critical_bg", "Critical Severity Background", "Status Indicators", "#FFE8E8", description="Critical badge and row background"),
    TokenMeta("status.high", "High Severity Color", "Status Indicators", "#FF7538", description="High compliance risk color"),
    TokenMeta("status.high_bg", "High Severity Background", "Status Indicators", "#FFF0E8", description="High risk badge background"),
    TokenMeta("status.medium", "Medium Severity Color", "Status Indicators", "#FFE500", description="Medium compliance risk color"),
    TokenMeta("status.medium_bg", "Medium Severity Background", "Status Indicators", "#FFF4C2", description="Medium risk badge background"),
    TokenMeta("status.low", "Low Severity Color", "Status Indicators", "#3155FF", description="Low compliance risk color"),
    TokenMeta("status.low_bg", "Low Severity Background", "Status Indicators", "#EBF0FF", description="Low risk badge background"),
    TokenMeta("status.success", "Success / Compliant Color", "Status Indicators", "#B8F044", description="Compliant, zero-violation, pass color"),
    TokenMeta("status.success_bg", "Success Background", "Status Indicators", "#F3FDE0", description="Compliant badge background"),
    TokenMeta("status.info", "Info Color", "Status Indicators", "#3155FF", description="General statutory guidance and notice color"),
    TokenMeta("status.info_bg", "Info Background", "Status Indicators", "#EBF0FF", description="Notice panel background"),
    TokenMeta("status.warning", "Warning Color", "Status Indicators", "#FF7538", description="Audit warning banner color"),
    TokenMeta("status.warning_bg", "Warning Background", "Status Indicators", "#FFF0E8", description="Warning banner background"),
    TokenMeta("status.resolved", "Resolved Color", "Status Indicators", "#B8F044", description="Remediated finding badge color"),
    TokenMeta("status.running", "Running Color", "Status Indicators", "#FFD400", description="Scan execution active color"),
    TokenMeta("status.pending", "Pending Color", "Status Indicators", "#595959", description="Queued stage indicator"),
    TokenMeta("status.failed", "Failed Color", "Status Indicators", "#FF4444", description="Failed pipeline stage indicator"),

    # ------------------------------------------------------------------------
    # 7. Component: Sidebar Navigation
    # ------------------------------------------------------------------------
    TokenMeta("component.sidebar.bg", "Sidebar Background", "Sidebar", "#EAE6DA", parent_key="global.bg.secondary"),
    TokenMeta("component.sidebar.text", "Sidebar Text", "Sidebar", "#111111", parent_key="global.text.primary", companion_bg_key="component.sidebar.bg"),
    TokenMeta("component.sidebar.active_bg", "Active Item Background", "Sidebar", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("component.sidebar.active_text", "Active Item Text", "Sidebar", "#111111", parent_key="global.text.primary", companion_bg_key="component.sidebar.active_bg"),
    TokenMeta("component.sidebar.hover_bg", "Hover Item Background", "Sidebar", "#FFF4C2", parent_key="global.hover.surface"),
    TokenMeta("component.sidebar.border", "Sidebar Border", "Sidebar", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.sidebar.divider", "Sidebar Separator", "Sidebar", "#111111", parent_key="global.border.divider"),

    # ------------------------------------------------------------------------
    # 8. Component: Toolbar & HUD Bar
    # ------------------------------------------------------------------------
    TokenMeta("component.toolbar.bg", "HUD Bar Background", "HUD Toolbar", "#EAE6DA", parent_key="global.bg.secondary"),
    TokenMeta("component.toolbar.text", "HUD Bar Text", "HUD Toolbar", "#111111", parent_key="global.text.primary", companion_bg_key="component.toolbar.bg"),
    TokenMeta("component.toolbar.border", "HUD Bottom Border", "HUD Toolbar", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.toolbar.version_badge_bg", "Version Badge Background", "HUD Toolbar", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("component.toolbar.privacy_badge_bg", "Zero-Egress Badge Background", "HUD Toolbar", "#B8F044", parent_key="status.success"),

    # ------------------------------------------------------------------------
    # 9. Component: Buttons
    # ------------------------------------------------------------------------
    TokenMeta("component.button.primary.bg", "Primary Button Background", "Buttons", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("component.button.primary.text", "Primary Button Text", "Buttons", "#111111", parent_key="global.text.primary", companion_bg_key="component.button.primary.bg"),
    TokenMeta("component.button.primary.border", "Primary Button Border", "Buttons", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.button.primary.hover_bg", "Primary Button Hover", "Buttons", "#FFD400", parent_key="global.active.surface"),
    TokenMeta("component.button.primary.pressed_bg", "Primary Button Pressed", "Buttons", "#111111", parent_key="global.text.primary"),
    TokenMeta("component.button.primary.shadow", "Primary Button Shadow", "Buttons", "#111111", parent_key="design.shadow.color"),

    TokenMeta("component.button.secondary.bg", "Secondary Button Background", "Buttons", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("component.button.secondary.text", "Secondary Button Text", "Buttons", "#111111", parent_key="global.text.primary", companion_bg_key="component.button.secondary.bg"),
    TokenMeta("component.button.secondary.border", "Secondary Button Border", "Buttons", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.button.secondary.hover_bg", "Secondary Button Hover", "Buttons", "#FFF4C2", parent_key="global.hover.surface"),

    TokenMeta("component.button.danger.bg", "Destructive Button Background", "Buttons", "#FF4444", parent_key="status.critical"),
    TokenMeta("component.button.danger.text", "Destructive Button Text", "Buttons", "#FFFFFF", parent_key="global.text.inverse", companion_bg_key="component.button.danger.bg"),
    TokenMeta("component.button.danger.border", "Destructive Button Border", "Buttons", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.button.danger.hover_bg", "Destructive Button Hover", "Buttons", "#E02E2E"),

    # ------------------------------------------------------------------------
    # 10. Component: Cards & Panels
    # ------------------------------------------------------------------------
    TokenMeta("component.card.bg", "Card Background", "Cards", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("component.card.heading_text", "Card Heading Text", "Cards", "#111111", parent_key="global.text.card_heading", companion_bg_key="component.card.bg"),
    TokenMeta("component.card.body_text", "Card Body Text", "Cards", "#111111", parent_key="global.text.body", companion_bg_key="component.card.bg"),
    TokenMeta("component.card.border", "Card Border", "Cards", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.card.shadow", "Card Shadow Color", "Cards", "#111111", parent_key="design.shadow.color"),
    TokenMeta("component.card.hover_bg", "Card Hover Background", "Cards", "#FFF4C2", parent_key="global.hover.surface"),

    # ------------------------------------------------------------------------
    # 11. Component: Inputs & Dropdowns
    # ------------------------------------------------------------------------
    TokenMeta("component.input.bg", "Input Background", "Inputs", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("component.input.text", "Input Text", "Inputs", "#111111", parent_key="global.text.primary", companion_bg_key="component.input.bg"),
    TokenMeta("component.input.placeholder", "Placeholder Text", "Inputs", "#888888", parent_key="global.text.muted", companion_bg_key="component.input.bg"),
    TokenMeta("component.input.border", "Input Border", "Inputs", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.input.focus_border", "Input Focus Border", "Inputs", "#111111", parent_key="global.border.focus"),
    TokenMeta("component.input.selection_bg", "Input Selection Highlight", "Inputs", "#FFE500", parent_key="global.selection.bg"),
    TokenMeta("component.input.disabled_bg", "Disabled Input Background", "Inputs", "#EAE6DA", parent_key="global.bg.secondary"),

    # ------------------------------------------------------------------------
    # 12. Component: Tables & Data Grids
    # ------------------------------------------------------------------------
    TokenMeta("component.table.header_bg", "Table Header Background", "Tables", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("component.table.header_text", "Table Header Text", "Tables", "#111111", parent_key="global.text.primary", companion_bg_key="component.table.header_bg"),
    TokenMeta("component.table.header_border", "Table Header Border", "Tables", "#111111", parent_key="global.border.primary"),
    TokenMeta("component.table.row_bg", "Table Row Background", "Tables", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("component.table.row_alt_bg", "Alternate Row Background", "Tables", "#FFF4C2", parent_key="global.bg.card_secondary"),
    TokenMeta("component.table.selected_row_bg", "Selected Row Background", "Tables", "#FFE500", parent_key="global.selection.bg"),
    TokenMeta("component.table.hover_row_bg", "Hover Row Background", "Tables", "#FFF4C2", parent_key="global.hover.surface"),
    TokenMeta("component.table.cell_text", "Cell Text", "Tables", "#111111", parent_key="global.text.primary", companion_bg_key="component.table.row_bg"),
    TokenMeta("component.table.grid_line", "Grid Line Color", "Tables", "#111111", parent_key="global.border.secondary"),

    # ------------------------------------------------------------------------
    # 13. Page: Dashboard
    # ------------------------------------------------------------------------
    TokenMeta("page.dashboard.bg", "Dashboard Background", "Page: Dashboard", "#FFF6CC", parent_key="global.bg.main"),
    TokenMeta("page.dashboard.heading", "Dashboard Title", "Page: Dashboard", "#111111", parent_key="global.text.heading", companion_bg_key="page.dashboard.bg"),
    TokenMeta("page.dashboard.subtitle", "Dashboard Subtitle", "Page: Dashboard", "#595959", parent_key="global.text.muted", companion_bg_key="page.dashboard.bg"),
    TokenMeta("page.dashboard.kpi_card_bg", "KPI Metric Card Background", "Page: Dashboard", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.dashboard.kpi_card_text", "KPI Metric Card Text", "Page: Dashboard", "#111111", parent_key="global.text.primary", companion_bg_key="page.dashboard.kpi_card_bg"),
    TokenMeta("page.dashboard.kpi_card_border", "KPI Metric Card Border", "Page: Dashboard", "#111111", parent_key="global.border.primary"),
    TokenMeta("page.dashboard.kpi_card_shadow", "KPI Metric Card Shadow", "Page: Dashboard", "#111111", parent_key="design.shadow.color"),
    TokenMeta("page.dashboard.gauge_color", "Readiness Gauge Accent", "Page: Dashboard", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("page.dashboard.penalty_bg", "Penalty Exposure Panel Background", "Page: Dashboard", "#FFE8E8", parent_key="status.critical_bg"),
    TokenMeta("page.dashboard.pillar_card_bg", "Statutory Pillar Card Background", "Page: Dashboard", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.dashboard.pillar_text", "Statutory Pillar Text", "Page: Dashboard", "#111111", parent_key="global.text.primary", companion_bg_key="page.dashboard.pillar_card_bg"),
    TokenMeta("page.dashboard.pillar_progress", "Pillar Progress Bar Foreground", "Page: Dashboard", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("page.dashboard.section_divider", "Dashboard Section Divider", "Page: Dashboard", "#111111", parent_key="global.border.divider"),

    # ------------------------------------------------------------------------
    # 14. Page: Scan Setup
    # ------------------------------------------------------------------------
    TokenMeta("page.scan_setup.bg", "Scan Setup Background", "Page: Scan Setup", "#FFF6CC", parent_key="global.bg.main"),
    TokenMeta("page.scan_setup.card_bg", "Setup Step Card Background", "Page: Scan Setup", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.scan_setup.input_bg", "Setup Input Background", "Page: Scan Setup", "#FFFFFF", parent_key="component.input.bg"),
    TokenMeta("page.scan_setup.input_text", "Setup Input Text", "Page: Scan Setup", "#111111", parent_key="component.input.text", companion_bg_key="page.scan_setup.input_bg"),
    TokenMeta("page.scan_setup.input_border", "Setup Input Border", "Page: Scan Setup", "#111111", parent_key="component.input.border"),
    TokenMeta("page.scan_setup.browse_btn_bg", "Browse Button Background", "Page: Scan Setup", "#FFFFFF", parent_key="component.button.secondary.bg"),
    TokenMeta("page.scan_setup.browse_btn_text", "Browse Button Text", "Page: Scan Setup", "#111111", parent_key="component.button.secondary.text", companion_bg_key="page.scan_setup.browse_btn_bg"),
    TokenMeta("page.scan_setup.primary_btn_bg", "Start Scan Button Background", "Page: Scan Setup", "#FFE500", parent_key="component.button.primary.bg"),
    TokenMeta("page.scan_setup.primary_btn_text", "Start Scan Button Text", "Page: Scan Setup", "#111111", parent_key="component.button.primary.text", companion_bg_key="page.scan_setup.primary_btn_bg"),
    TokenMeta("page.scan_setup.info_panel_bg", "Scope Info Panel Background", "Page: Scan Setup", "#FFF4C2", parent_key="global.bg.card_secondary"),
    TokenMeta("page.scan_setup.section_heading", "Setup Section Heading", "Page: Scan Setup", "#111111", parent_key="global.text.section_heading", companion_bg_key="page.scan_setup.bg"),

    # ------------------------------------------------------------------------
    # 15. Page: Execution
    # ------------------------------------------------------------------------
    TokenMeta("page.execution.workspace_bg", "Execution Workspace Background", "Page: Execution", "#FFF6CC", parent_key="global.bg.main"),
    TokenMeta("page.execution.progress_panel_bg", "Progress Panel Background", "Page: Execution", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.execution.stage_active", "Active Stage Highlight", "Page: Execution", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("page.execution.stage_completed", "Completed Stage Highlight", "Page: Execution", "#B8F044", parent_key="status.success"),
    TokenMeta("page.execution.stage_pending", "Pending Stage Muted", "Page: Execution", "#EAE6DA", parent_key="global.bg.secondary"),
    TokenMeta("page.execution.stage_failed", "Failed Stage Red", "Page: Execution", "#FF4444", parent_key="status.critical"),
    TokenMeta("page.execution.progress_bar_fg", "Progress Bar Fill", "Page: Execution", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("page.execution.progress_bar_bg", "Progress Bar Track", "Page: Execution", "#EAE6DA", parent_key="global.bg.secondary"),
    TokenMeta("page.execution.log_panel_bg", "Log Console Background", "Page: Execution", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.execution.log_text", "Log Console Text", "Page: Execution", "#111111", parent_key="global.text.primary", companion_bg_key="page.execution.log_panel_bg"),
    TokenMeta("page.execution.cancel_btn_bg", "Cancel Scan Button Background", "Page: Execution", "#FF4444", parent_key="component.button.danger.bg"),
    TokenMeta("page.execution.cancel_btn_text", "Cancel Scan Button Text", "Page: Execution", "#FFFFFF", parent_key="component.button.danger.text", companion_bg_key="page.execution.cancel_btn_bg"),

    # ------------------------------------------------------------------------
    # 16. Page: Findings
    # ------------------------------------------------------------------------
    TokenMeta("page.findings.workspace_bg", "Findings Workspace Background", "Page: Findings", "#FFF6CC", parent_key="global.bg.main"),
    TokenMeta("page.findings.card_bg", "Summary Cards Background", "Page: Findings", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.findings.filter_toolbar_bg", "Filter Bar Background", "Page: Findings", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.findings.search_bg", "Search Input Background", "Page: Findings", "#FFFFFF", parent_key="component.input.bg"),
    TokenMeta("page.findings.search_text", "Search Input Text", "Page: Findings", "#111111", parent_key="component.input.text", companion_bg_key="page.findings.search_bg"),
    TokenMeta("page.findings.table_header_bg", "Findings Table Header Background", "Page: Findings", "#FFFFFF", parent_key="component.table.header_bg"),
    TokenMeta("page.findings.table_header_text", "Findings Table Header Text", "Page: Findings", "#111111", parent_key="component.table.header_text", companion_bg_key="page.findings.table_header_bg"),
    TokenMeta("page.findings.table_row_bg", "Findings Table Row Background", "Page: Findings", "#FFFFFF", parent_key="component.table.row_bg"),
    TokenMeta("page.findings.table_row_alt_bg", "Findings Table Alt Row Background", "Page: Findings", "#FFF4C2", parent_key="component.table.row_alt_bg"),
    TokenMeta("page.findings.table_row_selected_bg", "Findings Table Selected Row", "Page: Findings", "#FFE500", parent_key="component.table.selected_row_bg"),
    TokenMeta("page.findings.table_text", "Findings Table Cell Text", "Page: Findings", "#111111", parent_key="component.table.cell_text", companion_bg_key="page.findings.table_row_bg"),
    TokenMeta("page.findings.detail_panel_bg", "Detail Drawer Background", "Page: Findings", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.findings.code_panel_bg", "Code Evidence Background", "Page: Findings", "#FFF4C2", parent_key="global.bg.card_secondary"),
    TokenMeta("page.findings.remediation_panel_bg", "Remediation Well Background", "Page: Findings", "#F3FDE0", parent_key="status.success_bg"),
    TokenMeta("page.findings.patch_btn_bg", "Apply Patch Button Background", "Page: Findings", "#FFE500", parent_key="component.button.primary.bg"),
    TokenMeta("page.findings.patch_btn_text", "Apply Patch Button Text", "Page: Findings", "#111111", parent_key="component.button.primary.text", companion_bg_key="page.findings.patch_btn_bg"),

    # ------------------------------------------------------------------------
    # 17. Page: PII Inventory
    # ------------------------------------------------------------------------
    TokenMeta("page.pii.page_bg", "PII Inventory Page Background", "Page: PII Inventory", "#FFF6CC", parent_key="global.bg.main"),
    TokenMeta("page.pii.card_bg", "PII Metric Card Background", "Page: PII Inventory", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.pii.table_header_bg", "PII Table Header Background", "Page: PII Inventory", "#FFFFFF", parent_key="component.table.header_bg"),
    TokenMeta("page.pii.table_row_bg", "PII Table Row Background", "Page: PII Inventory", "#FFFFFF", parent_key="component.table.row_bg"),
    TokenMeta("page.pii.table_row_alt_bg", "PII Table Alt Row Background", "Page: PII Inventory", "#FFF4C2", parent_key="component.table.row_alt_bg"),
    TokenMeta("page.pii.badge_bg", "PII Category Badge Background", "Page: PII Inventory", "#FFE500", parent_key="global.accent.primary"),
    TokenMeta("page.pii.masked_bg", "Masked Value Capsule Background", "Page: PII Inventory", "#EAE6DA", parent_key="global.bg.secondary"),
    TokenMeta("page.pii.confidence_fg", "High Confidence Highlight", "Page: PII Inventory", "#B8F044", parent_key="status.success"),
    TokenMeta("page.pii.hash_text", "SHA-256 Hash Text Color", "Page: PII Inventory", "#595959", parent_key="global.text.muted", companion_bg_key="page.pii.table_row_bg"),

    # ------------------------------------------------------------------------
    # 18. Page: Reports
    # ------------------------------------------------------------------------
    TokenMeta("page.reports.workspace_bg", "Reports Workspace Background", "Page: Reports", "#FFF6CC", parent_key="global.bg.main"),
    TokenMeta("page.reports.card_bg", "Report Artifact Card Background", "Page: Reports", "#FFFFFF", parent_key="global.bg.card"),
    TokenMeta("page.reports.table_header_bg", "Reports Table Header Background", "Page: Reports", "#FFFFFF", parent_key="component.table.header_bg"),
    TokenMeta("page.reports.table_row_bg", "Reports Table Row Background", "Page: Reports", "#FFFFFF", parent_key="component.table.row_bg"),
    TokenMeta("page.reports.badge_bg", "Available Report Badge Background", "Page: Reports", "#B8F044", parent_key="status.success"),
    TokenMeta("page.reports.load_btn_bg", "View / Load Button Background", "Page: Reports", "#FFE500", parent_key="component.button.primary.bg"),
    TokenMeta("page.reports.export_btn_bg", "Export Report Button Background", "Page: Reports", "#3155FF", parent_key="global.accent.secondary"),
    TokenMeta("page.reports.delete_btn_bg", "Delete Report Button Background", "Page: Reports", "#FF4444", parent_key="component.button.danger.bg"),
]

TOKEN_MAP: dict[str, TokenMeta] = {t.key: t for t in TOKEN_DEFINITIONS}


@dataclass
class ThemeConfig:
    """
    Mutable theme configuration container holding active overrides and metadata.
    Supports resolution hierarchy: Component Override -> Page Override -> User Global -> Default.
    """
    name: str = "Bold Enterprise"
    description: str = "Default Neo-Brutalist enterprise theme"
    schema_version: int = 1
    overrides: dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieves raw override value or default from definitions."""
        if key in self.overrides:
            return self.overrides[key]
        if key in TOKEN_MAP:
            return TOKEN_MAP[key].default_value
        return default

    def set(self, key: str, value: Any) -> None:
        """Sets a specific token override."""
        self.overrides[key] = value

    def reset(self, key: str) -> None:
        """Removes an override for a token so it inherits."""
        self.overrides.pop(key, None)

    def is_overridden(self, key: str) -> bool:
        """Checks if token has explicit override."""
        return key in self.overrides

    def resolve(self, key: str) -> Any:
        """
        Resolves token following full inheritance chain:
        1. Token's own override in self.overrides
        2. Parent token's override in self.overrides (recursively)
        3. Token's default value
        4. Parent token's default value (recursively)
        """
        # 1. Direct override
        if key in self.overrides:
            return self.overrides[key]

        # 2. Walk parent inheritance for override
        curr = TOKEN_MAP.get(key)
        while curr and curr.parent_key:
            parent_key = curr.parent_key
            if parent_key in self.overrides:
                return self.overrides[parent_key]
            curr = TOKEN_MAP.get(parent_key)

        # 3. Default value of key
        if key in TOKEN_MAP:
            return TOKEN_MAP[key].default_value

        return None

    def get_inheritance_status(self, key: str) -> str:
        """Returns inheritance label: 'Direct Override', 'Inherited Override', or 'Default'."""
        if key in self.overrides:
            if key.startswith("component."):
                return "Component Override"
            if key.startswith("page."):
                return "Page Override"
            return "Global Override"

        curr = TOKEN_MAP.get(key)
        while curr and curr.parent_key:
            parent_key = curr.parent_key
            if parent_key in self.overrides:
                return f"Inherited ({parent_key})"
            curr = TOKEN_MAP.get(parent_key)

        return "Inherited (Default)"

    def to_dict(self) -> dict[str, Any]:
        """Serializes configuration to dictionary for JSON persistence."""
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "description": self.description,
            "overrides": copy.deepcopy(self.overrides),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ThemeConfig:
        """Safely deserializes configuration from dictionary."""
        name = str(data.get("name", "Custom"))
        desc = str(data.get("description", ""))
        ver = int(data.get("schema_version", 1))
        raw_overrides = data.get("overrides", {})
        clean_overrides: dict[str, Any] = {}
        if isinstance(raw_overrides, dict):
            for k, v in raw_overrides.items():
                if isinstance(k, str) and (isinstance(v, (str, int, float, bool))):
                    clean_overrides[k] = v
        return cls(name=name, description=desc, schema_version=ver, overrides=clean_overrides)
