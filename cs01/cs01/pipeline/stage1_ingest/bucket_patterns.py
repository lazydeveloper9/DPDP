"""
File Bucket Classifier
======================
Assigns each file to one or more of the 5 semantic buckets:
  FRONTEND | BACKEND | DB_SCHEMA | INFRA | SECRETS

Rules are purely based on file path, filename, and extension.
No file content is read here (that's Stage 2's job).
"""

from __future__ import annotations
import re
from pathlib import Path

from cs01.models import Bucket

_SECRETS_PATTERNS = [
    r"\.env(\.|$)",
    r"\.env$",
    r"secrets?[\._-]",
    r"credentials?[\._-]",
    r"\.pem$", r"\.key$", r"\.p12$", r"\.pfx$", r"\.crt$",
    r"config/(secrets?|credentials?)\.(json|yaml|yml)$",
    r"vault[\._-]",
]

_DB_PATTERNS = [
    r"\.sql$",
    r"\.prisma$",
    r"migrations?/.*",
    r"schema\.(rb|sql|prisma)$",
    r"models?/.*",
    r"models?\.(py|ts|js)$",
    r"entities?/.*\.(ts|java|kt)$",
    r"database/.*",
    r"db/.*",
]

_INFRA_PATTERNS = [
    r"\.tf$",
    r"\.hcl$",
    r"dockerfile$",
    r"docker-compose.*\.ya?ml$",
    r"kubernetes/.*",
    r"k8s/.*",
    r"helm/.*",
    r"charts?/.*",
    r"\.(yaml|yml)$",
    r"\.github/workflows/.*",
    r"\.gitlab-ci\.ya?ml$",
    r"cloudbuild\.ya?ml$",
    r"serverless\.ya?ml$",
    r"cdk\.json$",
]

_FRONTEND_PATTERNS = [
    r"\.(jsx|tsx|vue|svelte)$",
    r"\.html$",
    r"components?/.*",
    r"pages?/.*",
    r"views?/.*",
    r"src/(app|pages|components|layouts)/.*",
    r"public/.*\.(js|ts)$",
    r"static/.*\.(js|ts)$",
]

_BACKEND_PATTERNS = [
    r"\.(py|java|go|kt|rb|php|cs|rs)$",
    r"\.(ts|js)$",
    r"routes?/.*",
    r"controllers?/.*",
    r"handlers?/.*",
    r"services?/.*",
    r"api/.*",
    r"middleware/.*",
    r"auth/.*",
]

def _matches_any(patterns: list[str], rel_path: str, filename: str) -> bool:
    combined = rel_path.lower()
    for pat in patterns:
        if re.search(pat, combined, re.IGNORECASE):
            return True
    return False

def classify_bucket(
    rel_path: str,
    filename: str,
    ext: str,
) -> tuple[Bucket, list[Bucket]]:
    """
    Returns (primary_bucket, extra_buckets).
    Primary bucket is the first matching category.
    Extra buckets capture secondary memberships (e.g. a .ts API file → BACKEND + FRONTEND).
    """
    extra: list[Bucket] = []

    if _matches_any(_SECRETS_PATTERNS, rel_path, filename):
        return Bucket.SECRETS, extra

    if _matches_any(_DB_PATTERNS, rel_path, filename):
        return Bucket.DB_SCHEMA, extra

    if _matches_any(_INFRA_PATTERNS, rel_path, filename):
        return Bucket.INFRA, extra

    is_frontend = _matches_any(_FRONTEND_PATTERNS, rel_path, filename)
    is_backend = _matches_any(_BACKEND_PATTERNS, rel_path, filename)

    if is_frontend and is_backend:
        if ext in (".jsx", ".tsx", ".vue", ".svelte", ".html"):
            extra.append(Bucket.BACKEND)
            return Bucket.FRONTEND, extra
        else:
            extra.append(Bucket.FRONTEND)
            return Bucket.BACKEND, extra

    if is_frontend:
        return Bucket.FRONTEND, extra

    if is_backend:
        return Bucket.BACKEND, extra

    return Bucket.UNKNOWN, extra
