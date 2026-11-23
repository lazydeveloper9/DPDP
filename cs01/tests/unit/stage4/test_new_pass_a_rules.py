import pytest
from cs01.models.repo_model import RepoModel, SchemaRecord, IacTree
from cs01.models.flow_graph import FlowGraph, PiiHitList
from cs01.models.scan_config import ScanConfig
from cs01.pipeline.stage4_evaluate.pass_a_engine import evaluate_pass_a

def test_sql_dpdp_003_soft_delete():
    rec = SchemaRecord(
        source_orm="sql_ddl",
        source_file="schema.sql",
        table_or_model="users",
        column_or_field="is_deleted",
        data_type="BOOLEAN",
        is_soft_delete_column=True,
        has_hard_purge_reference=False,
    )
    model = RepoModel(schema_records=[rec])
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    r_ids = [f.rule_id for f in findings]
    assert "SQL-DPDP-003" in r_ids

def test_sql_dpdp_004_log_retention():
    rec = SchemaRecord(
        source_orm="sql_ddl",
        source_file="audit.sql",
        table_or_model="audit_logs",
        column_or_field="logged_at",
        data_type="TIMESTAMP",
        has_retention_comment=True,
        constraints=["retention 90 days"],
    )
    model = RepoModel(schema_records=[rec])
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    r_ids = [f.rule_id for f in findings]
    assert "SQL-DPDP-004" in r_ids

def test_iac_dpdp_003_s3_public_access():
    tree = IacTree(
        source_file="main.tf",
        file_type="terraform",
        resource_type="aws_s3_bucket",
        resource_name="public_assets",
        attributes={"acl": "public-read"},
    )
    model = RepoModel(iac_trees=[tree])
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    r_ids = [f.rule_id for f in findings]
    assert "IAC-DPDP-003" in r_ids

def test_iac_dpdp_004_root_dockerfile():
    tree = IacTree(
        source_file="Dockerfile",
        file_type="dockerfile",
        resource_type="Dockerfile",
        resource_name="Dockerfile",
        attributes={"instructions": [{"instruction": "FROM", "value": "node:18", "line": 1}]},
    )
    model = RepoModel(iac_trees=[tree])
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    r_ids = [f.rule_id for f in findings]
    assert "IAC-DPDP-004" in r_ids

def test_iac_dpdp_005_cross_border_region():
    tree = IacTree(
        source_file="main.tf",
        file_type="terraform",
        resource_type="aws_db_instance",
        resource_name="primary_db",
        attributes={"region": "us-east-1"},
    )
    model = RepoModel(iac_trees=[tree])
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    r_ids = [f.rule_id for f in findings]
    assert "IAC-DPDP-005" in r_ids

def test_iac_dpdp_006_missing_backup():
    tree = IacTree(
        source_file="main.tf",
        file_type="terraform",
        resource_type="aws_db_instance",
        resource_name="primary_db",
        attributes={"backup_retention_period": 0},
    )
    model = RepoModel(iac_trees=[tree])
    findings = evaluate_pass_a(FlowGraph(), PiiHitList(), model, ScanConfig())
    r_ids = [f.rule_id for f in findings]
    assert "IAC-DPDP-006" in r_ids
