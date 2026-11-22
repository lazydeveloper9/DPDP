"""
Stage 2 Secrets & Env Parser
============================
Parses .env files and JSON configurations into normalized EnvVar records.
Crucial invariant: Raw secret values are NEVER stored in memory or on disk;
only their SHA-256 digests and length/entropy markers are retained.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Any

from cs01.models import EnvVar
from cs01.utils import sha256_of

SECRET_KEY_PATTERNS = re.compile(
    r"(secret|password|passwd|token|apikey|api_key|auth|credential|privkey|private_key)",
    re.IGNORECASE,
)


def parse_env_file(abs_path: Path, rel_path: str) -> list[EnvVar]:
    """Parse a .env formatted file line by line."""
    records: list[EnvVar] = []
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return records

    for line_idx, raw_line in enumerate(content.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if "=" not in line:
            continue

        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip().strip("'\"")

        is_secret = bool(SECRET_KEY_PATTERNS.search(key)) or len(val) >= 32

        records.append(
            EnvVar(
                key=key,
                value_sha256=sha256_of(val),
                value_length=len(val),
                source_file=rel_path,
                line=line_idx,
                is_potential_secret=is_secret,
            )
        )

    return records


def parse_json_config(abs_path: Path, rel_path: str) -> list[EnvVar]:
    """Parse JSON configuration files, flattening nested dictionaries."""
    records: list[EnvVar] = []
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
            data = json.load(fh)
    except Exception:
        return records

    def _flatten(obj: Any, prefix: str = "", line: int = 1) -> None:
        if isinstance(obj, dict):
            for k, v in obj.items():
                new_key = f"{prefix}.{k}" if prefix else k
                _flatten(v, new_key, line)
        elif isinstance(obj, (str, int, float, bool)):
            str_val = str(obj)
            is_secret = bool(SECRET_KEY_PATTERNS.search(prefix)) or len(str_val) >= 32
            records.append(
                EnvVar(
                    key=prefix,
                    value_sha256=sha256_of(str_val),
                    value_length=len(str_val),
                    source_file=rel_path,
                    line=line,
                    is_potential_secret=is_secret,
                )
            )

    _flatten(data)
    return records


def parse_secrets_and_env(abs_path: Path, rel_path: str) -> list[EnvVar]:
    """Dispatcher for SECRETS bucket files."""
    name = abs_path.name.lower()
    if ".env" in name:
        return parse_env_file(abs_path, rel_path)
    elif name.endswith(".json"):
        return parse_json_config(abs_path, rel_path)
    return []
