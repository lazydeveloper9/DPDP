"""
Unit tests for archive extraction and zip scanning in Stage 1.
"""

import io
import tempfile
import zipfile
from pathlib import Path
import pytest

from cs01.utils.archive import is_archive, safe_extract_zip, extracted_workspace
from cs01.models.scan_config import ScanConfig
from cs01.pipeline.stage1_ingest.ingestor import run_ingest


def test_is_archive():
    with tempfile.NamedTemporaryFile(suffix=".zip", delete=False) as f:
        with zipfile.ZipFile(f.name, "w") as zf:
            zf.writestr("test.py", "print('hello')")
        zip_path = Path(f.name)

    try:
        assert is_archive(zip_path) is True
        assert is_archive(Path("non_existent_file.xyz")) is False
    finally:
        zip_path.unlink(missing_ok=True)


def test_safe_extract_zip_prevents_zip_slip():
    """Verify that any archive member with directory traversal causes ValueError."""
    zip_bytes = io.BytesIO()
    with zipfile.ZipFile(zip_bytes, "w") as zf:
        # Create a malicious member attempting Zip Slip
        zf.writestr("../../etc/passwd", "malicious")
    zip_bytes.seek(0)

    with tempfile.TemporaryDirectory() as dest_dir:
        temp_zip = Path(dest_dir) / "test_malicious.zip"
        temp_zip.write_bytes(zip_bytes.getvalue())

        extract_target = Path(dest_dir) / "unpacked"
        extract_target.mkdir()

        with pytest.raises(ValueError, match="Zip Slip"):
            safe_extract_zip(temp_zip, extract_target)


def test_extracted_workspace_with_zip():
    """Verify scanning works directly on a zip archive."""
    with tempfile.TemporaryDirectory() as tmp:
        zip_file = Path(tmp) / "sample_app.zip"
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("main.py", "import os\nprint('hello world')\n")
            zf.writestr("requirements.txt", "fastapi==0.100.0\n")

        # Scan using extracted_workspace
        with extracted_workspace(zip_file) as ws:
            assert (ws / "main.py").exists()
            assert (ws / "requirements.txt").exists()
            cfg = ScanConfig(scan_root=str(ws))
            manifest = run_ingest(cfg)
            assert manifest.total_scanned >= 2
            assert any(f.path.endswith("main.py") for f in manifest.files)
