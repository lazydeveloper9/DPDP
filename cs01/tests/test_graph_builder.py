"""
Unit and generalization tests for CS-01 DataFlowGraph and GraphBuilder.
======================================================================
Tests:
  1. Target A: Vulnerable Full-Stack Target (asserts dynamic pii_leak / unconsented edges).
  2. Target B: Clean Negative Control Target (asserts 0 leaks, 0 unconsented edges, compliant edges).
  3. Target C: Minimal / Partial-Stack Target (asserts honest empty handling, zero phantom tiers).
  4. Static Hygiene: Asserts zero hardcoded app-specific identifiers in graph engine or templates.
  5. Offline Zero-Egress: Asserts standalone HTML contains zero external CDN scripts or stylesheet links.
"""

from __future__ import annotations
from pathlib import Path

from cs01.models.scan_config import ScanConfig
from cs01.models.repo_model import RepoModel, AstFileRecord, SchemaRecord, IacTree
from cs01.models.flow_graph import FlowGraph, PiiHitList, DataSink, SinkType
from cs01.models.scored_finding import ScoredFindingBundle, ScoredFinding, DpdpReadinessScore
from cs01.models.raw_finding import Severity, PassType
from cs01.models.graph import (
    DataFlowGraph, LayerTier, FlowStatus, GraphNodeType, GraphEdgeFlowType,
)
from cs01.pipeline.stage6_report.graph_builder import GraphBuilder, build_dataflow_graph
from cs01.pipeline.stage6_report.visualizer.template import render_standalone_html

FIXTURES_DIR = Path(__file__).parent / "fixtures"

def test_target_a_vulnerable_full_stack():
    """Target A: Vulnerable full-stack app with unmasked logger and unconsented tables."""
    bundle = ScoredFindingBundle(
        scan_id="scan-vuln-001",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="tests/fixtures/fixture_fastapi_app",
        findings=[
            ScoredFinding(
                id="CODE-DPDP-001:src/main.py:10",
                rule_id="CODE-DPDP-001",
                pass_type=PassType.A,
                file="src/main.py",
                line_start=10,
                line_end=10,
                snippet="logger.info(data)",
                dpdp_section="§8(5)",
                dpdp_rule="Rule 6(1)(a)",
                penalty_band="250_crore",
                severity=Severity.CRITICAL,
                message="Personal data flows directly into an unguarded logger sink",
                remediation="Apply deterministic masking",
            ),
            ScoredFinding(
                id="SQL-DPDP-005:src/models.py:7",
                rule_id="SQL-DPDP-005",
                pass_type=PassType.A,
                file="src/models.py",
                line_start=7,
                line_end=7,
                snippet="class User(Base):",
                matched_entity="User",
                dpdp_section="§6(1)",
                dpdp_rule="Rule 5",
                penalty_band="50_crore",
                severity=Severity.MEDIUM,
                message="Personal data table schema missing verifiable consent ledger linkage",
                remediation="Add foreign key reference to consent record",
            ),
        ],
        readiness=DpdpReadinessScore(overall=35.0, max_statutory_ceiling_engaged="Up to ₹250 Crore"),
    )

    repo_model = RepoModel(
        ast_index=[
            AstFileRecord(
                path="src/main.py",
                language="python",
                functions=[{
                    "name": "register",
                    "start_line": 8,
                    "end_line": 12,
                    "params": ["request"],
                    "decorators": ["@app.post('/register')"],
                    "body_snippet": "data = await request.json()\nlogger.info(data)\nreturn {'status': 'ok'}",
                }],
                calls=[
                    {"callee": "logger.info", "line": 10, "snippet": "logger.info(data)"}
                ],
            )
        ],
        schema_records=[
            SchemaRecord(
                source_orm="sqlalchemy",
                source_file="src/models.py",
                table_or_model="User",
                column_or_field="aadhaar_number",
                data_type="String(12)",
                is_nullable=False,
                has_encryption_marker=False,
                has_consent_linkage=False,
                line=7,
            )
        ],
        iac_trees=[
            IacTree(
                source_file="src/main.tf",
                file_type="terraform",
                resource_type="aws_db_instance",
                resource_name="app_db",
                attributes={"storage_encrypted": False},
                line_map={"app_db": 2},
            )
        ],
    )

    builder = GraphBuilder(bundle=bundle, repo_model=repo_model)
    dfg = builder.build()

    assert dfg.summary_metrics.total_nodes >= 3
    assert dfg.summary_metrics.leak_edges >= 1 or any(n.status == FlowStatus.PII_LEAK for n in dfg.nodes)
    assert any(n.status == FlowStatus.UNCONSENTED_STORAGE for n in dfg.nodes)
    assert "INFRA_CLOUD" in dfg.summary_metrics.active_layers

    # Verify real file path and finding IDs
    leak_nodes = [n for n in dfg.nodes if n.status == FlowStatus.PII_LEAK]
    assert len(leak_nodes) > 0
    assert any("CODE-DPDP-001" in fid for n in leak_nodes for fid in n.finding_ids)

def test_target_b_clean_negative_control():
    """Target B: Clean negative control app (0 leaks, 0 unconsented edges, compliant flows)."""
    bundle = ScoredFindingBundle(
        scan_id="scan-clean-001",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="tests/fixtures/fixture_clean_app",
        findings=[],  # 0 findings!
        readiness=DpdpReadinessScore(overall=100.0),
    )

    repo_model = RepoModel(
        ast_index=[
            AstFileRecord(
                path="src/main.py",
                language="python",
                functions=[
                    {
                        "name": "create_user",
                        "start_line": 15,
                        "end_line": 20,
                        "params": ["request", "current_user: User = Depends(get_current_user)"],
                        "decorators": ["@app.post('/user')"],
                        "body_snippet": "data = await request.json()\nlogger.info(mask_pii(data))\nreturn {'status': 'ok'}",
                    }
                ],
                calls=[
                    {"callee": "logger.info", "line": 18, "snippet": "logger.info(mask_pii(data))"}
                ],
            )
        ],
        schema_records=[
            SchemaRecord(
                source_orm="sqlalchemy",
                source_file="src/models.py",
                table_or_model="User",
                column_or_field="email",
                data_type="String",
                has_encryption_marker=True,
                has_consent_linkage=True,
                line=5,
            )
        ],
    )

    builder = GraphBuilder(bundle=bundle, repo_model=repo_model)
    dfg = builder.build()

    assert dfg.summary_metrics.leak_edges == 0
    assert dfg.summary_metrics.unconsented_storage_edges == 0
    assert all(n.status != FlowStatus.PII_LEAK for n in dfg.nodes)
    assert all(n.status != FlowStatus.UNCONSENTED_STORAGE for n in dfg.nodes)

def test_target_c_minimal_partial_stack():
    """Target C: Minimal single-file Express.js API with no SQL or Terraform (Honest empty handling)."""
    bundle = ScoredFindingBundle(
        scan_id="scan-express-001",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="tests/fixtures/fixture_express_app",
        findings=[],
        readiness=DpdpReadinessScore(overall=95.0),
    )

    repo_model = RepoModel(
        ast_index=[
            AstFileRecord(
                path="src/app.js",
                language="javascript",
                functions=[{
                    "name": "contact_handler",
                    "start_line": 5,
                    "end_line": 9,
                    "params": ["req", "res"],
                    "decorators": ["app.post('/api/contact')"],
                    "body_snippet": "const { email, message } = req.body;\nconsole.log('Received');\nres.json({status: 'ok'});",
                }],
                calls=[
                    {"callee": "console.log", "line": 7, "snippet": "console.log('Received')"}
                ],
            )
        ],
        schema_records=[],  # No SQL / DB models!
        iac_trees=[],       # No Terraform / Cloud!
    )

    builder = GraphBuilder(bundle=bundle, repo_model=repo_model)
    dfg = builder.build()

    # Honest empty handling assertions
    assert "STORAGE" not in dfg.summary_metrics.active_layers
    assert "INFRA_CLOUD" not in dfg.summary_metrics.active_layers
    assert "API_LOGIC" in dfg.summary_metrics.active_layers
    assert "EGRESS_SINK" in dfg.summary_metrics.active_layers
    assert dfg.summary_metrics.leak_edges == 0

def test_static_hygiene_zero_hardcoding():
    """Static hygiene: Ensure zero hardcoded target names exist in graph builder or template."""
    forbidden = ["medivault", "quickrupee", "patient_id", "ayushman_ref", "target.local"]

    cs01_pkg = Path(__file__).parent.parent / "cs01"
    files_to_check = [
        cs01_pkg / "pipeline" / "stage6_report" / "graph_builder.py",
        cs01_pkg / "models" / "graph.py",
        cs01_pkg / "pipeline" / "stage6_report" / "visualizer" / "template.py",
    ]

    for fpath in files_to_check:
        assert fpath.exists(), f"File {fpath} does not exist"
        content = fpath.read_text(encoding="utf-8").lower()
        for word in forbidden:
            assert word not in content, f"Hardcoded identifier '{word}' found in {fpath}"

def test_offline_zero_egress_standalone_html():
    """Assert standalone HTML contains zero external CDN scripts or stylesheet links."""
    bundle = ScoredFindingBundle(
        scan_id="scan-offline-001",
        scan_timestamp="2026-11-23T12:00:00Z",
        scan_root="test_repo",
        findings=[],
    )
    dfg = build_dataflow_graph(bundle=bundle)
    html = render_standalone_html(dfg)

    # Must contain inlined JS code from vendored libraries
    assert "cytoscape" in html
    assert "THREE" in html

    # Must NOT contain external network links
    assert "<script src=\"http" not in html
    assert "<link rel=\"stylesheet\" href=\"http" not in html
    assert "<script src=\"https" not in html
    assert "<link rel=\"stylesheet\" href=\"https" not in html
