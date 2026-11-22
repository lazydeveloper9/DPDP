"""
CS-01 CLI entry point.
Built with Typer + Rich.

Subcommands:
  cs01 scan <path>      — Full pipeline (Stages 1-6)
  cs01 ingest <path>    — Stage 1 only (debug)
  cs01 parse <manifest> — Stage 2 only (debug)
  cs01 detect <model>   — Stage 3 only (debug)
  cs01 evaluate <flow>  — Stage 4 only (debug)
  cs01 classify <finds> — Stage 5 only (debug)
  cs01 report <bundle>  — Stage 6 only (debug)
  cs01 probe <url>      — DAST prober (opt-in)
  cs01 rules            — List/explain loaded rules
  cs01 baseline         — Baseline management
"""

from __future__ import annotations
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel

from cs01.config import load_config

app = typer.Typer(
    name="cs01",
    help=(
        "[bold]CS-01[/bold] — Full-Stack DPDP Compliance Auditor\n"
        "India DPDP Act 2023 & Rules 2025 · Zero-egress · Local-first"
    ),
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console(stderr=True)

# --- cs01 scan ---
@app.command()
def scan(
    path: str = typer.Argument(..., help="Path to the repository root to scan"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to cs01.yaml"),
    fail_on: Optional[str] = typer.Option(None, "--fail-on", help="critical|high|medium|never"),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="sarif|json|html|all"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o"),
    save_stages: bool = typer.Option(False, "--save-stage-output", help="Save intermediate JSONs"),
    debug: bool = typer.Option(False, "--debug", help="Verbose debug output"),
    diff_base: Optional[str] = typer.Option(None, "--diff-base", help="Git ref for diff-only scan"),
    baseline: Optional[str] = typer.Option(None, "--baseline", help="Path to .cs01-baseline.json"),
) -> None:
    """Run the full 6-stage compliance scan pipeline on a repository."""
    overrides = {
        "scan_root": path,
        "fail_on": fail_on,
        "output_dir": output_dir,
        "save_stage_output": save_stages or None,
        "debug": debug or None,
        "diff_base": diff_base,
        "baseline_path": baseline,
    }
    if format:
        overrides["output_formats"] = ["sarif", "json", "html"] if format == "all" else [format]

    cfg = load_config(config_path=config, overrides=overrides)

    console.print(Panel(
        f"[bold green]CS-01 Scan Starting[/bold green]\n"
        f"Target: [cyan]{path}[/cyan]\n"
        f"Fail-on: [yellow]{cfg.fail_on}[/yellow]  "
        f"Engine: tree-sitter{'+ opengrep' if cfg.engine.opengrep else ''}",
        title="CS-01",
        border_style="blue",
    ))

    # Import pipeline runner lazily (keeps startup fast)
    from cs01.pipeline.runner import run_pipeline
    exit_code = run_pipeline(cfg)
    sys.exit(exit_code)


# --- Individual stage debug commands ---
@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to scan"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    debug: bool = typer.Option(False, "--debug"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save RepoManifest JSON"),
) -> None:
    """[Stage 1] Ingest & classify repository only. Useful for debugging file bucketing."""
    cfg = load_config(config_path=config, overrides={"scan_root": path, "debug": debug or None})
    from cs01.pipeline.stage1_ingest.ingestor import run_ingest
    from cs01.utils import save_json
    manifest = run_ingest(cfg)
    if output:
        save_json(manifest, output)
        console.print(f"[green]RepoManifest saved to {output}[/green]")
    else:
        import json
        console.print(json.dumps(manifest.model_dump(mode="json"), indent=2))


@app.command()
def parse(
    target: str = typer.Argument(..., help="Directory path to scan or path to RepoManifest JSON file"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    debug: bool = typer.Option(False, "--debug"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save RepoModel JSON"),
) -> None:
    """[Stage 2] Parse into structured representations (AST, Schemas, IaC, Env)."""
    from cs01.models import RepoManifest
    from cs01.pipeline.stage1_ingest.ingestor import run_ingest
    from cs01.pipeline.stage2_parse.parser import run_parse
    from cs01.utils import save_json, load_json
    import json

    target_path = Path(target)
    if target_path.is_file() and target_path.suffix == ".json":
        manifest_data = load_json(target_path)
        manifest = RepoManifest.model_validate(manifest_data)
        cfg = load_config(config_path=config, overrides={"scan_root": manifest.scan_root, "debug": debug or None})
    else:
        cfg = load_config(config_path=config, overrides={"scan_root": str(target_path), "debug": debug or None})
        manifest = run_ingest(cfg)

    repo_model = run_parse(manifest, cfg)
    if output:
        save_json(repo_model, output)
        console.print(f"[green]RepoModel saved to {output}[/green]")
    else:
        console.print(json.dumps(repo_model.model_dump(mode="json"), indent=2))


@app.command()
def detect(
    target: str = typer.Argument(..., help="Path to RepoModel JSON file or directory to scan"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    debug: bool = typer.Option(False, "--debug"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save FlowGraph + PiiHitList JSON"),
) -> None:
    """[Stage 3] Detect personal data and trace source-sink-guard flows."""
    from cs01.models import RepoManifest, RepoModel
    from cs01.pipeline.stage1_ingest.ingestor import run_ingest
    from cs01.pipeline.stage2_parse.parser import run_parse
    from cs01.pipeline.stage3_detect.detector import run_detect
    from cs01.utils import save_json, load_json
    import json

    target_path = Path(target)
    if target_path.is_file() and target_path.suffix == ".json":
        model_data = load_json(target_path)
        model = RepoModel.model_validate(model_data)
        cfg = load_config(config_path=config, overrides={"debug": debug or None})
    else:
        cfg = load_config(config_path=config, overrides={"scan_root": str(target_path), "debug": debug or None})
        manifest = run_ingest(cfg)
        model = run_parse(manifest, cfg)

    flow_graph, pii_hits = run_detect(model, cfg)
    combined = {
        "flow_graph": flow_graph.model_dump(mode="json"),
        "pii_hits": pii_hits.model_dump(mode="json"),
    }
    if output:
        save_json(combined, output)
        console.print(f"[green]FlowGraph & PiiHits saved to {output}[/green]")
    else:
        console.print(json.dumps(combined, indent=2))


@app.command()
def rules(
    rule_id: Optional[str] = typer.Argument(None, help="Explain a specific rule"),
    pass_filter: Optional[str] = typer.Option(None, "--pass", help="A or B"),
) -> None:
    """List active DPDP rules with statutory citations, or explain a single rule."""
    from cs01.pipeline.stage4_evaluate.rule_loader import load_all_rules
    all_rules = load_all_rules()
    if rule_id:
        matched = [r for r in all_rules if r.get("rule_id") == rule_id]
        if not matched:
            console.print(f"[red]Rule '{rule_id}' not found.[/red]")
            raise typer.Exit(1)
        import json
        console.print(json.dumps(matched[0], indent=2))
    else:
        from rich.table import Table
        table = Table(title="CS-01 Active Rules", show_lines=True)
        table.add_column("Rule ID", style="cyan")
        table.add_column("Pass", style="yellow")
        table.add_column("Severity", style="red")
        table.add_column("DPDP §", style="green")
        table.add_column("Penalty Band")
        table.add_column("Description")
        for r in all_rules:
            if pass_filter and r.get("pass", "A") != pass_filter:
                continue
            table.add_row(
                r.get("rule_id", ""),
                r.get("pass", "A"),
                r.get("severity", ""),
                r.get("dpdp_section", ""),
                r.get("penalty_band", ""),
                r.get("description", "")[:60],
            )
        console.print(table)


if __name__ == "__main__":
    app()
