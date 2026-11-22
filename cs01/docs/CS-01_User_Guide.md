# CS-01: End-User & Operator Documentation
*Full-Stack DPDP Compliance Auditor for India's Digital Personal Data Protection Act, 2023 & DPDP Rules, 2025*

---

## 1. Quick Start (0 to Scan in 60 Seconds)

### System Requirements
- **Operating System:** Windows 10/11, macOS, or Linux (Ubuntu 20.04+)
- **Python Version:** Python 3.11 or higher
- **Network Access:** **None required.** CS-01 operates 100% locally and offline. Zero source code or detected data ever leaves your machine.

### Installation

1. Open PowerShell / your terminal in the repository root:
   ```powershell
   cd c:\DPDP\cs01
   ```

2. (Recommended) Activate your Python virtual environment:
   ```powershell
   # If using an existing venv:
   .\venv\Scripts\Activate.ps1   # On Windows
   # source venv/bin/activate    # On Linux/macOS
   ```

3. Install `cs01` in editable mode:
   ```powershell
   pip install -e .
   ```

4. Verify installation:
   ```powershell
   cs01 --help
   ```

---

## 2. Basic Usage (All-in-One Command)

You can execute the entire compliance pipeline from ingestion to reports, Qwen 2.5 Coder AI briefing, and Rule 13 evidence verification with **one single command**:

```powershell
# For any codebase directory:
cs01 audit C:\path\to\your\project

# Or for a software ZIP archive directly:
cs01 audit C:\path\to\software.zip
```

*(Note: `cs01 audit` and `cs01 scan` are identical all-in-one commands).*

---

## 3. CLI Command Reference

CS-01 provides both high-level scanning commands and granular stage-by-stage debugging tools.

### 3.1 `cs01 scan` (Full 6-Stage Pipeline)
Runs the entire pipeline from repo ingestion to final report and patch generation.

```powershell
cs01 scan <TARGET> [OPTIONS]
```

**Options:**
- `<TARGET>`: Path to a repository folder or `.zip` / `.tar.gz` archive (required).
- `-o, --output-dir <DIR>`: Directory where all report artifacts will be written (default: `./cs01-reports`).
- `-c, --config <FILE>`: Path to custom `cs01.yaml` configuration file.
- `--fail-on <LEVEL>`: Policy gate failure threshold: `critical`, `high`, `medium`, or `never` (default: `high`). If any finding meets or exceeds this severity, the CLI exits with non-zero exit code `1`.
- `-f, --format <FORMAT>`: Report formats to generate: `all`, `sarif`, `json`, or `html` (default: `all`).
- `--baseline <FILE>`: Path to `.cs01-baseline.json` file. Suppresses known baseline findings from failing CI/CD builds.
- `--save-stage-output`: Exports intermediate JSON payloads for all 6 pipeline stages (`stage1_manifest.json`, `stage2_model.json`, etc.) to the output directory.
- `--debug`: Enables verbose, detailed console logging.

**Exit Codes:**
- `0`: Scan clean — no findings at or above `--fail-on` threshold.
- `1`: Policy gate failed — one or more findings violated the threshold.
- `2`: Configuration or runtime error.
- `3`: Partial scan — some files could not be parsed (non-fatal warnings recorded).

---

### 3.2 `cs01 baseline` (Managing Technical Debt in CI/CD)
Prevents existing compliance debt from breaking active pull requests while ensuring that **new regressions** are blocked immediately.

#### Create a Baseline
Captures the deterministic SHA-256 fingerprints of all current findings and saves them to a baseline file:
```powershell
# Create baseline from a project folder or archive:
cs01 baseline create C:\path\to\project -o .cs01-baseline.json

# Or create baseline from an existing stage5_bundle.json:
cs01 baseline create ./cs01-reports/stage5_bundle.json -o .cs01-baseline.json
```

#### Diff Against a Baseline
Compares current findings against the baseline to isolate new regressions, tolerated baseline debt, and resolved violations:
```powershell
cs01 baseline diff ./cs01-reports/stage5_bundle.json --baseline .cs01-baseline.json
```

#### Enforce Baseline in CI Builds
Pass the baseline file during standard scanning:
```powershell
cs01 scan ./myapp --baseline .cs01-baseline.json --fail-on high
```
*Findings matching the baseline are marked as `is_baseline_suppressed = true` and will NOT trigger a build failure. Only newly introduced violations fail the build.*

---

### 3.3 `cs01 rules` (Rule Catalog & Legal Citations)
Inspect the compliance rules loaded by the engine.

```powershell
# List all active rules in a formatted terminal table:
cs01 rules

# Filter by pass (Pass A: Local AST/IaC; Pass B: Cross-file Architectural):
cs01 rules --pass A
cs01 rules --pass B

# Explain a specific statutory rule in JSON:
cs01 rules CODE-DPDP-001
cs01 rules ARCH-DPDP-001
```

---

### 3.4 `cs01 verify-evidence` (Rule 13 Evidence Cryptography)
Under DPDP Rule 13, audit evidence must be verifiable and tamper-evident. CS-01 generates cryptographic ZIP archives containing SHA-256 sidecars.

```powershell
cs01 verify-evidence ./cs01-reports/cs01-evidence-bundle.zip
```

**Verification checks performed:**
- Validates the manifest SHA-256 against the included `.sig` sidecar.
- Validates every individual report artifact's SHA-256 digest against the manifest.
- Validates the internal hash tree to confirm zero tampering, modification, or truncation.

---

### 3.5 `cs01 probe` (Opt-in Live DAST Safeguard Prober)
Audits live HTTP(S) endpoints for technical safeguards, TLS cipher strength, missing security headers, and §5 Privacy Notice accessibility.

> [!CAUTION]
> **Safety Guardrail:** Probing live network endpoints is strictly opt-in. You **must** pass `--allow-live-probe` to confirm you own or are authorized to audit the target.

```powershell
cs01 probe https://api.mycompany.in --allow-live-probe -o ./probe-results.json
```

---

### 3.6 Debugging Commands (Stage-by-Stage Inspection)
For developers debugging specific parsers or rules:

| Command | Stage | Purpose |
|---|---|---|
| `cs01 ingest <path>` | Stage 1 | Inspect file discovery, ignore exclusions, and semantic bucketing. |
| `cs01 parse <manifest_or_dir>` | Stage 2 | Inspect tree-sitter ASTs, SQL DDL tables, Terraform resources, and env keys. |
| `cs01 detect <model_or_dir>` | Stage 3 | View PII detections and intra-procedural flow graph edges. |
| `cs01 evaluate <dir>` | Stage 4 | View raw rule violations before scoring and deduplication. |
| `cs01 classify <dir>` | Stage 5 | Inspect 8-pillar readiness scorecard and priority scores. |
| `cs01 report <bundle.json>` | Stage 6 | Re-render reports and patches from an existing scored bundle. |

---

## 4. Understanding Output Deliverables

After a scan completes, the output directory contains 8 complementary artifacts:

```
cs01-reports/
├── cs01-dpo-report.html            # Executive & Legal Dashboard
├── cs01-sarif.sarif                # Developer IDE & GitHub Code Scanning SARIF
├── gl-sast-report.json             # GitLab SAST Vulnerability Format
├── ropa_map.json                   # Technical Record of Processing Activities
├── consent_audit.json              # Consent Lifecycle & Withdrawal Verification
├── cs01-evidence-bundle.zip        # Cryptographic Rule 13 Evidence Archive
├── cs01-evidence-bundle.zip.sha256 # Cryptographic Checksum Sidecar
└── remediation_patches/            # Git-Applicable Remediation Patches
    ├── CODE-DPDP-001-app.py.patch
    └── IAC-DPDP-001-main.tf.patch
```

### 1. `cs01-dpo-report.html` (Executive DPO Report)
- Open this file in any web browser.
- Displays the **Overall DPDP Readiness Score (0–100)**.
- Breaks down compliance across the **8 Statutory Pillars**:
  1. Notice & Consent (§5, §6, Rule 3)
  2. Security Safeguards (§8(5), Rule 6(1)(a))
  3. Breach Readiness (§8(6), Rule 7)
  4. Retention & Erasure (Rule 6(1)(e), Rule 8)
  5. Children & PwD Protection (§9, Rule 10)
  6. SDF Duties (§10, Rule 12, Rule 13)
  7. Data Principal Rights (Rule 14, §11, §12, §13)
  8. Cross-Border & CERT-In Controls (Rule 15, CERT-In)
- **Dynamic Capping Alert:** If any unresolved `CRITICAL` finding exists under a high-penalty band (§8(5) ₹250 Cr or §9 ₹200 Cr), the overall score is automatically capped at **60.0/100**, alerting executives to acute regulatory exposure.

### 2. `cs01-sarif.sarif` (Developer Integration)
- Standard SARIF 2.1.0 format.
- Upload directly to **GitHub Code Scanning**, Azure DevOps, or open in the **SARIF Viewer extension in VS Code**.
- Rules include full statutory context, exact file line/column coordinates, and remediation recommendations.

### 3. `remediation_patches/` (Automated Fixes)
- Contains unified diff patches generated deterministically for detected violations (e.g., masking PII in loggers, adding encryption flags to Terraform DB instances).
- Apply a patch directly:
  ```powershell
  git apply cs01-reports/remediation_patches/CODE-DPDP-001-app.py.patch
  ```

---

## 5. Configuration Guide

CS-01 works out of the box with zero configuration using statutory defaults. To tailor the scan to your company's profile, create a `cs01.yaml` file in your repository root.

### Example `cs01.yaml`

```yaml
# Organization Profile
org_name: "FinTech Enterprises India Pvt Ltd"
entity_type: "data_fiduciary"
is_sdf: false                        # Set to true if designated as a Significant Data Fiduciary

# Third Schedule Sensitive Data Categories Handled
third_schedule:
  health_data: false
  financial_data: true               # UPI, PAN, Bank Details
  biometric_data: false
  children_data: false               # If true, §9 age-gating rules are enforced strictly

# Approved Third-Party Data Processors (whitelisted from exfiltration warnings)
approved_processors:
  - name: "aws"
    services: ["s3", "rds", "kms"]
  - name: "razorpay"
    services: ["payments", "payouts"]
  - name: "cashfree"
    services: ["verification"]

# Allowed Cross-Border Transfer Regions (§16 / Rule 15)
allowed_cross_border_regions:
  - "ap-south-1"                     # Mumbai
  - "ap-south-2"                     # Hyderabad

# Scan Settings
scan_layers:
  - code
  - schema
  - iac
  - secrets

fail_on: "high"                      # critical | high | medium | never
output_formats:
  - sarif
  - json
  - html
output_dir: "./cs01-reports"
```

### Excluding Files via `.dpdpignore`
Create a `.dpdpignore` file in your repository root (uses standard `.gitignore` syntax) to exclude third-party vendor code, documentation, or fixtures:

```gitignore
# Exclude vendor directories
vendor/
third_party/

# Exclude generated docs
docs/site/

# Exclude synthetic mock data
fixtures/mock_seeds/
```
*(Standard directories like `node_modules`, `.git`, `venv`, and `__pycache__` are excluded automatically by default).*

---

## 6. CI/CD Pipeline Automation

### GitHub Actions Workflow
Create `.github/workflows/dpdp-compliance.yml`:

```yaml
name: DPDP Compliance Audit

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  compliance-scan:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install CS-01
        run: |
          pip install --upgrade pip
          pip install cs01  # or pip install git+https://github.com/your-org/cs01.git

      - name: Run CS-01 Scan
        run: |
          cs01 scan . \
            --baseline .cs01-baseline.json \
            --fail-on high \
            --output-dir ./cs01-reports

      - name: Upload SARIF to GitHub Security Tab
        uses: github/codeql-action/upload-sarif@v3
        if: always()
        with:
          sarif_file: ./cs01-reports/cs01-sarif.sarif

      - name: Archive Compliance Deliverables
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: dpdp-compliance-reports
          path: ./cs01-reports/
```

### GitLab CI Pipeline
Add to `.gitlab-ci.yml`:

```yaml
dpdp_compliance:
  stage: test
  image: python:3.11
  script:
    - pip install -e /path/to/cs01
    - cs01 scan . --baseline .cs01-baseline.json --fail-on high --output-dir ./cs01-reports
  artifacts:
    reports:
      sast: ./cs01-reports/gl-sast-report.json
    paths:
      - ./cs01-reports/cs01-dpo-report.html
      - ./cs01-reports/cs01-evidence-bundle.zip
    when: always
```

---

## 7. LLM Reporting Rules & Standards (Qwen 2.5 Coder)

The local AI engine enforces the following **10 Reporting Rules** when writing reports:

1. **Mandatory Exact Code Citation:** Every vulnerability must quote its exact file, line number, and code snippet.
2. **Mechanics of Failure:** The report must explain how the code operates line-by-line and why it constitutes a breach or leak.
3. **India DPDP Grounding:** Must explicitly cite the governing section (§8(5), §8(6), §9, §10, Rule 6/8/10) and statutory maximum ceiling.
4. **"Before vs. After" Code Fix:** Drop-in, production-ready replacement code demonstrating masking, ORM encryption, or routing.
5. **Two-Tier Framing:** Plain-English business risk for the DPO and Board, paired with technical root-cause analysis for developers.
6. **Zero Hallucination & Redaction Integrity:** Never invent files or identities; always preserve placeholders like `[AADHAAR_1]`.
7. **Verification Steps:** Concrete instructions on how developers can verify that the vulnerability has been resolved.
8. **Data Principal Impact:** Assessment of real-world harm to individuals (e.g., identity theft, financial fraud).
9. **Active Leaks vs. Architectural Gaps:** Distinct categorization between active plaintext exfiltration vs. missing purge routines.
10. **Statutory Disclaimer:** Disclaims that penalties are discretionary ceilings under §33(2) and CS-01 is a technical auditing tool.

---

## 8. Frequently Asked Questions (FAQ)

#### Q1: Does CS-01 send my code or customer data to any cloud service?
**No.** CS-01 is 100% local-first and zero-egress. All AST parsing, regular expression matching, and mathematical validator calculations execute on your CPU. No code or PII is ever transmitted externally.

#### Q2: How does CS-01 prevent false positives on synthetic test data?
Any PII found inside test folders (`tests/`, `spec/`, `__tests__/`) is automatically capped at a low confidence score of `0.30` and downgraded to `INTERNAL` exposure, preventing test fixtures from failing production CI gates. Furthermore, numbers with invalid checksums (e.g. failing the Verhoeff algorithm for Aadhaar) are discarded before any violation is recorded.

#### Q3: How do we fix an unencrypted database finding?
Inspect the `remediation_patches/` folder in your output directory. CS-01 automatically generates `.patch` files showing the exact migration or ORM attribute change required to achieve compliance.
