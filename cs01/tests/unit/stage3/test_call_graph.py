import pytest
from cs01.models.repo_model import RepoModel, AstFileRecord
from cs01.pipeline.stage3_detect.call_graph import CallGraph

def test_call_graph_resolution_and_reachability():
    rec1 = AstFileRecord(
        path="src/api/routes.py",
        language="python",
        functions=[
            {
                "name": "create_user",
                "start_line": 10,
                "end_line": 15,
                "params": ["request"],
                "calls": [{"callee": "save_user", "line": 12}],
            }
        ],
        decorators=[{"name": "@app.post('/users')", "line": 9}],
    )

    rec2 = AstFileRecord(
        path="src/services/user_service.py",
        language="python",
        functions=[
            {
                "name": "save_user",
                "start_line": 5,
                "end_line": 10,
                "params": ["payload"],
                "calls": [{"callee": "log_event", "line": 7}],
            },
            {
                "name": "unused_helper",
                "start_line": 20,
                "end_line": 25,
                "params": [],
                "calls": [],
            }
        ],
    )

    model = RepoModel(ast_index=[rec1, rec2])
    cg = CallGraph(model)

    assert cg.is_route_entrypoint("src/api/routes.py", "create_user") is True
    assert ("src/services/user_service.py", "save_user") in cg.get_callees("src/api/routes.py", "create_user")

    assert cg.compute_reachability("src/api/routes.py", "create_user") == "REACHABLE_EXTERNAL"
    assert cg.compute_reachability("src/services/user_service.py", "save_user") == "REACHABLE_EXTERNAL"
    assert cg.compute_reachability("src/services/user_service.py", "unused_helper") == "UNREACHABLE"
