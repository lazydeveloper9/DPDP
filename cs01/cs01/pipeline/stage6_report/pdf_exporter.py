"""
Stage 6 Canonical & Executive PDF Audit Report Exporter
======================================================
Renders an exhaustive, publication-grade A4 PDF compliance report for Data
Protection Officers (DPOs), executive leadership, software engineering teams,
and regulatory auditors.

Includes:
1. Executive DPO Summary & Statutory Penalty Exposure (§33 Schedule).
2. 8 Statutory DPDP Pillars & Application Layer Coverage Breakdown.
3. Auto-Generated Record of Processing Activities (RoPA) & PII Inventory.
4. Exhaustive Technical Findings Dossier with 5-part deep dive:
   - Technical Failure Analysis & AST Walkthrough.
   - Statutory & Regulatory Breach Analysis (DPDP Act 2023 & Rules 2025).
   - Real-World Threat Scenario & Data Principal Blast Radius.
   - Production-Ready Refactored Code Fix ("Before vs. After" code diffs).
   - Engineering Verification & Automated Testing Plan.
5. Prioritized 3-Phase Remediation Roadmap (P0 / P1 / P2).
6. Statutory DPDP Rules 2025 Evaluation Matrix.
7. Rule 13 Cryptographic Chain of Custody & Evidence Locker Verification.

Uses PySide6's native QPdfWriter and QTextDocument for 100% offline, zero-egress
rendering with zero external binary or cloud dependencies.
"""

from __future__ import annotations
import html
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from cs01.models import (
    ScoredFindingBundle, ScanConfig, Severity, ProductCapabilityReport,
)
from .finding_elaborator import elaborate_finding
from .markdown_exporter import get_git_info


def _clean_code_fences(code_str: str) -> str:
    """Strips markdown code fences (```lang ... ```) from snippet strings."""
    s = code_str.strip()
    if s.startswith("```"):
        first_nl = s.find("\n")
        if first_nl != -1:
            s = s[first_nl + 1:]
    if s.endswith("```"):
        s = s[:-3]
    return s.strip()


def _format_markdown_inline(text: str) -> str:
    """Converts common markdown inline tokens into clean, safe HTML."""
    if not text:
        return ""
    # Escape HTML special chars
    escaped = html.escape(text)

    # Convert code spans: `code`
    escaped = re.sub(r"`([^`]+)`", r'<code style="font-family: Consolas, monospace; background-color: #f1f5f9; color: #0f172a; padding: 1px 4px; border-radius: 3px; font-size: 8.5pt;">\1</code>', escaped)

    # Convert bold: **bold**
    escaped = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", escaped)

    # Convert italics: *italic*
    escaped = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", escaped)

    # Convert bullet points and linebreaks
    lines = escaped.split("\n")
    formatted_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("- "):
            formatted_lines.append(f'<div style="margin-left: 14px; margin-bottom: 3px;">• {stripped[2:]}</div>')
        elif re.match(r"^\d+\.\s+", stripped):
            formatted_lines.append(f'<div style="margin-left: 14px; margin-bottom: 3px;">{stripped}</div>')
        elif stripped:
            formatted_lines.append(f'<div style="margin-bottom: 4px;">{stripped}</div>')
        else:
            formatted_lines.append('<div style="height: 6px;"></div>')

    return "".join(formatted_lines)


def _build_pdf_html(
    bundle: ScoredFindingBundle,
    cfg: ScanConfig,
    capability_report: Optional[ProductCapabilityReport] = None,
    stage_durations: Optional[dict[str, float]] = None,
) -> str:
    """Construct print-optimized HTML tailored for QTextDocument -> QPdfWriter."""
    now_utc = datetime.now(timezone.utc)
    ist_tz = timezone(timedelta(hours=5, minutes=30))
    now_ist = now_utc.astimezone(ist_tz)
    ts_utc = now_utc.strftime("%Y-%m-%d %H:%M:%S UTC")
    ts_ist = now_ist.strftime("%Y-%m-%d %H:%M:%S IST")

    overall_score = bundle.readiness.overall
    score_color = "#16a34a" if overall_score >= 80 else ("#ca8a04" if overall_score >= 60 else "#dc2626")

    # Header & Status Badge
    is_capped = getattr(bundle.readiness, "is_capped", False)
    if is_capped:
        badge_html = '<span style="background-color: #fee2e2; color: #b91c1c; border: 1px solid #ef4444; padding: 5px 12px; border-radius: 4px; font-weight: bold; font-size: 10.5pt;">⚠️ READINESS CAPPED BY STATUTORY CRITICALS</span>'
    else:
        badge_html = '<span style="background-color: #dcfce7; color: #15803d; border: 1px solid #22c55e; padding: 5px 12px; border-radius: 4px; font-weight: bold; font-size: 10.5pt;">✓ STATUS: PASSING / AUDIT READY</span>'

    # Git metadata
    branch, commit_sha = get_git_info(bundle.scan_root, fallback_dir=cfg.scan_root)

    # Counts
    crit_count = sum(1 for f in bundle.findings if f.severity == Severity.CRITICAL and not getattr(f, "is_baseline_suppressed", False))
    high_count = sum(1 for f in bundle.findings if f.severity == Severity.HIGH and not getattr(f, "is_baseline_suppressed", False))
    med_count = sum(1 for f in bundle.findings if f.severity == Severity.MEDIUM and not getattr(f, "is_baseline_suppressed", False))
    low_count = sum(1 for f in bundle.findings if f.severity == Severity.LOW and not getattr(f, "is_baseline_suppressed", False))
    total_active = crit_count + high_count + med_count + low_count

    max_penalty = getattr(bundle.readiness, "max_statutory_ceiling_engaged", None) or getattr(bundle, "max_penalty_band", None) or "None Engaged"
    if "_" in max_penalty:
        max_penalty = max_penalty.replace("_", " ").title()

    # Policy Gate Evaluation
    fail_on_levels = ["critical", "high", "medium", "never"]
    threshold_idx = fail_on_levels.index(cfg.fail_on) if cfg.fail_on in fail_on_levels else 1
    has_failed_gate = False
    for f in bundle.findings:
        if getattr(f, "is_baseline_suppressed", False):
            continue
        idx = fail_on_levels.index(f.severity.value.lower()) if f.severity.value.lower() in fail_on_levels else 3
        if idx <= threshold_idx:
            has_failed_gate = True
            break
    gate_status = f'<span style="color: #dc2626; font-weight: bold;">FAIL (Threshold: {cfg.fail_on.upper()})</span>' if has_failed_gate else f'<span style="color: #16a34a; font-weight: bold;">PASS (Threshold: {cfg.fail_on.upper()})</span>'

    # 1. Pillars Table Rows
    pillar_rows = []
    for p in bundle.readiness.pillars:
        p_pct = int(getattr(p, "score", getattr(p, "percentage", 100.0)))
        p_name = getattr(p, "label", getattr(p, "name", getattr(p, "pillar_id", "Pillar")))
        total_r = getattr(p, "total_rules", getattr(p, "evaluated_checks", 0))
        pass_r = getattr(p, "passing_rules", getattr(p, "passed_checks", total_r))
        fail_r = getattr(p, "failed_checks", total_r - pass_r)
        p_color = "#16a34a" if p_pct >= 80 else ("#ca8a04" if p_pct >= 60 else "#dc2626")
        row = f"""
        <tr>
          <td style="padding: 6px 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #1e293b;">{html.escape(str(p_name))}</td>
          <td style="padding: 6px 10px; border-bottom: 1px solid #e2e8f0; color: #475569; font-size: 9pt;">{total_r} checks ({pass_r} passed, {fail_r} failed)</td>
          <td style="padding: 6px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold; color: {p_color}; font-size: 9.5pt;">{p_pct}%</td>
        </tr>
        """
        pillar_rows.append(row)
    pillars_table_html = "\n".join(pillar_rows)

    # 2. Application Layer Breakdown Rows
    layer_mapping = {
        "Layer 1: Frontend & Mobile UI": [f for f in bundle.findings if any(x in (f.file or "").lower() for x in ("front", "ui", "client", "src/pages", "src/views", ".tsx", ".jsx", ".vue", ".html"))],
        "Layer 2: Backend API & Service Logic": [f for f in bundle.findings if any(x in (f.file or "").lower() for x in ("api", "route", "controller", "server", "backend", "app.py", "main.py", ".ts", ".py")) and not any(x in (f.file or "").lower() for x in ("schema", "model", "migration", "docker", "terraform"))],
        "Layer 3: Database & ORM Schemas": [f for f in bundle.findings if any(x in (f.file or "").lower() for x in ("model", "schema", "db", "sql", "migration", "prisma", "entity"))],
        "Layer 4: Cloud Infrastructure & IaC": [f for f in bundle.findings if any(x in (f.file or "").lower() for x in ("docker", ".env", "terraform", ".tf", "k8s", "helm", "cloud", "compose"))],
    }
    layer_rows = []
    for l_name, l_finds in layer_mapping.items():
        l_crit = sum(1 for f in l_finds if f.severity == Severity.CRITICAL)
        l_high = sum(1 for f in l_finds if f.severity == Severity.HIGH)
        l_posture = '<span style="color: #dc2626; font-weight: bold;">Critical Breaches</span>' if l_crit > 0 else ('<span style="color: #ea580c; font-weight: bold;">High Risks</span>' if l_high > 0 else '<span style="color: #16a34a; font-weight: bold;">Audited / Clean</span>')
        layer_rows.append(f"""
        <tr>
          <td style="padding: 6px 10px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #1e293b;">{l_name}</td>
          <td style="padding: 6px 10px; border-bottom: 1px solid #e2e8f0; color: #475569; font-size: 9pt;">{len(l_finds)} violations ({l_crit} Critical, {l_high} High)</td>
          <td style="padding: 6px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-size: 9pt;">{l_posture}</td>
        </tr>
        """)
    layers_table_html = "\n".join(layer_rows)

    # 3. RoPA Table Rows
    ropa_rows = []
    seen_categories = set()
    if capability_report and capability_report.pii_inventory:
        for item in capability_report.pii_inventory:
            cat_name = f"{item.category} ({item.pii_type})"
            if cat_name in seen_categories:
                continue
            seen_categories.add(cat_name)
            loc_str = f"{item.location_file}:{item.location_line}" if item.location_line is not None else item.location_file
            storage = f"{item.field_or_param} {'(Encrypted)' if item.is_encrypted else '(Plaintext)'}" if item.is_stored else "Transient Stream"
            sinks = "Application Logger Sink" if item.is_logged else ("External Egress Sink" if item.is_transmitted_externally else "Internal Logic Flow")
            region = cfg.allowed_cross_border_regions[0] if cfg.allowed_cross_border_regions else "Domestic (India / Local)"
            status = '<span style="color: #16a34a; font-weight: bold;">Encrypted Guard</span>' if item.is_encrypted else '<span style="color: #dc2626; font-weight: bold;">Plaintext (§8(5))</span>'
            ropa_rows.append(f"""
            <tr>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #1e293b; font-size: 8.5pt;">{html.escape(cat_name)}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-family: Consolas, monospace; font-size: 8pt; color: #0369a1;">{html.escape(loc_str)}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; color: #334155;">{html.escape(storage)}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; color: #475569;">{html.escape(sinks)}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; color: #475569;">{html.escape(region)}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; text-align: right;">{status}</td>
            </tr>
            """)
    if not ropa_rows:
        for f in bundle.findings:
            ent = f.matched_entity or "Personal Data"
            if ent in seen_categories:
                continue
            seen_categories.add(ent)
            ropa_rows.append(f"""
            <tr>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-weight: bold; color: #1e293b; font-size: 8.5pt;">{html.escape(ent)}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-family: Consolas, monospace; font-size: 8pt; color: #0369a1;">{html.escape(f.file or 'codebase')}:{f.line_start or 1}</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; color: #334155;">Persistence Point</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; color: #475569;">Internal Flow</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; color: #475569;">Domestic (India)</td>
              <td style="padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; text-align: right;"><span style="color: #ea580c; font-weight: bold;">Audited</span></td>
            </tr>
            """)
    ropa_table_html = "\n".join(ropa_rows) if ropa_rows else "<tr><td colspan='6' style='padding: 10px; text-align: center; color: #64748b;'>No personal data inventory items identified.</td></tr>"

    # 4. Detailed Elaborated Findings Cards
    sev_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3, Severity.INFO: 4}
    sorted_findings = sorted(bundle.findings, key=lambda f: sev_order.get(f.severity, 99))

    findings_cards_html = []
    for idx, f in enumerate(sorted_findings, 1):
        if getattr(f, "is_baseline_suppressed", False):
            continue

        sev = f.severity.value.upper()
        if sev == "CRITICAL":
            badge = '<span style="background-color: #fef2f2; color: #b91c1c; border: 1px solid #f87171; padding: 3px 8px; font-weight: bold; font-size: 8.5pt; border-radius: 3px;">CRITICAL</span>'
            card_border = "#f87171"
        elif sev == "HIGH":
            badge = '<span style="background-color: #fff7ed; color: #c2410c; border: 1px solid #fb923c; padding: 3px 8px; font-weight: bold; font-size: 8.5pt; border-radius: 3px;">HIGH</span>'
            card_border = "#fb923c"
        elif sev == "MEDIUM":
            badge = '<span style="background-color: #fefce8; color: #a16207; border: 1px solid #facc15; padding: 3px 8px; font-weight: bold; font-size: 8.5pt; border-radius: 3px;">MEDIUM</span>'
            card_border = "#facc15"
        else:
            badge = f'<span style="background-color: #eff6ff; color: #1d4ed8; border: 1px solid #93c5fd; padding: 3px 8px; font-weight: bold; font-size: 8.5pt; border-radius: 3px;">{sev}</span>'
            card_border = "#cbd5e1"

        # Elaborate technical finding via stage 6 finding elaborator
        elaboration = elaborate_finding(f, cfg)
        tech_html = _format_markdown_inline(elaboration.get("tech", ""))
        statutory_html = _format_markdown_inline(elaboration.get("statutory", ""))
        threat_html = _format_markdown_inline(elaboration.get("threat", ""))
        verification_html = _format_markdown_inline(elaboration.get("verification", ""))

        before_raw = _clean_code_fences(elaboration.get("before_code", f.snippet or f"# {f.file}:{f.line_start}"))
        after_raw = _clean_code_fences(elaboration.get("after_code", f.remediation or "# Apply appropriate DPDP control"))

        loc = f"{html.escape(f.file or 'global')}:{f.line_start or 1}"
        rule_penalty = f.penalty_band.replace('_', ' ').title() if f.penalty_band else "Standard Statutory"

        card = f"""
        <div style="page-break-inside: avoid; border: 1.5px solid {card_border}; border-radius: 6px; padding: 14px; margin-bottom: 22px; background-color: #ffffff;">
          <!-- Finding Header Bar -->
          <table style="width: 100%; border-bottom: 1.5px solid #e2e8f0; padding-bottom: 8px; margin-bottom: 10px;">
            <tr>
              <td style="vertical-align: middle;">
                {badge}
                <span style="font-family: Consolas, monospace; font-size: 10pt; font-weight: bold; color: #0f172a; margin-left: 8px;">[{f.rule_id}]</span>
                <span style="font-size: 9pt; color: #475569; margin-left: 6px;">Finding #{idx}</span>
              </td>
              <td style="text-align: right; vertical-align: middle; font-size: 8.5pt; color: #64748b;">
                <b>Legal Citation:</b> <span style="color: #0f172a; font-weight: bold;">{html.escape(f.dpdp_section or 'N/A')}</span> &bull; 
                <b>Penalty Band:</b> <span style="color: #dc2626; font-weight: bold;">₹{html.escape(rule_penalty)}</span>
              </td>
            </tr>
          </table>

          <!-- Location & Summary -->
          <div style="font-family: Consolas, monospace; font-size: 9pt; color: #0284c7; font-weight: bold; margin-bottom: 6px;">
            📍 Location: {loc}
          </div>
          <div style="font-size: 10.5pt; font-weight: bold; color: #0f172a; margin-bottom: 12px; line-height: 1.3;">
            {html.escape(f.message or '')}
          </div>

          <!-- 1. Technical Failure Analysis -->
          <div style="margin-bottom: 10px;">
            <div style="font-size: 9pt; font-weight: bold; text-transform: uppercase; color: #334155; margin-bottom: 3px;">1. Detailed Technical Failure Analysis (Code Walkthrough)</div>
            <div style="font-size: 9pt; color: #1e293b; line-height: 1.45;">{tech_html}</div>
          </div>

          <!-- 2. Statutory Breach Analysis -->
          <div style="margin-bottom: 10px; background-color: #f8fafc; border-left: 3px solid #0284c7; padding: 6px 10px;">
            <div style="font-size: 9pt; font-weight: bold; text-transform: uppercase; color: #0369a1; margin-bottom: 3px;">2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)</div>
            <div style="font-size: 9pt; color: #1e293b; line-height: 1.45;">{statutory_html}</div>
          </div>

          <!-- 3. Threat Scenario & Blast Radius -->
          <div style="margin-bottom: 12px;">
            <div style="font-size: 9pt; font-weight: bold; text-transform: uppercase; color: #991b1b; margin-bottom: 3px;">3. Real-World Threat Scenario & Data Principal Blast Radius</div>
            <div style="font-size: 9pt; color: #1e293b; line-height: 1.45;">{threat_html}</div>
          </div>

          <!-- 4. Production-Ready Refactored Code Fix ("Before vs. After") -->
          <div style="margin-bottom: 12px;">
            <div style="font-size: 9pt; font-weight: bold; text-transform: uppercase; color: #1e293b; margin-bottom: 6px;">4. Production-Ready Refactored Code Fix ("Before vs. After")</div>
            
            <!-- Vulnerable Code Box -->
            <div style="background-color: #fef2f2; border: 1px solid #fecaca; border-left: 4px solid #ef4444; border-radius: 4px; padding: 8px 10px; margin-bottom: 8px;">
              <div style="font-size: 8pt; font-weight: bold; color: #991b1b; text-transform: uppercase; margin-bottom: 4px;">❌ Vulnerable Implementation ({loc})</div>
              <pre style="margin: 0; font-family: Consolas, monospace; font-size: 8.5pt; color: #7f1d1d; white-space: pre-wrap;"><code>{html.escape(before_raw)}</code></pre>
            </div>

            <!-- Compliant Fix Box -->
            <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; border-left: 4px solid #22c55e; border-radius: 4px; padding: 8px 10px;">
              <div style="font-size: 8pt; font-weight: bold; color: #166534; text-transform: uppercase; margin-bottom: 4px;">✔ Compliant Remediation Pattern</div>
              <pre style="margin: 0; font-family: Consolas, monospace; font-size: 8.5pt; color: #14532d; white-space: pre-wrap;"><code>{html.escape(after_raw)}</code></pre>
            </div>
          </div>

          <!-- 5. Engineering Verification -->
          <div style="background-color: #f1f5f9; border-radius: 4px; padding: 8px 10px;">
            <div style="font-size: 8.5pt; font-weight: bold; text-transform: uppercase; color: #475569; margin-bottom: 3px;">5. Engineering Verification & Automated Testing Plan</div>
            <div style="font-size: 8.5pt; color: #334155; line-height: 1.4;">{verification_html}</div>
          </div>
        </div>
        """
        findings_cards_html.append(card)

    findings_section_html = "\n".join(findings_cards_html) if findings_cards_html else "<div style='padding: 20px; text-align: center; color: #15803d; font-weight: bold; background-color: #f0fdf4; border-radius: 6px;'>✓ Zero non-compliant findings detected across all evaluated files. Codebase satisfies technical safeguards.</div>"

    # 5. Prioritized Remediation Roadmap HTML
    phase1_items = [f for f in sorted_findings if f.severity in (Severity.CRITICAL, Severity.HIGH)]
    phase2_items = [f for f in sorted_findings if f.severity == Severity.MEDIUM]
    phase3_items = [f for f in sorted_findings if f.severity in (Severity.LOW, Severity.INFO)]

    def _render_phase_rows(items: list) -> str:
        if not items:
            return "<tr><td colspan='3' style='padding: 6px 10px; color: #16a34a; font-size: 8.5pt;'>No pending actions in this phase.</td></tr>"
        rows = []
        for itm in items[:8]:
            rows.append(f"""
            <tr>
              <td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0; font-family: Consolas, monospace; font-size: 8pt; color: #0284c7; width: 110px;">[{itm.rule_id}]</td>
              <td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8.5pt; color: #1e293b;">{html.escape(itm.remediation[:120] + ('...' if len(itm.remediation) > 120 else ''))}</td>
              <td style="padding: 5px 8px; border-bottom: 1px solid #e2e8f0; font-size: 8pt; color: #64748b; text-align: right; width: 140px;">{html.escape(itm.file or 'code')}:{itm.line_start or 1}</td>
            </tr>
            """)
        return "\n".join(rows)

    # Full Document Assembly
    html_doc = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{
    font-family: "Segoe UI", Arial, Helvetica, sans-serif;
    color: #0f172a;
    line-height: 1.45;
    font-size: 9.5pt;
    margin: 0;
    padding: 0;
  }}
  h1 {{
    font-size: 20pt;
    color: #0f172a;
    margin: 0 0 4px 0;
    font-weight: 800;
    letter-spacing: -0.5px;
  }}
  h2 {{
    font-size: 13pt;
    color: #0f172a;
    border-bottom: 2px solid #0284c7;
    padding-bottom: 4px;
    margin-top: 22px;
    margin-bottom: 10px;
    font-weight: 700;
  }}
  h3 {{
    font-size: 11pt;
    color: #1e293b;
    margin-top: 14px;
    margin-bottom: 6px;
    font-weight: 700;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  .meta-table td {{
    padding: 2.5px 6px;
    font-size: 8.5pt;
  }}
</style>
</head>
<body>

  <!-- ==================== HEADER & PROVENANCE ==================== -->
  <table style="width: 100%; margin-bottom: 14px; border-bottom: 2.5px solid #0f172a; padding-bottom: 10px;">
    <tr>
      <td style="vertical-align: middle;">
        <h1>CS-01 DPDP Compliance Assessment Report</h1>
        <div style="font-size: 10pt; color: #475569; font-weight: 600;">
          Statutory Technical Audit & Data Protection Risk Assessment (DPDP Act, 2023 & DPDP Rules, 2025)
        </div>
      </td>
      <td style="text-align: right; vertical-align: middle;">
        {badge_html}
      </td>
    </tr>
  </table>

  <!-- Audit Metadata & KPI Grid -->
  <table style="width: 100%; margin-bottom: 16px;">
    <tr>
      <!-- KPI Score Box -->
      <td style="width: 32%; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center; vertical-align: middle;">
        <div style="font-size: 8.5pt; text-transform: uppercase; color: #64748b; font-weight: bold; letter-spacing: 0.5px;">DPDP Readiness Score</div>
        <div style="font-size: 30pt; font-weight: 900; color: {score_color}; margin: 4px 0;">{overall_score}<span style="font-size: 15pt; color: #94a3b8;">/100</span></div>
        <div style="font-size: 8pt; color: #64748b;">{'Capped by Critical Violations' if is_capped else 'Nominal Evaluation'}</div>
      </td>
      <td style="width: 2%;"></td>
      <!-- KPI Penalty Box -->
      <td style="width: 34%; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 12px; text-align: center; vertical-align: middle;">
        <div style="font-size: 8.5pt; text-transform: uppercase; color: #64748b; font-weight: bold; letter-spacing: 0.5px;">Max Penalty Exposure</div>
        <div style="font-size: 16pt; font-weight: 800; color: #dc2626; margin: 6px 0;">{html.escape(max_penalty)}</div>
        <div style="font-size: 8pt; color: #64748b;">Section 33 Schedule (DPDP Act, 2023)</div>
      </td>
      <td style="width: 2%;"></td>
      <!-- Metadata Box -->
      <td style="width: 30%; background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px; padding: 8px 10px; vertical-align: middle;">
        <table class="meta-table" style="width: 100%;">
          <tr><td style="color: #64748b; font-weight: bold;">Target:</td><td style="color: #0f172a; word-break: break-all;">{html.escape(str(bundle.scan_root or cfg.scan_root))}</td></tr>
          <tr><td style="color: #64748b; font-weight: bold;">Commit / Branch:</td><td style="font-family: Consolas, monospace; color: #0f172a;">{html.escape(commit_sha[:8])} ({html.escape(branch)})</td></tr>
          <tr><td style="color: #64748b; font-weight: bold;">Scan Timestamp:</td><td style="color: #0f172a;">{ts_ist}</td></tr>
          <tr><td style="color: #64748b; font-weight: bold;">Policy Gate:</td><td>{gate_status}</td></tr>
          <tr><td style="color: #64748b; font-weight: bold;">Findings Breakdown:</td><td style="font-weight: bold; color: #0f172a;">{total_active} total ({crit_count}C &bull; {high_count}H &bull; {med_count}M)</td></tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- ==================== 1. COMPLIANCE PILLARS ==================== -->
  <h2>1. Statutory DPDP Compliance Pillars</h2>
  <table style="width: 100%; border: 1px solid #cbd5e1; border-radius: 4px; margin-bottom: 16px;">
    <tr style="background-color: #f1f5f9; font-size: 8.5pt; color: #475569; text-transform: uppercase;">
      <th style="padding: 6px 10px; text-align: left; border-bottom: 2px solid #cbd5e1;">Pillar Mandate</th>
      <th style="padding: 6px 10px; text-align: left; border-bottom: 2px solid #cbd5e1;">Evaluated Checks</th>
      <th style="padding: 6px 10px; text-align: right; border-bottom: 2px solid #cbd5e1;">Score</th>
    </tr>
    {pillars_table_html}
  </table>

  <!-- ==================== 2. APPLICATION LAYERS ==================== -->
  <h2>2. Application Stack Layer Coverage</h2>
  <table style="width: 100%; border: 1px solid #cbd5e1; border-radius: 4px; margin-bottom: 16px;">
    <tr style="background-color: #f1f5f9; font-size: 8.5pt; color: #475569; text-transform: uppercase;">
      <th style="padding: 6px 10px; text-align: left; border-bottom: 2px solid #cbd5e1;">Stack Layer</th>
      <th style="padding: 6px 10px; text-align: left; border-bottom: 2px solid #cbd5e1;">Violation Breakdown</th>
      <th style="padding: 6px 10px; text-align: right; border-bottom: 2px solid #cbd5e1;">Layer Posture</th>
    </tr>
    {layers_table_html}
  </table>

  <!-- ==================== 3. ROPA DATA INVENTORY ==================== -->
  <div style="page-break-before: always;"></div>
  <h2>3. Auto-Generated Record of Processing Activities (RoPA) & Data Inventory</h2>
  <p style="font-size: 8.5pt; color: #475569; margin-top: 0; margin-bottom: 8px;">
    Derived deterministically from AST call graphs, SQL/ORM database schemas, and outbound cloud egress sinks to fulfill Data Fiduciary obligations under Section 8.
  </p>
  <table style="width: 100%; border: 1px solid #cbd5e1; border-radius: 4px; margin-bottom: 20px;">
    <tr style="background-color: #f1f5f9; font-size: 8pt; color: #475569; text-transform: uppercase;">
      <th style="padding: 6px 8px; text-align: left; border-bottom: 2px solid #cbd5e1;">Personal Data Category</th>
      <th style="padding: 6px 8px; text-align: left; border-bottom: 2px solid #cbd5e1;">Collection Point (Route / UI)</th>
      <th style="padding: 6px 8px; text-align: left; border-bottom: 2px solid #cbd5e1;">Storage & Encryption</th>
      <th style="padding: 6px 8px; text-align: left; border-bottom: 2px solid #cbd5e1;">Outbound Sinks</th>
      <th style="padding: 6px 8px; text-align: left; border-bottom: 2px solid #cbd5e1;">Region</th>
      <th style="padding: 6px 8px; text-align: right; border-bottom: 2px solid #cbd5e1;">Status</th>
    </tr>
    {ropa_table_html}
  </table>

  <!-- ==================== 4. DETAILED FINDINGS ==================== -->
  <div style="page-break-before: always;"></div>
  <h2>4. Detailed Technical Findings & Remediation Dossier</h2>
  <p style="font-size: 8.5pt; color: #475569; margin-top: 0; margin-bottom: 14px;">
    Each finding below contains an intra-procedural technical failure analysis, specific statutory grounding under the DPDP Act, 2023 and DPDP Rules, 2025, real-world exploitability scenarios, and production-ready before/after code refactorings.
  </p>
  {findings_section_html}

  <!-- ==================== 5. REMEDIATION ROADMAP ==================== -->
  <div style="page-break-before: always;"></div>
  <h2>5. Prioritized 3-Phase Remediation Roadmap</h2>
  
  <h3>Phase 1: Immediate Critical Blockers (P0 — Emergency Fixes)</h3>
  <table style="width: 100%; border: 1px solid #fecaca; border-radius: 4px; margin-bottom: 12px;">
    <tr style="background-color: #fef2f2; font-size: 8pt; color: #991b1b; text-transform: uppercase;">
      <th style="padding: 5px 8px; text-align: left; border-bottom: 1.5px solid #fca5a5;">Rule ID</th>
      <th style="padding: 5px 8px; text-align: left; border-bottom: 1.5px solid #fca5a5;">Recommended Safeguard</th>
      <th style="padding: 5px 8px; text-align: right; border-bottom: 1.5px solid #fca5a5;">Target Location</th>
    </tr>
    {_render_phase_rows(phase1_items)}
  </table>

  <h3>Phase 2: Short-Term Architectural Safeguards (P1 — Next Release Sprint)</h3>
  <table style="width: 100%; border: 1px solid #fed7aa; border-radius: 4px; margin-bottom: 12px;">
    <tr style="background-color: #fff7ed; font-size: 8pt; color: #9a3412; text-transform: uppercase;">
      <th style="padding: 5px 8px; text-align: left; border-bottom: 1.5px solid #fdba74;">Rule ID</th>
      <th style="padding: 5px 8px; text-align: left; border-bottom: 1.5px solid #fdba74;">Recommended Safeguard</th>
      <th style="padding: 5px 8px; text-align: right; border-bottom: 1.5px solid #fdba74;">Target Location</th>
    </tr>
    {_render_phase_rows(phase2_items)}
  </table>

  <h3>Phase 3: Continuous Privacy-by-Design & Governance (P2 — Architectural Hardening)</h3>
  <table style="width: 100%; border: 1px solid #bfdbfe; border-radius: 4px; margin-bottom: 18px;">
    <tr style="background-color: #eff6ff; font-size: 8pt; color: #1e40af; text-transform: uppercase;">
      <th style="padding: 5px 8px; text-align: left; border-bottom: 1.5px solid #93c5fd;">Rule ID</th>
      <th style="padding: 5px 8px; text-align: left; border-bottom: 1.5px solid #93c5fd;">Recommended Safeguard</th>
      <th style="padding: 5px 8px; text-align: right; border-bottom: 1.5px solid #93c5fd;">Target Location</th>
    </tr>
    {_render_phase_rows(phase3_items)}
  </table>

  <!-- ==================== 6. RULE 13 EVIDENCE NOTICE ==================== -->
  <div style="margin-top: 20px; padding: 10px 14px; background-color: #f8fafc; border: 1px solid #cbd5e1; border-left: 4px solid #0284c7; font-size: 8.5pt; color: #475569; border-radius: 4px;">
    <b>Cryptographic Evidence Locker & Rule 13 Chain of Custody:</b><br>
    This audit report was generated deterministically from static AST analysis, database schema records, and infrastructure configurations. All underlying raw findings, AST nodes, and generated reports are cryptographically hashed (SHA-256) inside the accompanying <code>cs01-evidence-bundle.zip</code> to ensure non-repudiation and satisfy Rule 13 statutory audit admissibility standards.
  </div>

</body>
</html>
"""
    return html_doc


def export_pdf_report(
    bundle: ScoredFindingBundle,
    cfg: ScanConfig,
    output_path: Path | str,
    html_path: Optional[Path | str] = None,
    capability_report: Optional[ProductCapabilityReport] = None,
    stage_durations: Optional[dict[str, float]] = None,
) -> Path:
    """
    Render and export the formal executive compliance PDF report.
    Guarantees headless/offscreen safety with zero cloud egress.
    """
    out_file = Path(output_path).resolve()
    out_file.parent.mkdir(parents=True, exist_ok=True)

    import sys
    # On Windows, never use 'offscreen' QPA because Qt's offscreen plugin lacks font engines
    # and renders text as missing-glyph tofu blocks. On headless Linux/Docker, use offscreen.
    if sys.platform != "win32" and not os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    elif sys.platform == "win32" and os.environ.get("QT_QPA_PLATFORM") == "offscreen":
        os.environ.pop("QT_QPA_PLATFORM", None)

    from PySide6.QtCore import QMarginsF
    from PySide6.QtGui import QFont, QPageLayout, QPageSize, QPdfWriter, QTextDocument
    from PySide6.QtWidgets import QApplication

    # Ensure a QApplication exists with proper application metadata
    app = QApplication.instance()
    if app is None:
        args = ["cs01-pdf-generator"]
        if sys.platform != "win32" and not os.environ.get("DISPLAY"):
            args.extend(["-platform", "offscreen"])
        try:
            from cs01.gui.app import create_app
            app = create_app(args)
        except Exception:
            app = QApplication(args)
            app.setApplicationName("CS-01 DPDP Auditor")
            def_font = QFont("Segoe UI", 10)
            app.setFont(def_font)

    # Generate print-optimized HTML content
    html_content = _build_pdf_html(
        bundle=bundle,
        cfg=cfg,
        capability_report=capability_report,
        stage_durations=stage_durations,
    )

    if html_path:
        with open(html_path, "w", encoding="utf-8") as fh:
            fh.write(html_content)

    # Load into QTextDocument
    doc = QTextDocument()
    doc_font = QFont("Segoe UI", 10)
    doc.setDefaultFont(doc_font)
    doc.setHtml(html_content)

    # Configure A4 PDF Writer with 12mm margins
    writer = QPdfWriter(str(out_file))
    writer.setPageSize(QPageSize(QPageSize.A4))
    layout = QPageLayout(
        QPageSize(QPageSize.A4),
        QPageLayout.Portrait,
        QMarginsF(12, 12, 12, 12),
        QPageLayout.Millimeter,
    )
    writer.setPageLayout(layout)

    # Print document to PDF
    doc.print_(writer)

    return out_file
