"""
Stage 4 Pass B Engine — Cross-File Architectural Assertions
===========================================================
Queries the whole-repo inventory and Base Product Capability Report to surface systemic
compliance gaps across the full statutory framework (DPDP Rules 1 to 23).
"""

from __future__ import annotations
import re
from typing import Any, Optional

from cs01.models import (
    RepoModel, RawFinding, PassType, Severity, ScanConfig, ProductCapabilityReport,
)
from .rule_loader import get_rule_by_id

ROUTE_DECORATOR_PATTERN = re.compile(
    r"@(?:app|router|blueprint|api)\.(get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.I,
)

CONSENT_WITHDRAWAL_ROUTE_PATTERN = re.compile(
    r"(consent/withdraw|withdraw-consent|consent/revoke|opt-out|user/delete|account/delete|erasure|forget-me)",
    re.I,
)

AGE_GATE_PATTERN = re.compile(
    r"(is_minor|check_age|parental_consent|guardian_consent|age\s*<\s*18|min_age)",
    re.I,
)

RETENTION_JOB_PATTERN = re.compile(
    r"(purge_expired|cleanup_pii|delete_old_users|retention_job|scheduled_purge|data_retention)",
    re.I,
)

RIGHTS_ROUTE_PATTERN = re.compile(
    r"(user/data-summary|export-data|user/nominee|nomination|grievance)",
    re.I,
)

DPO_CONTACT_PATTERN = re.compile(
    r"(dpo@|privacy@|grievance@|data_protection_officer|grievance_officer)",
    re.I,
)

TRACKING_SDK_PATTERN = re.compile(
    r"(google-analytics|mixpanel|amplitude|facebook-pixel|adjust|appsflyer|segment)",
    re.I,
)

BREACH_INTIMATION_PATTERN = re.compile(
    r"(notify_breach|breach_intimation|incident_notice|notify_dpbi|report_breach)",
    re.I,
)


class RepoInventory:
    """Aggregated whole-repo architectural facts extracted from RepoModel."""
    def __init__(self, model: RepoModel, capability_report: Optional[ProductCapabilityReport] = None):
        self.api_routes: list[dict[str, str]] = []
        self.schema_pii_tables: set[str] = set()
        self.has_children_dob_data: bool = False
        self.has_age_gate: bool = False
        self.has_retention_routine: bool = False
        self.has_dpo_contact: bool = False
        self.has_rights_endpoint: bool = False
        self.has_breach_intimation: bool = False
        self.outbound_third_party_hosts: set[str] = set()
        self.has_child_tracking: bool = False

        self._build_inventory(model, capability_report)

    def _build_inventory(self, model: RepoModel, capability_report: Optional[ProductCapabilityReport]) -> None:
        from cs01.pipeline.stage3_detect.pii_detector import PII_FIELD_NAME_PATTERNS

        for schema in model.schema_records:
            col = schema.column_or_field.lower()
            if any(pat.search(col) for pat, _ in PII_FIELD_NAME_PATTERNS):
                self.schema_pii_tables.add(schema.table_or_model)
            if any(k in col for k in ("dob", "date_of_birth", "birth_date", "child_age", "minor")):
                self.has_children_dob_data = True

        for ast_file in model.ast_index:
            for dec in ast_file.decorators:
                d_name = dec.get("name", "")
                m = ROUTE_DECORATOR_PATTERN.search(d_name)
                if m:
                    route_path = m.group(2)
                    self.api_routes.append({
                        "method": m.group(1).upper(),
                        "path": route_path,
                        "file": ast_file.path,
                        "line": dec.get("line", 1),
                    })
                    if RIGHTS_ROUTE_PATTERN.search(route_path):
                        self.has_rights_endpoint = True

            for func in ast_file.functions:
                fname = func.get("name", "")
                calls_str = " ".join(c.get("snippet", "") for c in func.get("calls", []))
                combined_func_text = f"{fname} {calls_str}"

                if AGE_GATE_PATTERN.search(combined_func_text):
                    self.has_age_gate = True
                if RETENTION_JOB_PATTERN.search(combined_func_text):
                    self.has_retention_routine = True
                if BREACH_INTIMATION_PATTERN.search(combined_func_text):
                    self.has_breach_intimation = True

            for call in ast_file.calls:
                snip = call.get("snippet", "")
                if DPO_CONTACT_PATTERN.search(snip):
                    self.has_dpo_contact = True
                if TRACKING_SDK_PATTERN.search(snip):
                    self.has_child_tracking = True


def evaluate_pass_b(
    model: RepoModel,
    cfg: ScanConfig,
    capability_report: Optional[ProductCapabilityReport] = None,
) -> list[RawFinding]:
    """Evaluate whole-repo Pass B assertions against the constructed inventory and capabilities."""
    findings: list[RawFinding] = []
    inventory = RepoInventory(model, capability_report)

    def _create_assertion_finding(
        rule_id: str,
        snippet: str,
        matched_entity: str,
        file: Optional[str] = None,
        line: Optional[int] = None,
    ) -> None:
        rule_def = get_rule_by_id(rule_id)
        if not rule_def:
            return

        fid = f"{rule_id}:{file or 'repo_architecture'}:{line or 1}"
        findings.append(
            RawFinding(
                id=fid,
                rule_id=rule_id,
                pass_type=PassType.B,
                file=file,
                line_start=line,
                line_end=line,
                snippet=snippet,
                matched_entity=matched_entity,
                dpdp_section=rule_def["dpdp_section"],
                dpdp_rule=rule_def["dpdp_rule"],
                penalty_band=rule_def["penalty_band"],
                severity=Severity(rule_def["severity"]),
                engine="inventory",
                message=rule_def["description"],
                remediation=rule_def["remediation"],
            )
        )

    # -------------------------------------------------------------------------
    # Rule ARCH-DPDP-001 (Rule 3(c)): Missing Consent Withdrawal / Erasure Route
    # -------------------------------------------------------------------------
    if inventory.schema_pii_tables:
        has_withdrawal_endpoint = any(
            CONSENT_WITHDRAWAL_ROUTE_PATTERN.search(r["path"]) for r in inventory.api_routes
        )
        if not has_withdrawal_endpoint:
            table_list = ", ".join(sorted(inventory.schema_pii_tables)[:5])
            _create_assertion_finding(
                rule_id="ARCH-DPDP-001",
                snippet=f"Discovered PII tables: [{table_list}], but 0 consent withdrawal or user erasure routes found.",
                matched_entity="repo_routes",
            )

    # -------------------------------------------------------------------------
    # Rule ARCH-DPDP-002 (Rule 8(2)): Missing Scheduled Purge Routine
    # -------------------------------------------------------------------------
    if inventory.schema_pii_tables and not inventory.has_retention_routine:
        _create_assertion_finding(
            rule_id="ARCH-DPDP-002",
            snippet="PII tables persist data, but no automated retention cleanup routine detected across repository.",
            matched_entity="background_jobs",
        )

    # -------------------------------------------------------------------------
    # Rule ARCH-DPDP-003 (Rule 10): Children DOB Without Guardian Age-Gate
    # -------------------------------------------------------------------------
    if inventory.has_children_dob_data and not inventory.has_age_gate:
        _create_assertion_finding(
            rule_id="ARCH-DPDP-003",
            snippet="Schema captures date_of_birth/age fields, but no verifiable minor age-gate routine found in backend logic.",
            matched_entity="age_verification",
        )

    # -------------------------------------------------------------------------
    # Rule ARCH-DPDP-005 (Rule 7(1)): Incomplete Breach-Response & Audit Telemetry
    # -------------------------------------------------------------------------
    AUDIT_TABLE_PATTERN = re.compile(r"(audit_?log|security_?log|access_?log|incident_?log)", re.I)
    TARGET_RESOURCE_PATTERN = re.compile(r"(target_resource_id|resource_id|subject_id|target_id)", re.I)

    has_audit_table = False
    audit_has_target_resource = False
    target_resource_is_nullable = False

    for schema in model.schema_records:
        tname = schema.table_or_model
        col = schema.column_or_field
        if AUDIT_TABLE_PATTERN.search(tname):
            has_audit_table = True
            if TARGET_RESOURCE_PATTERN.search(col):
                audit_has_target_resource = True
                if schema.is_nullable or "null" in " ".join(schema.constraints).lower():
                    target_resource_is_nullable = True

    null_target_found = False
    null_target_file = None

    for ast_file in model.ast_index:
        for call in ast_file.calls:
            csnip = call.get("snippet", "")
            if "AuditLog(" in csnip or "log_audit(" in csnip or "create_audit" in csnip:
                if re.search(r"target_resource_id\s*=\s*(None|null|\"\")", csnip, re.I):
                    null_target_found = True
                    null_target_file = ast_file.path
                    break

    if (has_audit_table and (not audit_has_target_resource or target_resource_is_nullable)) or null_target_found:
        _create_assertion_finding(
            rule_id="ARCH-DPDP-005",
            snippet=f"Audit telemetry in {null_target_file or 'audit schema'} omits non-null target_resource_id, preventing breach blast-radius notification",
            matched_entity="audit_telemetry:target_resource_id",
            file=null_target_file,
        )

    # -------------------------------------------------------------------------
    # Rule ARCH-DPDP-008 (Rule 12): Child Tracking & Behavioral Monitoring
    # -------------------------------------------------------------------------
    if inventory.has_children_dob_data and inventory.has_child_tracking:
        _create_assertion_finding(
            rule_id="ARCH-DPDP-008",
            snippet="Children date-of-birth stored alongside active third-party tracking / analytics telemetry SDK calls.",
            matched_entity="child_tracking_sdk",
        )

    # -------------------------------------------------------------------------
    # Rule ARCH-DPDP-009 (Rule 13): Significant Data Fiduciary (SDF) Obligations
    # -------------------------------------------------------------------------
    if cfg.is_sdf:
        has_dpia_file = any("dpia" in f.path.lower() for f in model.ast_index)
        if not has_dpia_file:
            _create_assertion_finding(
                rule_id="ARCH-DPDP-009",
                snippet="Organization profile is Significant Data Fiduciary (SDF), but zero DPIA or periodic audit metadata was detected.",
                matched_entity="sdf_governance:dpia",
            )

    # -------------------------------------------------------------------------
    # Rule ARCH-DPDP-010 (Rule 15): Cross-Border Data Transfer
    # -------------------------------------------------------------------------
    if cfg.allowed_cross_border_regions:
        for iac in model.iac_trees:
            reg = getattr(iac, "region", None) or ""
            if reg and reg not in cfg.allowed_cross_border_regions and reg not in ("ap-south-1", "asia-south1"):
                _create_assertion_finding(
                    rule_id="ARCH-DPDP-010",
                    snippet=f"Infrastructure resource '{iac.resource_type}' deployed to unapproved cross-border region '{reg}'.",
                    matched_entity=f"iac_region:{reg}",
                    file=iac.file,
                    line=iac.line,
                )

    return findings
