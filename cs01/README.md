# CS-01: Full-Stack DPDP Compliance Auditor
*Automated Codebase, Schema, Infrastructure & Configuration Scanner for India's DPDP Act, 2023 & DPDP Rules, 2025*

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-green.svg)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Alpha_Verified-brightgreen.svg)]()
[![Tests](https://img.shields.io/badge/Tests-56%2F56_Passing-success.svg)]()

---

## What is CS-01?

**CS-01** is an open-core, local-first compliance auditing tool designed to audit software applications against India's **Digital Personal Data Protection Act, 2023 (DPDP)** and the **DPDP Rules, 2025**.

It analyzes source code (AST), database DDL/ORM models, infrastructure configurations (Terraform, K8s, Dockerfiles), and `.env` configs to detect personal data mishandling, trace data flows to unapproved sinks, and calculate statutory penalty exposure ceilings (up to ₹250 Crore under §8(5) and ₹200 Crore under §9).

---

## Key Features

- **Zero Cloud Egress / Local-First:** 100% offline analysis. No source code or customer data ever leaves your machine.
- **Native Directory & Archive Support:** Scans local directories or `.zip` / `.tar.gz` archives directly with built-in Zip Slip protection.
- **Pure-Math Indian PII Validators:** 
  - **Aadhaar:** Verhoeff checksum algorithm + IIN check.
  - **PAN:** 10-character structure + 4th character entity type (`P`, `C`, `H`, etc.) validation.
  - **GSTIN:** State code + embedded PAN validation + Luhn mod-36 checksum.
  - **UPI:** Verified against NPCI handle catalog (Google Pay, PhonePe, Paytm, BHIM, etc.).
  - **Others:** Mobile, Passport, Voter ID, IFSC, Email, IP addresses.
- **6-Stage Structured Pipeline:** Ingest $\to$ Parse $\to$ Detect $\to$ Evaluate $\to$ Classify $\to$ Report.
- **Cross-File Architectural Checks (Pass B):** Identifies whole-repo compliance gaps (e.g., missing consent withdrawal routes, missing retention purge jobs, children DOB collection without age-gating).
- **8-Pillar DPDP Readiness Score (0–100):** Executive scorecard with dynamic score capping for acute critical exposure.
- **Multi-Format Reporting:** Generates SARIF 2.1.0, GitLab SAST, Jinja2 Executive HTML Report, RoPA Draft, Consent Audit, and Rule 13 tamper-evident signed ZIP evidence lockers.
- **Baseline Technical Debt Management:** Suppresses existing baseline findings in CI/CD so only new pull-request regressions fail builds.

---

## Quick Start

### 1. Installation

Ensure you have Python 3.11+ installed:

```powershell
# Navigate to the cs01 package directory
cd cs01

# Install in editable mode
pip install -e .
```

Verify installation:
```powershell
cs01 --help
```

### 2. Run an Audit

```powershell
# Scan any codebase directory
cs01 scan C:\path\to\your\project --output-dir ./cs01-reports

# Or scan a zipped application directly
cs01 scan C:\path\to\software.zip --output-dir ./cs01-reports
```

---

## CLI Commands

| Command | Description |
|---|---|
| `cs01 scan <target>` | Run full 6-stage compliance audit (`--fail-on high`, `--output-dir`, `--baseline`) |
| `cs01 baseline create <target>` | Generate `.cs01-baseline.json` to freeze existing technical debt |
| `cs01 baseline diff <bundle>` | Compare scan results against baseline to isolate regressions |
| `cs01 rules` | List all active statutory DPDP rules and penalty bands |
| `cs01 verify-evidence <zip>` | Cryptographically verify SHA-256 integrity of a Rule 13 evidence bundle |
| `cs01 probe <url>` | Opt-in live safeguard DAST probe (`--allow-live-probe`) |

---

## Output Deliverables

After a scan completes, `./cs01-reports` will contain:

- `cs01-dpo-report.html` — Interactive executive dashboard with readiness score and statutory pillars.
- `cs01-sarif.sarif` — GitHub Code Scanning & VS Code SARIF 2.1.0 format.
- `gl-sast-report.json` — GitLab SAST format.
- `ropa_map.json` — Technical Record of Processing Activities draft.
- `consent_audit.json` — Verification of consent collection and withdrawal mechanisms.
- `remediation_patches/` — Git-applicable unified `.patch` fixes.
- `cs01-evidence-bundle.zip` — Tamper-evident cryptographic audit archive.

---

## Documentation

For the complete end-user and operator guide including configuration (`cs01.yaml`, `.dpdpignore`) and CI/CD pipelines (GitHub Actions, GitLab CI), see:
- [CS-01 End-User Guide](docs/CS-01_User_Guide.md)
