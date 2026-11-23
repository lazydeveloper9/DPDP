"""
Stage 4 Pass A Engine — Local Rule Evaluation
==============================================
Evaluates AST taint flows, concrete PII hits, DB schema records, IaC trees, and env vars
against local DPDP statutory rules.
"""

from __future__ import annotations
import re
from typing import Any

from cs01.models import (
    FlowGraph, PiiHitList, RepoModel, RawFinding, PassType, Severity,
    SinkType, FileRole, ScanConfig, PiiType,
)
from .rule_loader import get_rule_by_id

def evaluate_pass_a(
    flow_graph: FlowGraph,
    pii_hits: PiiHitList,
    model: RepoModel,
    cfg: ScanConfig,
) -> list[RawFinding]:
    """Evaluate all Pass A rules and return raw findings."""
    findings: list[RawFinding] = []

    def _create_finding(
        rule_id: str,
        file: str | None,
        line: int | None,
        snippet: str,
        matched_entity: str | None = None,
        line_end: int | None = None,
    ) -> None:
        rule_def = get_rule_by_id(rule_id)
        if not rule_def:
            return

        fid = f"{rule_id}:{file or 'global'}:{line or 1}"
        findings.append(
            RawFinding(
                id=fid,
                rule_id=rule_id,
                pass_type=PassType.A,
                file=file,
                line_start=line,
                line_end=line_end or line,
                snippet=snippet,
                matched_entity=matched_entity,
                dpdp_section=rule_def["dpdp_section"],
                dpdp_rule=rule_def["dpdp_rule"],
                penalty_band=rule_def["penalty_band"],
                severity=Severity(rule_def["severity"]),
                message=rule_def["description"],
                remediation=rule_def["remediation"],
            )
        )

    for edge in flow_graph.edges:
        if edge.is_unguarded:
            sink = next((s for s in flow_graph.sinks if s.id == edge.sink_id), None)
            if not sink:
                continue

            if sink.sink_type == SinkType.LOGGER:
                _create_finding(
                    rule_id="CODE-DPDP-001",
                    file=edge.file,
                    line=sink.line,
                    snippet=sink.call_expression,
                    matched_entity=f"function:{edge.function_name}",
                )
            elif sink.sink_type == SinkType.THIRD_PARTY_SDK:
                _create_finding(
                    rule_id="CODE-DPDP-002",
                    file=edge.file,
                    line=sink.line,
                    snippet=sink.call_expression,
                    matched_entity=f"outbound_call:{sink.call_expression[:40]}",
                )

    INDIAN_IDENTITY_TYPES = {
        PiiType.AADHAAR,
        PiiType.PAN,
        PiiType.GSTIN,
        PiiType.PASSPORT,
        PiiType.VOTER_ID,
        PiiType.DRIVING_LICENCE,
        PiiType.ABHA_HEALTH_ID,
        PiiType.PAYMENT_CARD,
        PiiType.UPI_HANDLE,
    }

    for hit in pii_hits.hits:
        if hit.pii_type not in INDIAN_IDENTITY_TYPES:
            continue
        val_res = hit.validator_result.lower()
        is_valid_res = (
            val_res.startswith("valid")
            or val_res.endswith("_pass")
            or "pan" in val_res
        )
        if hit.file_role == FileRole.PRODUCTION and hit.confidence >= 0.80 and is_valid_res:
            snip = hit.line_snippet
            if not snip:
                fpath = Path(cfg.scan_root) / hit.file
                if fpath.exists() and fpath.is_file():
                    try:
                        flines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
                        if 1 <= hit.line <= len(flines):
                            snip = flines[hit.line - 1].strip()[:160]
                    except Exception:
                        pass
            if not snip:
                snip = f"Hardcoded {hit.pii_type.value} literal at line {hit.line}"

            _create_finding(
                rule_id="CODE-DPDP-003",
                file=hit.file,
                line=hit.line,
                snippet=snip,
                matched_entity=hit.pii_type.value,
            )

    from cs01.pipeline.stage3_detect.pii_detector import PII_FIELD_NAME_PATTERNS

    schemas_by_table: dict[str, list] = {}
    for s in model.schema_records:
        schemas_by_table.setdefault(s.table_or_model, []).append(s)

    for tname, cols in schemas_by_table.items():
        has_soft_del = any(c.is_soft_delete_column for c in cols)
        has_hard_purge = any(c.has_hard_purge_reference for c in cols)
        if has_soft_del and not has_hard_purge:
            sc = next(c for c in cols if c.is_soft_delete_column)
            _create_finding(
                rule_id="SQL-DPDP-003",
                file=sc.source_file,
                line=sc.line or 1,
                snippet=f"Table '{tname}' defines soft-delete column '{sc.column_or_field}' without hard purge policy",
                matched_entity=f"{tname}.{sc.column_or_field}",
            )

        if any(w in tname.lower() for w in ("audit", "log", "telemetry")):
            for c in cols:
                for comment in [c.data_type] + c.constraints:
                    m = re.search(r"retention\s*:?\s*(\d+)", comment, re.I)
                    if m and int(m.group(1)) < 365:
                        _create_finding(
                            rule_id="SQL-DPDP-004",
                            file=c.source_file,
                            line=c.line or 1,
                            snippet=f"Table '{tname}' retention configured as {m.group(1)} days (minimum required: 365)",
                            matched_entity=tname,
                        )
                        break

        is_pii_table = any(any(pat.search(c.column_or_field) for pat, _ in PII_FIELD_NAME_PATTERNS) for c in cols)
        has_consent_link = any(c.has_consent_linkage for c in cols)
        if is_pii_table and not has_consent_link:
            first_c = cols[0]
            _create_finding(
                rule_id="SQL-DPDP-005",
                file=first_c.source_file,
                line=first_c.line or 1,
                snippet=f"Table '{tname}' stores personal data but lacks verifiable consent ledger linkage reference",
                matched_entity=f"{tname}.consent_linkage",
            )

    for schema in model.schema_records:
        is_pii_col = any(pat.search(schema.column_or_field) for pat, _ in PII_FIELD_NAME_PATTERNS)
        if not is_pii_col:
            continue

        if not schema.has_encryption_marker:
            _create_finding(
                rule_id="SQL-DPDP-001",
                file=schema.source_file,
                line=schema.line or 1,
                snippet=f"Column: {schema.column_or_field} ({schema.data_type})",
                matched_entity=f"{schema.table_or_model}.{schema.column_or_field}",
            )

        if not schema.has_retention_comment:
            _create_finding(
                rule_id="SQL-DPDP-002",
                file=schema.source_file,
                line=schema.line or 1,
                snippet=f"Table: {schema.table_or_model}, Column: {schema.column_or_field}",
                matched_entity=f"{schema.table_or_model}.{schema.column_or_field}",
            )

    for iac in model.iac_trees:
        attrs = iac.attributes
        if iac.resource_type == "aws_db_instance":
            if attrs.get("storage_encrypted") is False:
                line = iac.line_map.get("storage_encrypted", iac.line_map.get("__self__", 1))
                _create_finding(
                    rule_id="IAC-DPDP-001",
                    file=iac.source_file,
                    line=line,
                    snippet=f'resource "aws_db_instance" "{iac.resource_name}" {{ storage_encrypted = false }}',
                    matched_entity=iac.resource_name,
                )

            backup_retention = attrs.get("backup_retention_period")
            if backup_retention is not None and int(backup_retention) == 0:
                line = iac.line_map.get("backup_retention_period", iac.line_map.get("__self__", 1))
                _create_finding(
                    rule_id="IAC-DPDP-006",
                    file=iac.source_file,
                    line=line,
                    snippet=f"Database '{iac.resource_name}' backup_retention_period is 0 (backups disabled)",
                    matched_entity=iac.resource_name,
                )

        if iac.resource_type in ("aws_s3_bucket", "aws_s3_bucket_public_access_block"):
            is_public = False
            if iac.resource_type == "aws_s3_bucket" and attrs.get("acl") in ("public-read", "public-read-write"):
                is_public = True
            elif iac.resource_type == "aws_s3_bucket_public_access_block":
                if attrs.get("block_public_acls") is False or attrs.get("block_public_policy") is False:
                    is_public = True
            if is_public:
                line = iac.line_map.get("acl", iac.line_map.get("__self__", 1))
                _create_finding(
                    rule_id="IAC-DPDP-003",
                    file=iac.source_file,
                    line=line,
                    snippet=f'resource "{iac.resource_type}" "{iac.resource_name}" has public access enabled',
                    matched_entity=iac.resource_name,
                )

        if iac.file_type == "dockerfile":
            instructions = attrs.get("instructions", [])
            has_user = any(ins.get("instruction") == "USER" and ins.get("value") not in ("root", "0") for ins in instructions)
            if not has_user and instructions:
                _create_finding(
                    rule_id="IAC-DPDP-004",
                    file=iac.source_file,
                    line=1,
                    snippet="Dockerfile runs as root user by default (missing non-root USER instruction)",
                    matched_entity=iac.resource_name,
                )

        if iac.resource_type in ("aws_db_instance", "aws_instance"):
            region = str(attrs.get("region") or attrs.get("availability_zone") or "")
            if region:
                is_india = any(r in region for r in ("ap-south-1", "ap-south-2", "in-central"))
                if not is_india and not any(r in region for r in cfg.allowed_cross_border_regions):
                    line = iac.line_map.get("region", iac.line_map.get("__self__", 1))
                    _create_finding(
                        rule_id="IAC-DPDP-005",
                        file=iac.source_file,
                        line=line,
                        snippet=f"Cloud resource '{iac.resource_name}' located in unauthorized region '{region}'",
                        matched_entity=region,
                    )

        if iac.resource_type == "aws_cloudwatch_log_group":
            retention = attrs.get("retention_in_days")
            if retention is not None and int(retention) < 365:
                line = iac.line_map.get("retention_in_days", iac.line_map.get("__self__", 1))
                _create_finding(
                    rule_id="IAC-DPDP-002",
                    file=iac.source_file,
                    line=line,
                    snippet=f'retention_in_days = {retention} (minimum required: 365)',
                    matched_entity=iac.resource_name,
                )

    for ev in model.env_vars:
        key_lower = ev.key.lower()
        val_lower = (ev.non_secret_value or "").lower()
        full_text = f"{key_lower}={val_lower}"
        if ("ssl" in full_text or "tls" in full_text) and any(sub in full_text for sub in ("disable", "false", "none", "no", "0")):
            _create_finding(
                rule_id="ENV-DPDP-001",
                file=ev.source_file,
                line=ev.line,
                snippet=f"{ev.key}={ev.non_secret_value or '...'}",
                matched_entity=ev.key,
            )

    SECRET_KEY_PATTERN = re.compile(
        r"(api_secret|demo_secret|api_key|auth_token|secret_key|jwt_secret|private_key|client_secret)",
        re.I,
    )
    for ast_file in model.ast_index:
        for assign in ast_file.assignments:
            aname = assign.get("name", "")
            asnippet = assign.get("value_snippet", "")
            if SECRET_KEY_PATTERN.search(aname):
                m = re.search(r"['\"]([^'\"]{8,})['\"]", asnippet)
                if m:
                    secret_val = m.group(1)
                    if not any(dummy in secret_val.lower() for dummy in ("your-key", "change_me", "placeholder")):
                        masked_snippet = asnippet.replace(secret_val, "[REDACTED_SECRET]")
                        _create_finding(
                            rule_id="CODE-DPDP-003",
                            file=ast_file.path,
                            line=assign.get("line", 1),
                            snippet=masked_snippet,
                            matched_entity=aname,
                        )

    # -------------------------------------------------------------------------
    # Rule CODE-DPDP-004: Excessive Personal Data or Credentials in Response DTOs
    # -------------------------------------------------------------------------
    CREDENTIAL_FIELD_PATTERNS = re.compile(
        r"(password.*|.*_hash|hashed_password|salt|secret.*|api_key|token|private_key|jwt_secret|otp)",
        re.I,
    )
    SENSITIVE_ID_FIELD_PATTERNS = re.compile(
        r"(aadhaar.*|uidai.*|pan_.*|ayushman.*|abha.*|passport.*|driving_lic.*|ssn|social_security|bank_account)",
        re.I,
    )

    for ast_file in model.ast_index:
        for cls_dict in ast_file.classes:
            cname = cls_dict.get("name", "")
            bases = cls_dict.get("bases", [])
            fields = cls_dict.get("fields", [])
            bsnip = cls_dict.get("body_snippet", "")

            is_response_schema = (
                any("base" in b.lower() or "schema" in b.lower() or "dto" in b.lower() or "model" in b.lower() for b in bases)
                or any(cname.lower().endswith(sfx) for sfx in ("response", "out", "dto", "public", "profile", "summary", "view"))
            )
            is_request_only = any(cname.lower().endswith(sfx) for sfx in ("create", "request", "input", "in", "login", "update", "filter"))

            if is_response_schema and not is_request_only:
                for fld in fields:
                    fname = fld.get("name", "")
                    fsnip = fld.get("snippet", "")
                    fline = fld.get("line", cls_dict.get("start_line", 1))

                    if "exclude=true" in fsnip.lower() or f"mask_{fname.lower()}" in bsnip.lower() or f"@field_serializer('{fname}')" in bsnip:
                        continue

                    if CREDENTIAL_FIELD_PATTERNS.fullmatch(fname) or CREDENTIAL_FIELD_PATTERNS.search(fname):
                        _create_finding(
                            rule_id="CODE-DPDP-004",
                            file=ast_file.path,
                            line=fline,
                            snippet=fsnip or f"{fname}: {fld.get('type', '')}",
                            matched_entity=f"{cname}.{fname}",
                        )
                    elif SENSITIVE_ID_FIELD_PATTERNS.fullmatch(fname) or SENSITIVE_ID_FIELD_PATTERNS.search(fname):
                        _create_finding(
                            rule_id="CODE-DPDP-004",
                            file=ast_file.path,
                            line=fline,
                            snippet=fsnip or f"{fname}: {fld.get('type', '')}",
                            matched_entity=f"{cname}.{fname}",
                        )

    # -------------------------------------------------------------------------
    # Rule CODE-DPDP-005: Publicly Mounted Sensitive Static Directories & Backups
    # -------------------------------------------------------------------------
    SENSITIVE_STORAGE_TOKENS = (
        "upload", "uploads", "backup", "backups", "dump", "dumps",
        "export", "exports", "document", "documents", "record", "records",
        "private", "db", "sqlite", "kyc", "patient", "patients"
    )

    for ast_file in model.ast_index:
        for call in ast_file.calls:
            callee = call.get("callee", "")
            csnip = call.get("snippet", "")
            cline = call.get("line", 1)

            is_mount = (
                ("mount" in callee or "use" in callee)
                and any(kw in csnip for kw in ("StaticFiles", "static", "directory"))
            ) or ("send_from_directory" in callee)

            if is_mount:
                csnip_lower = csnip.lower()
                has_sensitive_dir = any(tok in csnip_lower for tok in SENSITIVE_STORAGE_TOKENS)

                if has_sensitive_dir:
                    _create_finding(
                        rule_id="CODE-DPDP-005",
                        file=ast_file.path,
                        line=cline,
                        snippet=csnip,
                        matched_entity=f"static_mount:{callee}",
                    )

    # -------------------------------------------------------------------------
    # Rule CODE-DPDP-006: Unvalidated File Upload Written to Storage
    # -------------------------------------------------------------------------
    FILE_PERSIST_PATTERNS = re.compile(
        r"(open\s*\([^)]*['\"]wb['\"]\)|write_bytes|\.write\s*\(|copyfileobj|\.save\s*\()",
        re.I,
    )
    FILE_DEFENSE_PATTERNS = re.compile(
        r"(allowed_extensions|allowed_mimes|\.endswith|splitext|\.suffix|magic\.|filetype\.|content_type\s*in)",
        re.I,
    )

    for ast_file in model.ast_index:
        for func in ast_file.functions:
            params = func.get("params", [])
            bsnip = func.get("body_snippet", "")
            fline = func.get("start_line", 1)

            is_upload_handler = any(
                any(kw in p for kw in ("UploadFile", "File(", "request.files", "multer", "File["))
                for p in params
            ) or "file: uploadfile" in bsnip.lower() or "uploadfile" in " ".join(params).lower()

            if is_upload_handler:
                persists_file = bool(FILE_PERSIST_PATTERNS.search(bsnip))
                has_defense = bool(FILE_DEFENSE_PATTERNS.search(bsnip))

                if persists_file and not has_defense:
                    _create_finding(
                        rule_id="CODE-DPDP-006",
                        file=ast_file.path,
                        line=fline,
                        snippet=f"def {func.get('name', 'upload')}(...): file persisted without extension allowlist verification",
                        matched_entity=f"upload_endpoint:{func.get('name')}",
                    )

    # -------------------------------------------------------------------------
    # Rule CODE-DPDP-007: Missing Object-Level Authorization Boundary (IDOR / BOLA)
    # -------------------------------------------------------------------------
    PATH_PARAM_PATTERN = re.compile(r"\{([a-zA-Z0-9_]*id[a-zA-Z0-9_]*)\}", re.I)
    DB_QUERY_PATTERN = re.compile(r"(\.filter\(|\.where\(|\.get\(|findbyid\(|query\()", re.I)
    OWNERSHIP_GUARD_PATTERN = re.compile(
        r"(current_user\.[a-zA-Z0-9_]*\s*(==|!=)|(==|!=)\s*current_user|current_user\s*==|current_user\s*!=|user\.id\s*==|user\.id\s*!=|role\s*==\s*['\"]admin|role\s*in\s*\[|staff_clinical)",
        re.I,
    )

    for ast_file in model.ast_index:
        for func in ast_file.functions:
            decs = func.get("decorators", [])
            bsnip = func.get("body_snippet", "")
            fline = func.get("start_line", 1)

            route_param = ""
            for d in decs:
                m_path = PATH_PARAM_PATTERN.search(d)
                if m_path:
                    route_param = m_path.group(1)
                    break

            if route_param:
                params_str = " ".join(func.get("params", [])) + " " + bsnip[:200]
                is_authenticated = (
                    "Depends" in params_str
                    or "current_user" in params_str
                    or any("login_required" in d or "auth" in d.lower() for d in decs)
                )
                queries_db = bool(DB_QUERY_PATTERN.search(bsnip)) and route_param in bsnip
                has_ownership_or_role_guard = bool(OWNERSHIP_GUARD_PATTERN.search(bsnip))

                if is_authenticated and queries_db and not has_ownership_or_role_guard:
                    _create_finding(
                        rule_id="CODE-DPDP-007",
                        file=ast_file.path,
                        line=fline,
                        snippet=f"def {func.get('name')}(...): queries database by {route_param} without principal ownership verification",
                        matched_entity=f"route:{func.get('name')}:{route_param}",
                    )

    # -------------------------------------------------------------------------
    # Rule CODE-DPDP-008: Broken Function-Level Authorization / Excessive Role Privileges
    # -------------------------------------------------------------------------
    SENSITIVE_ENDPOINT_TOKENS = (
        "clinical", "medical", "psychiatric", "consultation", "prescription",
        "diagnosis", "health_record", "kyc", "salary", "payroll"
    )

    for ast_file in model.ast_index:
        for func in ast_file.functions:
            decs = func.get("decorators", [])
            bsnip = func.get("body_snippet", "")
            fline = func.get("start_line", 1)

            is_sensitive_route = False
            for d in decs:
                if any(tok in d.lower() for tok in SENSITIVE_ENDPOINT_TOKENS):
                    is_sensitive_route = True
                    break
            if any(tok in func.get("name", "").lower() for tok in SENSITIVE_ENDPOINT_TOKENS):
                is_sensitive_route = True

            if is_sensitive_route:
                params_str = " ".join(func.get("params", [])) + " " + bsnip[:200]
                uses_generic_staff = "require_staff_user" in params_str or ("staff" in params_str.lower() and "clinical" not in params_str.lower())
                has_strict_check = "require_clinical" in params_str or "staff_clinical" in bsnip or "admin_dpo" in bsnip

                if uses_generic_staff and not has_strict_check:
                    _create_finding(
                        rule_id="CODE-DPDP-008",
                        file=ast_file.path,
                        line=fline,
                        snippet=f"def {func.get('name')}(...): permits operational staff access to confidential clinical record",
                        matched_entity=f"route:{func.get('name')}",
                    )

    return findings
