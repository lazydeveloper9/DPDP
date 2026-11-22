"""
Stage 4 output model: RawFinding
A single DPDP violation finding before deduplication and scoring.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"       # used for PII in test/docs files


class PassType(str, Enum):
    A = "A"   # local rule (per file / per entity)
    B = "B"   # cross-file architectural assertion


class RawFinding(BaseModel):
    """
    A single DPDP violation emitted by the Stage 4 rule engine.
    One RawFinding per rule match — duplicates resolved in Stage 5.
    """
    id: str                                     # unique: f"{rule_id}:{file}:{line_start}"
    rule_id: str                                # e.g. "CODE-DPDP-001"
    pass_type: PassType

    # Location (None for cross-file Pass B findings that have no single location)
    file: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    # Evidence
    snippet: str = ""                           # redacted code snippet (PII replaced)
    matched_entity: Optional[str] = None        # table/column/resource name that triggered rule

    # Statutory mapping
    dpdp_section: str                           # e.g. "§8(5)"
    dpdp_rule: str                              # e.g. "Rule 6(1)(a)"
    penalty_band: str                           # e.g. "250_crore"

    # Classification
    severity: Severity
    engine: str = "tree-sitter"                 # "tree-sitter" | "opengrep" | "inventory"

    # Human-readable fields
    message: str
    remediation: str

    # Back-references
    contributing_pii_hit_ids: list[str] = Field(default_factory=list)
    contributing_flow_edge_ids: list[str] = Field(default_factory=list)
