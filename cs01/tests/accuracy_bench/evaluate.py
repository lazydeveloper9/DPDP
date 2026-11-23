#!/usr/bin/env python3
"""
CS-01 Accuracy Benchmark Harness
================================
Runs the CS-01 compliance scanner against paired True Positive / True Negative
fixtures in tests/accuracy_bench/fixtures/ to compute:
- Precision = TP / (TP + FP)
- Recall = TP / (TP + FN)
- F1 Score = 2 * (P * R) / (P + R)
- False Positive Rate (FPR) = FP / (FP + TN)

Saves baseline_metrics.json and prints a structured Rich table.
"""

from __future__ import annotations
import io
import json
import os
import sys
import contextlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from cs01.models.scan_config import ScanConfig
from cs01.pipeline.stage1_ingest.ingestor import run_ingest
from cs01.pipeline.stage2_parse.parser import run_parse
from cs01.pipeline.stage3_detect.detector import run_detect
from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate

BENCH_ROOT = Path(__file__).resolve().parent
FIXTURES_DIR = BENCH_ROOT / "fixtures"
DEFAULT_OUTPUT = BENCH_ROOT / "baseline_metrics.json"

console = Console()

def scan_fixture(fixture_dir: Path) -> set[str]:
    """Run scanner pipeline stages 1-4 on a fixture and return detected rule IDs."""
    cfg = ScanConfig(
        scan_root=str(fixture_dir),
        output_dir=str(fixture_dir / ".cs01_tmp"),
        strict_test_scanning=False,
    )

    with open(os.devnull, "w") as devnull:
        with contextlib.redirect_stdout(devnull), contextlib.redirect_stderr(devnull):
            manifest = run_ingest(cfg)
            repo_model = run_parse(manifest, cfg)
            flow_graph, pii_hits = run_detect(repo_model, cfg)
            raw_findings = run_evaluate(flow_graph, pii_hits, repo_model, cfg)

    return {f.rule_id for f in raw_findings}

def evaluate_bench(fixtures_dir: Path = FIXTURES_DIR) -> dict[str, Any]:
    """Run the benchmark evaluation across all fixture directories."""
    results: dict[str, Any] = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fixtures_dir": str(fixtures_dir),
        "rules": {},
        "aggregate": {},
    }

    total_tp = 0
    total_fp = 0
    total_tn = 0
    total_fn = 0
    total_fixtures = 0

    rule_dirs = sorted([d for d in fixtures_dir.iterdir() if d.is_dir()])

    for rule_dir in rule_dirs:
        rule_id = rule_dir.name.replace("_", "-")
        tp_count = 0
        fp_count = 0
        tn_count = 0
        fn_count = 0
        fixture_details = []

        subdirs = sorted([d for d in rule_dir.iterdir() if d.is_dir()])
        for fix_dir in subdirs:
            name = fix_dir.name
            is_tp = name.startswith("tp_")
            is_tn = name.startswith("tn_")
            if not (is_tp or is_tn):
                continue

            total_fixtures += 1
            detected_rules = scan_fixture(fix_dir)
            fired = rule_id in detected_rules

            if is_tp:
                if fired:
                    tp_count += 1
                    outcome = "TP"
                else:
                    fn_count += 1
                    outcome = "FN"
            else:
                if fired:
                    fp_count += 1
                    outcome = "FP"
                else:
                    tn_count += 1
                    outcome = "TN"

            fixture_details.append({
                "scenario": name,
                "expected_fired": is_tp,
                "actual_fired": fired,
                "outcome": outcome,
                "detected_rules": sorted(detected_rules),
            })

        rule_p = (tp_count / (tp_count + fp_count)) if (tp_count + fp_count) > 0 else 0.0
        rule_r = (tp_count / (tp_count + fn_count)) if (tp_count + fn_count) > 0 else 0.0
        rule_f1 = (2 * rule_p * rule_r / (rule_p + rule_r)) if (rule_p + rule_r) > 0 else 0.0
        rule_fpr = (fp_count / (fp_count + tn_count)) if (fp_count + tn_count) > 0 else 0.0

        results["rules"][rule_id] = {
            "tp": tp_count,
            "fp": fp_count,
            "tn": tn_count,
            "fn": fn_count,
            "precision": round(rule_p, 4),
            "recall": round(rule_r, 4),
            "f1": round(rule_f1, 4),
            "fpr": round(rule_fpr, 4),
            "fixtures": fixture_details,
        }

        total_tp += tp_count
        total_fp += fp_count
        total_tn += tn_count
        total_fn += fn_count

    agg_p = (total_tp / (total_tp + total_fp)) if (total_tp + total_fp) > 0 else 0.0
    agg_r = (total_tp / (total_tp + total_fn)) if (total_tp + total_fn) > 0 else 0.0
    agg_f1 = (2 * agg_p * agg_r / (agg_p + agg_r)) if (agg_p + agg_r) > 0 else 0.0
    agg_fpr = (total_fp / (total_fp + total_tn)) if (total_fp + total_tn) > 0 else 0.0

    results["aggregate"] = {
        "total_fixtures": total_fixtures,
        "tp": total_tp,
        "fp": total_fp,
        "tn": total_tn,
        "fn": total_fn,
        "precision": round(agg_p, 4),
        "recall": round(agg_r, 4),
        "f1": round(agg_f1, 4),
        "fpr": round(agg_fpr, 4),
    }

    return results

def print_results_table(results: dict[str, Any]) -> None:
    """Print benchmark metrics using rich table."""
    table = Table(
        title="CS-01 Accuracy Benchmark Results",
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("Rule ID", style="bold white", width=16)
    table.add_column("TP", justify="right", width=5)
    table.add_column("FP", justify="right", width=5)
    table.add_column("TN", justify="right", width=5)
    table.add_column("FN", justify="right", width=5)
    table.add_column("Precision", justify="right", width=10)
    table.add_column("Recall", justify="right", width=10)
    table.add_column("F1", justify="right", width=10)
    table.add_column("FPR", justify="right", width=10)

    for rule_id, m in sorted(results["rules"].items()):
        p_pct = f"{m['precision'] * 100:.1f}%"
        r_pct = f"{m['recall'] * 100:.1f}%"
        f1_str = f"{m['f1']:.3f}"
        fpr_pct = f"{m['fpr'] * 100:.1f}%"

        fpr_style = "red" if m["fpr"] > 0.05 else "green"
        p_style = "green" if m["precision"] >= 0.90 else ("yellow" if m["precision"] >= 0.70 else "red")
        r_style = "green" if m["recall"] >= 0.90 else ("yellow" if m["recall"] >= 0.70 else "red")

        table.add_row(
            rule_id,
            str(m["tp"]),
            f"[red]{m['fp']}[/red]" if m["fp"] > 0 else "0",
            str(m["tn"]),
            f"[red]{m['fn']}[/red]" if m["fn"] > 0 else "0",
            f"[{p_style}]{p_pct}[/{p_style}]",
            f"[{r_style}]{r_pct}[/{r_style}]",
            f1_str,
            f"[{fpr_style}]{fpr_pct}[/{fpr_style}]",
        )

    agg = results["aggregate"]
    agg_p_pct = f"{agg['precision'] * 100:.1f}%"
    agg_r_pct = f"{agg['recall'] * 100:.1f}%"
    agg_f1_str = f"{agg['f1']:.3f}"
    agg_fpr_pct = f"{agg['fpr'] * 100:.1f}%"

    table.add_section()
    table.add_row(
        "[bold cyan]AGGREGATE[/bold cyan]",
        f"[bold]{agg['tp']}[/bold]",
        f"[bold red]{agg['fp']}[/bold red]" if agg["fp"] > 0 else "0",
        f"[bold]{agg['tn']}[/bold]",
        f"[bold red]{agg['fn']}[/bold red]" if agg["fn"] > 0 else "0",
        f"[bold]{agg_p_pct}[/bold]",
        f"[bold]{agg_r_pct}[/bold]",
        f"[bold]{agg_f1_str}[/bold]",
        f"[bold]{agg_fpr_pct}[/bold]",
    )

    console.print()
    console.print(table)
    console.print()

def main() -> int:
    output_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUTPUT
    console.print(Panel(
        f"[bold cyan]CS-01 Accuracy Benchmark Harness[/bold cyan]\n"
        f"Evaluating fixtures in: [yellow]{FIXTURES_DIR}[/yellow]\n"
        f"Output metrics: [yellow]{output_path}[/yellow]",
        border_style="cyan",
    ))

    results = evaluate_bench(FIXTURES_DIR)
    print_results_table(results)

    with open(output_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)

    console.print(f"[green]✔ Baseline metrics saved to: [bold]{output_path}[/bold][/green]\n")
    return 0

if __name__ == "__main__":
    sys.exit(main())
