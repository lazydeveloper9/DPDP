"""
cs01.ai.pii_placeholder — Reversible Typed PII Placeholder Substitution.
Zero-egress privacy safety layer: replaces PII literals with typed placeholders
before sending code snippets to any local or remote LLM prompt.
"""

from __future__ import annotations
import re

PATTERNS = [
    ("AADHAAR", re.compile(r"\b\d{4}\s?\d{4}\s?\d{4}\b")),
    ("PAN", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),
    ("GSTIN", re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b")),
    ("EMAIL", re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")),
    ("MOBILE", re.compile(r"\b(?:\+91|91|0)?[6-9]\d{9}\b")),
]

def mask_pii_with_placeholders(text: str) -> tuple[str, dict[str, str]]:
    """
    Replace PII candidate strings with typed placeholders.
    Returns (masked_text, placeholder_map).
    """
    mapping: dict[str, str] = {}
    counters: dict[str, int] = {}
    masked = text

    for pii_type, regex in PATTERNS:
        matches = regex.findall(masked)
        for m in set(matches):
            count = counters.get(pii_type, 0) + 1
            counters[pii_type] = count
            token = f"[{pii_type}_{count}]"
            mapping[token] = m
            masked = masked.replace(m, token)

    return masked, mapping

def unmask_placeholders(text: str, mapping: dict[str, str]) -> str:
    """Reconstitute original text from placeholders."""
    result = text
    for token, original in mapping.items():
        result = result.replace(token, original)
    return result
