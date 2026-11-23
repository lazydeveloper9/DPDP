"""
Stage 3 output model: FlowGraph + PiiHitList
Source-sink-guard taint graph and raw PII matches.
"""

from __future__ import annotations
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field

class FileRole(str, Enum):
    """Influences default severity of PII hits found in this file context."""
    PRODUCTION = "production"
    TEST = "test"
    FIXTURE = "fixture"
    DOCS = "docs"
    CONFIG = "config"

class PiiType(str, Enum):
    """All recognised Indian PII identifier types."""
    AADHAAR = "AADHAAR"
    PAN = "PAN"
    GSTIN = "GSTIN"
    PASSPORT = "PASSPORT"
    VOTER_ID = "VOTER_ID"
    UPI_HANDLE = "UPI_HANDLE"
    IFSC = "IFSC"
    MOBILE = "MOBILE"
    EMAIL = "EMAIL"
    IP_ADDRESS = "IP_ADDRESS"
    GEOLOCATION = "GEOLOCATION"
    DEVICE_ID = "DEVICE_ID"
    DATE_OF_BIRTH = "DATE_OF_BIRTH"
    BIOMETRIC = "BIOMETRIC"
    FINANCIAL = "FINANCIAL"
    DRIVING_LICENCE = "DRIVING_LICENCE"
    ABHA_HEALTH_ID = "ABHA_HEALTH_ID"
    PAYMENT_CARD = "PAYMENT_CARD"

class PiiHit(BaseModel):
    """A single detected PII instance anywhere in the codebase."""
    id: str
    pii_type: PiiType
    file: str
    line: int
    col: int
    confidence: float
    file_role: FileRole
    value_sha256: str
    context_tokens: list[str] = Field(default_factory=list)
    validator_result: str = "not_validated"
    line_snippet: Optional[str] = None
class PiiHitList(BaseModel):
    """All PII hits detected across the full codebase."""
    hits: list[PiiHit] = Field(default_factory=list)

    def by_type(self, pii_type: PiiType) -> list[PiiHit]:
        return [h for h in self.hits if h.pii_type == pii_type]

    def production_hits(self) -> list[PiiHit]:
        return [h for h in self.hits if h.file_role == FileRole.PRODUCTION]

class SourceType(str, Enum):
    REQUEST_BODY = "request_body"
    QUERY_PARAM = "query_param"
    FORM_INPUT = "form_input"
    DB_READ = "db_read"
    API_RESPONSE_INBOUND = "api_response_inbound"

class SinkType(str, Enum):
    LOGGER = "logger"
    DB_WRITE = "db_write"
    HTTP_RESPONSE = "http_response"
    THIRD_PARTY_SDK = "third_party_sdk"
    FILE_WRITE = "file_write"

class GuardType(str, Enum):
    MASKING = "masking"
    ENCRYPTION = "encryption"
    AUTH_MIDDLEWARE = "auth_middleware"
    CONSENT_CHECK = "consent_check"
    REDACTION = "redaction"

class DataSource(BaseModel):
    id: str
    source_type: SourceType
    file: str
    line: int
    function_name: Optional[str] = None
    variable_name: Optional[str] = None
    pii_types_suspected: list[PiiType] = Field(default_factory=list)

class DataSink(BaseModel):
    id: str
    sink_type: SinkType
    file: str
    line: int
    function_name: Optional[str] = None
    call_expression: str = ""

class DataGuard(BaseModel):
    id: str
    guard_type: GuardType
    file: str
    line: int
    function_name: Optional[str] = None
    guard_function_name: str = ""

class FlowEdge(BaseModel):
    """
    A single taint flow path: source → (guard?) → sink.
    If guard_id is None, the flow is UNGUARDED — a potential violation.
    """
    id: str
    source_id: str
    sink_id: str
    guard_id: Optional[str] = None
    guard_type: Optional[GuardType] = None
    tainted_variables: list[str] = Field(default_factory=list)
    file: str
    function_name: Optional[str] = None
    is_unguarded: bool = True
    reachability: str = "REACHABLE_EXTERNAL"

    def model_post_init(self, __context: object) -> None:
        self.is_unguarded = self.guard_id is None

class FlowGraph(BaseModel):
    """
    Output of Pipeline Stage 3 — PII Detection & Flow Tracing.

    Contains the taint flow graph (sources, guards, sinks, edges)
    and all raw PII hits. Both are consumed by Stage 4.
    """
    sources: list[DataSource] = Field(default_factory=list)
    sinks: list[DataSink] = Field(default_factory=list)
    guards: list[DataGuard] = Field(default_factory=list)
    edges: list[FlowEdge] = Field(default_factory=list)

    def unguarded_edges(self) -> list[FlowEdge]:
        return [e for e in self.edges if e.is_unguarded]
