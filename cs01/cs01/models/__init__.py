"""
cs01.models — Shared Pydantic data models for the 6-stage pipeline.

Every pipeline stage communicates ONLY through these typed models.
No stage imports from another stage's implementation module.

Serialisation contract: every model must be JSON-serialisable via
  model.model_dump(mode="json")
and reconstructable via
  Model.model_validate(json_data)
"""

from .repo_manifest import RepoManifest, FileRecord, Bucket, StackProfile
from .repo_model import RepoModel, SchemaRecord, IacTree, EnvVar, AstFileRecord
from .flow_graph import (
    FlowGraph, PiiHitList, PiiHit, PiiType, FileRole,
    DataSource, DataSink, DataGuard, FlowEdge,
    SourceType, SinkType, GuardType,
)
from .raw_finding import RawFinding, PassType, Severity
from .scored_finding import (
    ScoredFinding, ScoredFindingBundle, DpdpReadinessScore,
    ExposureContext, PillarScore,
)
from .scan_config import (
    ScanConfig, EngineConfig, AiConfig, BonusConfig,
    ApprovedProcessor, ThirdScheduleFlags,
)
from .graph import (
    LayerTier, FlowStatus, GraphNodeType, GraphEdgeFlowType,
    ControlChecklist, GraphNode, GraphEdge, GraphSummaryMetrics, DataFlowGraph,
)
from .capability import (
    StackCapabilities, PersonalDataInventoryItem,
    ImplementedControl, MissingControl, ProductCapabilityReport,
)

__all__ = [
    "RepoManifest", "FileRecord", "Bucket", "StackProfile",
    "RepoModel", "SchemaRecord", "IacTree", "EnvVar", "AstFileRecord",
    "FlowGraph", "PiiHitList", "PiiHit", "PiiType", "FileRole",
    "DataSource", "DataSink", "DataGuard", "FlowEdge",
    "SourceType", "SinkType", "GuardType",
    "RawFinding", "PassType", "Severity",
    "ScoredFinding", "ScoredFindingBundle", "DpdpReadinessScore",
    "ExposureContext", "PillarScore",
    "ScanConfig", "EngineConfig", "AiConfig", "BonusConfig",
    "ApprovedProcessor", "ThirdScheduleFlags",
    "LayerTier", "FlowStatus", "GraphNodeType", "GraphEdgeFlowType",
    "ControlChecklist", "GraphNode", "GraphEdge", "GraphSummaryMetrics", "DataFlowGraph",
    "StackCapabilities", "PersonalDataInventoryItem",
    "ImplementedControl", "MissingControl", "ProductCapabilityReport",
]
