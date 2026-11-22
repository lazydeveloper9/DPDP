"""
Stage 4 Pass B Engine — Cross-File Architectural Assertions
===========================================================
Queries the whole-repo inventory to surface systemic compliance gaps
that cannot be detected on a single-file basis (e.g. missing consent withdrawal,
erasure routes, age-gate checks, or uncontracted processors).
"""

from __future__ import annotations
import re
from typing import Any

from cs01.models import (
    RepoModel, RawFinding, PassType, Severity, ScanConfig,
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


class RepoInventory:
    """Aggregated whole-repo architectural facts extracted from RepoModel."""
    def __init__(self, model: RepoModel):
        self.api_routes: list[dict[str, str]] = []  # {path, method, file, line}
        self.schema_pii_tables: set[str] = set()
        self.has_children_dob_data: bool = False
        self.has_age_gate: bool = False
        self.has_retention_routine: bool = False

        self._build_inventory(model)

    def _build_inventory(self, model: RepoModel) -> None:
        from cs01.pipeline.stage3_detect.pii_detector import PII_FIELD_NAME_PATTERNS

        # 1. Inspect DB schemas
        for schema in model.schema_records:
            col = schema.column_or_field.lower()
            if any(pat.search(col) for pat, _ in PII_FIELD_NAME_PATTERNS):
                self.schema_pii_tables.add(schema.table_or_model)
            if any(k in col for k in ("dob", "date_of_birth", "birth_date", "child_age", "minor")):
                self.has_children_dob_data = True

        # 2. Inspect AST for routes, age-gates, and scheduled routines
        for ast_file in model.ast_index:
            for dec in ast_file.decorators:
                d_name = dec.get("name", "")
                m = ROUTE_DECORATOR_PATTERN.search(d_name)
                if m:
                    self.api_routes.append({
                        "method": m.group(1).upper(),
                        "path": m.group(2),
                        "file": ast_file.path,
                        "line": dec.get("line", 1),
                    })

            for func in ast_file.functions:
                fname = func.get("name", "")
                calls_str = " ".join(c.get("snippet", "") for c in func.get("calls", []))
                combined_func_text = f"{fname} {calls_str}"

                if AGE_GATE_PATTERN.search(combined_func_text):
                    self.has_age_gate = True
                if RETENTION_JOB_PATTERN.search(combined_func_text):
                    self.has_retention_routine = True


def evaluate_pass_b(
    model: RepoModel,
    cfg: ScanConfig,
) -> list[RawFinding]:
    """Evaluate whole-repo Pass B assertions against the constructed inventory."""
    findings: list[RawFinding] = []
    inventory = RepoInventory(model)

    def _create_assertion_finding(rule_id: str, snippet: str, matched_entity: str) -> None:
        rule_def = get_rule_by_id(rule_id)
        if not rule_def:
            return

        findings.append(
            RawFinding(
                id=f"{rule_id}:repo_architecture",
                rule_id=rule_id,
                pass_type=PassType.B,
                file=None,
                line_start=None,
                line_end=None,
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

    # ── Assertion ARCH-DPDP-001: PII in DB but no consent withdrawal / erasure route ──
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

    # ── Assertion ARCH-DPDP-002: PII in DB but no scheduled retention purge routine ──
    if inventory.schema_pii_tables and not inventory.has_retention_routine:
        _create_assertion_finding(
            rule_id="ARCH-DPDP-002",
            snippet="PII tables persist data, but no automated retention cleanup routine detected across repository.",
            matched_entity="background_jobs",
        )

    # ── Assertion ARCH-DPDP-003: Children data in DB but no age-gate in code ──
    if inventory.has_children_dob_data and not inventory.has_age_gate:
        _create_assertion_finding(
            rule_id="ARCH-DPDP-003",
            snippet="Schema captures date_of_birth/age fields, but no verifiable minor age-gate routine found in backend logic.",
            matched_entity="age_verification",
        )

    return findings
