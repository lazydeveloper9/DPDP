"""
Stage 6 Executive HTML DPO Audit Report Exporter
================================================
Renders a standalone, responsive, modern HTML compliance report for DPOs, AppSec teams,
and executive leadership.
"""

from __future__ import annotations
from pathlib import Path
from jinja2 import Template

from cs01.models import ScoredFindingBundle, Severity
from cs01.models.graph import DataFlowGraph

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CS-01 DPDP Compliance Audit Report</title>
<style>
  :root {
    --bg: #0f172a; --surface: #1e293b; --border: #334155;
    --text: #f8fafc; --text-muted: #94a3b8;
    --critical: #ef4444; --high: #f97316; --medium: #eab308; --low: #3b82f6; --success: #22c55e;
  }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: var(--bg); color: var(--text); margin: 0; padding: 2rem;
  }
  .container { max-width: 1200px; margin: 0 auto; }
  .header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid var(--border); padding-bottom: 1.5rem; margin-bottom: 2rem; }
  .header h1 { margin: 0; font-size: 1.8rem; color: #38bdf8; }
  .badge { padding: 0.35rem 0.8rem; border-radius: 9999px; font-weight: 600; font-size: 0.85rem; }
  .badge-capped { background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid #ef4444; }
  .badge-clean { background: rgba(34, 197, 94, 0.2); color: #86efac; border: 1px solid #22c55e; }
  .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
  .metric-card { background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.25rem; }
  .metric-label { font-size: 0.85rem; color: var(--text-muted); text-transform: uppercase; margin-bottom: 0.5rem; }
  .metric-value { font-size: 2.2rem; font-weight: 700; }
  .pillars-section { margin-bottom: 2.5rem; }
  .pillar-card { background: var(--surface); border: 1px solid var(--border); border-radius: 0.5rem; padding: 1rem; margin-bottom: 0.75rem; }
  .pillar-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
  .progress-bar { width: 100%; height: 8px; background: #334155; border-radius: 4px; overflow: hidden; }
  .progress-fill { height: 100%; background: #38bdf8; transition: width 0.3s; }
  .findings-table { width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.95rem; }
  .findings-table th { background: #1e293b; color: var(--text-muted); text-align: left; padding: 0.75rem; border-bottom: 2px solid var(--border); }
  .findings-table td { padding: 0.85rem 0.75rem; border-bottom: 1px solid var(--border); }
  .sev-tag { font-weight: 700; font-size: 0.8rem; padding: 0.2rem 0.5rem; border-radius: 4px; }
  .sev-CRITICAL { background: rgba(239, 68, 68, 0.2); color: #f87171; }
  .sev-HIGH { background: rgba(249, 115, 22, 0.2); color: #fb923c; }
  .sev-MEDIUM { background: rgba(234, 179, 8, 0.2); color: #facc15; }
  .code-snippet { background: #0b1120; padding: 0.6rem; border-radius: 4px; font-family: monospace; font-size: 0.85rem; color: #cbd5e1; margin-top: 0.4rem; overflow-x: auto; }
  .disclaimer { margin-top: 3rem; padding: 1.25rem; background: rgba(51, 65, 85, 0.3); border: 1px solid var(--border); border-radius: 0.5rem; font-size: 0.8rem; color: var(--text-muted); }
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <div>
      <h1>CS-01 DPDP Compliance Audit</h1>
      <p style="color: var(--text-muted); margin: 0.3rem 0 0 0;">Target: <code>{{ bundle.scan_root }}</code> · Scan ID: <code>{{ bundle.scan_id[:8] }}</code></p>
    </div>
    <div>
      {% if bundle.readiness.is_capped %}
        <span class="badge badge-capped">⚠️ READINESS CAPPED BY STATUTORY CRITICALS</span>
      {% else %}
        <span class="badge badge-clean">STATUS: CLEAN EXECUTION</span>
      {% endif %}
    </div>
  </div>

  <div class="metrics-grid">
    <div class="metric-card">
      <div class="metric-label">DPDP Readiness Score</div>
      <div class="metric-value" style="color: {% if bundle.readiness.overall < 70 %}#ef4444{% else %}#22c55e{% endif %};">
        {{ bundle.readiness.overall }}<span style="font-size: 1.2rem; color: var(--text-muted);">/100</span>
      </div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Max Penalty Ceiling Engaged</div>
      <div class="metric-value" style="font-size: 1.25rem; color: #fb923c; padding-top: 0.5rem;">
        {{ bundle.readiness.max_statutory_ceiling_engaged }}
      </div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Open Critical Findings</div>
      <div class="metric-value" style="color: #ef4444;">{{ bundle.readiness.open_critical_count }}</div>
    </div>
    <div class="metric-card">
      <div class="metric-label">Open High Findings</div>
      <div class="metric-value" style="color: #f97316;">{{ bundle.readiness.open_high_count }}</div>
    </div>
  </div>

  {% if bundle.readiness.cap_reason %}
  <div style="background: rgba(239, 68, 68, 0.1); border-left: 4px solid #ef4444; padding: 1rem; margin-bottom: 2rem; border-radius: 0 4px 4px 0;">
    <strong>Statutory Capping Activated:</strong> {{ bundle.readiness.cap_reason }}
  </div>
  {% endif %}

  <div class="pillars-section">
    <h2>Compliance by Statutory Pillar</h2>
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem;">
      {% for pillar in bundle.readiness.pillars %}
      <div class="pillar-card">
        <div class="pillar-header">
          <strong>{{ pillar.label }}</strong>
          <span style="color: #38bdf8; font-weight: 700;">{{ pillar.score }}%</span>
        </div>
        <div class="progress-bar">
          <div class="progress-fill" style="width: {{ pillar.score }}%;"></div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>

  {% if dataflow_graph %}
  <div style="margin-bottom: 2.5rem; background: var(--surface); border: 1px solid var(--border); border-radius: 0.75rem; padding: 1.25rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
      <div>
        <h2 style="margin: 0; font-size: 1.3rem; color: #38bdf8;">Interactive Personal Data-Flow &amp; Leak Visualization (2D + 3D)</h2>
        <p style="color: var(--text-muted); font-size: 0.85rem; margin-top: 0.25rem;">
          Dynamic architectural map tracing personal data flows across Collection, API, Storage, Infra, and Egress sinks.
        </p>
      </div>
      <div>
        <a href="cs01-dataflow.html" target="_blank" style="background: #2563eb; color: #ffffff; text-decoration: none; padding: 0.5rem 1rem; border-radius: 6px; font-weight: 600; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 0.5rem;">
          🚀 Open Fullscreen 2D/3D Cockpit ↗
        </a>
      </div>
    </div>
    <div style="display: flex; gap: 1rem; margin-bottom: 1rem; font-size: 0.82rem;">
      <span style="color: #ef4444; font-weight: 700;">⚠️ PII Leaks: {{ dataflow_graph.summary_metrics.leak_edges }}</span>
      <span style="color: #f59e0b; font-weight: 700;">⚠️ Unconsented Sinks: {{ dataflow_graph.summary_metrics.unconsented_storage_edges }}</span>
      <span style="color: #10b981; font-weight: 700;">✔ Compliant Controls: {{ dataflow_graph.summary_metrics.compliant_edges }}</span>
      <span style="color: #94a3b8;">Active Tiers: {{ dataflow_graph.summary_metrics.active_layers|join(', ') }}</span>
    </div>
    <div style="border: 1px solid var(--border); border-radius: 6px; overflow: hidden; height: 560px; background: #05070d;">
      <iframe src="cs01-dataflow.html" style="width: 100%; height: 100%; border: none;"></iframe>
    </div>
  </div>
  {% endif %}

  <h2>Statutory Remediation Backlog (Ranked by Priority Score)</h2>
  <table class="findings-table">
    <thead>
      <tr>
        <th style="width: 100px;">Priority</th>
        <th style="width: 100px;">Severity</th>
        <th style="width: 140px;">Rule & Section</th>
        <th>Violation & Remediation</th>
        <th style="width: 220px;">Location</th>
      </tr>
    </thead>
    <tbody>
      {% for f in bundle.findings %}
      <tr>
        <td><strong>{{ "%.3f"|format(f.priority_score) }}</strong></td>
        <td><span class="sev-tag sev-{{ f.severity.value }}">{{ f.severity.value }}</span></td>
        <td>
          <code>{{ f.rule_id }}</code><br>
          <small style="color: #38bdf8;">{{ f.dpdp_section }}</small>
        </td>
        <td>
          <strong>{{ f.message }}</strong><br>
          <small style="color: #94a3b8;">{{ f.statutory_ceiling_display }}</small>
          {% if f.snippet %}
            <div class="code-snippet">{{ f.snippet }}</div>
          {% endif %}
          <div style="margin-top: 0.4rem; color: #86efac; font-size: 0.85rem;">
            💡 <strong>Remediation:</strong> {{ f.remediation }}
          </div>
        </td>
        <td>
          <code>{{ f.file or 'Whole Repository' }}</code>
          {% if f.line_start %}:{{ f.line_start }}{% endif %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="disclaimer">
    <strong>Statutory Disclaimer:</strong>
    This document is a technical compliance audit generated by CS-01. Penalties under India's Digital Personal Data Protection Act, 2023 are statutory maximum ceilings prescribed in the Schedule. Actual penalties are discretionary and determined by the Data Protection Board of India (DPBI) after inquiry under Section 33(2). CS-01 is a technical auditing instrument and does not constitute formal legal counsel.
  </div>
</div>
</body>
</html>
"""


def export_html_report(
    bundle: ScoredFindingBundle,
    output_path: Path | str,
    dataflow_graph: Optional[DataFlowGraph] = None,
) -> None:
    """Render the executive HTML audit report via Jinja2."""
    template = Template(HTML_TEMPLATE)
    rendered = template.render(bundle=bundle, dataflow_graph=dataflow_graph)

    p = Path(output_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(rendered)
