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

@app.command()
def scan(
    path: str = typer.Argument(..., help="Path to local repository, zip/tar archive, or remote GitHub URL (e.g. https://github.com/org/repo)"),
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to cs01.yaml"),
    fail_on: Optional[str] = typer.Option(None, "--fail-on", help="critical|high|medium|never"),
    format: Optional[str] = typer.Option(None, "--format", "-f", help="sarif|json|html|all"),
    output_dir: Optional[str] = typer.Option(None, "--output-dir", "-o"),
    save_stages: bool = typer.Option(False, "--save-stage-output", help="Save intermediate JSONs"),
    debug: bool = typer.Option(False, "--debug", help="Verbose debug output"),
    diff_base: Optional[str] = typer.Option(None, "--diff-base", help="Git ref for diff-only scan"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Git branch, tag, or ref for remote repositories"),
    baseline: Optional[str] = typer.Option(None, "--baseline", help="Path to .cs01-baseline.json"),
    ai: bool = typer.Option(True, "--ai/--no-ai", help="Auto-generate AI DPO brief via local Qwen 2.5 Coder if running"),
    ai_model: Optional[str] = typer.Option(None, "--ai-model", help="Local LLM model name (default: auto-detected)"),
    ai_endpoint: Optional[str] = typer.Option(None, "--ai-endpoint", help="Local LLM endpoint (default: http://localhost:11434)"),
    engine: Optional[str] = typer.Option(None, "--engine", help="SAST engine: 'tree-sitter' (default), 'opengrep'/'semgrep', or 'all'"),
) -> None:
    """Run the full 6-stage compliance scan pipeline on a repository or zip archive."""
    overrides = {
        "scan_root": path,
        "fail_on": fail_on,
        "output_dir": output_dir,
        "save_stage_output": save_stages or None,
        "debug": debug or None,
        "diff_base": diff_base,
        "git_ref": branch,
        "baseline_path": baseline,
        "ai": {
            "enabled": ai,
            "model": ai_model or "qwen2.5-coder:3b",
            "endpoint": ai_endpoint or "http://localhost:11434",
        },
    }
    if engine:
        eng = engine.lower()
        if eng in ("opengrep", "semgrep"):
            overrides["engine"] = {"opengrep": True, "tree_sitter": False}
        elif eng in ("all", "both"):
            overrides["engine"] = {"opengrep": True, "tree_sitter": True}
        elif eng in ("tree-sitter", "treesitter"):
            overrides["engine"] = {"opengrep": False, "tree_sitter": True}
    if format:
        overrides["output_formats"] = ["sarif", "json", "html"] if format == "all" else [format]

    cfg = load_config(config_path=config, overrides=overrides)

    engines = []
    if cfg.engine.tree_sitter:
        engines.append("tree-sitter")
    if cfg.engine.opengrep:
        engines.append("opengrep")
    engine_str = " + ".join(engines) if engines else "tree-sitter"

    console.print(Panel(
        f"[bold green]CS-01 Scan Starting[/bold green]\n"
        f"Target: [cyan]{path}[/cyan]\n"
        f"Fail-on: [yellow]{cfg.fail_on}[/yellow]  "
        f"Engine: {engine_str}",
        title="CS-01",
        border_style="blue",
    ))

    from cs01.pipeline.runner import run_pipeline
    exit_code = run_pipeline(cfg)
    sys.exit(exit_code)

app.command("audit", help="All-in-one compliance audit command (alias for scan).")(scan)

@app.command()
def ingest(
    path: str = typer.Argument(..., help="Path to local repository, archive file, or remote GitHub URL"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    branch: Optional[str] = typer.Option(None, "--branch", "-b", help="Git branch, tag, or ref for remote repository"),
    debug: bool = typer.Option(False, "--debug"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save RepoManifest JSON"),
) -> None:
    """[Stage 1] Ingest & classify repository only. Useful for debugging file bucketing."""
    from cs01.utils import extracted_workspace, save_json
    with extracted_workspace(path, ref=branch) as resolved_path:
        cfg = load_config(config_path=config, overrides={"scan_root": str(resolved_path), "debug": debug or None})
        from cs01.pipeline.stage1_ingest.ingestor import run_ingest
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
def evaluate(
    target: str = typer.Argument(..., help="Path to directory or scan target"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    debug: bool = typer.Option(False, "--debug"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save RawFindingList JSON"),
) -> None:
    """[Stage 4] Evaluate DPDP rules (Pass A local + Pass B cross-file)."""
    from cs01.pipeline.stage1_ingest.ingestor import run_ingest
    from cs01.pipeline.stage2_parse.parser import run_parse
    from cs01.pipeline.stage3_detect.detector import run_detect
    from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
    from cs01.utils import save_json
    import json

    cfg = load_config(config_path=config, overrides={"scan_root": str(target), "debug": debug or None})
    manifest = run_ingest(cfg)
    model = run_parse(manifest, cfg)
    flow_graph, pii_hits = run_detect(model, cfg)
    findings = run_evaluate(flow_graph, pii_hits, model, cfg)

    output_payload = [f.model_dump(mode="json") for f in findings]
    if output:
        save_json(output_payload, output)
        console.print(f"[green]{len(findings)} findings saved to {output}[/green]")
    else:
        console.print(json.dumps(output_payload, indent=2))

@app.command()
def classify(
    target: str = typer.Argument(..., help="Path to directory or scan target"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    debug: bool = typer.Option(False, "--debug"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save ScoredFindingBundle JSON"),
) -> None:
    """[Stage 5] Classify risk, compute DPDP Readiness Score, and package evidence."""
    from cs01.pipeline.stage1_ingest.ingestor import run_ingest
    from cs01.pipeline.stage2_parse.parser import run_parse
    from cs01.pipeline.stage3_detect.detector import run_detect
    from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
    from cs01.pipeline.stage5_classify.classifier import run_classify
    from cs01.utils import save_json, new_scan_id, utc_now_iso
    import json

    cfg = load_config(config_path=config, overrides={"scan_root": str(target), "debug": debug or None})
    manifest = run_ingest(cfg)
    model = run_parse(manifest, cfg)
    flow_graph, pii_hits = run_detect(model, cfg)
    raw_findings = run_evaluate(flow_graph, pii_hits, model, cfg)
    bundle = run_classify(
        raw_findings=raw_findings,
        cfg=cfg,
        scan_id=new_scan_id(),
        scan_timestamp=utc_now_iso(),
        scan_root=str(target),
        total_files=manifest.total_scanned,
    )

    if output:
        save_json(bundle, output)
        console.print(f"[green]ScoredFindingBundle saved to {output} (Readiness: {bundle.readiness.overall:.1f}/100)[/green]")
    else:
        console.print(json.dumps(bundle.model_dump(mode="json"), indent=2))

@app.command()
def report(
    bundle_path: str = typer.Argument(..., help="Path to ScoredFindingBundle JSON file"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
    output_dir: str = typer.Option("./cs01-reports", "--output-dir", "-o"),
    format: Optional[str] = typer.Option("all", "--format", "-f", help="sarif|json|html|all"),
) -> None:
    """[Stage 6] Generate all reports, diff patches, and evidence bundle from a scored bundle."""
    from cs01.models import ScoredFindingBundle
    from cs01.pipeline.stage6_report.reporter import run_report
    from cs01.utils import load_json

    bundle_data = load_json(bundle_path)
    bundle = ScoredFindingBundle.model_validate(bundle_data)
    formats = ["sarif", "json", "html"] if format == "all" else [format]
    cfg = load_config(config_path=config, overrides={"output_formats": formats, "output_dir": output_dir})

    generated = run_report(bundle, cfg, output_dir)
    console.print(f"[green]✔ Reports generated in [cyan]{output_dir}[/cyan]:[/green]")
    for name in generated:
        console.print(f"  • {name}")

@app.command("verify-evidence")
def verify_evidence(
    bundle_zip: str = typer.Argument(..., help="Path to cs01-evidence-bundle.zip"),
) -> None:
    """Cryptographically verify the integrity and provenance of a Rule 13 audit evidence bundle."""
    from cs01.pipeline.stage6_report.evidence_locker import verify_evidence_bundle
    is_valid, logs = verify_evidence_bundle(bundle_zip)

    for msg in logs:
        if "VERIFIED" in msg or "SUCCESS" in msg:
            console.print(f"[green]{msg}[/green]")
        elif "VIOLATION" in msg or "MISSING" in msg or "Invalid" in msg:
            console.print(f"[red bold]{msg}[/red bold]")
        else:
            console.print(f"[dim]{msg}[/dim]")

    if is_valid:
        console.print("[bold green]✔ EVIDENCE BUNDLE INTEGRITY CONFIRMED[/bold green]")
    else:
        console.print("[bold red]✖ TAMPERING OR CORRUPTION DETECTED[/bold red]")
        raise typer.Exit(1)

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

@app.command()
def probe(
    url: str = typer.Argument(..., help="Target HTTP(S) URL to probe"),
    allow_live_probe: bool = typer.Option(
        False, "--allow-live-probe", help="Explicit confirmation to probe live network target"
    ),
    timeout: float = typer.Option(5.0, "--timeout", help="Timeout in seconds"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save probe result JSON"),
) -> None:
    """[DAST] Opt-in live HTTP probe for technical safeguards, TLS, and Privacy Notice."""
    from cs01.bonus.dast_prober import run_dast_probe
    from cs01.utils import save_json

    try:
        result = run_dast_probe(url, allow_live_probe=allow_live_probe, timeout=timeout)
    except PermissionError as e:
        console.print(f"[bold red]✖ PERMISSION DENIED:[/bold red] {e}")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold]DAST Live Probe Result for {result.target_url}[/bold]\n"
        f"Host: [cyan]{result.probed_host}:{result.probed_port}[/cyan] · "
        f"TLS: [{'green' if result.tls_valid else 'red'}]{result.tls_version or 'N/A'}[/]\n"
        f"Privacy Notice: [{'green' if result.privacy_notice_found else 'yellow'}]{result.privacy_notice_url or 'Not Found'}[/]\n"
        f"Missing Headers: [yellow]{', '.join(result.missing_security_headers) or 'None'}[/yellow]\n"
        f"Findings: [red]{len(result.findings)}[/red]",
        title="CS-01 DAST Probe",
        border_style="blue",
    ))

    if result.findings:
        from rich.table import Table
        t = Table(title="Live Safeguard Findings", show_lines=True)
        t.add_column("Check ID", style="cyan")
        t.add_column("Severity", style="red")
        t.add_column("DPDP Section", style="green")
        t.add_column("Message")
        for f in result.findings:
            t.add_row(f.check_id, f.severity, f.dpdp_section, f.message)
        console.print(t)

    if output:
        save_json(result.model_dump(mode="json"), output)
        console.print(f"[green]Probe results saved to {output}[/green]")

baseline_app = typer.Typer(name="baseline", help="Manage DPDP baseline files for CI/CD suppression.")
app.add_typer(baseline_app, name="baseline")

@baseline_app.command("create")
def baseline_create(
    target: str = typer.Argument(..., help="Path to repo directory, archive, or stage5_bundle.json"),
    output: str = typer.Option(".cs01-baseline.json", "--output", "-o", help="Output baseline JSON path"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
) -> None:
    """Create a .cs01-baseline.json file containing unique finding fingerprints."""
    from cs01.utils import save_json, load_json, utc_now_iso, extracted_workspace

    target_path = Path(target)
    if target_path.is_file() and target_path.suffix == ".json":
        data = load_json(target_path)
        findings = data.get("findings", []) if isinstance(data, dict) else data
    else:
        with extracted_workspace(target) as resolved:
            cfg = load_config(config_path=config, overrides={"scan_root": str(resolved)})
            from cs01.pipeline.stage1_ingest.ingestor import run_ingest
            from cs01.pipeline.stage2_parse.parser import run_parse
            from cs01.pipeline.stage3_detect.detector import run_detect
            from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
            from cs01.pipeline.stage5_classify.classifier import run_classify
            manifest = run_ingest(cfg)
            model = run_parse(manifest, cfg)
            flow, hits = run_detect(model, cfg)
            raw = run_evaluate(flow, hits, model, cfg)
            bundle = run_classify(raw, cfg, total_files=manifest.total_scanned)
            findings = [f.model_dump(mode="json") for f in bundle.findings]

    fingerprints = sorted(list({f.get("dedupe_key") for f in findings if f.get("dedupe_key")}))
    baseline_payload = {
        "version": "1.0",
        "generated_at": utc_now_iso(),
        "target": str(target),
        "fingerprints": fingerprints,
        "findings_count": len(fingerprints),
        "findings": [
            {
                "dedupe_key": f.get("dedupe_key"),
                "rule_id": f.get("rule_id"),
                "file": f.get("file"),
                "line_start": f.get("line_start"),
                "severity": f.get("severity"),
            }
            for f in findings
        ],
    }
    save_json(baseline_payload, output)
    console.print(f"[bold green]✔ Baseline created with {len(fingerprints)} fingerprints in [cyan]{output}[/cyan][/bold green]")

@baseline_app.command("diff")
def baseline_diff(
    bundle_path: str = typer.Argument(..., help="Path to new stage5_bundle.json"),
    baseline_path: str = typer.Option(".cs01-baseline.json", "--baseline", "-b", help="Path to baseline file"),
) -> None:
    """Compare scan findings against an established baseline."""
    from cs01.utils import load_json
    from rich.table import Table

    b_file = Path(baseline_path)
    if not b_file.exists():
        console.print(f"[red]Baseline file not found: {baseline_path}[/red]")
        raise typer.Exit(1)

    bdata = load_json(b_file)
    baseline_fps = set(bdata.get("fingerprints", [])) if isinstance(bdata, dict) else set()

    c_file = Path(bundle_path)
    if c_file.is_file() and c_file.suffix == ".json":
        cdata = load_json(c_file)
        current_findings = cdata.get("findings", []) if isinstance(cdata, dict) else []
    else:
        console.print(f"[red]Please provide a stage5_bundle.json file: {bundle_path}[/red]")
        raise typer.Exit(1)

    current_fps = {f.get("dedupe_key") for f in current_findings if f.get("dedupe_key")}

    new_fps = current_fps - baseline_fps
    suppressed_fps = current_fps & baseline_fps
    fixed_fps = baseline_fps - current_fps

    table = Table(title="Baseline Diff Summary", show_lines=True)
    table.add_column("Category", style="bold")
    table.add_column("Count", justify="right")
    table.add_column("Status / Impact")

    table.add_row(
        "New Regressions",
        str(len(new_fps)),
        "[red bold]FAILS POLICY GATE[/red bold]" if new_fps else "[green]None[/green]",
    )
    table.add_row(
        "Suppressed (Baseline Debt)",
        str(len(suppressed_fps)),
        "[yellow]Tolerated under baseline[/yellow]",
    )
    table.add_row(
        "Resolved Violations",
        str(len(fixed_fps)),
        "[green]Fixed compared to baseline[/green]",
    )
    console.print(table)

@app.command("report-ai", help="Generate an audit-grade DPDP Compliance Report using local Qwen 2.5 Coder 3B.")
@app.command("summarize", help="Generate an Executive DPO Compliance Brief using local Qwen 2.5 Coder 3B.")
def summarize(
    target: str = typer.Argument(..., help="Path to repository, archive, or stage5_bundle.json"),
    model: str = typer.Option("qwen2.5-coder:3b", "--model", "-m", help="Local LLM model name (default: qwen2.5-coder:3b)"),
    endpoint: str = typer.Option("http://localhost:11434", "--endpoint", "-e", help="Local LLM endpoint"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Save AI compliance report Markdown to file"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
) -> None:
    """[AI] Generate a Comprehensive DPDP Compliance Report using local Qwen 2.5 Coder 3B."""
    from cs01.ai import LocalLLMClient, generate_full_compliance_report
    from cs01.models import ScoredFindingBundle
    from cs01.utils import load_json, extracted_workspace

    client = LocalLLMClient(model=model, endpoint=endpoint)
    if not client.is_available():
        console.print(
            f"[bold red]✖ Local LLM server unreachable at {endpoint}[/bold red]\n"
            f"[yellow]Ensure Ollama or vLLM is running (e.g., 'ollama run {model}').[/yellow]"
        )
        raise typer.Exit(1)

    target_path = Path(target)
    if target_path.is_file() and target_path.suffix == ".json":
        data = load_json(target_path)
        bundle = ScoredFindingBundle.model_validate(data)
        cfg = load_config(config_path=config)
    else:
        with extracted_workspace(target) as resolved:
            cfg = load_config(config_path=config, overrides={"scan_root": str(resolved)})
            from cs01.pipeline.stage1_ingest.ingestor import run_ingest
            from cs01.pipeline.stage2_parse.parser import run_parse
            from cs01.pipeline.stage3_detect.detector import run_detect
            from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
            from cs01.pipeline.stage5_classify.classifier import run_classify
            manifest = run_ingest(cfg)
            repo_model = run_parse(manifest, cfg)
            flow, hits = run_detect(repo_model, cfg)
            raw = run_evaluate(flow, hits, repo_model, cfg)
            bundle = run_classify(raw, cfg, total_files=manifest.total_scanned)

    resolved_model = client.resolve_model()
    console.print(f"[cyan]🤖 Synthesizing Full DPDP Compliance Report via local {resolved_model}...[/cyan]")
    report_md = generate_full_compliance_report(bundle, client, cfg)

    if output:
        out_p = Path(output)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(report_md, encoding="utf-8")
        console.print(f"[bold green]✔ Compliance Report saved to [cyan]{output}[/cyan][/bold green]")
    else:
        from rich.markdown import Markdown
        console.print(Markdown(report_md))

@app.command()
def explain(
    target: str = typer.Argument(..., help="Path to repository, archive, or stage5_bundle.json"),
    rule_or_id: Optional[str] = typer.Argument(None, help="Specific Rule ID (e.g. CODE-DPDP-001) or finding ID to explain"),
    model: str = typer.Option("qwen2.5-coder:3b", "--model", "-m", help="Local LLM model name (default: qwen2.5-coder:3b)"),
    endpoint: str = typer.Option("http://localhost:11434", "--endpoint", "-e", help="Local LLM endpoint"),
    config: Optional[str] = typer.Option(None, "--config", "-c"),
) -> None:
    """[AI] Use local Qwen 2.5 Coder to explain a finding in depth and produce a production code fix."""
    from cs01.ai import LocalLLMClient, explain_finding_in_depth
    from cs01.models import ScoredFindingBundle
    from cs01.utils import load_json, extracted_workspace

    client = LocalLLMClient(model=model, endpoint=endpoint)
    if not client.is_available():
        console.print(
            f"[bold red]✖ Local LLM server unreachable at {endpoint}[/bold red]\n"
            f"[yellow]Ensure Ollama or vLLM is running (e.g., 'ollama run {model}').[/yellow]"
        )
        raise typer.Exit(1)

    target_path = Path(target)
    if target_path.is_file() and target_path.suffix == ".json":
        data = load_json(target_path)
        bundle = ScoredFindingBundle.model_validate(data)
    else:
        with extracted_workspace(target) as resolved:
            cfg = load_config(config_path=config, overrides={"scan_root": str(resolved)})
            from cs01.pipeline.stage1_ingest.ingestor import run_ingest
            from cs01.pipeline.stage2_parse.parser import run_parse
            from cs01.pipeline.stage3_detect.detector import run_detect
            from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
            from cs01.pipeline.stage5_classify.classifier import run_classify
            manifest = run_ingest(cfg)
            repo_model = run_parse(manifest, cfg)
            flow, hits = run_detect(repo_model, cfg)
            raw = run_evaluate(flow, hits, repo_model, cfg)
            bundle = run_classify(raw, cfg, total_files=manifest.total_scanned)

    if not bundle.findings:
        console.print("[green]No findings in this bundle to explain![/green]")
        return

    target_finding = None
    if rule_or_id:
        for f in bundle.findings:
            if f.id == rule_or_id or f.rule_id == rule_or_id:
                target_finding = f
                break
        if not target_finding:
            console.print(f"[red]Finding with ID or Rule '{rule_or_id}' not found in scan.[/red]")
            raise typer.Exit(1)
    else:
        target_finding = bundle.findings[0]

    console.print(f"[cyan]🤖 Asking local Qwen 2.5 Coder to explain [bold]{target_finding.rule_id}[/bold] in {target_finding.file}...[/cyan]")
    explanation = explain_finding_in_depth(target_finding, client)
    from rich.markdown import Markdown
    console.print(Markdown(explanation))

if __name__ == "__main__":
    app()
