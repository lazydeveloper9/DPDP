# CS-01 DPDP Compliance Auditor — Workspace Engineering Invariants

## Non-Negotiable Architecture Rules
1. **Zero-Egress Static Core:** All static layers (`cs01 scan`) MUST run 100% locally with zero outbound network requests or telemetry. Live API probing (`cs01 probe`) and local LLM triage MUST remain disabled by default behind explicit opt-in flags.
2. **Law-Agnostic Analyzers:** Analyzers emit strictly technical `RawSignal` objects tagged with `rule_id`. NEVER hardcode DPDP legal citations, penalty amounts, or remediation prose inside analyzer Python code—all statutory metadata lives exclusively in `rules/dpdp_rules/*.yaml`.
3. **Mandatory PII & Secret Redaction:** Mask all matched Indian PII literals (e.g., `XXXX-XXXX-9012`) and secrets in memory before serializing to terminal output, JSON, SARIF, Markdown, HTML, or local LLM prompts.
4. **Fail-Explicit Exit Codes:** Never silently swallow parser or subprocess errors.
   - `0`: Clean pass
   - `1`: Policy gate failure (`>= --fail-on`)
   - `2`: Fatal CLI or `cs01.yaml` schema error
   - `3`: Partial scan warning (missing optional binary, timeout, or unparseable file)
5. **License Hygiene:** Use permissive Python packages only (MIT/BSD/Apache-2.0/MPL-2.0). Never bundle `semgrep/semgrep-rules`—write 100% original Apache-2.0 YAML rules for optional Opengrep subprocess calls.
6. **SARIF 2.1.0 GitHub Safety:** Always emit exactly 1 run per SARIF file, <= 8 tags per rule, <= 4,500 priority-sorted results, root-relative `%SRCROOT%` URIs, and gzip size under 9.5 MB.

## Coding & Verification Standards
- **Python 3.11+**, strict type hints, **Pydantic v2** for all data contracts, **Typer + Rich** for CLI.
- **No Unverified Accuracy Claims:** Every rule or detection upgrade MUST include paired True Positive (TP) and True Negative (TN) fixtures under `tests/accuracy_bench/<RULE_ID>/` and pass `pytest` + `python tests/accuracy_bench/evaluate.py`.
- **Preserve Line Accuracy:** All SQL (`sqlglot`), Terraform (`python-hcl2` with line metadata), YAML (`ruamel.yaml` RoundTrip `.lc.line`), and Dockerfile (`dockerfile-parse`) findings MUST report exact file paths and 1-indexed line numbers.