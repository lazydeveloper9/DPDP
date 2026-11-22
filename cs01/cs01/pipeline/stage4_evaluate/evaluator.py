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
    """Execute Pass A and Pass B rule evaluation."""
    pass_a_findings = evaluate_pass_a(flow_graph, pii_hits, model, cfg)
    pass_b_findings = evaluate_pass_b(model, cfg)
    return pass_a_findings + pass_b_findings
