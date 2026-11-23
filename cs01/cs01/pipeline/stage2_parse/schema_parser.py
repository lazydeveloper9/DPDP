"""
Stage 2 Database Schema & ORM Parser
====================================
Extracts normalized SchemaRecord instances from:
  1. SQL DDL migrations and schema files (.sql) via sqlglot
  2. Prisma schema files (.prisma)
  3. SQLAlchemy model files (.py)
  4. Mongoose schema files (.js, .ts)
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

import sqlglot
from sqlglot import exp

from cs01.models import SchemaRecord

ENCRYPTION_KEYWORDS = re.compile(r"(encrypt|cipher|kms|pgp|vault|aes|masked)", re.IGNORECASE)
RETENTION_KEYWORDS = re.compile(r"(retention|retain|purge|ttl|expire|expiry|delete_after)", re.IGNORECASE)

def parse_sql_ddl(abs_path: Path, rel_path: str) -> list[SchemaRecord]:
    """Parse SQL DDL files using sqlglot across common dialects."""
    records: list[SchemaRecord] = []
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return records

    try:
        expressions = sqlglot.parse(content)
    except Exception:
        try:
            expressions = sqlglot.parse(content, read="postgres")
        except Exception:
            return records

    for expression in expressions:
        if not expression:
            continue

        if isinstance(expression, exp.Create):
            table_name = ""
            if isinstance(expression.this, exp.Schema):
                table_name = expression.this.this.name if expression.this.this else "unknown"
            elif expression.this:
                table_name = getattr(expression.this, "name", "unknown")

            schema = expression.find(exp.Schema)
            if not schema:
                continue

            for col_def in schema.find_all(exp.ColumnDef):
                col_name = col_def.this.name if col_def.this else "unknown"
                col_type = col_def.kind.sql() if col_def.kind else "UNKNOWN"
                
                constraints: list[str] = []
                is_nullable = True
                has_encryption = False
                has_retention = False

                for constraint in col_def.find_all(exp.ColumnConstraint):
                    c_sql = constraint.sql().upper()
                    constraints.append(c_sql)
                    if "NOT NULL" in c_sql:
                        is_nullable = False

                full_col_sql = col_def.sql()
                if ENCRYPTION_KEYWORDS.search(full_col_sql):
                    has_encryption = True
                if RETENTION_KEYWORDS.search(full_col_sql):
                    has_retention = True

                records.append(
                    SchemaRecord(
                        source_orm="sql_ddl",
                        source_file=rel_path,
                        table_or_model=table_name or "unknown",
                        column_or_field=col_name,
                        data_type=col_type,
                        is_nullable=is_nullable,
                        has_encryption_marker=has_encryption,
                        has_retention_comment=has_retention,
                        constraints=constraints,
                    )
                )

    return records

def parse_prisma_schema(abs_path: Path, rel_path: str) -> list[SchemaRecord]:
    """Parse Prisma schema models."""
    records: list[SchemaRecord] = []
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return records

    model_regex = re.compile(r"model\s+(\w+)\s*\{([^}]+)\}", re.MULTILINE)
    field_regex = re.compile(r"^\s*(\w+)\s+([A-Za-z0-9_?\[\]]+)(.*)$", re.MULTILINE)

    for m in model_regex.finditer(content):
        model_name = m.group(1)
        body = m.group(2)

        for line_idx, line in enumerate(body.splitlines(), start=1):
            line_str = line.strip()
            if not line_str or line_str.startswith("//") or line_str.startswith("@@"):
                continue

            match = field_regex.match(line)
            if match:
                field_name = match.group(1)
                field_type = match.group(2)
                attrs = match.group(3)

                is_nullable = "?" in field_type
                has_encryption = bool(ENCRYPTION_KEYWORDS.search(attrs) or ENCRYPTION_KEYWORDS.search(line_str))
                has_retention = bool(RETENTION_KEYWORDS.search(attrs) or RETENTION_KEYWORDS.search(line_str))

                records.append(
                    SchemaRecord(
                        source_orm="prisma",
                        source_file=rel_path,
                        table_or_model=model_name,
                        column_or_field=field_name,
                        data_type=field_type.replace("?", ""),
                        is_nullable=is_nullable,
                        has_encryption_marker=has_encryption,
                        has_retention_comment=has_retention,
                        constraints=[attrs.strip()] if attrs.strip() else [],
                        line=line_idx,
                    )
                )

    return records

def parse_sqlalchemy_models(abs_path: Path, rel_path: str) -> list[SchemaRecord]:
    """Parse SQLAlchemy models in Python source files."""
    records: list[SchemaRecord] = []
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return records

    class_pattern = re.compile(r"^class\s+(\w+)\s*\([^)]*\):")
    col_pattern = re.compile(
        r"^\s*(\w+)\s*=\s*(?:db\.)?Column\s*\((.*)\)\s*$"
    )
    mapped_col_pattern = re.compile(
        r"^\s*(\w+)\s*:\s*Mapped\[([^\]]+)\]\s*=\s*mapped_column\s*\((.*)\)\s*$"
    )

    current_class = "UnknownModel"
    for line_idx, line in enumerate(content.splitlines(), start=1):
        c_match = class_pattern.match(line)
        if c_match:
            current_class = c_match.group(1)
            continue

        m1 = col_pattern.match(line)
        if m1:
            col_name = m1.group(1)
            args = m1.group(2)
            dtype = args.split(",")[0].strip()
            is_nullable = "nullable=False" not in args
            has_enc = bool(ENCRYPTION_KEYWORDS.search(args))
            has_ret = bool(RETENTION_KEYWORDS.search(args))

            records.append(
                SchemaRecord(
                    source_orm="sqlalchemy",
                    source_file=rel_path,
                    table_or_model=current_class,
                    column_or_field=col_name,
                    data_type=dtype,
                    is_nullable=is_nullable,
                    has_encryption_marker=has_enc,
                    has_retention_comment=has_ret,
                    line=line_idx,
                )
            )
            continue

        m2 = mapped_col_pattern.match(line)
        if m2:
            col_name = m2.group(1)
            dtype = m2.group(2).strip()
            args = m2.group(3)
            is_nullable = "Optional[" in dtype or "nullable=False" not in args
            has_enc = bool(ENCRYPTION_KEYWORDS.search(args))
            has_ret = bool(RETENTION_KEYWORDS.search(args))

            records.append(
                SchemaRecord(
                    source_orm="sqlalchemy",
                    source_file=rel_path,
                    table_or_model=current_class,
                    column_or_field=col_name,
                    data_type=dtype,
                    is_nullable=is_nullable,
                    has_encryption_marker=has_enc,
                    has_retention_comment=has_ret,
                    line=line_idx,
                )
            )

    return records

def parse_mongoose_schema(abs_path: Path, rel_path: str) -> list[SchemaRecord]:
    """Parse Mongoose schemas in JS/TS files."""
    records: list[SchemaRecord] = []
    try:
        content = abs_path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return records

    schema_block_pattern = re.compile(
        r"(?:const|var|let)\s+(\w+)\s*=\s*new\s+(?:mongoose\.)?Schema\s*\(\s*\{([^;]+)\}\s*\)",
        re.MULTILINE,
    )
    field_pattern = re.compile(
        r"^\s*(\w+)\s*:\s*(?:\{[^}]*type\s*:\s*([A-Za-z0-9_]+)[^}]*\}|([A-Za-z0-9_]+))",
        re.MULTILINE,
    )

    for m in schema_block_pattern.finditer(content):
        schema_name = m.group(1)
        body = m.group(2)

        for line in body.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("//"):
                continue

            fm = field_pattern.match(line_str)
            if fm:
                field_name = fm.group(1)
                field_type = fm.group(2) or fm.group(3) or "Mixed"
                has_enc = bool(ENCRYPTION_KEYWORDS.search(line_str))
                has_ret = bool(RETENTION_KEYWORDS.search(line_str))

                records.append(
                    SchemaRecord(
                        source_orm="mongoose",
                        source_file=rel_path,
                        table_or_model=schema_name,
                        column_or_field=field_name,
                        data_type=field_type,
                        is_nullable=True,
                        has_encryption_marker=has_enc,
                        has_retention_comment=has_ret,
                    )
                )

    return records

def parse_db_schema(abs_path: Path, rel_path: str) -> list[SchemaRecord]:
    """Dispatch file to the appropriate schema/ORM parser."""
    name = abs_path.name.lower()
    if name.endswith(".sql"):
        return parse_sql_ddl(abs_path, rel_path)
    elif name.endswith(".prisma"):
        return parse_prisma_schema(abs_path, rel_path)
    elif name.endswith(".py"):
        return parse_sqlalchemy_models(abs_path, rel_path)
    elif name.endswith(".js") or name.endswith(".ts"):
        return parse_mongoose_schema(abs_path, rel_path)
    return []
