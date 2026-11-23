"""
Stack Fingerprinter
===================
Detects the technology stack from repository file inventory.
Rules are data-driven: each entry maps a file/content pattern to a StackProfile.

Adding a new framework: add an entry to STACK_SIGNATURES below.
No code change needed in the main ingestor.
"""

from __future__ import annotations
import json
import re
from pathlib import Path
from typing import Optional

from cs01.models import FileRecord, StackProfile

STACK_SIGNATURES: list[dict] = [
    {
        "filename": "package.json",
        "content_key": "express",
        "framework": "express",
        "language": "javascript",
        "orm_type": None,
    },
    {
        "filename": "package.json",
        "content_key": "fastify",
        "framework": "fastify",
        "language": "javascript",
        "orm_type": None,
    },
    {
        "filename": "package.json",
        "content_key": "next",
        "framework": "nextjs",
        "language": "typescript",
        "orm_type": None,
    },
    {
        "filename": "package.json",
        "content_key": "react",
        "framework": "react",
        "language": "javascript",
        "orm_type": None,
    },
    {
        "filename": "package.json",
        "content_key": "nestjs/core",
        "framework": "nestjs",
        "language": "typescript",
        "orm_type": None,
    },
    {
        "filename": "package.json",
        "content_key": "mongoose",
        "framework": None,
        "language": "javascript",
        "orm_type": "mongoose",
    },
    {
        "filename": "package.json",
        "content_key": "@prisma/client",
        "framework": None,
        "language": "typescript",
        "orm_type": "prisma",
    },
    {
        "filename": "package.json",
        "content_key": "sequelize",
        "framework": None,
        "language": "javascript",
        "orm_type": "sequelize",
    },
    {
        "filename": "package.json",
        "content_key": "typeorm",
        "framework": None,
        "language": "typescript",
        "orm_type": "typeorm",
    },
    {
        "filename": "requirements.txt",
        "content_key": "fastapi",
        "framework": "fastapi",
        "language": "python",
        "orm_type": None,
    },
    {
        "filename": "requirements.txt",
        "content_key": "django",
        "framework": "django",
        "language": "python",
        "orm_type": "django_orm",
    },
    {
        "filename": "requirements.txt",
        "content_key": "flask",
        "framework": "flask",
        "language": "python",
        "orm_type": None,
    },
    {
        "filename": "requirements.txt",
        "content_key": "sqlalchemy",
        "framework": None,
        "language": "python",
        "orm_type": "sqlalchemy",
    },
    {
        "filename": "pyproject.toml",
        "content_key": "fastapi",
        "framework": "fastapi",
        "language": "python",
        "orm_type": None,
    },
    {
        "filename": "pyproject.toml",
        "content_key": "django",
        "framework": "django",
        "language": "python",
        "orm_type": "django_orm",
    },
    {
        "filename": "pom.xml",
        "content_key": "spring-boot",
        "framework": "spring_boot",
        "language": "java",
        "orm_type": "jpa",
    },
    {
        "filename": "build.gradle",
        "content_key": "spring-boot",
        "framework": "spring_boot",
        "language": "kotlin",
        "orm_type": "jpa",
    },
    {
        "filename": "build.gradle.kts",
        "content_key": "spring-boot",
        "framework": "spring_boot",
        "language": "kotlin",
        "orm_type": "jpa",
    },
    {
        "filename": "go.mod",
        "content_key": None,
        "framework": "go",
        "language": "go",
        "orm_type": None,
    },
    {
        "filename": "pubspec.yaml",
        "content_key": None,
        "framework": "flutter",
        "language": "dart",
        "orm_type": None,
    },
    {
        "filename": "schema.prisma",
        "content_key": None,
        "framework": None,
        "language": "prisma",
        "orm_type": "prisma",
    },
]

def detect_stacks(
    scan_root: str,
    accepted_files: list[FileRecord],
    debug: bool = False,
) -> list[StackProfile]:
    """
    Scan the accepted file list for stack-identifying files and produce
    one StackProfile per detected root (handles monorepos).
    """
    root_dirs: set[str] = {""}
    for rec in accepted_files:
        parts = rec.path.split("/")
        if len(parts) > 2:
            root_dirs.add(parts[0])

    stacks: list[StackProfile] = []
    seen_combos: set[tuple] = set()

    for file_rec in accepted_files:
        filename = Path(file_rec.path).name
        abs_path = Path(scan_root) / file_rec.path

        for sig in STACK_SIGNATURES:
            if filename.lower() != sig["filename"].lower():
                continue

            matches = True
            if sig["content_key"]:
                try:
                    content = abs_path.read_text(encoding="utf-8", errors="replace")
                    matches = sig["content_key"] in content
                except OSError:
                    matches = False

            if not matches:
                continue

            parts = file_rec.path.split("/")
            sub_root = parts[0] if len(parts) > 2 else "."

            combo = (sub_root, sig["framework"], sig["language"], sig["orm_type"])
            if combo in seen_combos:
                continue
            seen_combos.add(combo)

            stacks.append(StackProfile(
                root=sub_root,
                framework=sig["framework"],
                language=sig["language"],
                orm_type=sig["orm_type"],
                detected_from=file_rec.path,
            ))

    merged = _merge_stacks(stacks)
    return merged

def _merge_stacks(stacks: list[StackProfile]) -> list[StackProfile]:
    """Merge multiple detections for the same root (e.g. framework from one file, ORM from another)."""
    by_root: dict[str, StackProfile] = {}
    for s in stacks:
        if s.root not in by_root:
            by_root[s.root] = s
        else:
            existing = by_root[s.root]
            if not existing.framework and s.framework:
                existing = existing.model_copy(update={"framework": s.framework})
            if not existing.language and s.language:
                existing = existing.model_copy(update={"language": s.language})
            if not existing.orm_type and s.orm_type:
                existing = existing.model_copy(update={"orm_type": s.orm_type})
            by_root[s.root] = existing
    return list(by_root.values())
