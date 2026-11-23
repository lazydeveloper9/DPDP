"""
Canonical Pydantic v2 schemas for CS-01 2D + 3D Personal Data-Flow & Leak Visualization.
========================================================================================
Serialisable data graph structure mapping collection, processing, storage, infra,
and egress sinks with attached DPDP compliance posture.
"""

from __future__ import annotations
from enum import Enum, IntEnum
from typing import Optional
from pydantic import BaseModel, Field

class LayerTier(IntEnum):
    COLLECTION = 0    # Frontend forms, client components, public entrypoints
    API_LOGIC = 1     # REST/GraphQL routes, controllers, middleware, response DTOs
    STORAGE = 2       # SQL tables, ORM models, local disk/upload directories, caches
    INFRA_CLOUD = 3   # Terraform/K8s/Docker resources, DB instances, buckets, log groups
    EGRESS_SINK = 4   # Application loggers, third-party analytics/webhooks, Shadow AI/LLM APIs, public static mounts

class FlowStatus(str, Enum):
    COMPLIANT = "compliant"
    UNCONSENTED_STORAGE = "unconsented_storage"
    PII_LEAK = "pii_leak"
    MISCONFIGURED_CONTROL = "misconfigured_control"
    INFORMATIONAL = "informational"

class GraphNodeType(str, Enum):
    FORM = "form"
    CLIENT_COMPONENT = "client_component"
    ROUTE = "route"
    DTO = "dto"
    TABLE = "table"
    DISK = "disk"
    CLOUD_RESOURCE = "cloud_resource"
    LOGGER = "logger"
    THIRD_PARTY = "third_party"
    STATIC_MOUNT = "static_mount"

class GraphEdgeFlowType(str, Enum):
    NORMAL_FLOW = "normal_flow"
    UNCONSENTED_STORAGE = "unconsented_storage"
    PII_LEAK = "pii_leak"
    CROSS_BORDER_EGRESS = "cross_border_egress"

class ControlChecklist(BaseModel):
    auth_checked: Optional[bool] = None
    ownership_checked: Optional[bool] = None
    consent_checked: Optional[bool] = None
    encrypted: Optional[bool] = None
    retention_defined: Optional[bool] = None

class GraphNode(BaseModel):
    id: str
    label: str
    layer: LayerTier
    node_type: GraphNodeType
    file_path: Optional[str] = None
    start_line: Optional[int] = None
    end_line: Optional[int] = None
    status: FlowStatus = FlowStatus.INFORMATIONAL
    pii_types: list[str] = Field(default_factory=list)
    controls: ControlChecklist = Field(default_factory=ControlChecklist)
    finding_ids: list[str] = Field(default_factory=list)
    group_key: Optional[str] = None  # Directory or module path for anti-hairball clustering

class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    flow_type: GraphEdgeFlowType = GraphEdgeFlowType.NORMAL_FLOW
    pii_types: list[str] = Field(default_factory=list)
    consent_verified: Optional[bool] = None
    encrypted: Optional[bool] = None
    severity: Optional[str] = None
    dpdp_provisions: list[str] = Field(default_factory=list)
    penalty_ceiling: Optional[str] = None
    finding_ids: list[str] = Field(default_factory=list)
    evidence_summary: str = ""

class GraphSummaryMetrics(BaseModel):
    total_nodes: int = 0
    total_edges: int = 0
    leak_edges: int = 0
    unconsented_storage_edges: int = 0
    compliant_edges: int = 0
    active_layers: list[str] = Field(default_factory=list)
    max_penalty_engaged: Optional[str] = None

class DataFlowGraph(BaseModel):
    repo_name: str
    commit_sha: Optional[str] = None
    generated_at: str
    summary_metrics: GraphSummaryMetrics = Field(default_factory=GraphSummaryMetrics)
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)
