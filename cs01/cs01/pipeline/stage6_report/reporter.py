"""
Pipeline Stage 6 — Generate Reports & Trigger Bonus Modules
============================================================
Entry point: run_report(bundle, cfg, output_dir)

Generates:
  1. cs01-findings.sarif (GitHub Code Scanning)
  2. gl-sast-report.json (GitLab SAST)
  3. cs01-dpo-report.html (Executive HTML)
  4. cs01-compliance.json (Canonical compliance register)
  5. ropa_map.json (Draft RoPA data-flow)
  6. consent_audit.json (Consent lifecycle audit)
  7. patches/*.patch (Deterministic fix diffs)
  8. cs01-evidence-bundle.zip (Rule 13 tamper-evident bundle with SHA-256 sidecars)
"""

from __future__ import annotations
from pathlib import Path
from typing import Any

from cs01.models import ScoredFindingBundle, ScanConfig
from cs01.utils import save_json
from .sarif_exporter import export_sarif
from .gitlab_exporter import export_gitlab_sast
from .html_exporter import export_html_report
from .markdown_exporter import export_markdown_report
from .ropa_exporter import export_ropa_draft
from .evidence_locker import create_evidence_bundle
from cs01.bonus.patch_generator.patcher import generate_patches
from cs01.bonus.consent_auditor.auditor import audit_consent_flow


def run_report(
    bundle: ScoredFindingBundle,
    cfg: ScanConfig,
    output_dir: Path | str,
) -> dict[str, Path]:
    """Execute all report renderers and package the evidence bundle."""
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    generated_files: dict[str, Path] = {}

    # 1. Canonical JSON Compliance Register
    json_path = out_dir / "cs01-compliance.json"
    save_json(bundle, json_path)
    generated_files["cs01-compliance.json"] = json_path

    # 2. SARIF 2.1.0 (GitHub Code Scanning)
    if "sarif" in cfg.output_formats or "all" in cfg.output_formats:
        sarif_path = out_dir / "cs01-findings.sarif"
        export_sarif(bundle, sarif_path)
        generated_files["cs01-findings.sarif"] = sarif_path

    # 3. GitLab SAST JSON
    gl_path = out_dir / "gl-sast-report.json"
    export_gitlab_sast(bundle, gl_path)
    generated_files["gl-sast-report.json"] = gl_path

    # 4. Executive HTML DPO Report
    if "html" in cfg.output_formats or "all" in cfg.output_formats:
        html_path = out_dir / "cs01-dpo-report.html"
        export_html_report(bundle, html_path)
        generated_files["cs01-dpo-report.html"] = html_path

    # 4b. Canonical Assessment Markdown Report
    md_path = out_dir / "cs01-report.md"
    export_markdown_report(bundle, cfg, md_path)
    generated_files["cs01-report.md"] = md_path

    # 5. RoPA Technical Draft
    ropa_path = out_dir / "ropa_map.json"
    export_ropa_draft(bundle, ropa_path)
    generated_files["ropa_map.json"] = ropa_path

    # 6. Bonus: Consent Flow Audit
    consent_path = out_dir / "consent_audit.json"
    audit_consent_flow(bundle, consent_path)
    generated_files["consent_audit.json"] = consent_path

    # 7. Bonus: Patch Generator
    generate_patches(bundle, out_dir)

    # 7b. Local AI Compliance Report (Qwen 2.5 Coder 3B)
    if cfg.ai.enabled or cfg.engine.ai_triage:
        from cs01.ai import LocalLLMClient, generate_full_compliance_report
        client = LocalLLMClient(
            model=cfg.ai.model,
            endpoint=cfg.ai.endpoint,
            temperature=cfg.ai.temperature,
            timeout=cfg.ai.timeout_seconds,
        )
        if client.is_available():
            try:
                ai_report_md = generate_full_compliance_report(bundle, client, cfg)
                ai_brief_path = out_dir / "dpo_ai_executive_brief.md"
                ai_full_path = out_dir / "ai_compliance_report.md"
                with open(ai_brief_path, "w", encoding="utf-8") as f:
                    f.write(ai_report_md)
                with open(ai_full_path, "w", encoding="utf-8") as f:
                    f.write(ai_report_md)
                generated_files["dpo_ai_executive_brief.md"] = ai_brief_path
                generated_files["ai_compliance_report.md"] = ai_full_path
            except Exception as e:
                if cfg.debug:
                    print(f"[dim]Local LLM generation note: {e}[/dim]")
        elif cfg.debug:
            print(f"[dim]Local LLM endpoint {cfg.ai.endpoint} not reachable. Skipping AI brief.[/dim]")

    # 8. Cryptographic Rule 13 Evidence Bundle
    bundle_zip_path = out_dir / "cs01-evidence-bundle.zip"
    create_evidence_bundle(
        report_files=generated_files,
        scan_id=bundle.scan_id,
        scan_timestamp=bundle.scan_timestamp,
        cs01_version=bundle.cs01_version,
        output_zip_path=bundle_zip_path,
    )
    generated_files["cs01-evidence-bundle.zip"] = bundle_zip_path

    return generated_files
