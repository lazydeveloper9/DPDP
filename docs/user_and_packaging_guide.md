# CS-01 DPDP Compliance Auditor
## Desktop GUI, CLI & Packaging User Guide

---

### 1. Overview & Architecture
**CS-01** is an open-core, local-first static compliance auditing instrument designed specifically to evaluate software systems against India's **Digital Personal Data Protection Act, 2023 (DPDP Act)** and the **DPDP Rules, 2025**.

CS-01 guarantees **100% local execution (Zero Cloud Egress)**: all AST parsing, data flow resolution, database schema inspection, and report generation execute locally with zero outbound network transmissions.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        CS-01 EXECUTION MODEL                           │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   [ Windowed GUI (cs01-gui.exe) ]       [ Terminal CLI (cs01.exe) ]    │
│                 │                                    │                 │
│                 ▼                                    ▼                 │
│         AuditWorker (QObject)                 CLI scan Handler         │
│         • Runs in QThread                     • Rich CLI progress      │
│         • Non-blocking Qt signals             • Exit codes 0, 2, 3     │
│                 │                                    │                 │
│                 └─────────────────┬──────────────────┘                 │
│                                   ▼                                    │
│                     execute_pipeline(cfg, callbacks)                   │
│                                   │                                    │
│       ┌───────────────────────────┴────────────────────────────┐      │
│       │ 6-Stage Deterministic Zero-Egress Pipeline:            │      │
│       │   1. Ingest Target & Polyglot Tree-Sitter AST Parse    │      │
│       │   2. Resolve Call Graph & 2D/3D Data Flow Models       │      │
│       │   3. Detect Indian PII & Deterministic Checksums       │      │
│       │   4. Evaluate Pass A & Pass B DPDP Statutory Rules     │      │
│       │   5. Penalty Band Risk Classification & Gate Check     │      │
│       │   6. Generate 15 Compliance Deliverables & Cryptography│      │
│       └────────────────────────────────────────────────────────┘      │
│                                                                        │
└────────────────────────────────────────────────────────────────────────┘
```

---

### 2. Launching the Desktop GUI

The PySide6 corporate desktop application provides an interactive workspace for running audits, inspecting finding details, filtering by severity and penalty bands, and visualizing data flows.

#### Methods to Launch:
1. **Standalone Windows Executable (No Python Required):**
   ```powershell
   .\dist\CS-01\cs01-gui.exe
   ```
2. **One-Click Batch Launcher:**
   Double-click `launch_gui.bat` in the root folder. It automatically detects and launches the standalone executable if present, or falls back to your local virtual environment.
3. **CLI Shortcut:**
   ```bash
   cs01 gui
   # or
   cs01-gui
   ```
4. **Python Module:**
   ```bash
   python -m cs01.gui
   ```

#### Key GUI Capabilities:
- **Audit Configuration View:** Select local repository folders or software archives (`.zip`, `.tar.gz`), set output directories, and choose failure severity thresholds.
- **Asynchronous Execution:** Scans execute on a dedicated `QThread` via `AuditWorker`. The interface remains responsive with active stage progress and finding counters.
- **Control Locking:** The "Start Audit" button locks during active audits and the "Cancel" button is enabled. Controls automatically restore upon completion or error.
- **Fail-Explicit Feedback:** Any invalid path or scan failure surfaces immediately with clear error logs in the status drawer.
- **One-Click Deliverable Access:** Open executive HTML dashboards, 2D/3D visualizers, and generated diff patches directly from the GUI.

---

### 3. CLI Auditing & Automation

The console binary `cs01.exe` (or `cs01` python command) provides full automation for CI/CD pipelines:

#### Basic Audit
```bash
cs01 scan /path/to/project --output-dir ./cs01-reports
```

#### Fail Policy Gates
Enforce strict compliance gates in CI/CD workflows:
```bash
# Fail build if CRITICAL violations exist (e.g. ₹250 Crore penalty band)
cs01 scan /path/to/project --fail-on critical

# Fail build on any HIGH or CRITICAL violations
cs01 scan /path/to/project --fail-on high
```

#### Inspect Active Statutory Rules
```bash
cs01 rules
```
Displays all loaded Pass A (Code/SQL/IaC) and Pass B (Architectural) DPDP rules, statutory penalty bands, and section citations.

---

### 4. Generated Compliance Deliverables Catalog

Every audit generates a suite of 15 deliverables in the designated output directory:

| Deliverable | Format | Purpose |
|---|---|---|
| `cs01-dpo-report.html` | HTML / CSS | **Executive DPO Dashboard** with readiness score, penalty exposure, and pillar breakdown. |
| `cs01-dataflow.html` | HTML / WebGL | **2D Swimlane & 3D Spatial Visualizer** (1.35 MB) mapping source-to-sink data leaks. |
| `cs01-report.md` | Markdown | **Detailed Technical Audit Report** with code snippets and remediation guidance. |
| `cs01-findings.sarif` | SARIF 2.1.0 | **Static Analysis Interchange Format** for VS Code, GitHub Security, and SonarQube. |
| `gl-sast-report.json` | JSON | **GitLab SAST Report** for native GitLab CI/CD vulnerability integration. |
| `cs01-compliance.json` | JSON | **Complete Machine-Readable Model** containing all findings, scores, and metadata. |
| `ropa_map.json` | JSON | **Technical RoPA Draft** supporting Record of Processing Activities under Section 8. |
| `consent_audit.json` | JSON | **Consent Lifecycle Audit** evaluating consent collection, notice, and withdrawal routes. |
| `cs01-evidence-bundle.zip` | ZIP (Signed) | **Rule 13 Evidence Locker** with SHA-256 manifest and digital signatures. |
| `remediation_patches/` | Git Diffs | **Automated Fix Patches** with unified diffs ready for `git apply`. |
| `dpo_ai_executive_brief.md` | Markdown | **AI Triage Prompt & Brief** tailored for local LLMs (e.g. Qwen 2.5 Coder). |

---

### 5. Standalone Windows Packaging & Distribution

CS-01 is packaged using PyInstaller into an enterprise-ready `--onedir` release:

#### Standalone Directory: `dist/CS-01/`
- **`cs01-gui.exe`** (10.9 MB): Windowed desktop GUI with embedded multi-resolution shield icon (`assets/cs01.ico`).
- **`cs01.exe`** (10.9 MB): Terminal CLI executable.
- **`_internal/`**: Bundled PySide6 libraries, Python runtime, DPDP rule YAML definitions, and visualization assets.

#### Building the Distribution:
Run the automated build orchestrator:
```powershell
python scripts/build_dist.py
```
This script handles:
1. Environment and dependency verification (`pyinstaller`, `pillow`).
2. Generating high-resolution multi-size application icons (`16x16` through `256x256`).
3. Compiling the PyInstaller spec (`cs01.spec`).
4. Generating the Inno Setup installer script (`dist/CS-01-Setup.iss`).
5. Running automated post-build binary verification (`cs01.exe --help`, `cs01.exe rules`, and `cs01-gui.exe`).

#### Compiling the Windows Installer:
With [Inno Setup 6](https://jrsoftware.org/isinfo.php) installed, compile the setup executable with:
```powershell
iscc dist\CS-01-Setup.iss
```
This produces `dist\CS-01-DPDP-Auditor-Setup-v0.1.0-alpha.exe` with standard Program Files installation, desktop shortcuts, and uninstaller support.

---

### 6. Accuracy Benchmarking & Ground-Truth Verification

CS-01 includes a paired ground-truth benchmark suite evaluating precision, recall, and F1 score against vulnerable and clean application repositories:

```powershell
python cs01/tests/accuracy_bench/evaluate.py
```

#### Benchmark Results:
- **Evaluated Rules:** 17 Statutory DPDP Rules
- **True Positives (TP):** 17 / 17
- **False Positives (FP):** 0
- **True Negatives (TN):** 18 / 18
- **False Negatives (FN):** 0
- **Precision:** **100.0%**
- **Recall:** **100.0%**
- **F1 Score:** **1.000**
- **False Positive Rate (FPR):** **0.0%**
