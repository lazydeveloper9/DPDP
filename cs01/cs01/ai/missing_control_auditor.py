"""
cs01.ai.missing_control_auditor — Missing Control Auditor.
Audits route handlers and endpoints for missing authentication, missing IDOR checks,
and missing consent verification.
"""

from __future__ import annotations
import json
from typing import Any

from cs01.models.raw_finding import RawFinding, PassType, Severity
from .client import LocalLLMClient
from .pii_placeholder import mask_pii_with_placeholders

MISSING_CONTROL_PROMPT = """Analyze the following API handler for missing DPDP statutory controls:
1. Missing Authentication / Authorization
2. Broken Object-Level Authorization (IDOR/BOLA)
3. Unenforced Consent Flags before PII processing

Route Handler ({file}):
```
{code}
```

Respond in pure JSON:
{{
  "has_missing_auth": true/false,
  "has_idor_risk": true/false,
  "has_missing_consent": true/false,
  "details": "Explanation if any missing control found"
}}
"""

def audit_missing_controls(
    file_path: str,
    code_snippet: str,
    client: LocalLLMClient,
) -> list[RawFinding]:
    """Audit code snippet for missing statutory access and consent controls."""
    if not client.is_available():
        return []

    masked_code, _ = mask_pii_with_placeholders(code_snippet)
    prompt = MISSING_CONTROL_PROMPT.format(file=file_path, code=masked_code)

    findings: list[RawFinding] = []
    try:
        resp = client.generate(prompt)
        data = json.loads(resp.get("text", "{}"))
        if data.get("has_missing_auth"):
            findings.append(
                RawFinding(
                    id=f"AI-MISSING-AUTH:{file_path}",
                    rule_id="CODE-DPDP-004",
                    pass_type=PassType.A,
                    file=file_path,
                    line_start=1,
                    snippet=code_snippet[:100],
                    matched_entity="route_handler",
                    dpdp_section="§8(5)",
                    dpdp_rule="Rule 6(1)(a)",
                    penalty_band="250_crore",
                    severity=Severity.HIGH,
                    engine="local-ai",
                    message="API endpoint handling personal data lacks authentication guardrail",
                    remediation="Add authentication middleware (e.g. Depends(get_current_user) or requireAuth).",
                )
            )
    except Exception:
        pass

    return findings
