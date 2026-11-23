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
    parse_error: Optional[str] = None
    functions: list[dict] = Field(default_factory=list)
    classes: list[dict] = Field(default_factory=list)
    imports: list[dict] = Field(default_factory=list)
    assignments: list[dict] = Field(default_factory=list)
    string_literals: list[dict] = Field(default_factory=list)
    decorators: list[dict] = Field(default_factory=list)
class SchemaRecord(BaseModel):
    """
    Normalised record for a database column/field from any ORM or DDL format.
    Produced by Stage 2 schema parsers (SQL DDL, SQLAlchemy, Prisma, Mongoose, Django ORM).
    """
    source_orm: str
    source_file: str
    table_or_model: str
    column_or_field: str
    data_type: str
    is_nullable: bool = True
    has_encryption_marker: bool = False
    has_retention_comment: bool = False
    constraints: list[str] = Field(default_factory=list)
    line: Optional[int] = None

class IacTree(BaseModel):
    """
    Normalised key-value tree extracted from an IaC or container file.
    Preserves line numbers for every extracted attribute.
    """
    source_file: str
    file_type: str
    resource_type: Optional[str] = None
    resource_name: Optional[str] = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    line_map: dict[str, int] = Field(default_factory=dict)
    parse_error: Optional[str] = None

class EnvVar(BaseModel):
    """
    A key-value pair extracted from .env or JSON config files.
    Raw values are NEVER stored — only the SHA-256 hash of the value.
    """
    key: str
    value_sha256: str
    value_length: int
    source_file: str
    line: int
    is_potential_secret: bool = False

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
    def ast_for_file(self, path: str) -> Optional[AstFileRecord]:
        for rec in self.ast_index:
            if rec.path == path:
                return rec
        return None

    def schemas_for_table(self, table: str) -> list[SchemaRecord]:
        return [s for s in self.schema_records if s.table_or_model.lower() == table.lower()]
