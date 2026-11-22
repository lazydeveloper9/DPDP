"""
cs01.ai.narrator — Generates DPO Executive Briefs and in-depth violation remediations
using local Qwen 2.5 Coder under strict DPDP compliance and accuracy rules.
"""

from __future__ import annotations
import json
from typing import Callable, Optional
from cs01.models import ScoredFindingBundle, ScoredFinding
from .client import LocalLLMClient

DPO_SYSTEM_PROMPT = """You are a senior Data Protection Officer (DPO) and Principal Security Auditor specializing in India's Digital Personal Data Protection Act, 2023 (DPDP) and DPDP Rules, 2025.

You must strictly adhere to the following 7 Core Rules for Compliance Reporting:

1. MANDATORY EXACT CODE CITATION: For every vulnerability, always quote the exact file path, line number, and offending code snippet. Never describe a vulnerability without showing the code.
2. DETAILED MECHANICS EXPLANATION: Clearly explain the line-by-line mechanics of how the code operates and why it creates a statutory compliance failure.
3. STATUTORY GROUNDING: Explicitly cite the governing DPDP Section (§8(5) for technical safeguards, §8(6) for breach notification, §9 for children/PwD protection, §10 for SDF duties, §6/Rule 3 for consent, Rule 6(1)(e)/Rule 8 for retention) and the statutory maximum penalty ceiling.
4. "BEFORE VS AFTER" REFACTORED CODE: Provide the exact, production-ready drop-in replacement code fix demonstrating proper masking, column encryption, or architectural routing.
5. TWO-TIER AUDIENCE FRAMING: Structure each finding with:
   - Executive Impact (plain English for DPO / Leadership)
   - Technical Root Cause & Fix (for Developers)
6. ZERO HALLUCINATION & REDACTION INTEGRITY: Use only verified findings from the audit. Never hallucinate files. Preserve all redacted PII placeholders (e.g. [AADHAAR_1], [PAN_1]).
7. VERIFICATION STEP: Provide concrete steps for developers to verify the fix works.
"""


def generate_executive_dpo_brief(
    bundle: ScoredFindingBundle,
    client: LocalLLMClient,
    on_token: Optional[Callable[[str], None]] = None,
) -> str:
    """Generate a structured, authoritative Executive DPO Compliance Brief for a scan bundle."""
    top_findings = []
    for f in bundle.findings[:4]:
        top_findings.append({
            "rule_id": f.rule_id,
            "severity": f.severity.value,
            "dpdp_section": f.dpdp_section,
            "penalty_band": f.penalty_band,
            "file": f.file,
            "line": f.line_start,
            "message": f.message,
            "code_snippet": f.redacted_snippet or f.snippet,
            "remediation_hint": f.remediation,
        })

    pillar_summary = [
        {"pillar": p.label, "score": f"{p.score:.1f}/100"}
        for p in bundle.readiness.pillars[:6]
    ]

    prompt = f"""Generate an Executive DPDP Compliance Brief for our software application following the Core Reporting Rules:

Audit Metrics:
- Target Codebase: {bundle.scan_root}
- DPDP Readiness Score: {bundle.readiness.overall:.1f}/100 (Score Capped: {bundle.readiness.is_capped} - Reason: {bundle.readiness.cap_reason or 'None'})
- Maximum Statutory Penalty Ceiling Engaged: {bundle.readiness.max_statutory_ceiling_engaged or 'None'}
- Open Critical Findings: {bundle.readiness.open_critical_count} | Open High: {bundle.readiness.open_high_count} | Total Unique: {len(bundle.findings)}

Pillar Score Breakdown:
{json.dumps(pillar_summary, indent=2)}

Priority Violations to Analyze:
{json.dumps(top_findings, indent=2)}

Format with:
# Executive Summary & Risk Posture
Briefly evaluate the overall readiness score, compliance posture, and whether dynamic capping was triggered.

## Statutory Penalty Ceiling Exposure
Detail the maximum exposure ceilings engaged (e.g. §8(5) ₹250 Cr, §9 ₹200 Cr) and note that actual penalties under §33(2) are discretionary.

## High-Priority Vulnerability Deep-Dive
For each priority violation:
- **Finding**: Rule ID & Severity
- **Location & Code**: Quote the file, line, and code snippet.
- **Why It Fails**: Plain-English explanation of how the code operates and why it mishandles personal data.
- **Production-Ready Fix**: The exact refactored code snippet.

## Immediate Action Roadmap
Bulleted checklist of prioritized remediation tasks for the engineering team.
"""

    return client.generate(prompt=prompt, system_prompt=DPO_SYSTEM_PROMPT, on_token=on_token)


def explain_finding_in_depth(
    finding: ScoredFinding,
    client: LocalLLMClient,
    on_token: Optional[Callable[[str], None]] = None,
) -> str:
    """Generate an in-depth developer root-cause, explanation, and code fix for a specific finding."""
    prompt = f"""Generate an in-depth developer compliance briefing and production code fix for the following violation following the Core Reporting Rules:

Rule ID: {finding.rule_id}
Severity: {finding.severity.value}
Statutory Citation: Section {finding.dpdp_section} · Rule {finding.dpdp_rule}
Ceiling: {finding.statutory_ceiling_display}
Location: {finding.file}:{finding.line_start}
Violation Summary: {finding.message}

Vulnerable Code Snippet:
```
{finding.redacted_snippet or finding.snippet}
```

Standard Remediation Recommendation:
{finding.remediation}

Structure your response into:
1. **Statutory Non-Compliance & Legal Risk**: Explain the specific requirement under DPDP §{finding.dpdp_section} and the statutory penalty ceiling.
2. **Code Walkthrough & Failure Mechanics**: Explain what this specific code does, how data flows through it, and why it is vulnerable (e.g., plaintext exfiltration, unencrypted storage, or missing guardrails).
3. **Production-Ready Refactored Fix**: Provide a "Before vs After" comparison showing the exact refactored code.
4. **Verification Step**: Explain how the developer can test and verify that this issue has been resolved.
"""

    return client.generate(prompt=prompt, system_prompt=DPO_SYSTEM_PROMPT, on_token=on_token)
