"""
cs01.utils — Shared utilities used across all pipeline stages.
No stage-specific logic lives here.
"""

import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def sha256_of(value: str) -> str:
    """Return hex SHA-256 digest of a string value."""
    return hashlib.sha256(value.encode("utf-8")).digest().hex()


def new_scan_id() -> str:
    """Generate a unique scan invocation ID."""
    return str(uuid.uuid4())


def utc_now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def save_json(data: Any, path: str | Path, indent: int = 2) -> None:
    """Serialise a Pydantic model or plain dict to a JSON file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if hasattr(data, "model_dump"):
        payload = data.model_dump(mode="json")
    else:
        payload = data
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=indent, ensure_ascii=False)


def load_json(path: str | Path) -> Any:
    """Load a JSON file and return parsed content."""
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def is_binary_file(path: str | Path) -> bool:
    """
    Quick binary-file detector: reads first 512 bytes and checks for null bytes.
    Avoids trying to parse images, compiled binaries, etc.
    """
    try:
        with open(path, "rb") as fh:
            chunk = fh.read(512)
        return b"\x00" in chunk
    except OSError:
        return True  # treat unreadable files as binary/skipped


def relative_posix(path: str | Path, root: str | Path) -> str:
    """Return a POSIX-style path relative to root."""
    return Path(path).relative_to(root).as_posix()


def redact_pii_in_snippet(snippet: str, pii_values: list[str]) -> str:
    """
    Replace known PII literal values in a code snippet with typed placeholders.
    Placeholders are deterministic: [AADHAAR_1], [PAN_1], etc.
    Used before any snippet is stored in a finding or sent anywhere.
    """
    result = snippet
    counters: dict[str, int] = {}
    for val in pii_values:
        if val and val in result:
            ptype = "PII"
            counters[ptype] = counters.get(ptype, 0) + 1
            result = result.replace(val, f"[{ptype}_{counters[ptype]}]")
    return result


from .archive import is_archive, safe_extract_zip, safe_extract_tar, extracted_workspace
from .git_ingest import is_git_url, parse_git_url, clone_git_repo, cloned_workspace
