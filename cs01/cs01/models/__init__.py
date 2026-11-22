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
from .flow_graph import FlowGraph, PiiHitList, PiiHit, DataSource, DataSink, DataGuard, FlowEdge
from .raw_finding import RawFinding, PassType, Severity
from .scored_finding import ScoredFinding, ScoredFindingBundle, DpdpReadinessScore
from .scan_config import ScanConfig

__all__ = [
    # Stage 1
    "RepoManifest", "FileRecord", "Bucket", "StackProfile",
    # Stage 2
    "RepoModel", "SchemaRecord", "IacTree", "EnvVar", "AstFileRecord",
    # Stage 3
    "FlowGraph", "PiiHitList", "PiiHit", "DataSource", "DataSink", "DataGuard", "FlowEdge",
    # Stage 4
    "RawFinding", "PassType", "Severity",
    # Stage 5
    "ScoredFinding", "ScoredFindingBundle", "DpdpReadinessScore",
    # Config
    "ScanConfig",
]
