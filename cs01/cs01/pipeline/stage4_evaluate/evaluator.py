"""
Pipeline Stage 4 — Evaluate DPDP Rules & Cross-File Checks
===========================================================
Entry point: run_evaluate(flow_graph, pii_hits, model, cfg) -> list[RawFinding]

Coordinates:
  - Pass A: Local rules (AST flows, hardcoded PII, unencrypted schemas, insecure IaC/env)
  - Pass B: Cross-file assertions (whole-repo inventory gaps: consent withdrawal, age-gates, retention)
"""

from __future__ import annotations
from cs01.models import (
    FlowGraph, PiiHitList, RepoModel, RawFinding, ScanConfig,
)
from .pass_a_engine import evaluate_pass_a
from .pass_b_engine import evaluate_pass_b


def run_evaluate(
    flow_graph: FlowGraph,
    pii_hits: PiiHitList,
    model: RepoModel,
    cfg: ScanConfig,
) -> list[RawFinding]:
    """Execute Pass A, Pass B, and optional Opengrep/Semgrep rule evaluation."""
    findings: list[RawFinding] = []

    # 1. Native AST Pass A evaluation (if tree_sitter enabled)
    if cfg.engine.tree_sitter:
        findings.extend(evaluate_pass_a(flow_graph, pii_hits, model, cfg))

    # 2. Native Pass B evaluation (whole-repo cross-file assertions)
    findings.extend(evaluate_pass_b(model, cfg))

    # 3. Optional Opengrep / Semgrep subprocess bridge
    if cfg.engine.opengrep:
        from cs01.pipeline.stage3_detect.opengrep_bridge import OpengrepBridge
        bridge = OpengrepBridge()
        opengrep_findings = bridge.run_scan(cfg.scan_root, cfg)
        findings.extend(opengrep_findings)

    return findings
