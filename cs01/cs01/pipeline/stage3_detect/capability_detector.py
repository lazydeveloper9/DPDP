"""
Pipeline Stage 3 — Base Product Capability & Data-Flow Inventory Detector
========================================================================
Analyzes the codebase to build an authoritative inventory of:
1. Application stack, frameworks, entrypoints, workers, and databases.
2. Collected, stored, and transmitted personal data elements (PII catalog).
3. Implemented technical and organizational security/privacy controls.
4. Missing required controls dynamically computed from the processed data.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Any, Optional

from cs01.models import (
    RepoModel, FlowGraph, PiiHitList, ScanConfig,
    PiiType, FileRole, SinkType,
    StackCapabilities, PersonalDataInventoryItem,
    ImplementedControl, MissingControl, ProductCapabilityReport,
)

ROUTE_PATTERN = re.compile(
    r"@(?:app|router|blueprint|api)\.(get|post|put|delete|patch|route)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.I,
)
JS_ROUTE_PATTERN = re.compile(
    r"(?:app|router)\.(get|post|put|delete|patch|use)\s*\(\s*['\"]([^'\"]+)['\"]",
    re.I,
)
AGE_GATE_PATTERN = re.compile(
    r"(is_minor|check_age|parental_consent|guardian_consent|age\s*<\s*18|min_age|verify_age)",
    re.I,
)
RETENTION_PATTERN = re.compile(
    r"(purge_expired|cleanup_pii|delete_old_users|retention_job|scheduled_purge|data_retention|clean_expired)",
    re.I,
)
ERASURE_ROUTE_PATTERN = re.compile(
    r"(consent/withdraw|withdraw-consent|consent/revoke|opt-out|user/delete|account/delete|erasure|forget-me|delete_account)",
    re.I,
)
AUTH_MIDDLEWARE_PATTERN = re.compile(
    r"(verify_token|get_current_user|auth_required|authenticate|jwt\.verify|passport\.authenticate|check_auth)",
    re.I,
)
RBAC_PATTERN = re.compile(
    r"(require_role|has_role|RoleChecker|is_admin|check_permission|role_required|clinical_staff|staff_basic)",
    re.I,
)
DPO_CONTACT_PATTERN = re.compile(
    r"(dpo@|privacy@|grievance@|data_protection_officer|grievance_officer)",
    re.I,
)
GRIEVANCE_ROUTE_PATTERN = re.compile(
    r"(grievance|dispute|complaint|redressal)",
    re.I,
)


def _classify_pii_category(field_name: str, pii_type: Optional[PiiType] = None) -> str:
    """Classify a field or PII type into a high-level privacy category."""
    fn = field_name.lower()
    if pii_type in (PiiType.AADHAAR, PiiType.PAN, PiiType.PASSPORT, PiiType.VOTER_ID, PiiType.DRIVING_LICENCE, PiiType.GSTIN):
        return "National Identity"
    if pii_type in (PiiType.ABHA_HEALTH_ID,) or any(k in fn for k in ("health", "medical", "diagnosis", "prescription", "patient", "blood", "doctor", "clinical")):
        return "Health"
    if pii_type in (PiiType.PAYMENT_CARD, PiiType.UPI_HANDLE) or any(k in fn for k in ("salary", "account_number", "ifsc", "pan", "bank", "credit", "debit", "card")):
        return "Financial"
    if pii_type in (PiiType.MOBILE, PiiType.EMAIL) or any(k in fn for k in ("phone", "mobile", "email", "address", "postal", "pincode", "city", "state")):
        return "Contact"
    if any(k in fn for k in ("dob", "date_of_birth", "birth_date", "child", "minor", "guardian", "parent", "age")):
        return "Children"
    if any(k in fn for k in ("password", "hash", "secret", "salt", "token", "auth")):
        return "Credentials"
    return "Demographic"


def detect_product_capabilities(
    model: RepoModel,
    flow_graph: FlowGraph,
    pii_hits: PiiHitList,
    cfg: ScanConfig,
) -> ProductCapabilityReport:
    """Analyze the parsed repository model and flow graph to extract product capabilities."""
    report = ProductCapabilityReport(target_path=cfg.scan_root)
    stack = report.stack

    # 1. Discover Languages & Frameworks from AST and file paths
    languages: set[str] = set()
    frameworks: set[str] = set()
    database_engines: set[str] = set()
    workers: set[str] = set()
    entrypoints: list[str] = []

    for ast_file in model.ast_index:
        languages.add(ast_file.language.lower())
        file_path_str = ast_file.path.lower()

        # Route extraction (Python)
        for dec in ast_file.decorators:
            d_name = dec.get("name", "")
            m = ROUTE_PATTERN.search(d_name)
            if m:
                frameworks.add("FastAPI/Flask" if "fastapi" in file_path_str or "app." in d_name else "Python-Web")
                entrypoints.append(f"{m.group(1).upper()} {m.group(2)} ({ast_file.path}:{dec.get('line', 1)})")

        # Route extraction (JS/TS)
        for call in getattr(ast_file, "calls", []):
            callee = call.get("callee", "")
            snip = call.get("snippet", "")
            m = JS_ROUTE_PATTERN.search(snip)
            if m:
                frameworks.add("Express/Node")
                entrypoints.append(f"{m.group(1).upper()} {m.group(2)} ({ast_file.path}:{call.get('line', 1)})")

        # Background workers
        for func in ast_file.functions:
            fname = func.get("name", "")
            fcalls = " ".join(c.get("snippet", "") for c in func.get("calls", []))
            body_text = f"{fname} {fcalls}".lower()
            if "celery" in body_text or "@celery" in body_text:
                workers.add("Celery")
            if "scheduler" in body_text or "add_job" in body_text:
                workers.add("APScheduler/Cron")

    # Inspect schema ORMs
    for s in model.schema_records:
        if s.source_orm:
            database_engines.add(s.source_orm.capitalize())

    # Inspect IaC trees for Cloud Providers & Databases
    for iac in model.iac_trees:
        if not iac.resource_type:
            continue
        if iac.resource_type.startswith("aws_"):
            stack.cloud_providers.append("AWS")
        elif iac.resource_type.startswith("google_"):
            stack.cloud_providers.append("GCP")
        elif iac.resource_type.startswith("azurerm_"):
            stack.cloud_providers.append("Azure")

    stack.languages = sorted(list(languages))
    stack.frameworks = sorted(list(frameworks))
    stack.database_engines = sorted(list(database_engines))
    stack.background_workers = sorted(list(workers))
    stack.cloud_providers = sorted(list(set(stack.cloud_providers)))
    stack.entrypoints = entrypoints

    # 2. Build Personal Data & PII Inventory
    inventory_items: list[PersonalDataInventoryItem] = []
    seen_keys: set[str] = set()

    # From concrete PII hits (Layer 2)
    for hit in pii_hits.hits:
        if hit.file_role != FileRole.PRODUCTION:
            continue
        key = f"{hit.file}:{hit.line}:{hit.pii_type.value}"
        if key in seen_keys:
            continue
        seen_keys.add(key)

        val_name = getattr(hit, "matched_text", None) or (hit.line_snippet.strip()[:40] if hit.line_snippet else hit.pii_type.value)
        category = _classify_pii_category(val_name, hit.pii_type)
        inventory_items.append(
            PersonalDataInventoryItem(
                category=category,
                field_or_param=val_name,
                location_file=hit.file,
                location_line=hit.line,
                pii_type=hit.pii_type.value,
                is_stored=False,
                is_transmitted_externally=False,
                is_logged=False,
                is_encrypted=False,
            )
        )

    # From DB Schemas (Layer 3)
    from cs01.pipeline.stage3_detect.pii_detector import PII_FIELD_NAME_PATTERNS
    for schema in model.schema_records:
        col = schema.column_or_field
        col_lower = col.lower()
        matched_pii_type: Optional[PiiType] = None
        for pat, ptype in PII_FIELD_NAME_PATTERNS:
            if pat.search(col_lower):
                matched_pii_type = ptype
                break

        if matched_pii_type or any(k in col_lower for k in ("name", "email", "phone", "address", "dob", "patient", "medical", "diagnosis", "ssn", "aadhaar", "pan")):
            key = f"{schema.source_file}:{schema.line}:{schema.table_or_model}.{col}"
            if key not in seen_keys:
                seen_keys.add(key)
                category = _classify_pii_category(col, matched_pii_type)
                inventory_items.append(
                    PersonalDataInventoryItem(
                        category=category,
                        field_or_param=f"{schema.table_or_model}.{col}",
                        location_file=schema.source_file,
                        location_line=schema.line,
                        pii_type=matched_pii_type.value if matched_pii_type else "USER_PROFILE",
                        is_stored=True,
                        is_transmitted_externally=False,
                        is_logged=False,
                        is_encrypted=schema.has_encryption_marker,
                    )
                )

    report.pii_inventory = inventory_items
    report.has_personal_data = len(inventory_items) > 0
    report.has_children_data = any(item.category == "Children" for item in inventory_items)
    report.has_health_data = any(item.category == "Health" for item in inventory_items)
    report.has_financial_data = any(item.category == "Financial" for item in inventory_items)

    # 3. Detect Implemented Controls
    implemented: list[ImplementedControl] = []

    # Check for Age Gates
    has_age_gate = False
    for ast_file in model.ast_index:
        for func in ast_file.functions:
            fname = func.get("name", "")
            fcalls = " ".join(c.get("snippet", "") for c in func.get("calls", []))
            combined = f"{fname} {fcalls}"
            if AGE_GATE_PATTERN.search(combined):
                has_age_gate = True
                implemented.append(
                    ImplementedControl(
                        control_type="AGE_GATE",
                        file=ast_file.path,
                        line=func.get("start_line", 1),
                        evidence=f"Age verification guard function '{fname}'",
                    )
                )
                break

    # Check for Retention Purge routines
    has_retention_purge = False
    for ast_file in model.ast_index:
        for func in ast_file.functions:
            fname = func.get("name", "")
            fcalls = " ".join(c.get("snippet", "") for c in func.get("calls", []))
            combined = f"{fname} {fcalls}"
            if RETENTION_PATTERN.search(combined):
                has_retention_purge = True
                implemented.append(
                    ImplementedControl(
                        control_type="RETENTION_PURGE",
                        file=ast_file.path,
                        line=func.get("start_line", 1),
                        evidence=f"Scheduled data purging routine '{fname}'",
                    )
                )
                break

    # Check for Erasure / Withdrawal Routes
    has_erasure_route = False
    for route in entrypoints:
        if ERASURE_ROUTE_PATTERN.search(route):
            has_erasure_route = True
            implemented.append(
                ImplementedControl(
                    control_type="ERASURE_ROUTE",
                    file=route.split("(")[-1].rstrip(")").split(":")[0] if "(" in route else "routes",
                    line=1,
                    evidence=f"Consent withdrawal / account erasure route: {route}",
                )
            )
            break

    # Check for Auth Middleware / RBAC
    for ast_file in model.ast_index:
        for dec in ast_file.decorators:
            d_name = dec.get("name", "")
            if AUTH_MIDDLEWARE_PATTERN.search(d_name) or RBAC_PATTERN.search(d_name):
                implemented.append(
                    ImplementedControl(
                        control_type="AUTH_AND_RBAC",
                        file=ast_file.path,
                        line=dec.get("line", 1),
                        evidence=f"Authentication or RBAC guard decorator: {d_name}",
                    )
                )

    # Check for DPO Contact / Grievance Redressal
    has_dpo_contact = False
    for ast_file in model.ast_index:
        for call in ast_file.calls:
            snip = call.get("snippet", "")
            if DPO_CONTACT_PATTERN.search(snip):
                has_dpo_contact = True
                implemented.append(
                    ImplementedControl(
                        control_type="DPO_CONTACT",
                        file=ast_file.path,
                        line=call.get("line", 1),
                        evidence=f"Published DPO / Grievance contact: {snip[:60]}",
                    )
                )
                break
    for route in entrypoints:
        if GRIEVANCE_ROUTE_PATTERN.search(route):
            implemented.append(
                ImplementedControl(
                    control_type="GRIEVANCE_SLA",
                    file=route.split("(")[-1].rstrip(")").split(":")[0] if "(" in route else "routes",
                    line=1,
                    evidence=f"Grievance redressal endpoint: {route}",
                )
            )

    report.implemented_controls = implemented

    # 4. Calculate Missing Required Controls
    missing: list[MissingControl] = []

    if report.has_personal_data:
        # Rule 3(c) & Rule 14(3) / §6(4) & §12(3) — Erasure & Withdrawal Route
        if not has_erasure_route:
            missing.append(
                MissingControl(
                    control_type="ERASURE_ROUTE",
                    required_by_rule="Rule 3(c) & Rule 14(3)",
                    dpdp_section="§6(4) & §12(3)",
                    severity="HIGH",
                    reason="Application stores or processes personal data, but provides no dedicated consent withdrawal or erasure route.",
                )
            )

        # Rule 8(2) / §8(7) — Scheduled Retention Purging Routine
        has_stored_pii = any(item.is_stored for item in report.pii_inventory)
        if has_stored_pii and not has_retention_purge:
            missing.append(
                MissingControl(
                    control_type="RETENTION_PURGE",
                    required_by_rule="Rule 8(2)",
                    dpdp_section="§8(7)",
                    severity="HIGH",
                    reason="Personal data is persisted in database models, but no automated retention purging job was detected.",
                )
            )

        # Rule 10 / §9(1) — Child Age-Gating & Parental Verification
        if report.has_children_data and not has_age_gate:
            missing.append(
                MissingControl(
                    control_type="AGE_GATE",
                    required_by_rule="Rule 10",
                    dpdp_section="§9(1)",
                    severity="CRITICAL",
                    reason="Children's date-of-birth or minor markers collected without a verifiable parental consent age-gate.",
                )
            )

        # Rule 9 / §8(9) — DPO & Privacy Officer Contact
        if not has_dpo_contact:
            missing.append(
                MissingControl(
                    control_type="DPO_CONTACT",
                    required_by_rule="Rule 9",
                    dpdp_section="§8(9)",
                    severity="MEDIUM",
                    reason="No published Data Protection Officer (DPO) or designated grievance officer contact found in application routes or configuration.",
                )
            )

    report.missing_controls = missing
    return report
