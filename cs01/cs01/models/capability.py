"""
cs01.models.capability — Base Product Capability & Data-Flow Inventory Models.
==============================================================================
Provides structured data contracts for:
1. Stack capabilities (frameworks, entrypoints, workers, databases, cloud).
2. Personal data inventory (PII categories, fields, storage, egress, encryption).
3. Implemented security/privacy controls.
4. Missing required controls calculated from the capability gap.
"""

from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class StackCapabilities(BaseModel):
    """Discovered application stack components and runtime entrypoints."""
    languages: list[str] = Field(default_factory=list)
    frameworks: list[str] = Field(default_factory=list)
    entrypoints: list[str] = Field(default_factory=list)
    background_workers: list[str] = Field(default_factory=list)
    database_engines: list[str] = Field(default_factory=list)
    cloud_providers: list[str] = Field(default_factory=list)


class PersonalDataInventoryItem(BaseModel):
    """An itemized record of personal data collected, stored, or processed."""
    category: str  # National Identity, Financial, Health, Contact, Children, Demographic, Credentials
    field_or_param: str
    location_file: str
    location_line: Optional[int] = None
    pii_type: str
    is_stored: bool = False
    is_transmitted_externally: bool = False
    is_logged: bool = False
    is_encrypted: bool = False


class ImplementedControl(BaseModel):
    """A detected compliance or security control in the codebase."""
    control_type: str  # e.g. AUTH_MIDDLEWARE, ENCRYPTION_REST, AGE_GATE, CONSENT_LEDGER, ERASURE_ROUTE, RETENTION_PURGE, BREACH_TELEMETRY, DPO_CONTACT
    file: str
    line: Optional[int] = None
    evidence: str


class MissingControl(BaseModel):
    """A required statutory control that is absent given the personal data processed."""
    control_type: str
    required_by_rule: str  # e.g. Rule 8(2), Rule 10, Rule 14(3)
    dpdp_section: str      # e.g. §8(7), §9, §12(3)
    severity: str          # CRITICAL, HIGH, MEDIUM, LOW
    reason: str


class ProductCapabilityReport(BaseModel):
    """
    Comprehensive Base Product Capability & Data-Flow Inventory for the audited target.
    Produced before rule evaluation to provide grounding for compliance assertions.
    """
    target_path: str
    stack: StackCapabilities = Field(default_factory=StackCapabilities)
    pii_inventory: list[PersonalDataInventoryItem] = Field(default_factory=list)
    has_personal_data: bool = False
    has_children_data: bool = False
    has_health_data: bool = False
    has_financial_data: bool = False
    implemented_controls: list[ImplementedControl] = Field(default_factory=list)
    missing_controls: list[MissingControl] = Field(default_factory=list)
