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
    root: str                              # sub-directory root, relative to scan root
    framework: Optional[str] = None       # e.g. "express", "fastapi", "django", "spring"
    language: Optional[str] = None        # e.g. "python", "javascript", "java", "go"
    orm_type: Optional[str] = None        # e.g. "sqlalchemy", "prisma", "mongoose", "django_orm"
    detected_from: Optional[str] = None  # the file that triggered detection (e.g. package.json)
    extra: dict = Field(default_factory=dict)


class FileRecord(BaseModel):
    """Metadata for a single file discovered during repository traversal."""
    path: str                             # root-relative POSIX path
    bucket: Bucket                        # primary semantic bucket
    extra_buckets: list[Bucket] = Field(default_factory=list)  # a file can belong to >1 bucket
    language: Optional[str] = None       # detected language (None for config/data files)
    size_bytes: int = 0
    is_test_file: bool = False            # inside tests/, spec/, __tests__/, *.test.*, *.spec.*
    skip_reason: Optional[str] = None    # set if the file is excluded (binary, dpdpignore, etc.)

    @property
    def is_skipped(self) -> bool:
        return self.skip_reason is not None


class RepoManifest(BaseModel):
    """
    Output of Pipeline Stage 1 — Ingest & Classify Repository.

    Contains the full file inventory and detected stack profiles.
    This is the ONLY input to Stage 2.
    """
    scan_root: str                                      # absolute path that was scanned
    stacks: list[StackProfile] = Field(default_factory=list)
    files: list[FileRecord] = Field(default_factory=list)
    skipped_count: int = 0
    total_scanned: int = 0

    # Convenience accessors
    def accepted_files(self) -> list[FileRecord]:
        """Return only files that were accepted (not skipped)."""
        return [f for f in self.files if not f.is_skipped]

    def files_in_bucket(self, bucket: Bucket) -> list[FileRecord]:
        """Return accepted files belonging to a given bucket."""
        return [
            f for f in self.accepted_files()
            if f.bucket == bucket or bucket in f.extra_buckets
        ]
