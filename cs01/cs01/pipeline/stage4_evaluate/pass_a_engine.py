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

    return findings
