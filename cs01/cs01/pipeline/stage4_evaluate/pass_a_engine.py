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
    SinkType, FileRole, ScanConfig,
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

    for hit in pii_hits.hits:
        if hit.file_role == FileRole.PRODUCTION and hit.confidence >= 0.80 and hit.validator_result.startswith("valid"):
            _create_finding(
                rule_id="CODE-DPDP-003",
                file=hit.file,
                line=hit.line,
                snippet=f"[REDACTED_{hit.pii_type.value}] (confidence: {hit.confidence})",
                matched_entity=hit.pii_type.value,
            )

    from cs01.pipeline.stage3_detect.pii_detector import PII_FIELD_NAME_PATTERNS

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
        if "ssl" in key_lower and any(sub in key_lower for sub in ("disable", "false", "none", "no")):
            _create_finding(
                rule_id="ENV-DPDP-001",
                file=ev.source_file,
                line=ev.line,
                snippet=f"{ev.key}=...",
                matched_entity=ev.key,
            )

    return findings
