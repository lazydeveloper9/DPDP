import pytest
from cs01.models import (
    RepoModel, SchemaRecord, AstFileRecord, ScanConfig,
)
from cs01.pipeline.stage4_evaluate.pass_b_engine import evaluate_pass_b


def test_pass_b_missing_consent_withdrawal_route():
    # Schema has personal data, but no routes exist
    model = RepoModel(
        schema_records=[
            SchemaRecord(
                source_orm="sql_ddl",
                source_file="schema.sql",
                table_or_model="users",
                column_or_field="email_address",
                data_type="VARCHAR(255)",
            )
        ],
        ast_index=[
            AstFileRecord(
                path="routes.py",
                language="python",
                decorators=[{"name": '@app.get("/login")', "line": 5}],
            )
        ],
    )
    findings = evaluate_pass_b(model, ScanConfig())
    assert any(f.rule_id == "ARCH-DPDP-001" for f in findings)


def test_pass_b_suppressed_when_consent_route_exists():
    # Schema has personal data, AND consent withdrawal route exists
    model = RepoModel(
        schema_records=[
            SchemaRecord(
                source_orm="sql_ddl",
                source_file="schema.sql",
                table_or_model="users",
                column_or_field="email_address",
                data_type="VARCHAR(255)",
            )
        ],
        ast_index=[
            AstFileRecord(
                path="routes.py",
                language="python",
                decorators=[
                    {"name": '@app.get("/login")', "line": 5},
                    {"name": '@app.post("/consent/withdraw")', "line": 15},
                ],
                functions=[{"name": "cleanup_pii", "calls": []}],
            )
        ],
    )
    findings = evaluate_pass_b(model, ScanConfig())
    assert not any(f.rule_id == "ARCH-DPDP-001" for f in findings)


def test_pass_b_children_age_gate_missing():
    # Schema has date_of_birth, but no age-gate in code
    model = RepoModel(
        schema_records=[
            SchemaRecord(
                source_orm="sql_ddl",
                source_file="schema.sql",
                table_or_model="users",
                column_or_field="date_of_birth",
                data_type="DATE",
            )
        ],
        ast_index=[
            AstFileRecord(
                path="routes.py",
                language="python",
                functions=[{"name": "get_user", "calls": []}],
            )
        ],
    )
    findings = evaluate_pass_b(model, ScanConfig())
    assert any(f.rule_id == "ARCH-DPDP-003" for f in findings)
    f = next(f for f in findings if f.rule_id == "ARCH-DPDP-003")
    assert f.severity.value == "CRITICAL"
    assert f.penalty_band == "200_crore_children"
