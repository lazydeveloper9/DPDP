import re
from pathlib import Path
from cs01.models.scan_config import ScanConfig
from cs01.pipeline.stage1_ingest.ingestor import run_ingest
from cs01.pipeline.stage2_parse.parser import run_parse
from cs01.pipeline.stage3_detect.detector import run_detect
from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
from cs01.pipeline.stage5_classify.classifier import run_classify
from cs01.pipeline.stage6_report.markdown_exporter import export_markdown_report

def test_report_integrity_and_math(tmp_path: Path):
    """Regression test ensuring report contains zero hardcoded mock placeholders and exact mathematical parity."""
    # Create a small realistic target repo
    repo_dir = tmp_path / "sample_repo"
    repo_dir.mkdir()
    (repo_dir / "app.py").write_text(
        'import logging\n'
        'def process(user_data):\n'
        '    logging.info(user_data)\n',
        encoding="utf-8"
    )

    out_dir = tmp_path / "reports"
    out_dir.mkdir()

    cfg = ScanConfig(scan_root=str(repo_dir), output_dir=str(out_dir))
    manifest = run_ingest(cfg)
    model = run_parse(manifest, cfg)
    flow, hits = run_detect(model, cfg)
    raw = run_evaluate(flow, hits, model, cfg)
    bundle = run_classify(raw, cfg, total_files=manifest.total_scanned)

    md_report_path = out_dir / "cs01-report.md"
    export_markdown_report(bundle, cfg, md_report_path)

    assert md_report_path.exists()
    content = md_report_path.read_text(encoding="utf-8")

    # 1. Zero hardcoded mock dummy strings
    assert "https://target.local" not in content, "Found hardcoded dummy target.local in report"
    assert "src/main.py" not in content, "Found hardcoded dummy src/main.py in report"
    assert "DELETE /consent/withdraw" not in content, "Found hardcoded dummy DELETE /consent/withdraw in report"
    assert "[REDACTED_EMAIL] (confidence: 0.85)" not in content, "Found synthetic placeholder in snippet"

    # 2. Strict Mathematical Invariant
    # Parse Severity Breakdown table
    # | **TOTAL** | **`X`** | **`+X`** | **`0`** | |
    tot_match = re.search(r"\|\s*\*\*TOTAL\*\*\s*\|\s*\*\*`(\d+)`\*\*", content)
    assert tot_match, "Could not find TOTAL in severity breakdown table"
    total_active_from_summary = int(tot_match.group(1))

    # Parse Layer Matrix table
    # Layer 1..5 lines: | Layer X: ... | `total` | `crit` | `high` | `med` | `low` |
    layer_rows = re.findall(r"\|\s*Layer\s*\d+:[^|]+\|\s*`[^`]+`\s*\|\s*`(\d+)`\s*\|\s*`(\d+)`\s*\|\s*`(\d+)`\s*\|\s*`(\d+)`\s*\|", content)
    assert len(layer_rows) == 5, f"Expected 5 layer rows, found {len(layer_rows)}"

    sum_layer_counts = sum(int(c) + int(h) + int(m) + int(l) for c, h, m, l in layer_rows)
    assert sum_layer_counts == total_active_from_summary, (
        f"Layer matrix sum ({sum_layer_counts}) != severity breakdown total ({total_active_from_summary})"
    )

    # 3. Roadmap Math: readiness + sum(lifts) <= 100
    readiness = bundle.readiness.overall
    roadmap_lifts = [int(m) for m in re.findall(r"\+(\d+)\s*pts", content)]
    assert readiness + sum(roadmap_lifts) <= 100, (
        f"Readiness ({readiness}) + lifts ({sum(roadmap_lifts)}) exceeds 100!"
    )
