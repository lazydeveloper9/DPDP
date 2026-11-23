"""
Pipeline Stage 4 — Evaluate DPDP Rules & Cross-File Checks
===========================================================
Entry point: run_evaluate(flow_graph, pii_hits, model, cfg) -> list[RawFinding]

Coordinates:
  - Pass A: Local rules (AST flows, hardcoded PII, unencrypted schemas, insecure IaC/env)
  - Pass B: Cross-file assertions (whole-repo inventory gaps: consent withdrawal, age-gates, retention)
"""

from __future__ import annotations
from typing import Optional
from cs01.models import (
    FlowGraph, PiiHitList, RepoModel, RawFinding, ScanConfig, ProductCapabilityReport,
)
from .pass_a_engine import evaluate_pass_a
from .pass_b_engine import evaluate_pass_b
from .correlator import correlate_findings

def run_evaluate(
    flow_graph: FlowGraph,
    pii_hits: PiiHitList,
    model: RepoModel,
    cfg: ScanConfig,
    capability_report: Optional[ProductCapabilityReport] = None,
) -> list[RawFinding]:
    """Execute Pass A, Pass B, and optional Opengrep/Semgrep rule evaluation."""
    findings: list[RawFinding] = []

    if capability_report is None:
        from cs01.pipeline.stage3_detect.capability_detector import detect_product_capabilities
        capability_report = detect_product_capabilities(model, flow_graph, pii_hits, cfg)

    if cfg.engine.tree_sitter:
        findings.extend(evaluate_pass_a(flow_graph, pii_hits, model, cfg))

    findings.extend(evaluate_pass_b(model, cfg, capability_report=capability_report))

    if cfg.engine.opengrep:
        from cs01.pipeline.stage3_detect.opengrep_bridge import OpengrepBridge
        bridge = OpengrepBridge()
        opengrep_findings = bridge.run_scan(cfg.scan_root, cfg)
        findings.extend(opengrep_findings)

    return correlate_findings(findings, flow_graph, pii_hits, model, cfg, capability_report=capability_report)
