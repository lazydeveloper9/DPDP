"""
Stage 1 output model: RepoManifest
Describes every file in the target repository after traversal,
classification, and stack fingerprinting.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class Bucket(str, Enum):
    """Semantic file bucket assigned during Stage 1 classification."""
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    DB_SCHEMA = "DB_SCHEMA"
    INFRA = "INFRA"
    SECRETS = "SECRETS"
    UNKNOWN = "UNKNOWN"

class StackProfile(BaseModel):
    """Detected technology stack for a repository root (or sub-root in a monorepo)."""
    root: str
    framework: Optional[str] = None
    language: Optional[str] = None
    orm_type: Optional[str] = None
    detected_from: Optional[str] = None
    extra: dict = Field(default_factory=dict)

class FileRecord(BaseModel):
    """Metadata for a single file discovered during repository traversal."""
    path: str
    bucket: Bucket
    extra_buckets: list[Bucket] = Field(default_factory=list)
    language: Optional[str] = None
    size_bytes: int = 0
    is_test_file: bool = False
    skip_reason: Optional[str] = None

    @property
    def is_skipped(self) -> bool:
        return self.skip_reason is not None

class RepoManifest(BaseModel):
    """
    Output of Pipeline Stage 1 — Ingest & Classify Repository.

    Contains the full file inventory and detected stack profiles.
    This is the ONLY input to Stage 2.
    """
    scan_root: str
    stacks: list[StackProfile] = Field(default_factory=list)
    files: list[FileRecord] = Field(default_factory=list)
    skipped_count: int = 0
    total_scanned: int = 0

    def accepted_files(self) -> list[FileRecord]:
        """Return only files that were accepted (not skipped)."""
        return [f for f in self.files if not f.is_skipped]

    def files_in_bucket(self, bucket: Bucket) -> list[FileRecord]:
        """Return accepted files belonging to a given bucket."""
        return [
            f for f in self.accepted_files()
            if f.bucket == bucket or bucket in f.extra_buckets
        ]
