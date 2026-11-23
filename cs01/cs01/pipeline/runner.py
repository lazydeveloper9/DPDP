"""
Pipeline runner — wires all 6 stages together.
Called by `cs01 scan`; each stage reads the previous stage's output model.
"""

from __future__ import annotations
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from cs01.models.scan_config import ScanConfig
from cs01.utils import (
    save_json, new_scan_id, utc_now_iso, is_archive, is_git_url,
    extracted_workspace,
)

console = Console(stderr=True)

EXIT_CLEAN = 0
EXIT_POLICY_FAIL = 1
EXIT_CONFIG_ERROR = 2
EXIT_PARTIAL_SCAN = 3

FAIL_ON_ORDER = ["critical", "high", "medium", "never"]


def run_pipeline(cfg: ScanConfig) -> int:
    """
    Execute the full 6-stage pipeline.
    Returns one of: 0 (clean), 1 (policy fail), 2 (config error), 3 (partial).
    """
    scan_id = new_scan_id()
    output_dir = Path(cfg.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with extracted_workspace(cfg.scan_root, ref=cfg.git_ref) as resolved_root:
        orig_scan_root = cfg.scan_root
        if is_git_url(orig_scan_root):
            console.print(f"[cyan]📦 Remote Git repository detected: [bold]{orig_scan_root}[/bold][/cyan]")
        elif is_archive(orig_scan_root):
            console.print(f"[cyan]📦 Archive detected ({orig_scan_root}). Safely unpacked to temporary workspace.[/cyan]")
        cfg.scan_root = str(resolved_root)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=True,
        ) as progress:

            # ── Stage 1: Ingest & Classify ──────────────────────────────────────
            t = progress.add_task("[cyan]Stage 1 · Ingest & Classify...", total=None)
            from cs01.pipeline.stage1_ingest.ingestor import run_ingest
            manifest = run_ingest(cfg)
            progress.remove_task(t)
            console.print(
                f"[green]✔ Stage 1[/green] — {manifest.total_scanned} files scanned, "
                f"{manifest.skipped_count} skipped"
            )
            if cfg.save_stage_output:
                save_json(manifest, output_dir / "stage1_manifest.json")

            # ── Stage 2: Parse ──────────────────────────────────────────────────
            t = progress.add_task("[cyan]Stage 2 · Parse...", total=None)
            from cs01.pipeline.stage2_parse.parser import run_parse
            repo_model = run_parse(manifest, cfg)
            progress.remove_task(t)
            console.print(
                f"[green]✔ Stage 2[/green] — "
                f"{len(repo_model.ast_index)} ASTs, "
                f"{len(repo_model.schema_records)} schema records, "
                f"{len(repo_model.iac_trees)} IaC trees"
            )
            if cfg.save_stage_output:
                save_json(repo_model, output_dir / "stage2_model.json")

            # ── Stage 3: Detect ─────────────────────────────────────────────────
            t = progress.add_task("[cyan]Stage 3 · Detect PII & Trace Flows...", total=None)
            from cs01.pipeline.stage3_detect.detector import run_detect
            flow_graph, pii_hits = run_detect(repo_model, cfg)
            progress.remove_task(t)
            console.print(
                f"[green]✔ Stage 3[/green] — "
                f"{len(pii_hits.hits)} PII hits, "
                f"{len(flow_graph.edges)} flow edges "
                f"({len(flow_graph.unguarded_edges())} unguarded)"
            )
            if cfg.save_stage_output:
                save_json(flow_graph, output_dir / "stage3_flow_graph.json")
                save_json(pii_hits, output_dir / "stage3_pii_hits.json")

            # ── Stage 4: Evaluate ───────────────────────────────────────────────
            t = progress.add_task("[cyan]Stage 4 · Evaluate DPDP Rules...", total=None)
            from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
            raw_findings = run_evaluate(flow_graph, pii_hits, repo_model, cfg)
            progress.remove_task(t)
            console.print(
                f"[green]✔ Stage 4[/green] — "
                f"{len(raw_findings)} raw findings "
                f"(Pass A + Pass B)"
            )
            if cfg.save_stage_output:
                save_json({"findings": [f.model_dump(mode="json") for f in raw_findings]},
                          output_dir / "stage4_raw_findings.json")

            # ── Stage 5: Classify ───────────────────────────────────────────────
            t = progress.add_task("[cyan]Stage 5 · Classify & Score...", total=None)
            from cs01.pipeline.stage5_classify.classifier import run_classify
            bundle = run_classify(
                raw_findings, cfg,
                scan_id=scan_id,
                scan_timestamp=utc_now_iso(),
                scan_root=orig_scan_root,
                total_files=manifest.total_scanned,
                partial_scan=len(repo_model.parse_errors) > 0,
                partial_details=[e.get("error", "") for e in repo_model.parse_errors],
            )
            progress.remove_task(t)
            console.print(
                f"[green]✔ Stage 5[/green] — "
                f"{len(bundle.findings)} unique findings · "
                f"Readiness: {bundle.readiness.overall:.0f}/100"
            )
            if cfg.save_stage_output:
                save_json(bundle, output_dir / "stage5_bundle.json")

            # ── Stage 6: Report ─────────────────────────────────────────────────
            t = progress.add_task("[cyan]Stage 6 · Generate Reports...", total=None)
            from cs01.pipeline.stage6_report.reporter import run_report
            run_report(bundle, cfg, output_dir)
            progress.remove_task(t)
            console.print(f"[green]✔ Stage 6[/green] — Reports written to [cyan]{output_dir}[/cyan]")

        # ── Cryptographic Evidence Integrity Verification ───────────────────────
        evidence_zip = output_dir / "cs01-evidence-bundle.zip"
        if evidence_zip.exists():
            from cs01.pipeline.stage6_report.evidence_locker import verify_evidence_bundle
            is_valid, _ = verify_evidence_bundle(evidence_zip)
            if is_valid:
                console.print("[green]✔ Evidence Bundle cryptographically verified (Rule 13 compliant)[/green]")

        # ── Executive Compliance Dashboard ──────────────────────────────────────
        score_color = "green" if bundle.readiness.overall >= 80 else ("yellow" if bundle.readiness.overall >= 60 else "red")
        ai_brief_file = output_dir / "dpo_ai_executive_brief.md"
        ai_brief_line = f"\n  • [bold green]Qwen 2.5 Coder Brief:[/bold green] [cyan]{ai_brief_file}[/cyan]" if ai_brief_file.exists() else ""

        console.print(Panel(
            f"[bold]DPDP Readiness Score:[/bold] [{score_color} bold]{bundle.readiness.overall:.0f}/100[/] "
            f"{'([red bold]CAPPED[/red bold] · ' + (bundle.readiness.cap_reason or 'Critical Violations') + ')' if bundle.readiness.is_capped else ''}\n"
            f"[bold]Max Statutory Penalty Ceiling Engaged:[/bold] [red]{bundle.readiness.max_statutory_ceiling_engaged or 'None'}[/red]\n"
            f"[bold]Violations Summary:[/bold] [red bold]{bundle.readiness.open_critical_count} Critical[/], [yellow]{bundle.readiness.open_high_count} High[/], {len(bundle.findings)} Total Unique\n\n"
            f"[bold]Generated Deliverables in [cyan]{output_dir}[/cyan]:[/bold]\n"
            f"  • Executive HTML Dashboard: [cyan]{output_dir / 'cs01-dpo-report.html'}[/cyan]\n"
            f"  • Assessment Markdown Report: [cyan]{output_dir / 'cs01-report.md'}[/cyan]\n"
            f"  • Developer SARIF 2.1.0:   [cyan]{output_dir / 'cs01-findings.sarif'}[/cyan]\n"
            f"  • Technical RoPA Draft:    [cyan]{output_dir / 'ropa_map.json'}[/cyan]\n"
            f"  • Consent Lifecycle Audit: [cyan]{output_dir / 'consent_audit.json'}[/cyan]\n"
            f"  • Auto-Remediation Patches: [cyan]{output_dir / 'remediation_patches'}[/cyan]\n"
            f"  • Rule 13 Cryptographic Zip: [cyan]{evidence_zip}[/cyan]"
            f"{ai_brief_line}",
            title="[bold green]CS-01 Compliance Audit Complete[/bold green]",
            border_style="green" if bundle.readiness.overall >= 80 else "yellow",
        ))

        # ── Determine exit code ─────────────────────────────────────────────────
        if bundle.partial_scan:
            base_exit = EXIT_PARTIAL_SCAN
        else:
            base_exit = EXIT_CLEAN

        if cfg.fail_on != "never":
            threshold_idx = FAIL_ON_ORDER.index(cfg.fail_on)
            suppressed_count = 0
            for finding in bundle.findings:
                if getattr(finding, "is_baseline_suppressed", False):
                    suppressed_count += 1
                    continue
                finding_idx = FAIL_ON_ORDER.index(finding.severity.value.lower())
                if finding_idx <= threshold_idx:
                    console.print(
                        f"[red bold]✖ POLICY GATE FAILED[/red bold] — "
                        f"One or more findings at or above '{cfg.fail_on}' severity."
                    )
                    return EXIT_POLICY_FAIL
            if suppressed_count > 0:
                console.print(f"[dim]ℹ {suppressed_count} findings suppressed by baseline[/dim]")

        if base_exit == EXIT_PARTIAL_SCAN:
            console.print(
                "[yellow]⚠ PARTIAL SCAN[/yellow] — Some files could not be parsed. "
                "See stage2_model.json for details."
            )
        else:
            console.print("[bold green]✔ SCAN CLEAN[/bold green] — No findings at or above threshold.")

        return base_exit
