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
    INFO = "INFO"

class PassType(str, Enum):
    A = "A"
    B = "B"

class RawFinding(BaseModel):
    """
    A single DPDP violation emitted by the Stage 4 rule engine.
    One RawFinding per rule match — duplicates resolved in Stage 5.
    """
    id: str
    rule_id: str
    pass_type: PassType

    file: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None

    snippet: str = ""
    matched_entity: Optional[str] = None

    dpdp_section: str
    dpdp_rule: str
    penalty_band: str

    severity: Severity
    engine: str = "tree-sitter"

    message: str
    remediation: str

    contributing_pii_hit_ids: list[str] = Field(default_factory=list)
    contributing_flow_edge_ids: list[str] = Field(default_factory=list)
    related_finding_ids: list[str] = Field(default_factory=list)
    correlation_chain: list[str] = Field(default_factory=list)
    compensating_controls: list[str] = Field(default_factory=list)
