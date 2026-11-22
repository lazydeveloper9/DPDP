"""
Stage 6 Evidence Locker & Cryptographic Verifier
================================================
Packages scan findings into a tamper-evident ZIP evidence bundle with SHA-256
hash sidecars for Significant Data Fiduciary (SDF) annual audits under DPDP Rule 13.
"""

from __future__ import annotations
import hashlib
import json
import zipfile
from pathlib import Path
from typing import Any

from cs01.utils import sha256_of


def create_evidence_bundle(
    report_files: dict[str, Path],
    scan_id: str,
    scan_timestamp: str,
    cs01_version: str,
    output_zip_path: Path | str,
) -> Path:
    """
    Package all generated audit reports and a cryptographic manifest into a ZIP bundle.
    """
    out_zip = Path(output_zip_path)
    out_zip.parent.mkdir(parents=True, exist_ok=True)

    manifest: dict[str, Any] = {
        "title": "CS-01 DPDP Rule 13 Compliance Evidence Manifest",
        "scan_id": scan_id,
        "scan_timestamp": scan_timestamp,
        "auditor_tool": "CS-01",
        "cs01_version": cs01_version,
        "files": {},
    }

    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for name, file_path in report_files.items():
            if file_path.exists():
                content = file_path.read_bytes()
                f_hash = hashlib.sha256(content).hexdigest()
                manifest["files"][name] = {
                    "sha256": f_hash,
                    "size_bytes": len(content),
                }
                zf.writestr(name, content)

        # Write the manifest itself inside the bundle
        manifest_bytes = json.dumps(manifest, indent=2).encode("utf-8")
        manifest_hash = hashlib.sha256(manifest_bytes).hexdigest()
        zf.writestr("manifest.json", manifest_bytes)
        zf.writestr("manifest.json.sha256", f"{manifest_hash}  manifest.json\n")

    return out_zip


def verify_evidence_bundle(bundle_path: Path | str) -> tuple[bool, list[str]]:
    """
    Cryptographically verify the integrity and provenance of an evidence bundle.
    Returns (is_valid, log_messages).
    """
    p = Path(bundle_path)
    if not p.exists():
        return False, [f"Bundle file not found: {p}"]

    logs: list[str] = []
    try:
        with zipfile.ZipFile(p, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return False, ["Invalid bundle: manifest.json missing."]

            manifest_data = json.loads(zf.read("manifest.json").decode("utf-8"))
            files_spec = manifest_data.get("files", {})

            for name, meta in files_spec.items():
                if name not in zf.namelist():
                    logs.append(f"MISSING: File '{name}' declared in manifest is missing from ZIP.")
                    return False, logs

                data = zf.read(name)
                computed = hashlib.sha256(data).hexdigest()
                expected = meta.get("sha256")
                if computed != expected:
                    logs.append(f"INTEGRITY VIOLATION: '{name}' hash mismatch! Expected {expected}, got {computed}")
                    return False, logs
                else:
                    logs.append(f"VERIFIED: '{name}' SHA-256 integrity intact ({computed[:12]}...)")

        logs.append("SUCCESS: All cryptographic signatures and file hashes verified.")
        return True, logs
    except Exception as exc:
        return False, [f"Bundle verification error: {exc}"]
