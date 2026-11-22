"""
Pipeline Stage 3 — Detect Personal Data & Trace Flows
======================================================
Entry point: run_detect(model, cfg) -> tuple[FlowGraph, PiiHitList]

Executes:
  1. Indian PII Taxonomy Detection (with Verhoeff, Luhn, NPCI validation)
  2. Source-Sink-Guard Intra-Procedural Taint Flow Graph construction
"""

from __future__ import annotations
from cs01.models import RepoModel, FlowGraph, PiiHitList, ScanConfig
from .pii_detector import detect_pii
from .flow_tracer import trace_flows


def run_detect(model: RepoModel, cfg: ScanConfig) -> tuple[FlowGraph, PiiHitList]:
    """Stage 3 execution: detect PII hits and build source-sink-guard flow graph."""
    pii_hits = detect_pii(model, cfg)
    flow_graph = trace_flows(model, pii_hits, cfg)
    return flow_graph, pii_hits
