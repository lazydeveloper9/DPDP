"""
Unit tests for CS-01 Base Product Capability Detector.
======================================================
Verifies:
1. Stack detection (languages, frameworks, entrypoints, database engines).
2. Personal data and PII catalog construction.
3. Implemented control discovery (auth, RBAC, age gate, retention, erasure).
4. Dynamic missing control calculation (Rule 3/14 erasure, Rule 8 retention, Rule 10 age gate).
"""

from __future__ import annotations
from cs01.models import (
    RepoModel, AstFileRecord, SchemaRecord, FlowGraph, PiiHitList, PiiHit,
    PiiType, FileRole, ScanConfig,
)
from cs01.pipeline.stage3_detect.capability_detector import detect_product_capabilities


def test_capability_detector_empty_repo():
    """An empty repo or one without personal data should have 0 missing statutory controls."""
    model = RepoModel(
        ast_index=[
            AstFileRecord(
                path="calculator.py",
                language="python",
                functions=[{"name": "add", "params": ["a", "b"], "body_snippet": "return a + b"}],
            )
        ]
    )
    flow_graph = FlowGraph()
    pii_hits = PiiHitList(hits=[])
    cfg = ScanConfig(scan_root="tests/dummy_calc")

    report = detect_product_capabilities(model, flow_graph, pii_hits, cfg)

    assert report.has_personal_data is False
    assert report.has_children_data is False
    assert len(report.missing_controls) == 0
    assert "python" in report.stack.languages


def test_capability_detector_full_stack_with_pii_and_missing_controls():
    """A full-stack app collecting Aadhaar, DOB, and storing in DB without retention/erasure."""
    model = RepoModel(
        ast_index=[
            AstFileRecord(
                path="api/main.py",
                language="python",
                decorators=[
                    {"name": "@app.get('/patients')", "line": 15},
                    {"name": "@app.post('/register')", "line": 25},
                ],
                functions=[
                    {
                        "name": "register_patient",
                        "start_line": 25,
                        "end_line": 35,
                        "params": ["request"],
                        "calls": [{"callee": "db.save", "line": 30, "snippet": "db.save(patient)"}],
                    }
                ],
            )
        ],
        schema_records=[
            SchemaRecord(
                source_orm="sqlalchemy",
                source_file="models/patient.py",
                table_or_model="Patient",
                column_or_field="aadhaar_ref",
                data_type="String(12)",
                is_nullable=False,
                has_encryption_marker=False,
                line=10,
            ),
            SchemaRecord(
                source_orm="sqlalchemy",
                source_file="models/patient.py",
                table_or_model="Patient",
                column_or_field="date_of_birth",
                data_type="Date",
                is_nullable=False,
                has_encryption_marker=False,
                line=14,
            ),
        ],
    )
    flow_graph = FlowGraph()
    pii_hits = PiiHitList(
        hits=[
            PiiHit(
                id="pii-1",
                file="api/main.py",
                line=26,
                col=10,
                pii_type=PiiType.AADHAAR,
                confidence=0.95,
                value_sha256="abc123sha",
                validator_result="valid",
                file_role=FileRole.PRODUCTION,
                line_snippet="aadhaar_number = '1234-5678-9012'",
            )
        ]
    )
    cfg = ScanConfig(scan_root="tests/dummy_app")

    report = detect_product_capabilities(model, flow_graph, pii_hits, cfg)

    assert report.has_personal_data is True
    assert report.has_children_data is True  # date_of_birth
    assert "Sqlalchemy" in report.stack.database_engines

    # Check missing controls
    missing_types = {mc.control_type for mc in report.missing_controls}
    assert "ERASURE_ROUTE" in missing_types  # Rule 3(c) & Rule 14(3)
    assert "RETENTION_PURGE" in missing_types  # Rule 8(2)
    assert "AGE_GATE" in missing_types  # Rule 10
    assert "DPO_CONTACT" in missing_types  # Rule 9


def test_capability_detector_compliant_controls():
    """An app with age-gate, retention routine, and erasure route detected."""
    model = RepoModel(
        ast_index=[
            AstFileRecord(
                path="api/main.py",
                language="python",
                decorators=[
                    {"name": "@app.delete('/user/delete')", "line": 40},
                ],
                functions=[
                    {
                        "name": "check_age",
                        "start_line": 10,
                        "end_line": 15,
                        "calls": [{"callee": "is_minor", "line": 12, "snippet": "if is_minor(dob): return False"}],
                    },
                    {
                        "name": "purge_expired_data",
                        "start_line": 20,
                        "end_line": 30,
                        "calls": [{"callee": "delete_old_users", "line": 25, "snippet": "delete_old_users()"}],
                    },
                ],
                calls=[
                    {"callee": "logger.info", "line": 5, "snippet": "contact dpo@company.com for inquiries"}
                ],
            )
        ],
        schema_records=[
            SchemaRecord(
                source_orm="sqlalchemy",
                source_file="models/user.py",
                table_or_model="User",
                column_or_field="date_of_birth",
                data_type="Date",
                is_nullable=False,
                has_encryption_marker=True,
                line=8,
            )
        ],
    )
    flow_graph = FlowGraph()
    pii_hits = PiiHitList(hits=[])
    cfg = ScanConfig(scan_root="tests/dummy_compliant")

    report = detect_product_capabilities(model, flow_graph, pii_hits, cfg)

    implemented_types = {ic.control_type for ic in report.implemented_controls}
    assert "AGE_GATE" in implemented_types
    assert "RETENTION_PURGE" in implemented_types
    assert "ERASURE_ROUTE" in implemented_types
    assert "DPO_CONTACT" in implemented_types

    missing_types = {mc.control_type for mc in report.missing_controls}
    assert "AGE_GATE" not in missing_types
    assert "RETENTION_PURGE" not in missing_types
    assert "ERASURE_ROUTE" not in missing_types
    assert "DPO_CONTACT" not in missing_types
