import pytest
from pathlib import Path
from cs01.models import RepoManifest, FileRecord, Bucket, ScanConfig
from cs01.pipeline.stage2_parse.parser import run_parse

def test_run_parse_orchestrator(tmp_path: Path):
    py_file = tmp_path / "app.py"
    py_file.write_text("def hello(): return 'world'", encoding="utf-8")

    sql_file = tmp_path / "schema.sql"
    sql_file.write_text("CREATE TABLE test (id INT);", encoding="utf-8")

    env_file = tmp_path / ".env"
    env_file.write_text("FOO=bar\n", encoding="utf-8")

    manifest = RepoManifest(
        scan_root=str(tmp_path),
        files=[
            FileRecord(path="app.py", bucket=Bucket.BACKEND, language="python"),
            FileRecord(path="schema.sql", bucket=Bucket.DB_SCHEMA, language="sql"),
            FileRecord(path=".env", bucket=Bucket.SECRETS),
        ],
        total_scanned=3,
    )

    cfg = ScanConfig(scan_root=str(tmp_path))
    model = run_parse(manifest, cfg)

    assert len(model.ast_index) == 1
    assert model.ast_index[0].path == "app.py"

    assert len(model.schema_records) == 1
    assert model.schema_records[0].table_or_model == "test"

    assert len(model.env_vars) == 1
    assert model.env_vars[0].key == "FOO"

    assert len(model.parse_errors) == 0
