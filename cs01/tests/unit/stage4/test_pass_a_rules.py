import pytest
from cs01.models import (
    FlowGraph, PiiHitList, RepoModel, ScanConfig,
    DataSource, DataSink, FlowEdge, SourceType, SinkType,
    SchemaRecord, IacTree,
)
from cs01.pipeline.stage4_evaluate.pass_a_engine import evaluate_pass_a


def test_pass_a_logger_flow():
    flow = FlowGraph(
        sources=[DataSource(id="src1", source_type=SourceType.REQUEST_BODY, file="app.py", line=5)],
        sinks=[DataSink(id="snk1", sink_type=SinkType.LOGGER, file="app.py", line=10, call_expression="logger.info(data)")],
        edges=[FlowEdge(id="e1", source_id="src1", sink_id="snk1", file="app.py", is_unguarded=True)],
    )
    model = RepoModel()
    cfg = ScanConfig()
    findings = evaluate_pass_a(flow, PiiHitList(), model, cfg)

    assert len(findings) == 1
    assert findings[0].rule_id == "CODE-DPDP-001"
    assert findings[0].severity.value == "CRITICAL"
    assert findings[0].dpdp_section == "§8(5)"


def test_pass_a_unencrypted_sql_schema():
    model = RepoModel(
        schema_records=[
            SchemaRecord(
                source_orm="sql_ddl",
                source_file="schema.sql",
                table_or_model="users",
                column_or_field="aadhaar_number",
                data_type="VARCHAR(12)",
                has_encryption_marker=False,
            )
        ]
    )
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    
    assert any(f.rule_id == "SQL-DPDP-001" for f in findings)
    sql_finding = next(f for f in findings if f.rule_id == "SQL-DPDP-001")
    assert sql_finding.severity.value == "CRITICAL"


def test_pass_a_unencrypted_terraform_rds():
    model = RepoModel(
        iac_trees=[
            IacTree(
                source_file="main.tf",
                file_type="terraform",
                resource_type="aws_db_instance",
                resource_name="db",
                attributes={"storage_encrypted": False},
                line_map={"storage_encrypted": 5},
            )
        ]
    )
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    assert any(f.rule_id == "IAC-DPDP-001" for f in findings)
