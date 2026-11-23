from __future__ import annotations
from pathlib import Path
from typing import NamedTuple

BENCH_ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = BENCH_ROOT / "fixtures"

class FixtureCase(NamedTuple):
    rule_id: str
    scenario: str
    fixture_path: Path
    is_true_positive: bool

def discover_fixture_cases() -> list[FixtureCase]:
    cases: list[FixtureCase] = []
    if not FIXTURES_DIR.exists():
        return cases

    for rule_dir in sorted(FIXTURES_DIR.iterdir()):
        if not rule_dir.is_dir():
            continue
        rule_id = rule_dir.name.replace("_", "-")
        for fix_dir in sorted(rule_dir.iterdir()):
            if not fix_dir.is_dir():
                continue
            name = fix_dir.name
            if name.startswith("tp_"):
                cases.append(FixtureCase(
                    rule_id=rule_id,
                    scenario=name,
                    fixture_path=fix_dir,
                    is_true_positive=True,
                ))
            elif name.startswith("tn_"):
                cases.append(FixtureCase(
                    rule_id=rule_id,
                    scenario=name,
                    fixture_path=fix_dir,
                    is_true_positive=False,
                ))
    return cases
