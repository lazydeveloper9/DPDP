import pytest
from cs01.models import (
    RepoModel, AstFileRecord, ScanConfig, FlowGraph, PiiHitList,
)
from cs01.pipeline.stage3_detect.flow_tracer import trace_flows
from cs01.pipeline.stage3_detect.pii_detector import detect_pii


def test_unguarded_flow_detection():
    # Setup AST function where request payload flows directly to a logger
    ast_file = AstFileRecord(
        path="api/user.py",
        language="python",
        functions=[
            {
                "name": "login_user",
                "start_line": 10,
                "end_line": 20,
                "params": ["request", "aadhaar_no"],
                "calls": [
                    {"callee": "logger.info", "snippet": "logger.info(aadhaar_no)", "line": 15},
                ],
            }
        ],
    )
    model = RepoModel(ast_index=[ast_file])
    cfg = ScanConfig()

    pii_hits = detect_pii(model, cfg)
    flow_graph = trace_flows(model, pii_hits, cfg)

    assert len(flow_graph.sources) >= 1
    assert len(flow_graph.sinks) >= 1
    assert len(flow_graph.edges) >= 1

    edge = flow_graph.edges[0]
    assert edge.is_unguarded is True
    assert edge.guard_id is None


def test_guarded_flow_detection():
    # Setup AST function where PII passes through a masking guard before logger
    ast_file = AstFileRecord(
        path="api/secure.py",
        language="python",
        functions=[
            {
                "name": "process_pii",
                "start_line": 5,
                "end_line": 18,
                "params": ["payload"],
                "calls": [
                    {"callee": "mask_pii", "snippet": "masked = mask_pii(payload)", "line": 8},
                    {"callee": "logger.info", "snippet": "logger.info(masked)", "line": 12},
                ],
            }
        ],
    )
    model = RepoModel(ast_index=[ast_file])
    cfg = ScanConfig()

    pii_hits = detect_pii(model, cfg)
    flow_graph = trace_flows(model, pii_hits, cfg)

    assert len(flow_graph.guards) >= 1
    assert len(flow_graph.edges) >= 1

    edge = flow_graph.edges[0]
    assert edge.is_unguarded is False
    assert edge.guard_id is not None
