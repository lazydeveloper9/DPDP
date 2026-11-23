import pytest
from pathlib import Path
from cs01.models import ScanConfig, Bucket
from cs01.pipeline.stage1_ingest.ingestor import run_ingest

def test_ingest_skips_binary_and_dpdpignore(tmp_path: Path):
    (tmp_path / "src").mkdir()
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "tests").mkdir()

    normal_file = tmp_path / "src" / "app.py"
    normal_file.write_text("print('hello')", encoding="utf-8")

    test_file = tmp_path / "tests" / "test_app.py"
    test_file.write_text("def test_dummy(): pass", encoding="utf-8")

    binary_file = tmp_path / "src" / "data.bin"
    binary_file.write_bytes(b"\x00\x01\x02\x03\x04")

    node_dep = tmp_path / "node_modules" / "dep.js"
    node_dep.write_text("console.log('dep')", encoding="utf-8")

    dpdpignore = tmp_path / ".dpdpignore"
    dpdpignore.write_text("secret_folder/\n*.tmp\n", encoding="utf-8")

    (tmp_path / "secret_folder").mkdir()
    ignored_file = tmp_path / "secret_folder" / "secret.txt"
    ignored_file.write_text("secret", encoding="utf-8")

    tmp_file = tmp_path / "src" / "scratch.tmp"
    tmp_file.write_text("scratch", encoding="utf-8")

    cfg = ScanConfig(scan_root=str(tmp_path))
    manifest = run_ingest(cfg)

    accepted = manifest.accepted_files()
    accepted_paths = [f.path for f in accepted]

    assert "src/app.py" in accepted_paths
    assert "tests/test_app.py" in accepted_paths
    test_record = next(f for f in accepted if f.path == "tests/test_app.py")
    assert test_record.is_test_file is True

    assert "src/data.bin" not in accepted_paths
    assert "node_modules/dep.js" not in accepted_paths
    assert "secret_folder/secret.txt" not in accepted_paths
    assert "src/scratch.tmp" not in accepted_paths

    assert manifest.skipped_count > 0
