"""
cs01.ai.compliance_report_generator — Qwen 2.5 Coder 3B Compliance Report Generator
===================================================================================
Produces comprehensive, audit-grade Data Protection (DPDP) compliance reports
tailored for executive leadership, DPOs, and engineering teams.

Core Architecture:
  - Model: Qwen 2.5 Coder 3B (local zero-egress inference via Ollama / vLLM)
  - Data Privacy: Strict PII redaction and secret sanitization before inference
  - Structured Sections:
      1. Executive Summary
      2. Methodology
      3. Findings & Statutory Breach Analysis
      4. Recommendations & Remediation Roadmap
      5. Appendices (Statutory Schedule, RoPA, Rule 13 Digest)
"""

from __future__ import annotations
import json
import logging
import os
from pathlib import Path
import re
from typing import Callable, Optional

from cs01.models import ScoredFindingBundle, ScoredFinding, ScanConfig, Severity
from cs01.ai.client import LocalLLMClient

logger = logging.getLogger("cs01.compliance_report_generator")

REPORT_SYSTEM_PROMPT = """You are an elite Data Protection Officer (DPO) and Principal AppSec Compliance Architect specializing in India's Digital Personal Data Protection (DPDP) Act, 2023, DPDP Rules, 2025 (G.S.R. 846(E)), and CERT-In 2022 Cybersecurity Directions.

You are writing a comprehensive, authoritative DPDP Compliance Assessment Report.
Your analysis must adhere strictly to these principles:

1. STATUTORY PRECISION: Reference exact statutory sections:
   - §4–6 (Lawful Ground, Purpose Limitation, Notice & Affirmative Consent)
   - §8(2) (Approved Processors & Data Protection Agreements)
   - §8(3) & Rule 8 (Retention, 1-Year Log Audits, Overlap with CERT-In 180-day rule)
   - §8(5) & Rule 6 (Reasonable Security Safeguards — Encryption & Masking)
   - §8(6) & Rule 7 (Mandatory Breach Notification to Board & Data Principals)
   - §9 & Rules 10–12 (Children's & PwD Data: Verifiable Parental Consent, No Tracking)
   - §10 & Rule 13 (Significant Data Fiduciary Duties: DPA, DPIA, Independent Audits)
   - §11–14 (Data Principal Rights: Access, Correction, Erasure, Grievance Redressal)
   - §16 (Cross-Border Transfer Restrictions)
   - §33 Schedule (Statutory Penalty Bands: Up to ₹250 Cr, ₹200 Cr, ₹150 Cr, ₹50 Cr)

2. STRICT DATA PRIVACY & ZERO EGRESS:
   - Work exclusively with the verified audit metrics and sanitized snippets provided.
   - Never invent or hallucinate files, URLs, or secrets.
   - Maintain all redacted PII placeholders (e.g. [AADHAAR_1], [PAN_1], [PHONE_1]).

3. PRODUCTION-READY CODE FIXES:
   - Refactored code must be complete, idiomatic, and directly applicable.
   - Include clear "Before (Vulnerable)" vs "After (Remediated)" code blocks.
"""


def _sanitize_finding_for_ai(finding: ScoredFinding) -> dict:
    """Prepare a finding record for AI prompt synthesis with strict privacy sanitization."""
    snippet = finding.redacted_snippet or finding.snippet or ""
    # Strip any potential residual secrets
    clean_snippet = re.sub(r'(?i)(password|secret|key|token)\s*[:=]\s*["\'][^"\']+["\']', r'\1: "[SECRET_REDACTED]"', snippet)

    return {
        "rule_id": finding.rule_id,
        "severity": finding.severity.value,
        "dpdp_section": finding.dpdp_section,
        "dpdp_rule": finding.dpdp_rule,
        "penalty_band": finding.penalty_band,
        "file": finding.file or "Global Repository",
        "line": finding.line_start or 1,
        "message": finding.message,
        "code_snippet": clean_snippet[:500],
        "remediation_hint": finding.remediation,
    }


def generate_full_compliance_report(
    bundle: ScoredFindingBundle,
    client: Optional[LocalLLMClient] = None,
    cfg: Optional[ScanConfig] = None,
    on_token: Optional[Callable[[str], None]] = None,
) -> str:
    """
    Generate an authoritative 5-section DPDP Compliance Report using Qwen 2.5 Coder 3B.
    """
    if client is None:
        model_name = cfg.ai.model if cfg else "qwen2.5-coder:3b"
        endpoint = cfg.ai.endpoint if cfg else "http://localhost:11434"
        client = LocalLLMClient(model=model_name, endpoint=endpoint)

    client.resolve_model()

    # 1. Group and analyze findings by rule category
    rule_counts: dict[str, int] = {}
    rule_samples: dict[str, ScoredFinding] = {}
    for f in bundle.findings:
        rule_counts[f.rule_id] = rule_counts.get(f.rule_id, 0) + 1
        if f.rule_id not in rule_samples:
            rule_samples[f.rule_id] = f

    # Select representative samples for each distinct violation class (up to 6)
    representative_samples = []
    for rid, f in list(rule_samples.items())[:6]:
        sanitized = _sanitize_finding_for_ai(f)
        sanitized["total_occurrences_in_codebase"] = rule_counts[rid]
        representative_samples.append(sanitized)

    # 2. Extract metrics
    pillar_data = [
        {"pillar": p.label, "score": f"{p.score:.1f}/100", "status": "PASS" if p.score >= 80 else ("PARTIAL" if p.score >= 40 else "FAIL")}
        for p in bundle.readiness.pillars
    ]

    total_active = len(bundle.findings)
    crit_count = bundle.readiness.open_critical_count
    high_count = bundle.readiness.open_high_count
    med_count = sum(1 for f in bundle.findings if f.severity == Severity.MEDIUM)
    low_count = sum(1 for f in bundle.findings if f.severity == Severity.LOW)

    prompt = f"""Generate a Comprehensive DPDP Compliance Assessment Report for the target application using the following verified audit data:

TARGET METRICS:
- Target Application / Path: {bundle.scan_root}
- DPDP Readiness Score: {bundle.readiness.overall:.1f} / 100
- Score Capping Status: {'CAPPED (' + bundle.readiness.cap_reason + ')' if bundle.readiness.is_capped else 'UNCAPPED (Nominal)'}
- Highest Statutory Penalty Ceiling Engaged: {bundle.readiness.max_statutory_ceiling_engaged or 'None'}
- Finding Breakdown: Total Active: {total_active} | Critical: {crit_count} | High: {high_count} | Medium: {med_count} | Low: {low_count}
- Violation Distribution by Rule Category:
{json.dumps(rule_counts, indent=2)}

STATUTORY PILLAR READINESS:
{json.dumps(pillar_data, indent=2)}

REPRESENTATIVE VIOLATION SAMPLES FOR IN-DEPTH ANALYSIS:
{json.dumps(representative_samples, indent=2)}

GENERATE THE REPORT FOLLOWING THIS EXACT 5-SECTION STRUCTURE:

# Full-Stack DPDP Compliance Assessment Report

## 1. Executive Summary
- **Overall Posture**: High-level evaluation of the organization's DPDP posture, current readiness score ({bundle.readiness.overall:.1f}/100), and whether statutory score capping occurred.
- **Key Metrics Table**: Markdown table displaying Overall Score, Max Penalty Ceiling, Open Critical, Open High, and Total Unique findings.
- **Statutory Penalty Exposure**: Analysis of Section 33 penalty ceiling bands engaged. Note that under Section 33(2), actual penalties are adjudicated by the Data Protection Board of India based on gravity and mitigation.

## 2. Methodology & Regulatory Scope
- **Evaluation Pipeline**: Overview of the 6-stage AST parsing, source-sink-guard taint tracking, and deterministic Indian PII checksum validators (Verhoeff for Aadhaar, Luhn for PAN).
- **Statutory Baseline**: Legal frameworks evaluated (DPDP Act 2023, DPDP Rules 2025, CERT-In Directions 2022).
- **Zero-Egress Security Guarantee**: Confirmation that all static analysis and Qwen 2.5 Coder 3B synthesis were conducted 100% locally with zero cloud egress.

## 3. Findings & Statutory Breach Analysis
For EACH of the representative violation classes provided:
- **Finding ID & Rule Title**: Rule ID, Severity, and Total Occurrences in Codebase.
- **Statutory Citation & Penalty Ceiling**: Section, Rule, and Section 33 Schedule Ceiling.
- **Technical Code Walkthrough**: Explain the vulnerable snippet, file, and line from the provided sample.
- **Data Principal Blast Radius**: Real-world threat scenario and privacy impact on Indian citizens.
- **Production-Ready Code Fix**: Complete "Before vs. After" refactored code snippet.
- **Engineering Verification Plan**: Exact automated test or verification command.

## 4. Recommendations & Remediation Roadmap
- **Immediate P0 Hotfixes (24-48 Hours)**: Critical code changes for unmasked PII, broken encryption, and hardcoded literals.
- **P1 Architecture & Governance (Sprint Cycle)**: Consent ledger implementation, withdrawal mechanisms, retention schedulers.
- **CI/CD Quality Gate**: Enforcing automated pipeline thresholds (`fail-on: high`).

## 5. Appendices
- **Appendix A: Statutory Penalty Ceiling Reference Matrix** (Section 33 Schedule breakdown).
- **Appendix B: Record of Processing Activities (RoPA) Summary** (Categorized personal data flows).
- **Appendix C: Rule 13 Cryptographic Evidence Ledger Notice**.
"""

    return client.generate(prompt=prompt, system_prompt=REPORT_SYSTEM_PROMPT, on_token=on_token)
