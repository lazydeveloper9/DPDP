"""Stage 4 rule loader — stub."""
from pathlib import Path
from ruamel.yaml import YAML

yaml = YAML()

RULES_DIR = Path(__file__).parent.parent.parent.parent / "rules"

def load_all_rules() -> list[dict]:
    rules = []
    for pass_dir in ["pass_a", "pass_b"]:
        d = RULES_DIR / pass_dir
        if d.exists():
            for f in sorted(d.glob("*.yaml")):
                try:
                    with open(f) as fh:
                        data = yaml.load(fh)
                    if isinstance(data, list):
                        rules.extend(data)
                    elif isinstance(data, dict):
                        rules.append(data)
                except Exception:
                    pass
    return rules
