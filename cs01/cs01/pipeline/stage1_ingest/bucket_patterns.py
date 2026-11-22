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

# ---------------------------------------------------------------------------
# Bucket pattern rules — evaluated in order; first match wins for primary bucket
# Extra buckets are accumulated (a file can belong to multiple buckets)
# ---------------------------------------------------------------------------

# SECRETS — highest priority (checked first)
_SECRETS_PATTERNS = [
    r"\.env(\.|$)",               # .env, .env.local, .env.production
    r"\.env$",
    r"secrets?[\._-]",
    r"credentials?[\._-]",
    r"\.pem$", r"\.key$", r"\.p12$", r"\.pfx$", r"\.crt$",
    r"config/(secrets?|credentials?)\.(json|yaml|yml)$",
    r"vault[\._-]",
]

# DB_SCHEMA — SQL files, ORM model files, migration directories
_DB_PATTERNS = [
    r"\.sql$",
    r"\.prisma$",
    r"migrations?/.*",
    r"schema\.(rb|sql|prisma)$",
    r"models?/.*",                    # models directory
    r"models?\.(py|ts|js)$",          # Django/SQLAlchemy/TypeORM models
    r"entities?/.*\.(ts|java|kt)$",   # JPA entities
    r"database/.*",
    r"db/.*",
]

# INFRA — IaC, container, cloud config
_INFRA_PATTERNS = [
    r"\.tf$",                          # Terraform
    r"\.hcl$",
    r"dockerfile$",                    # Dockerfile (case-insensitive)
    r"docker-compose.*\.ya?ml$",
    r"kubernetes/.*",
    r"k8s/.*",
    r"helm/.*",
    r"charts?/.*",
    r"\.(yaml|yml)$",                  # K8s manifests (broad; refined by content in Stage 2)
    r"\.github/workflows/.*",
    r"\.gitlab-ci\.ya?ml$",
    r"cloudbuild\.ya?ml$",
    r"serverless\.ya?ml$",
    r"cdk\.json$",
]

# FRONTEND — UI code
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

# BACKEND — application logic
_BACKEND_PATTERNS = [
    r"\.(py|java|go|kt|rb|php|cs|rs)$",
    r"\.(ts|js)$",                     # could be frontend too; both buckets assigned
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

    # --- SECRETS (always check first) ---
    if _matches_any(_SECRETS_PATTERNS, rel_path, filename):
        return Bucket.SECRETS, extra

    # --- DB_SCHEMA ---
    if _matches_any(_DB_PATTERNS, rel_path, filename):
        return Bucket.DB_SCHEMA, extra

    # --- INFRA ---
    if _matches_any(_INFRA_PATTERNS, rel_path, filename):
        return Bucket.INFRA, extra

    # --- FRONTEND ---
    is_frontend = _matches_any(_FRONTEND_PATTERNS, rel_path, filename)
    # --- BACKEND ---
    is_backend = _matches_any(_BACKEND_PATTERNS, rel_path, filename)

    if is_frontend and is_backend:
        # Assign both; primary = BACKEND for .ts/.js; FRONTEND for .jsx/.tsx/.vue
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
