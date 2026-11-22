import pytest
import zipfile
from pathlib import Path
from cs01.pipeline.stage6_report.evidence_locker import (
    create_evidence_bundle, verify_evidence_bundle,
)


def test_evidence_bundle_creation_and_verification(tmp_path: Path):
    f1 = tmp_path / "report.json"
    f1.write_text('{"compliance": "ok"}', encoding="utf-8")

    f2 = tmp_path / "report.html"
    f2.write_text('<html><body>Audit</body></html>', encoding="utf-8")

    report_files = {
        "report.json": f1,
        "report.html": f2,
    }

    bundle_zip = tmp_path / "cs01-evidence-bundle.zip"
    created_path = create_evidence_bundle(
        report_files=report_files,
        scan_id="scan-xyz-123",
        scan_timestamp="2026-11-23T00:00:00Z",
        cs01_version="0.1.0-alpha",
        output_zip_path=bundle_zip,
    )

    assert created_path.exists()

    # 1. Verify clean bundle
    is_valid, logs = verify_evidence_bundle(bundle_zip)
    assert is_valid is True
    assert any("VERIFIED" in l for l in logs)

    # 2. Tampering Test: modify a file inside the zip to prove tamper-evidence
    tampered_zip = tmp_path / "tampered-bundle.zip"
    with zipfile.ZipFile(bundle_zip, "r") as src_z:
        with zipfile.ZipFile(tampered_zip, "w") as dst_z:
            for item in src_z.namelist():
                content = src_z.read(item)
                if item == "report.json":
                    content = content + b"TAMPERED_BYTE"
                dst_z.writestr(item, content)

    # Verification must fail and report an integrity violation
    is_tampered_valid, tamper_logs = verify_evidence_bundle(tampered_zip)
    assert is_tampered_valid is False
    assert any("INTEGRITY VIOLATION" in l for l in tamper_logs)
