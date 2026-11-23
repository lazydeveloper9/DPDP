"""
cs01.ai.triage — Opt-in Local LLM Triage for SAST Alerts.
Performs AI-assisted review of medium-confidence findings without silently deleting alerts.
"""

from __future__ import annotations
import json
from typing import Optional

from cs01.models.raw_finding import RawFinding
from .client import LocalLLMClient
from .pii_placeholder import mask_pii_with_placeholders

TRIAGE_PROMPT_TEMPLATE = """You are a senior data protection auditor evaluating a potential DPDP compliance alert.
Rule ID: {rule_id}
File: {file}
Snippet:
```
{snippet}
```

Evaluate if this code represents a genuine non-compliance issue or a benign false positive (e.g. test decoy, mock helper, masked logging).
Respond in pure JSON:
{{
  "action": "confirm" or "dismiss",
  "confidence": 0.0 to 1.0,
  "justification": "One concise line-cited explanation"
}}
"""

def triage_alert(finding: RawFinding, client: LocalLLMClient) -> dict:
    """Triage a single finding using the local LLM."""
    if not client.is_available():
        return {"action": "skipped", "reason": "Local LLM unavailable"}

    masked_snippet, _ = mask_pii_with_placeholders(finding.snippet)
    prompt = TRIAGE_PROMPT_TEMPLATE.format(
        rule_id=finding.rule_id,
        file=finding.file or "unknown",
        snippet=masked_snippet,
    )

    try:
        response = client.generate(prompt)
        text = response.get("text", "").strip()
        data = json.loads(text)
        action = data.get("action", "confirm")
        if action == "dismiss":
            finding.message += f" [Dismissed by AI: {data.get('justification', 'False positive')}]"
        return data
    except Exception as exc:
        return {"action": "error", "reason": str(exc)}
