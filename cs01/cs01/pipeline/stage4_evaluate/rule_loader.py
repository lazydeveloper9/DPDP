"""
Stage 4 Rule Loader
===================
Loads and validates declarative YAML rules from rules/pass_a/ and rules/pass_b/.
Enforces structural invariants including tag limits (<= 8 tags per rule) for SARIF 2.1.0.
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

from ruamel.yaml import YAML

yaml = YAML()
RULES_DIR = Path(__file__).resolve().parent.parent.parent.parent / "rules"

def load_all_rules(custom_rules_dir: Path | str | None = None) -> list[dict[str, Any]]:
    """Load all Pass A and Pass B rules from disk."""
    base_dir = Path(custom_rules_dir) if custom_rules_dir else RULES_DIR
    rules: list[dict[str, Any]] = []

    for pass_dir in ("pass_a", "pass_b"):
        d = base_dir / pass_dir
        if not d.exists():
            continue

        for rule_file in sorted(d.glob("*.yaml")):
            try:
                with open(rule_file, "r", encoding="utf-8") as fh:
                    content = yaml.load(fh)
                if isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict):
                            _validate_rule(item, rule_file)
                            rules.append(item)
                elif isinstance(content, dict):
                    _validate_rule(content, rule_file)
                    rules.append(content)
            except Exception as exc:
                print(f"[CS-01] Warning loading rule {rule_file}: {exc}")

    return rules

def _validate_rule(rule: dict[str, Any], rule_file: Path) -> None:
    """Validate rule dictionary invariants."""
    required = ["rule_id", "pass", "severity", "dpdp_section", "dpdp_rule", "penalty_band"]
    for field in required:
        if field not in rule:
            raise ValueError(f"Rule in {rule_file} missing mandatory field: {field}")

    tags = rule.get("tags", [])
    if len(tags) > 8:
        rule["tags"] = tags[:8]

def get_rule_by_id(rule_id: str, custom_rules_dir: Path | str | None = None) -> dict[str, Any] | None:
    """Find a specific rule by its ID."""
    for r in load_all_rules(custom_rules_dir):
        if r.get("rule_id") == rule_id:
            return r
    return None
