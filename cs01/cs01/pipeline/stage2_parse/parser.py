"""
Pipeline Stage 2 — Parse into Structured Representations
=========================================================
Entry point: run_parse(manifest, cfg) -> RepoModel

Orchestrates bucket-based parsers across worker threads:
  - Source ASTs (tree-sitter)
  - DB Schemas (sqlglot, SQLAlchemy, Prisma, Mongoose)
  - IaC & Containers (python-hcl2, ruamel.yaml, dockerfile-parse)
  - Secrets & Env (.env, JSON configs)
"""

from __future__ import annotations
import concurrent.futures
from pathlib import Path
from typing import Any

from rich.console import Console

from cs01.models import (
    RepoManifest, RepoModel, ScanConfig, Bucket,
    AstFileRecord, SchemaRecord, IacTree, EnvVar,
)
from .ast_parser import parse_source_ast
from .schema_parser import parse_db_schema
from .iac_parser import parse_iac_file
from .env_parser import parse_secrets_and_env

console = Console(stderr=True)


def _process_file(
    file_rec,
    scan_root_path: Path,
    cfg: ScanConfig,
) -> dict[str, Any]:
    """Parse a single file based on its bucket memberships."""
    abs_path = scan_root_path / file_rec.path
    rel_path = file_rec.path
    buckets = [file_rec.bucket] + file_rec.extra_buckets

    result: dict[str, Any] = {
        "ast": None,
        "schemas": [],
        "iac": [],
        "env_vars": [],
        "errors": [],
    }

    # 1. SECRETS
    if Bucket.SECRETS in buckets:
        try:
            evs = parse_secrets_and_env(abs_path, rel_path)
            result["env_vars"].extend(evs)
        except Exception as exc:
            result["errors"].append({"file": rel_path, "stage": "secrets", "error": str(exc)})

    # 2. DB_SCHEMA
    if Bucket.DB_SCHEMA in buckets:
        try:
            schemas = parse_db_schema(abs_path, rel_path)
            result["schemas"].extend(schemas)
        except Exception as exc:
            result["errors"].append({"file": rel_path, "stage": "schema", "error": str(exc)})

    # 3. INFRA
    if Bucket.INFRA in buckets:
        try:
            trees = parse_iac_file(abs_path, rel_path)
            result["iac"].extend(trees)
            for t in trees:
                if t.parse_error:
                    result["errors"].append({"file": rel_path, "stage": "iac", "error": t.parse_error})
        except Exception as exc:
            result["errors"].append({"file": rel_path, "stage": "iac", "error": str(exc)})

    # 4. FRONTEND / BACKEND (Source code AST)
    if (Bucket.FRONTEND in buckets or Bucket.BACKEND in buckets) and file_rec.language:
        try:
            ast_rec = parse_source_ast(abs_path, rel_path, file_rec.language)
            result["ast"] = ast_rec
            if ast_rec.parse_error:
                result["errors"].append({"file": rel_path, "stage": "ast", "error": ast_rec.parse_error})
        except Exception as exc:
            result["errors"].append({"file": rel_path, "stage": "ast", "error": str(exc)})

    return result


def run_parse(manifest: RepoManifest, cfg: ScanConfig) -> RepoModel:
    """
    Stage 2 entry point.
    Dispatches parsers in parallel across all accepted files in RepoManifest.
    """
    scan_root_path = Path(manifest.scan_root)
    accepted = manifest.accepted_files()

    ast_index: list[AstFileRecord] = []
    schema_records: list[SchemaRecord] = []
    iac_trees: list[IacTree] = []
    env_vars: list[EnvVar] = []
    parse_errors: list[dict] = []

    # Use ThreadPoolExecutor for I/O and tree-sitter parsing across files
    max_workers = min(16, max(4, len(accepted) // 4 + 1))
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(_process_file, f, scan_root_path, cfg): f
            for f in accepted
        }
        for future in concurrent.futures.as_completed(futures):
            res = future.result()
            if res["ast"]:
                ast_index.append(res["ast"])
            if res["schemas"]:
                schema_records.extend(res["schemas"])
            if res["iac"]:
                iac_trees.extend(res["iac"])
            if res["env_vars"]:
                env_vars.extend(res["env_vars"])
            if res["errors"]:
                parse_errors.extend(res["errors"])

    if cfg.debug and parse_errors:
        for err in parse_errors:
            console.print(f"[yellow]Stage 2 parse error in {err['file']}: {err['error']}[/yellow]")

    return RepoModel(
        ast_index=ast_index,
        schema_records=schema_records,
        iac_trees=iac_trees,
        env_vars=env_vars,
        parse_errors=parse_errors,
    )
