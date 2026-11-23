"""
Pipeline Stage 1 — Ingest & Classify Repository
================================================
Entry point: run_ingest(cfg) → RepoManifest

Sub-components:
  - File traverser (respects .dpdpignore + hard defaults)
  - Binary file detector
  - Stack fingerprinter (framework/language detection)
  - File bucketer (5 semantic buckets)
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

import pathspec
from rich.console import Console

from cs01.models import RepoManifest, FileRecord, Bucket, StackProfile, ScanConfig
from cs01.config import load_dpdpignore
from cs01.utils import is_binary_file, relative_posix

from .stack_signatures import detect_stacks
from .bucket_patterns import classify_bucket

console = Console(stderr=True)

EXTENSION_TO_LANGUAGE: dict[str, str] = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".go": "go",
    ".kt": "kotlin",
    ".kts": "kotlin",
    ".dart": "dart",
    ".swift": "swift",
    ".rb": "ruby",
    ".cs": "csharp",
    ".php": "php",
    ".sql": "sql",
    ".tf": "terraform",
    ".hcl": "hcl",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".json": "json",
    ".toml": "toml",
    ".env": "env",
    ".prisma": "prisma",
    ".graphql": "graphql",
}

TEST_PATH_PATTERNS = [
    "/tests/", "/test/", "/spec/", "/__tests__/",
    "\\tests\\", "\\test\\", "\\spec\\",
    ".test.", ".spec.", "_test.", "_spec.",
    "test_",
]

def run_ingest(cfg: ScanConfig) -> RepoManifest:
    """
    Stage 1 entry point.
    Traverses the repository, classifies every file, and returns a RepoManifest.
    """
    scan_root = str(Path(cfg.scan_root).resolve())
    ignore_patterns = load_dpdpignore(scan_root, cfg.dpdpignore_path)
    spec = pathspec.PathSpec.from_lines("gitignore", ignore_patterns)

    if cfg.debug:
        console.print(f"[dim]Stage 1 · scan_root={scan_root}[/dim]")
        console.print(f"[dim]Stage 1 · {len(ignore_patterns)} ignore patterns loaded[/dim]")

    all_files: list[FileRecord] = []
    skipped = 0
    total = 0

    for dirpath, dirnames, filenames in os.walk(scan_root):
        rel_dir = relative_posix(dirpath, scan_root)
        dirnames[:] = [
            d for d in dirnames
            if not spec.match_file(rel_dir + "/" + d + "/")
        ]

        for filename in filenames:
            abs_path = os.path.join(dirpath, filename)
            rel_path = relative_posix(abs_path, scan_root)
            total += 1

            if spec.match_file(rel_path):
                all_files.append(FileRecord(
                    path=rel_path,
                    bucket=Bucket.UNKNOWN,
                    skip_reason="dpdpignore",
                ))
                skipped += 1
                continue

            if is_binary_file(abs_path):
                all_files.append(FileRecord(
                    path=rel_path,
                    bucket=Bucket.UNKNOWN,
                    skip_reason="binary_file",
                ))
                skipped += 1
                continue

            ext = Path(filename).suffix.lower()
            language = EXTENSION_TO_LANGUAGE.get(ext)

            bucket, extra_buckets = classify_bucket(rel_path, filename, ext)

            is_test = any(pat in rel_path.replace("\\", "/") for pat in TEST_PATH_PATTERNS)

            try:
                size = os.path.getsize(abs_path)
            except OSError:
                size = 0

            rec = FileRecord(
                path=rel_path,
                bucket=bucket,
                extra_buckets=extra_buckets,
                language=language,
                size_bytes=size,
                is_test_file=is_test,
            )
            all_files.append(rec)

            if cfg.debug:
                console.print(
                    f"[dim]  {rel_path} → {bucket.value}"
                    f"{'  [TEST]' if is_test else ''}[/dim]"
                )

    accepted = [f for f in all_files if not f.is_skipped]
    stacks = detect_stacks(scan_root, accepted, cfg.debug)

    if cfg.debug:
        for s in stacks:
            console.print(
                f"[dim]  Stack detected: {s.framework} / {s.language} "
                f"(from {s.detected_from})[/dim]"
            )

    return RepoManifest(
        scan_root=scan_root,
        stacks=stacks,
        files=all_files,
        skipped_count=skipped,
        total_scanned=total,
    )
