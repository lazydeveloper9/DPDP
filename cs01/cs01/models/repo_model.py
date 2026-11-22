"""
Stage 2 output model: RepoModel
Structured parsed representations of all source files.
"""

from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field


class AstFileRecord(BaseModel):
    """
    Lightweight AST summary for a single source file.
    Stores extracted structural nodes rather than the full raw tree
    to keep the model JSON-serialisable and compact.
    """
    path: str
    language: str
    parse_error: Optional[str] = None           # set if tree-sitter failed to parse
    functions: list[dict] = Field(default_factory=list)
    # Each function dict: {name, start_line, end_line, calls: [...], params: [...]}
    classes: list[dict] = Field(default_factory=list)
    imports: list[dict] = Field(default_factory=list)
    # {module, alias, line}
    assignments: list[dict] = Field(default_factory=list)
    # {name, value_snippet, line}
    string_literals: list[dict] = Field(default_factory=list)
    # {value, line, col} — for PII pre-filter in Stage 3
    decorators: list[dict] = Field(default_factory=list)
    # {name, args, target_function, line} — for route/auth detection


class SchemaRecord(BaseModel):
    """
    Normalised record for a database column/field from any ORM or DDL format.
    Produced by Stage 2 schema parsers (SQL DDL, SQLAlchemy, Prisma, Mongoose, Django ORM).
    """
    source_orm: str              # "sql_ddl" | "sqlalchemy" | "prisma" | "mongoose" | "django_orm"
    source_file: str
    table_or_model: str          # table name or ORM class/model name
    column_or_field: str         # column or field name
    data_type: str               # e.g. "VARCHAR(255)", "String", "str"
    is_nullable: bool = True
    has_encryption_marker: bool = False   # column-level encryption annotation/comment detected
    has_retention_comment: bool = False   # retention period documented in comment
    constraints: list[str] = Field(default_factory=list)  # e.g. ["NOT NULL", "UNIQUE"]
    line: Optional[int] = None


class IacTree(BaseModel):
    """
    Normalised key-value tree extracted from an IaC or container file.
    Preserves line numbers for every extracted attribute.
    """
    source_file: str
    file_type: str           # "terraform" | "kubernetes" | "dockerfile" | "docker_compose"
    resource_type: Optional[str] = None   # e.g. "aws_db_instance", "Deployment"
    resource_name: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    line_map: dict[str, int] = Field(default_factory=dict)  # attribute_key → line number
    parse_error: Optional[str] = None


class EnvVar(BaseModel):
    """
    A key-value pair extracted from .env or JSON config files.
    Raw values are NEVER stored — only the SHA-256 hash of the value.
    """
    key: str
    value_sha256: str           # SHA-256 hex digest of the value string
    value_length: int           # rough entropy signal (long values → potential secrets)
    source_file: str
    line: int
    is_potential_secret: bool = False   # high-entropy or matches secret patterns


class RepoModel(BaseModel):
    """
    Output of Pipeline Stage 2 — Parse into Structured Representations.

    Contains machine-queryable structured representations of all source files.
    This is the ONLY input to Stage 3 (and also read by Stage 4 for inventory).
    """
    ast_index: list[AstFileRecord] = Field(default_factory=list)
    schema_records: list[SchemaRecord] = Field(default_factory=list)
    iac_trees: list[IacTree] = Field(default_factory=list)
    env_vars: list[EnvVar] = Field(default_factory=list)
    parse_errors: list[dict] = Field(default_factory=list)
    # {file, stage, error} — partial scan errors; triggers exit code 3

    # Convenience accessors
    def ast_for_file(self, path: str) -> Optional[AstFileRecord]:
        for rec in self.ast_index:
            if rec.path == path:
                return rec
        return None

    def schemas_for_table(self, table: str) -> list[SchemaRecord]:
        return [s for s in self.schema_records if s.table_or_model.lower() == table.lower()]
