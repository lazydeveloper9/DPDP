"""
Pipeline runner — wires all 6 stages together.
Called by `cs01 scan`; each stage reads the previous stage's output model.
"""

from __future__ import annotations
import sys
import time
from pathlib import Path
from typing import Any, Callable, Optional

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.table import Table

from cs01.models.scan_config import ScanConfig
from cs01.models.scored_finding import ScoredFindingBundle
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

_STANDARD_REPORT_FILES = {
    "cs01-dpo-report.html",
    "cs01-dataflow.html",
    "cs01-report.md",
    "cs01-findings.sarif",
    "ropa_map.json",
    "consent_audit.json",
    "cs01-evidence-bundle.zip",
    "cs01-compliance.json",
    "dataflow_graph.json",
    "dpo_ai_executive_brief.md",
}


def collect_report_files(output_dir: Path) -> dict[str, Path]:
    """Scan output directory for standard CS-01 deliverable files and patches."""
    report_files: dict[str, Path] = {}
    if not output_dir.exists():
        return report_files

    for f in output_dir.iterdir():
        if f.is_file():
            report_files[f.name] = f

    patches_dir = output_dir / "remediation_patches"
    if not patches_dir.exists():
        patches_dir = output_dir / "patches"

    if patches_dir.exists():
        for pf in patches_dir.glob("*.patch"):
            report_files[pf.name] = pf

    return report_files


def execute_pipeline(
    cfg: ScanConfig,
    on_stage_start: Optional[Callable[[int, str], None]] = None,
    on_stage_complete: Optional[Callable[[int, str, float], None]] = None,
    on_progress: Optional[Callable[[int, str], None]] = None,
    on_log: Optional[Callable[[str, str], None]] = None,
    on_finding: Optional[Callable[[Any], None]] = None,
    is_cancelled: Optional[Callable[[], bool]] = None,
) -> tuple[int, ScoredFindingBundle, dict[str, Path]]:
    """
    Core law-agnostic 6-stage compliance audit pipeline.
    Shared execution engine called by both CLI (`cs01 scan`) and Desktop GUI (`AuditWorker`).

    Returns:
        tuple[int, ScoredFindingBundle, dict[str, Path]]: (exit_code, bundle, report_files)
    """
    scan_id = new_scan_id()
    output_dir = Path(cfg.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    cfg.output_dir = str(output_dir)

    def _check_cancel() -> None:
        if is_cancelled and is_cancelled():
            raise InterruptedError("Audit cancelled by user.")

    stage_names = [
        (1, "Ingest Target & Parse AST"),
        (2, "Resolve Call Graph & Data Flow"),
        (3, "Detect Indian PII & Validators"),
        (4, "Evaluate DPDP Statutory Rules"),
        (5, "Classify Risk & Package Evidence"),
        (6, "Generate Reports & Evidence Locker"),
    ]

    stage_durations: dict[str, float] = {}

    with extracted_workspace(cfg.scan_root, ref=cfg.git_ref) as resolved_root:
        orig_scan_root = cfg.scan_root
        cfg.scan_root = str(resolved_root)

        # ── Stage 1: Ingest ──────────────────────────────────────────
        _check_cancel()
        s_num, s_name = stage_names[0]
        if on_stage_start:
            on_stage_start(s_num, s_name)
        if on_progress:
            on_progress(10, f"Stage {s_num}: {s_name}")
        if on_log:
            on_log("INFO", f"▶ Stage {s_num} · {s_name}")

        t0 = time.perf_counter()
        from cs01.pipeline.stage1_ingest.ingestor import run_ingest
        manifest = run_ingest(cfg)
        elapsed = time.perf_counter() - t0
        stage_durations["stage1"] = elapsed
        if on_stage_complete:
            on_stage_complete(s_num, s_name, elapsed)
        if on_log:
            on_log("INFO", f"✔ Stage {s_num} · {s_name} completed in {elapsed:.2f}s ({manifest.total_scanned} files)")

        if cfg.save_stage_output:
            save_json(manifest, output_dir / "stage1_manifest.json")

        # ── Stage 2: Parse ───────────────────────────────────────────
        _check_cancel()
        s_num, s_name = stage_names[1]
        if on_stage_start:
            on_stage_start(s_num, s_name)
        if on_progress:
            on_progress(25, f"Stage {s_num}: {s_name}")
        if on_log:
            on_log("INFO", f"▶ Stage {s_num} · {s_name}")

        t0 = time.perf_counter()
        from cs01.pipeline.stage2_parse.parser import run_parse
        repo_model = run_parse(manifest, cfg)
        elapsed = time.perf_counter() - t0
        stage_durations["stage2"] = elapsed
        if on_stage_complete:
            on_stage_complete(s_num, s_name, elapsed)
        if on_log:
            on_log("INFO", f"✔ Stage {s_num} · {s_name} completed in {elapsed:.2f}s ({len(repo_model.ast_index)} ASTs)")

        if cfg.save_stage_output:
            save_json(repo_model, output_dir / "stage2_model.json")

        # ── Stage 3: Detect PII & Capabilities ───────────────────────
        _check_cancel()
        s_num, s_name = stage_names[2]
        if on_stage_start:
            on_stage_start(s_num, s_name)
        if on_progress:
            on_progress(45, f"Stage {s_num}: {s_name}")
        if on_log:
            on_log("INFO", f"▶ Stage {s_num} · {s_name}")

        t0 = time.perf_counter()
        from cs01.pipeline.stage3_detect.detector import run_detect
        from cs01.pipeline.stage3_detect.capability_detector import detect_product_capabilities
        flow_graph, pii_hits = run_detect(repo_model, cfg)
        capability_report = detect_product_capabilities(repo_model, flow_graph, pii_hits, cfg)
        elapsed = time.perf_counter() - t0
        stage_durations["stage3"] = elapsed
        if on_stage_complete:
            on_stage_complete(s_num, s_name, elapsed)
        if on_log:
            on_log("INFO", f"✔ Stage {s_num} · {s_name} completed in {elapsed:.2f}s ({len(pii_hits.hits)} PII hits)")

        # Always save stage 3 PII hits so UI can display PII catalog
        save_json(pii_hits, output_dir / "stage3_pii_hits.json")
        if cfg.save_stage_output:
            save_json(flow_graph, output_dir / "stage3_flow_graph.json")
            save_json(capability_report, output_dir / "stage3_capability_report.json")

        # ── Stage 4: Evaluate Rules ──────────────────────────────────
        _check_cancel()
        s_num, s_name = stage_names[3]
        if on_stage_start:
            on_stage_start(s_num, s_name)
        if on_progress:
            on_progress(65, f"Stage {s_num}: {s_name}")
        if on_log:
            on_log("INFO", f"▶ Stage {s_num} · {s_name}")

        t0 = time.perf_counter()
        from cs01.pipeline.stage4_evaluate.evaluator import run_evaluate
        raw_findings = run_evaluate(flow_graph, pii_hits, repo_model, cfg, capability_report=capability_report)
        elapsed = time.perf_counter() - t0
        stage_durations["stage4"] = elapsed
        if on_stage_complete:
            on_stage_complete(s_num, s_name, elapsed)
        if on_log:
            on_log("INFO", f"✔ Stage {s_num} · {s_name} completed in {elapsed:.2f}s ({len(raw_findings)} findings)")

        if on_finding:
            for f in raw_findings:
                on_finding(f)

        if cfg.save_stage_output:
            save_json({"findings": [f.model_dump(mode="json") for f in raw_findings]},
                      output_dir / "stage4_raw_findings.json")

        # ── Stage 5: Classify & Score ────────────────────────────────
        _check_cancel()
        s_num, s_name = stage_names[4]
        if on_stage_start:
            on_stage_start(s_num, s_name)
        if on_progress:
            on_progress(80, f"Stage {s_num}: {s_name}")
        if on_log:
            on_log("INFO", f"▶ Stage {s_num} · {s_name}")

        t0 = time.perf_counter()
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
        elapsed = time.perf_counter() - t0
        stage_durations["stage5"] = elapsed
        if on_stage_complete:
            on_stage_complete(s_num, s_name, elapsed)
        if on_log:
            on_log("INFO", f"✔ Stage {s_num} · {s_name} completed in {elapsed:.2f}s (Readiness: {bundle.readiness.overall:.1f}/100)")

        # Always save stage 5 bundle for audit trail & GUI reloading
        save_json(bundle, output_dir / "stage5_bundle.json")
        save_json(bundle, output_dir / "cs01-compliance.json")

        # ── Stage 6: Generate Reports ────────────────────────────────
        _check_cancel()
        s_num, s_name = stage_names[5]
        if on_stage_start:
            on_stage_start(s_num, s_name)
        if on_progress:
            on_progress(90, f"Stage {s_num}: {s_name}")
        if on_log:
            on_log("INFO", f"▶ Stage {s_num} · {s_name}")

        t0 = time.perf_counter()
        from cs01.pipeline.stage6_report.reporter import run_report
        run_report(
            bundle,
            cfg,
            output_dir,
            stage_durations=stage_durations,
            repo_model=repo_model,
            flow_graph=flow_graph,
            pii_hits=pii_hits,
            capability_report=capability_report,
        )
        elapsed = time.perf_counter() - t0
        stage_durations["stage6"] = elapsed
        if on_stage_complete:
            on_stage_complete(s_num, s_name, elapsed)
        if on_log:
            on_log("INFO", f"✔ Stage {s_num} · {s_name} completed in {elapsed:.2f}s")

        report_files = collect_report_files(output_dir)

        # Determine exit code
        if bundle.partial_scan:
            exit_code = EXIT_PARTIAL_SCAN
        else:
            exit_code = EXIT_CLEAN

        if cfg.fail_on != "never":
            threshold_idx = FAIL_ON_ORDER.index(cfg.fail_on)
            for finding in bundle.findings:
                if getattr(finding, "is_baseline_suppressed", False):
                    continue
                finding_idx = FAIL_ON_ORDER.index(finding.severity.value.lower())
                if finding_idx <= threshold_idx:
                    exit_code = EXIT_POLICY_FAIL
                    break

        if on_progress:
            on_progress(100, "Audit completed successfully.")

        return exit_code, bundle, report_files


def run_pipeline(cfg: ScanConfig) -> int:
    """
    Execute the full 6-stage pipeline from CLI.
    Returns one of: 0 (clean), 1 (policy fail), 2 (config error), 3 (partial).
    """
    output_dir = Path(cfg.output_dir).resolve()
    orig_scan_root = cfg.scan_root

    if is_git_url(orig_scan_root):
        console.print(f"[cyan]📦 Remote Git repository detected: [bold]{orig_scan_root}[/bold][/cyan]")
    elif is_archive(orig_scan_root):
        console.print(f"[cyan]📦 Archive detected ({orig_scan_root}). Safely unpacked to temporary workspace.[/cyan]")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        task = progress.add_task("[cyan]Running CS-01 Audit...", total=None)

        def _on_start(stage_num: int, stage_name: str) -> None:
            progress.update(task, description=f"[cyan]Stage {stage_num} · {stage_name}...")

        def _on_complete(stage_num: int, stage_name: str, elapsed: float) -> None:
            console.print(f"[green]✔ Stage {stage_num}[/green] — {stage_name} ({elapsed:.2f}s)")

        exit_code, bundle, report_files = execute_pipeline(
            cfg,
            on_stage_start=_on_start,
            on_stage_complete=_on_complete,
        )

    evidence_zip = output_dir / "cs01-evidence-bundle.zip"
    if evidence_zip.exists():
        from cs01.pipeline.stage6_report.evidence_locker import verify_evidence_bundle
        is_valid, _ = verify_evidence_bundle(evidence_zip)
        if is_valid:
            console.print("[green]✔ Evidence Bundle cryptographically verified (Rule 13 compliant)[/green]")

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

    if exit_code == EXIT_POLICY_FAIL:
        console.print(
            f"[red bold]✖ POLICY GATE FAILED[/red bold] — "
            f"One or more findings at or above '{cfg.fail_on}' severity."
        )
    elif exit_code == EXIT_PARTIAL_SCAN:
        console.print(
            "[yellow]⚠ PARTIAL SCAN[/yellow] — Some files could not be parsed. "
            "See stage2_model.json for details."
        )
    else:
        console.print("[bold green]✔ SCAN CLEAN[/bold green] — No findings at or above threshold.")

    return exit_code
