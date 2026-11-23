import pytest
from cs01.models.repo_model import RepoModel, AstFileRecord
from cs01.models.flow_graph import PiiHitList, SinkType
from cs01.models.scan_config import ScanConfig
from cs01.pipeline.stage3_detect.flow_tracer import trace_flows

def test_interprocedural_flow_tracing():
    rec1 = AstFileRecord(
        path="src/controllers/auth.py",
        language="python",
        functions=[
            {
                "name": "login",
                "start_line": 5,
                "end_line": 10,
                "params": ["request"],
                "calls": [
                    {"callee": "request.json", "snippet": "await request.json()", "line": 6},
                    {"callee": "forward_credentials", "snippet": "forward_credentials(data)", "line": 7},
                ],
            }
        ],
        decorators=[{"name": "@app.post('/login')", "line": 4}],
    )

    rec2 = AstFileRecord(
        path="src/adapters/vendor.py",
        language="python",
        functions=[
            {
                "name": "forward_credentials",
                "start_line": 8,
                "end_line": 12,
                "params": ["creds"],
                "calls": [
                    {"callee": "requests.post", "snippet": "requests.post('https://analytics.io', json=creds)", "line": 9},
                ],
            }
        ],
    )

    model = RepoModel(ast_index=[rec1, rec2])
    pii_hits = PiiHitList(hits=[])
    cfg = ScanConfig()

    flow_graph = trace_flows(model, pii_hits, cfg)

    inter_edges = [e for e in flow_graph.edges if "login->forward_credentials" in (e.function_name or "")]
    assert len(inter_edges) >= 1
    edge = inter_edges[0]
    assert edge.is_unguarded is True
    assert edge.reachability == "REACHABLE_EXTERNAL"
