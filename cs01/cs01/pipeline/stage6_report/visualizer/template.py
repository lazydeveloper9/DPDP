"""
Stage 6 Visualizer HTML & JS Template Engine
============================================
Generates 100% offline, standalone interactive 2D (Cytoscape) and 3D (Three.js)
data-flow maps with visible 2D/3D text labels, tier banners, HUD filters,
animated particle flows, and click-to-inspect compliance drawer.
"""

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

from cs01.models.graph import DataFlowGraph, LayerTier, FlowStatus

VENDOR_DIR = Path(__file__).parent / "vendor"

def _load_vendor_js(filename: str) -> str:
    """Read a vendored JS file for inlining."""
    fpath = VENDOR_DIR / filename
    if fpath.exists():
        return fpath.read_text(encoding="utf-8", errors="replace")
    return f"/* Missing vendored library: {filename} */"

def render_standalone_html(graph: DataFlowGraph) -> str:
    """Render a fully self-contained offline HTML page containing the 2D + 3D visualizer."""
    cytoscape_js = _load_vendor_js("cytoscape.min.js")
    dagre_js = _load_vendor_js("dagre.min.js")
    cytoscape_dagre_js = _load_vendor_js("cytoscape-dagre.js")
    three_js = _load_vendor_js("three.min.js")
    orbit_controls_js = _load_vendor_js("OrbitControls.js")

    graph_data_json = graph.model_dump_json()

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CS-01 DPDP Data-Flow &amp; Leak Visualizer — {graph.repo_name}</title>
<style>
  :root {{
    --bg-base: #090d16;
    --bg-surface: #0f172a;
    --bg-card: #1e293b;
    --border: #334155;
    --text: #f8fafc;
    --text-muted: #94a3b8;
    --leak: #ef4444;
    --unconsented: #f59e0b;
    --compliant: #10b981;
    --route: #38bdf8;
    --dto: #818cf8;
    --storage: #34d399;
    --infra: #a855f7;
    --sink: #f43f5e;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    background: var(--bg-base);
    color: var(--text);
    overflow: hidden;
    height: 100vh;
    width: 100vw;
    display: flex;
    flex-direction: column;
  }}

  /* Top Navigation & HUD */
  #header-hud {{
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border);
    padding: 0.6rem 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 100;
  }}

  .header-left {{ display: flex; align-items: center; gap: 1rem; }}
  .header-title {{ font-size: 1.15rem; font-weight: 700; color: #38bdf8; }}
  .header-repo {{ background: rgba(56, 189, 248, 0.15); color: #7dd3fc; border: 1px solid rgba(56, 189, 248, 0.3); font-size: 0.8rem; padding: 0.2rem 0.6rem; border-radius: 4px; font-family: monospace; }}

  .view-switcher {{ display: flex; background: var(--bg-base); border: 1px solid var(--border); border-radius: 6px; padding: 2px; }}
  .view-btn {{ background: transparent; border: none; color: var(--text-muted); padding: 0.4rem 0.9rem; font-size: 0.85rem; font-weight: 600; cursor: pointer; border-radius: 4px; transition: all 0.2s; }}
  .view-btn.active {{ background: #2563eb; color: #ffffff; }}

  .camera-presets {{ display: flex; gap: 0.5rem; }}
  .preset-btn {{ background: var(--bg-card); border: 1px solid var(--border); color: var(--text); padding: 0.35rem 0.75rem; font-size: 0.8rem; border-radius: 4px; cursor: pointer; }}
  .preset-btn:hover {{ background: #334155; }}

  /* Filter Ribbon */
  #filter-ribbon {{
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border);
    padding: 0.45rem 1.25rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 1rem;
    z-index: 99;
  }}

  .filter-pills {{ display: flex; gap: 0.4rem; align-items: center; }}
  .pill-btn {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 0.78rem;
    font-weight: 600;
    padding: 0.25rem 0.65rem;
    border-radius: 9999px;
    cursor: pointer;
    transition: all 0.2s;
  }}
  .pill-btn.active {{ background: #334155; color: var(--text); border-color: #64748b; }}
  .pill-btn.leak.active {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; border-color: var(--leak); }}
  .pill-btn.unconsented.active {{ background: rgba(245, 158, 11, 0.2); color: #fde68a; border-color: var(--unconsented); }}
  .pill-btn.compliant.active {{ background: rgba(16, 185, 129, 0.2); color: #86efac; border-color: var(--compliant); }}

  .search-box {{ position: relative; width: 280px; }}
  .search-input {{
    width: 100%;
    background: var(--bg-base);
    border: 1px solid var(--border);
    color: var(--text);
    padding: 0.3rem 0.75rem;
    border-radius: 6px;
    font-size: 0.82rem;
  }}
  .search-input:focus {{ outline: none; border-color: #38bdf8; }}

  /* KPI Summary Ribbon */
  #kpi-ribbon {{
    display: flex;
    gap: 1rem;
    align-items: center;
    background: rgba(15, 23, 42, 0.6);
    padding: 0.35rem 1.25rem;
    font-size: 0.78rem;
    border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  }}
  .kpi-item {{ display: flex; align-items: center; gap: 0.4rem; }}
  .kpi-num {{ font-weight: 700; }}
  .kpi-leak {{ color: var(--leak); }}
  .kpi-unconsented {{ color: var(--unconsented); }}
  .kpi-compliant {{ color: var(--compliant); }}
  .kpi-ceiling {{ background: rgba(239, 68, 68, 0.15); color: #fca5a5; padding: 0.1rem 0.4rem; border-radius: 4px; border: 1px solid rgba(239, 68, 68, 0.3); font-weight: 700; }}

  /* Viewports Container */
  #viewport-container {{
    flex: 1;
    position: relative;
    overflow: hidden;
    width: 100%;
    height: calc(100vh - 110px);
  }}

  #view-2d {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    display: block;
  }}
  #cy {{
    width: 100%;
    height: 100%;
    min-height: 500px;
    background: #080c14;
    display: block;
  }}

  #view-3d {{
    position: absolute;
    top: 0; left: 0; width: 100%; height: 100%;
    display: none;
  }}
  #three-container {{ width: 100%; height: 100%; background: #05070d; cursor: grab; }}
  #three-container:active {{ cursor: grabbing; }}

  #webgl-fallback {{
    display: none;
    position: absolute;
    top: 50%; left: 50%;
    transform: translate(-50%, -50%);
    background: var(--bg-card);
    border: 1px solid var(--border);
    padding: 2rem;
    border-radius: 8px;
    text-align: center;
    max-width: 480px;
  }}

  /* Legend Overlay */
  #legend-overlay {{
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    background: rgba(15, 23, 42, 0.88);
    backdrop-filter: blur(8px);
    border: 1px solid var(--border);
    padding: 0.6rem 0.9rem;
    border-radius: 6px;
    font-size: 0.75rem;
    z-index: 50;
    pointer-events: none;
  }}
  .legend-item {{ display: flex; align-items: center; gap: 0.5rem; margin-bottom: 0.25rem; }}
  .legend-item:last-child {{ margin-bottom: 0; }}
  .legend-dot {{ width: 10px; height: 10px; border-radius: 50%; }}

  /* Inspector Slide-Over Drawer */
  #inspector-drawer {{
    position: absolute;
    top: 0;
    right: -460px;
    width: 440px;
    height: 100%;
    background: var(--bg-surface);
    border-left: 1px solid var(--border);
    box-shadow: -8px 0 24px rgba(0, 0, 0, 0.5);
    transition: right 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    z-index: 200;
    display: flex;
    flex-direction: column;
    overflow-y: auto;
  }}
  #inspector-drawer.open {{ right: 0; }}

  .drawer-header {{
    padding: 1.25rem;
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }}
  .drawer-title {{ font-size: 1.05rem; font-weight: 700; margin-bottom: 0.3rem; }}
  .drawer-subtitle {{ font-size: 0.8rem; color: var(--text-muted); font-family: monospace; word-break: break-all; }}
  .drawer-close {{ background: transparent; border: none; color: var(--text-muted); font-size: 1.5rem; cursor: pointer; line-height: 1; }}
  .drawer-close:hover {{ color: var(--text); }}

  .drawer-body {{ padding: 1.25rem; display: flex; flex-direction: column; gap: 1.25rem; }}

  .section-label {{ font-size: 0.75rem; text-transform: uppercase; color: var(--text-muted); font-weight: 700; margin-bottom: 0.4rem; }}
  .badge-tag {{ display: inline-block; padding: 0.2rem 0.5rem; border-radius: 4px; font-size: 0.75rem; font-weight: 700; font-family: monospace; }}
  .badge-leak {{ background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid var(--leak); }}
  .badge-unconsented {{ background: rgba(245, 158, 11, 0.2); color: #fde68a; border: 1px solid var(--unconsented); }}
  .badge-compliant {{ background: rgba(16, 185, 129, 0.2); color: #86efac; border: 1px solid var(--compliant); }}
  .badge-info {{ background: rgba(56, 189, 248, 0.2); color: #7dd3fc; border: 1px solid var(--route); }}

  .pii-pills {{ display: flex; flex-wrap: wrap; gap: 0.3rem; }}
  .pii-pill {{ background: rgba(129, 140, 248, 0.15); color: #c7d2fe; border: 1px solid rgba(129, 140, 248, 0.3); font-size: 0.72rem; padding: 0.15rem 0.45rem; border-radius: 3px; font-weight: 600; }}

  .controls-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 0.5rem; }}
  .ctrl-item {{ background: var(--bg-card); padding: 0.45rem 0.6rem; border-radius: 4px; border: 1px solid var(--border); font-size: 0.75rem; display: flex; justify-content: space-between; }}
  .ctrl-pass {{ color: #86efac; font-weight: 700; }}
  .ctrl-fail {{ color: #fca5a5; font-weight: 700; }}
  .ctrl-na {{ color: var(--text-muted); }}

  .finding-card {{
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.85rem;
    margin-bottom: 0.6rem;
  }}
  .finding-header {{ display: flex; justify-content: space-between; margin-bottom: 0.4rem; font-size: 0.8rem; }}
  .finding-msg {{ font-size: 0.82rem; font-weight: 600; margin-bottom: 0.4rem; }}
  .finding-citation {{ font-size: 0.75rem; color: #38bdf8; margin-bottom: 0.4rem; }}
  .remediation-box {{ background: rgba(16, 185, 129, 0.1); border: 1px solid rgba(16, 185, 129, 0.3); color: #86efac; padding: 0.5rem; border-radius: 4px; font-size: 0.75rem; }}
</style>

<!-- Vendored Offline JS Libraries -->
<script>{cytoscape_js}</script>
<script>{dagre_js}</script>
<script>{cytoscape_dagre_js}</script>
<script>{three_js}</script>
<script>{orbit_controls_js}</script>
</head>
<body>

<!-- Header HUD -->
<div id="header-hud">
  <div class="header-left">
    <div class="header-title">CS-01 Data-Flow &amp; Leak Visualizer</div>
    <div class="header-repo">{graph.repo_name}</div>
  </div>

  <div class="view-switcher">
    <button id="btn-2d" class="view-btn active" onclick="switchView('2d')">2D Swimlane</button>
    <button id="btn-3d" class="view-btn" onclick="switchView('3d')">3D Spatial</button>
  </div>

  <div class="camera-presets" id="camera-presets-group" style="display: none;">
    <button class="preset-btn" onclick="setCameraPreset('isometric')">Isometric</button>
    <button class="preset-btn" onclick="setCameraPreset('top')">Top-Down</button>
    <button class="preset-btn" onclick="setCameraPreset('leaks')">Focus Leaks</button>
  </div>
</div>

<!-- Filter Ribbon -->
<div id="filter-ribbon">
  <div class="filter-pills">
    <span style="font-size: 0.75rem; color: var(--text-muted); margin-right: 0.2rem;">FILTER:</span>
    <button class="pill-btn active" onclick="filterGraph('all', this)">All Flows</button>
    <button class="pill-btn leak" onclick="filterGraph('leaks', this)">PII Leaks Only ({graph.summary_metrics.leak_edges})</button>
    <button class="pill-btn unconsented" onclick="filterGraph('unconsented', this)">No Consent ({graph.summary_metrics.unconsented_storage_edges})</button>
    <button class="pill-btn compliant" onclick="filterGraph('compliant', this)">Compliant ({graph.summary_metrics.compliant_edges})</button>
  </div>

  <div class="search-box">
    <input type="text" id="graph-search" class="search-input" placeholder="Search routes, tables, PII types..." oninput="handleSearch(this.value)">
  </div>
</div>

<!-- KPI Ribbon -->
<div id="kpi-ribbon">
  <div class="kpi-item">Nodes: <span class="kpi-num">{graph.summary_metrics.total_nodes}</span></div>
  <div class="kpi-item">Flows: <span class="kpi-num">{graph.summary_metrics.total_edges}</span></div>
  <div class="kpi-item kpi-leak">PII Leaks: <span class="kpi-num">{graph.summary_metrics.leak_edges}</span></div>
  <div class="kpi-item kpi-unconsented">Unconsented Sinks: <span class="kpi-num">{graph.summary_metrics.unconsented_storage_edges}</span></div>
  <div class="kpi-item kpi-compliant">Compliant Controls: <span class="kpi-num">{graph.summary_metrics.compliant_edges}</span></div>
  <div class="kpi-item" style="margin-left: auto;">
    Ceiling: <span class="kpi-ceiling">{graph.summary_metrics.max_penalty_engaged or 'Up to ₹250 Crore'}</span>
  </div>
</div>

<!-- Viewports -->
<div id="viewport-container">
  <!-- 2D Viewport -->
  <div id="view-2d">
    <div id="cy"></div>
  </div>

  <!-- 3D Viewport -->
  <div id="view-3d">
    <div id="three-container"></div>
    <div id="webgl-fallback">
      <h3>WebGL Acceleration Unavailable</h3>
      <p style="color: var(--text-muted); margin: 0.8rem 0;">Your browser environment does not support WebGL hardware rendering. The interactive 2D Architectural Swimlane view remains 100% available and functional.</p>
      <button class="preset-btn" onclick="switchView('2d')">Return to 2D View</button>
    </div>
  </div>

  <!-- Legend -->
  <div id="legend-overlay">
    <div class="legend-item"><div class="legend-dot" style="background: var(--leak);"></div> PII Leak / Exposure (§8(5))</div>
    <div class="legend-item"><div class="legend-dot" style="background: var(--unconsented);"></div> Unconsented Storage (§6(1))</div>
    <div class="legend-item"><div class="legend-dot" style="background: var(--compliant);"></div> Verified Compliant Controls</div>
    <div class="legend-item"><div class="legend-dot" style="background: var(--route);"></div> API Logic &amp; Routing</div>
    <div class="legend-item"><div class="legend-dot" style="background: var(--storage);"></div> Storage / Database Table</div>
  </div>

  <!-- Slide-Over Inspector Drawer -->
  <div id="inspector-drawer">
    <div class="drawer-header">
      <div>
        <div id="drawer-title" class="drawer-title">Entity Title</div>
        <div id="drawer-subtitle" class="drawer-subtitle">file/path.py:10</div>
      </div>
      <button class="drawer-close" onclick="closeDrawer()">&times;</button>
    </div>

    <div class="drawer-body">
      <div>
        <div class="section-label">Compliance Status</div>
        <div id="drawer-status"></div>
      </div>

      <div>
        <div class="section-label">Detected PII Types</div>
        <div id="drawer-pii" class="pii-pills"></div>
      </div>

      <div id="drawer-controls-section">
        <div class="section-label">Verified Controls Checklist</div>
        <div id="drawer-controls" class="controls-grid"></div>
      </div>

      <div>
        <div class="section-label">Statutory Findings &amp; DPDP Citations</div>
        <div id="drawer-findings"></div>
      </div>
    </div>
  </div>
</div>

<!-- Graph Data & Interactive Engine -->
<script>
const CS01_GRAPH_DATA = {graph_data_json};

let cy = null;
let currentView = '2d';
let activeFilter = 'all';

// Helper to create 3D Billboard Canvas Text Sprites
function createTextSprite(message, opts) {{
  opts = opts || {{}};
  const fontSize = opts.fontSize || 20;
  const textColor = opts.textColor || '#ffffff';
  const bgColor = opts.bgColor || 'rgba(15, 23, 42, 0.88)';
  const borderColor = opts.borderColor || '#38bdf8';

  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  ctx.font = 'bold ' + fontSize + 'px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';

  const textMetrics = ctx.measureText(message);
  const textWidth = textMetrics.width;
  canvas.width = Math.max(textWidth + 24, 120);
  canvas.height = fontSize + 20;

  // Draw rounded pill background
  ctx.font = 'bold ' + fontSize + 'px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif';
  ctx.fillStyle = bgColor;
  ctx.strokeStyle = borderColor;
  ctx.lineWidth = 3;

  const r = 6;
  const x = 3, y = 3, w = canvas.width - 6, h = canvas.height - 6;
  ctx.beginPath();
  ctx.moveTo(x + r, y);
  ctx.lineTo(x + w - r, y);
  ctx.quadraticCurveTo(x + w, y, x + w, y + r);
  ctx.lineTo(x + w, y + h - r);
  ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
  ctx.lineTo(x + r, y + h);
  ctx.quadraticCurveTo(x, y + h, x, y + h - r);
  ctx.lineTo(x, y + r);
  ctx.quadraticCurveTo(x, y, x + r, y);
  ctx.closePath();
  ctx.fill();
  ctx.stroke();

  // Draw text
  ctx.fillStyle = textColor;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  ctx.fillText(message, canvas.width / 2, canvas.height / 2);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  const spriteMat = new THREE.SpriteMaterial({{
    map: texture,
    depthTest: false,
    transparent: true
  }});
  const sprite = new THREE.Sprite(spriteMat);
  const aspect = canvas.width / canvas.height;
  const spriteHeight = opts.spriteHeight || 6.0;
  sprite.scale.set(spriteHeight * aspect, spriteHeight, 1);
  return sprite;
}}

// Initialize 2D Cytoscape Graph
function init2DGraph() {{
  const container = document.getElementById('cy');
  if (!container) return;

  const validNodeIds = new Set(CS01_GRAPH_DATA.nodes.map(n => n.id));
  const elements = [];

  const tierXMap = {{
    0: 120,  // Collection
    1: 440,  // API Logic
    2: 780,  // Storage
    3: 1120, // Infra Cloud
    4: 1460  // Egress Sink
  }};

  const tierNames = {{
    0: "TIER 0: COLLECTION",
    1: "TIER 1: API & AUTH LOGIC",
    2: "TIER 2: STORAGE (DB & DISK)",
    3: "TIER 3: CLOUD INFRASTRUCTURE",
    4: "TIER 4: EGRESS & LOG SINKS"
  }};

  // Add swimlane header pills
  const activeTiers = new Set(CS01_GRAPH_DATA.nodes.map(n => n.layer));
  activeTiers.forEach(tier => {{
    elements.push({{
      group: 'nodes',
      data: {{
        id: 'HEADER_TIER_' + tier,
        label: tierNames[tier] || ('TIER ' + tier),
        isHeader: true,
        nodeColor: '#0f172a',
        borderColor: '#0284c7'
      }},
      position: {{ x: tierXMap[tier] || 500, y: 35 }},
      locked: true,
      grabbable: false
    }});
  }});

  const tierCounts = {{ 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 }};

  CS01_GRAPH_DATA.nodes.forEach(n => {{
    const tier = n.layer;
    tierCounts[tier] = (tierCounts[tier] || 0) + 1;
    const yPos = 85 + (tierCounts[tier] * 72);

    let nodeColor = '#0f172a';
    let borderColor = '#38bdf8';
    if (n.status === 'pii_leak') {{
      nodeColor = '#450a0a';
      borderColor = '#ef4444';
    }} else if (n.status === 'unconsented_storage') {{
      nodeColor = '#451a03';
      borderColor = '#f59e0b';
    }} else if (n.status === 'compliant') {{
      nodeColor = '#064e3b';
      borderColor = '#10b981';
    }} else if (n.node_type === 'table') {{
      nodeColor = '#022c22';
      borderColor = '#34d399';
    }} else if (n.node_type === 'dto') {{
      nodeColor = '#1e1b4b';
      borderColor = '#818cf8';
    }}

    elements.push({{
      group: 'nodes',
      data: {{
        id: n.id,
        label: n.label,
        layer: n.layer,
        nodeType: n.node_type,
        status: n.status,
        piiTypes: n.pii_types,
        nodeColor: nodeColor,
        borderColor: borderColor,
        rawNode: n
      }},
      position: {{ x: tierXMap[tier] || 500, y: yPos }}
    }});
  }});

  CS01_GRAPH_DATA.edges.forEach(e => {{
    if (!validNodeIds.has(e.source) || !validNodeIds.has(e.target)) {{
      return; // Defensive: skip any dangling edge
    }}

    let edgeColor = '#475569';
    let lineStyle = 'solid';
    let width = 2;

    if (e.flow_type === 'pii_leak') {{
      edgeColor = '#ef4444';
      lineStyle = 'dashed';
      width = 3.5;
    }} else if (e.flow_type === 'unconsented_storage') {{
      edgeColor = '#f59e0b';
      lineStyle = 'dashed';
      width = 2.5;
    }} else if (e.flow_type === 'normal_flow' && (e.consent_verified || e.encrypted)) {{
      edgeColor = '#10b981';
      width = 2;
    }}

    elements.push({{
      group: 'edges',
      data: {{
        id: e.id,
        source: e.source,
        target: e.target,
        flowType: e.flow_type,
        edgeColor: edgeColor,
        lineStyle: lineStyle,
        edgeWidth: width,
        severity: e.severity,
        rawEdge: e
      }}
    }});
  }});

  try {{
    cy = cytoscape({{
      container: container,
      elements: elements,
      layout: {{ name: 'preset' }},
      style: [
        {{
          selector: 'node[?isHeader]',
          style: {{
            'shape': 'round-rectangle',
            'background-color': '#0f172a',
            'border-color': '#0284c7',
            'border-width': 2,
            'width': 180,
            'height': 30,
            'label': 'data(label)',
            'color': '#38bdf8',
            'font-size': '11px',
            'font-weight': 'bold',
            'text-valign': 'center',
            'text-halign': 'center'
          }}
        }},
        {{
          selector: 'node[!isHeader]',
          style: {{
            'shape': 'round-rectangle',
            'label': 'data(label)',
            'color': '#f8fafc',
            'font-size': '11px',
            'font-weight': 600,
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 6,
            'text-wrap': 'wrap',
            'text-max-width': '130px',
            'background-color': 'data(nodeColor)',
            'border-width': 2.5,
            'border-color': 'data(borderColor)',
            'width': 36,
            'height': 36
          }}
        }},
        {{
          selector: 'edge',
          style: {{
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'arrow-scale': 1.0,
            'line-color': 'data(edgeColor)',
            'target-arrow-color': 'data(edgeColor)',
            'line-style': 'data(lineStyle)',
            'width': 'data(edgeWidth)',
            'opacity': 0.85
          }}
        }},
        {{
          selector: '.dimmed',
          style: {{ 'opacity': 0.12 }}
        }},
        {{
          selector: '.highlighted',
          style: {{ 'opacity': 1.0, 'font-size': '13px' }}
        }}
      ]
    }});

    setTimeout(() => {{
      if (cy) {{
        cy.resize();
        cy.fit(null, 40);
      }}
    }}, 50);

    // Hover highlighting
    cy.on('mouseover', 'node', function(evt) {{
      const node = evt.target;
      if (node.data('isHeader')) return;
      const connectedEdges = node.connectedEdges();
      const connectedNodes = connectedEdges.connectedNodes();

      cy.elements().addClass('dimmed');
      node.removeClass('dimmed').addClass('highlighted');
      connectedNodes.removeClass('dimmed').addClass('highlighted');
      connectedEdges.removeClass('dimmed').addClass('highlighted');
    }});

    cy.on('mouseout', 'node', function() {{
      cy.elements().removeClass('dimmed').removeClass('highlighted');
    }});

    // Click on node
    cy.on('tap', 'node', function(evt) {{
      const nodeData = evt.target.data('rawNode');
      if (nodeData) openDrawerForNode(nodeData);
    }});

    // Click on edge
    cy.on('tap', 'edge', function(evt) {{
      const edgeData = evt.target.data('rawEdge');
      if (edgeData) openDrawerForEdge(edgeData);
    }});
  }} catch (err) {{
    console.error('Cytoscape 2D initialization error:', err);
  }}
}}

// Filter Logic
function filterGraph(type, btn) {{
  activeFilter = type;
  document.querySelectorAll('.pill-btn').forEach(b => b.classList.remove('active'));
  if (btn) btn.classList.add('active');

  if (!cy) return;

  cy.elements().show();

  if (type === 'leaks') {{
    cy.elements().forEach(el => {{
      if (el.isNode()) {{
        if (!el.data('isHeader') && el.data('status') !== 'pii_leak') el.hide();
      }} else {{
        if (el.data('flowType') !== 'pii_leak') el.hide();
      }}
    }});
  }} else if (type === 'unconsented') {{
    cy.elements().forEach(el => {{
      if (el.isNode()) {{
        if (!el.data('isHeader') && el.data('status') !== 'unconsented_storage') el.hide();
      }} else {{
        if (el.data('flowType') !== 'unconsented_storage') el.hide();
      }}
    }});
  }} else if (type === 'compliant') {{
    cy.elements().forEach(el => {{
      if (el.isNode()) {{
        if (!el.data('isHeader') && el.data('status') !== 'compliant') el.hide();
      }} else {{
        if (el.data('flowType') !== 'normal_flow' || (!el.data('rawEdge').consent_verified && !el.data('rawEdge').encrypted)) el.hide();
      }}
    }});
  }}
}}

// Live Search
function handleSearch(val) {{
  if (!cy) return;
  const q = val.trim().toLowerCase();
  if (!q) {{
    cy.elements().removeClass('dimmed').removeClass('highlighted');
    return;
  }}

  cy.elements().addClass('dimmed');
  cy.nodes().forEach(n => {{
    if (n.data('isHeader')) return;
    const label = (n.data('label') || '').toLowerCase();
    const pii = (n.data('piiTypes') || []).join(' ').toLowerCase();
    const path = ((n.data('rawNode') && n.data('rawNode').file_path) || '').toLowerCase();
    if (label.includes(q) || pii.includes(q) || path.includes(q)) {{
      n.removeClass('dimmed').addClass('highlighted');
      n.connectedEdges().removeClass('dimmed').addClass('highlighted');
      n.connectedEdges().connectedNodes().removeClass('dimmed');
    }}
  }});
}}

// Inspector Drawer Logic
function openDrawerForNode(node) {{
  const drawer = document.getElementById('inspector-drawer');
  document.getElementById('drawer-title').innerText = node.label;
  document.getElementById('drawer-subtitle').innerText = `${{node.file_path || 'Whole Repository'}}:${{node.start_line || 1}}`;

  let statusBadge = '<span class="badge-tag badge-info">INFORMATIONAL</span>';
  if (node.status === 'pii_leak') {{
    statusBadge = '<span class="badge-tag badge-leak">⚠️ PII LEAK / EXPOSURE</span>';
  }} else if (node.status === 'unconsented_storage') {{
    statusBadge = '<span class="badge-tag badge-unconsented">⚠️ UNCONSENTED STORAGE</span>';
  }} else if (node.status === 'compliant') {{
    statusBadge = '<span class="badge-tag badge-compliant">✔ VERIFIED COMPLIANT</span>';
  }}
  document.getElementById('drawer-status').innerHTML = statusBadge;

  // PII pills
  const piiContainer = document.getElementById('drawer-pii');
  if (node.pii_types && node.pii_types.length > 0) {{
    piiContainer.innerHTML = node.pii_types.map(p => `<span class="pii-pill">${{p}}</span>`).join('');
  }} else {{
    piiContainer.innerHTML = '<span style="color: var(--text-muted); font-size: 0.75rem;">None explicitly tagged</span>';
  }}

  // Controls
  const ctrlContainer = document.getElementById('drawer-controls');
  const c = node.controls || {{}};
  const fmt = val => val === true ? '<span class="ctrl-pass">PASS</span>' : (val === false ? '<span class="ctrl-fail">FAIL</span>' : '<span class="ctrl-na">N/A</span>');
  ctrlContainer.innerHTML = `
    <div class="ctrl-item"><span>Auth Guard</span>${{fmt(c.auth_checked)}}</div>
    <div class="ctrl-item"><span>IDOR / BOLA Guard</span>${{fmt(c.ownership_checked)}}</div>
    <div class="ctrl-item"><span>Consent Guard</span>${{fmt(c.consent_checked)}}</div>
    <div class="ctrl-item"><span>Column Encrypted</span>${{fmt(c.encrypted)}}</div>
    <div class="ctrl-item"><span>Retention Purge</span>${{fmt(c.retention_defined)}}</div>
  `;

  // Findings
  const findingsContainer = document.getElementById('drawer-findings');
  if (node.finding_ids && node.finding_ids.length > 0) {{
    findingsContainer.innerHTML = node.finding_ids.map(fid => {{
      return `
        <div class="finding-card">
          <div class="finding-header">
            <strong>${{fid}}</strong>
            <span style="color: #ef4444; font-weight: 700;">DPDP Violation</span>
          </div>
          <div class="finding-citation">Statutory Baseline: DPDP Act §8(5) &amp; DPDP Rules 2025</div>
          <div class="remediation-box">💡 Remediate in accordance with DPDP statutory requirements</div>
        </div>
      `;
    }}).join('');
  }} else {{
    findingsContainer.innerHTML = '<div style="color: #86efac; font-size: 0.8rem;">✔ Zero active statutory findings attached to this entity.</div>';
  }}

  drawer.classList.add('open');
}}

function openDrawerForEdge(edge) {{
  const drawer = document.getElementById('inspector-drawer');
  document.getElementById('drawer-title').innerText = `Flow: ${{edge.source}} → ${{edge.target}}`;
  document.getElementById('drawer-subtitle').innerText = edge.evidence_summary || 'Data transmission flow';

  let statusBadge = '<span class="badge-tag badge-info">NORMAL FLOW</span>';
  if (edge.flow_type === 'pii_leak') {{
    statusBadge = '<span class="badge-tag badge-leak">⚠️ PII LEAK EDGE</span>';
  }} else if (edge.flow_type === 'unconsented_storage') {{
    statusBadge = '<span class="badge-tag badge-unconsented">⚠️ UNCONSENTED STORAGE FLOW</span>';
  }}
  document.getElementById('drawer-status').innerHTML = statusBadge;

  document.getElementById('drawer-pii').innerHTML = (edge.pii_types || []).map(p => `<span class="pii-pill">${{p}}</span>`).join('') || '<span style="color: var(--text-muted); font-size: 0.75rem;">None</span>';
  document.getElementById('drawer-controls').innerHTML = '<div style="grid-column: span 2; color: var(--text-muted); font-size: 0.75rem;">Controls evaluated on source and target endpoints.</div>';

  const findingsContainer = document.getElementById('drawer-findings');
  if (edge.finding_ids && edge.finding_ids.length > 0) {{
    findingsContainer.innerHTML = edge.finding_ids.map(fid => `
      <div class="finding-card">
        <div class="finding-header"><strong>${{fid}}</strong></div>
        <div class="finding-citation">Penalty Ceiling: ${{edge.penalty_ceiling || 'Up to ₹250 Crore'}}</div>
      </div>
    `).join('');
  }} else {{
    findingsContainer.innerHTML = '<div style="color: #86efac; font-size: 0.8rem;">✔ No direct statutory violations on this edge.</div>';
  }}

  drawer.classList.add('open');
}}

function closeDrawer() {{
  document.getElementById('inspector-drawer').classList.remove('open');
}}

// 3D Spatial Three.js Implementation
let threeScene, threeCamera, threeRenderer, threeControls;
let threeParticles = [];
let threeNodeMeshes = [];
let threeInitialized = false;

function init3DGraph() {{
  if (threeInitialized) return;

  const container = document.getElementById('three-container');

  // WebGL availability check
  const hasWebGL = (function () {{
    try {{
      const canvas = document.createElement('canvas');
      return !!(window.WebGLRenderingContext && (canvas.getContext('webgl') || canvas.getContext('experimental-webgl')));
    }} catch (e) {{
      return false;
    }}
  }})();

  if (!hasWebGL || typeof THREE === 'undefined') {{
    document.getElementById('webgl-fallback').style.display = 'block';
    return;
  }}

  threeScene = new THREE.Scene();
  threeScene.background = new THREE.Color(0x060911);

  threeCamera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 1, 2000);
  threeCamera.position.set(220, 180, 260);

  threeRenderer = new THREE.WebGLRenderer({{ antialias: true }});
  threeRenderer.setSize(container.clientWidth, container.clientHeight);
  threeRenderer.setPixelRatio(window.devicePixelRatio);
  container.appendChild(threeRenderer.domElement);

  if (typeof THREE.OrbitControls !== 'undefined') {{
    threeControls = new THREE.OrbitControls(threeCamera, threeRenderer.domElement);
    threeControls.enableDamping = true;
    threeControls.dampingFactor = 0.05;
  }}

  // Lighting
  const ambLight = new THREE.AmbientLight(0xffffff, 0.7);
  threeScene.add(ambLight);
  const dirLight = new THREE.DirectionalLight(0x38bdf8, 1.2);
  dirLight.position.set(100, 200, 100);
  threeScene.add(dirLight);

  // Stacked Layer Glass Planes
  const layerY = {{ 0: 80, 1: 40, 2: 0, 3: -40, 4: -80 }};
  const layerNames = {{
    0: "TIER 0: COLLECTION (Frontend & Forms)",
    1: "TIER 1: API & AUTH LOGIC",
    2: "TIER 2: STORAGE (Databases & Uploads)",
    3: "TIER 3: CLOUD INFRASTRUCTURE",
    4: "TIER 4: EGRESS SINKS (Logs / Static Mounts)"
  }};

  const activeTiers = new Set(CS01_GRAPH_DATA.nodes.map(n => n.layer));

  activeTiers.forEach(tier => {{
    const y = layerY[tier] || 0;
    const planeGeo = new THREE.PlaneGeometry(360, 260);
    const planeMat = new THREE.MeshBasicMaterial({{
      color: 0x1e293b,
      transparent: true,
      opacity: 0.25,
      side: THREE.DoubleSide
    }});
    const plane = new THREE.Mesh(planeGeo, planeMat);
    plane.rotation.x = Math.PI / 2;
    plane.position.y = y;
    threeScene.add(plane);

    const grid = new THREE.GridHelper(360, 12, 0x334155, 0x1e293b);
    grid.position.y = y;
    threeScene.add(grid);

    // Add 3D Floating Tier Banner Billboard
    const tierBanner = createTextSprite(layerNames[tier] || ('TIER ' + tier), {{
      fontSize: 22,
      textColor: '#38bdf8',
      bgColor: 'rgba(15, 23, 42, 0.92)',
      borderColor: '#0284c7',
      spriteHeight: 9.0
    }});
    tierBanner.position.set(-110, y + 6, -110);
    threeScene.add(tierBanner);
  }});

  // Render 3D Nodes & Text Sprites
  const node3DMap = {{}};
  const tierCounts = {{ 0: 0, 1: 0, 2: 0, 3: 0, 4: 0 }};

  CS01_GRAPH_DATA.nodes.forEach(n => {{
    const tier = n.layer;
    tierCounts[tier] = (tierCounts[tier] || 0) + 1;
    const count = tierCounts[tier];

    const posX = -120 + ((count % 6) * 50);
    const posZ = -80 + (Math.floor(count / 6) * 50);
    const posY = (layerY[tier] || 0) + 5;

    let col = 0x38bdf8;
    let badgeBorder = '#38bdf8';
    let badgeText = '#e0f2fe';

    if (n.status === 'pii_leak') {{
      col = 0xef4444;
      badgeBorder = '#ef4444';
      badgeText = '#fecaca';
    }} else if (n.status === 'unconsented_storage') {{
      col = 0xf59e0b;
      badgeBorder = '#f59e0b';
      badgeText = '#fef3c7';
    }} else if (n.status === 'compliant') {{
      col = 0x10b981;
      badgeBorder = '#10b981';
      badgeText = '#d1fae5';
    }}

    let geo;
    if (n.node_type === 'route') geo = new THREE.SphereGeometry(6, 16, 16);
    else if (n.node_type === 'table') geo = new THREE.CylinderGeometry(6, 6, 8, 16);
    else if (n.node_type === 'dto') geo = new THREE.OctahedronGeometry(6);
    else if (n.node_type === 'cloud_resource') geo = new THREE.BoxGeometry(10, 10, 10);
    else geo = new THREE.DodecahedronGeometry(6);

    const mat = new THREE.MeshStandardMaterial({{
      color: col,
      roughness: 0.3,
      metalness: 0.4,
      emissive: col,
      emissiveIntensity: 0.3
    }});

    const mesh = new THREE.Mesh(geo, mat);
    mesh.position.set(posX, posY, posZ);
    mesh.userData = {{ node: n }};
    threeScene.add(mesh);
    threeNodeMeshes.push(mesh);
    node3DMap[n.id] = mesh.position;

    // Create 3D Floating Node Text Sprite Billboard
    let labelText = n.label;
    if (labelText.length > 24) labelText = labelText.substring(0, 22) + '..';

    const sprite = createTextSprite(labelText, {{
      fontSize: 18,
      borderColor: badgeBorder,
      textColor: badgeText,
      spriteHeight: 5.5
    }});
    sprite.position.set(posX, posY + 11, posZ);
    threeScene.add(sprite);
  }});

  // Render 3D Edges & Particle Tubes
  const validNodeIds = new Set(CS01_GRAPH_DATA.nodes.map(n => n.id));
  CS01_GRAPH_DATA.edges.forEach(e => {{
    if (!validNodeIds.has(e.source) || !validNodeIds.has(e.target)) return;

    const p1 = node3DMap[e.source];
    const p2 = node3DMap[e.target];
    if (!p1 || !p2) return;

    const mid = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
    mid.x += 15; // curve arc

    const curve = new THREE.CatmullRomCurve3([p1, mid, p2]);
    const tubeGeo = new THREE.TubeGeometry(curve, 20, 0.7, 8, false);

    let tubeCol = 0x475569;
    if (e.flow_type === 'pii_leak') tubeCol = 0xef4444;
    else if (e.flow_type === 'unconsented_storage') tubeCol = 0xf59e0b;
    else if (e.flow_type === 'normal_flow' && (e.consent_verified || e.encrypted)) tubeCol = 0x10b981;

    const tubeMat = new THREE.MeshBasicMaterial({{ color: tubeCol, transparent: true, opacity: 0.6 }});
    const tubeMesh = new THREE.Mesh(tubeGeo, tubeMat);
    threeScene.add(tubeMesh);

    // Particle
    const partGeo = new THREE.SphereGeometry(1.6, 8, 8);
    const partMat = new THREE.MeshBasicMaterial({{ color: tubeCol }});
    const partMesh = new THREE.Mesh(partGeo, partMat);
    threeScene.add(partMesh);
    threeParticles.push({{
      mesh: partMesh,
      curve: curve,
      progress: Math.random(),
      speed: e.flow_type === 'pii_leak' ? 0.007 : 0.003
    }});
  }});

  // 3D Raycasting click listener on container
  const raycaster = new THREE.Raycaster();
  const mouse = new THREE.Vector2();

  container.addEventListener('click', (event) => {{
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, threeCamera);
    const intersects = raycaster.intersectObjects(threeNodeMeshes, false);
    if (intersects.length > 0) {{
      const clickedMesh = intersects[0].object;
      if (clickedMesh.userData && clickedMesh.userData.node) {{
        openDrawerForNode(clickedMesh.userData.node);
      }}
    }}
  }});

  threeInitialized = true;

  function animate() {{
    requestAnimationFrame(animate);
    if (threeControls) threeControls.update();

    // Animate flow particles
    threeParticles.forEach(p => {{
      p.progress = (p.progress + p.speed) % 1.0;
      const pos = p.curve.getPointAt(p.progress);
      p.mesh.position.copy(pos);
    }});

    threeRenderer.render(threeScene, threeCamera);
  }}
  animate();

  window.addEventListener('resize', () => {{
    if (currentView === '3d' && threeRenderer) {{
      threeCamera.aspect = container.clientWidth / container.clientHeight;
      threeCamera.updateProjectionMatrix();
      threeRenderer.setSize(container.clientWidth, container.clientHeight);
    }}
  }});
}}

// View Switcher (2D / 3D)
function switchView(view) {{
  currentView = view;
  const btn2d = document.getElementById('btn-2d');
  const btn3d = document.getElementById('btn-3d');
  const view2d = document.getElementById('view-2d');
  const view3d = document.getElementById('view-3d');
  const camPresets = document.getElementById('camera-presets-group');

  if (view === '2d') {{
    btn2d.classList.add('active');
    btn3d.classList.remove('active');
    view2d.style.display = 'block';
    view3d.style.display = 'none';
    camPresets.style.display = 'none';
    if (cy) {{
      setTimeout(() => {{
        cy.resize();
        cy.fit(null, 40);
      }}, 50);
    }} else {{
      init2DGraph();
    }}
  }} else {{
    btn3d.classList.add('active');
    btn2d.classList.remove('active');
    view2d.style.display = 'none';
    view3d.style.display = 'block';
    camPresets.style.display = 'flex';
    init3DGraph();
  }}
}}

function setCameraPreset(mode) {{
  if (!threeCamera || !threeControls) return;
  if (mode === 'isometric') {{
    threeCamera.position.set(220, 180, 260);
    threeControls.target.set(0, 0, 0);
  }} else if (mode === 'top') {{
    threeCamera.position.set(0, 340, 1);
    threeControls.target.set(0, 0, 0);
  }} else if (mode === 'leaks') {{
    threeCamera.position.set(120, 40, 150);
    threeControls.target.set(0, 0, 0);
  }}
}}

// Initial load: render 2D on startup
window.addEventListener('DOMContentLoaded', () => {{
  init2DGraph();
}});
</script>
</body>
</html>
"""
