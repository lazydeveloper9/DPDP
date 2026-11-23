import pytest
from pathlib import Path
from cs01.pipeline.stage2_parse.ast_parser import parse_source_ast

def test_parse_python_ast(tmp_path: Path):
    py_file = tmp_path / "routes.py"
    py_file.write_text(
        """
import logging

logger = logging.getLogger(__name__)

@app.post("/register")
def register_user(aadhaar: str, email: str):
    logger.info(f"Registering {email}")
    dummy_pan = "ABCDE1234F"
    return {"status": "ok"}
        """,
        encoding="utf-8",
    )

    record = parse_source_ast(py_file, "routes.py", "python")
    assert record.parse_error is None
    assert len(record.functions) == 1

    fn = record.functions[0]
    assert fn["name"] == "register_user"
    assert len(fn["params"]) == 2
    assert any("logger.info" in c["callee"] for c in fn["calls"])

    vals = [s["value"] for s in record.string_literals]
    assert "ABCDE1234F" in vals
    assert "/register" in vals

    assert len(record.decorators) >= 1
    assert any("app.post" in d["name"] for d in record.decorators)

def test_parse_javascript_ast(tmp_path: Path):
    js_file = tmp_path / "api.js"
    js_file.write_text(
        """
function processPayment(upiId, amount) {
    console.log("Processing for", upiId);
    const testAadhaar = "234567890123";
    return true;
}
        """,
        encoding="utf-8",
    )

    record = parse_source_ast(js_file, "api.js", "javascript")
    assert record.parse_error is None
    assert len(record.functions) == 1

    fn = record.functions[0]
    assert fn["name"] == "processPayment"

    vals = [s["value"] for s in record.string_literals]
    assert "234567890123" in vals
