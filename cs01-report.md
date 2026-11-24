# Full-Stack Data Protection (DPDP) Compliance Assessment Report

**Target Application:** Unknown Org (dpdp-code-auditor)  
**Assessment Status:** [FAIL — Policy Gate: fail-on High]  
**DPDP Readiness Score:** 60 / 100 · **CAPPED** (Overall score capped at 60.0 due to 4 unresolved CRITICAL finding(s) in the ₹250 Crore (§8(5) Security Safeguards) penalty band.)  
**Highest Statutory Ceiling Band Engaged:** ₹250 Crore (§8(5) Security Safeguards)  
**Report Generated:** 2026-11-24 02:14:15 UTC / 2026-11-24 07:44:15 IST  

---

## 1. Document Control & Scan Provenance

| Attribute | Value |
|---|---|
| **Repository / Target Path** | `C:\Yogendra\dpdp-code-auditor` |
| **Git Branch & Commit SHA** | `main` @ `local-unversioned-dfde5c45c374` |
| **Scan Mode & Scope** | Full Repository (`20` files scanned, `0` skipped) |
| **Scanner & Rulepack Version** | `CS-01 v0.1.0-alpha` · Rulepack `DPDP-2025-v1.0` |
| **Applicable Legal Baseline** | DPDP Act, 2023 · DPDP Rules, 2025 (G.S.R. 846(E), Corr. G.S.R. 892(E), RoD Order 2026) · CERT-In 2022 |
| **Organization Profile (`cs01.yaml`)** | SDF: `No` · Third Schedule Class: `Standard` · Child Data: `No` · CERT-In Strict: `Yes` |
| **Execution Exit Code** | `1 = Policy Fail` |
| **Evidence Bundle Digest (SHA-256)** | `9c4d1d22b4de8d1e6ef84581d10f1a4f645d925d23bc3c4c5dd92ce628b4faf7` |

---

## 2. Executive & DPO Compliance Summary

### 2.1 Overall Posture & Severity Breakdown

Automated full-stack compliance assessment identified **10 active statutory finding(s)** across application source code, schemas, and cloud infrastructure. Acute regulatory exposure was detected with the engagement of high-penalty statutory ceilings, capping the overall DPDP Readiness Score. Immediate engineering remediation is advised ahead of the statutory enforcement deadline.

| Severity | Active Findings | New Since Baseline | Baselined / Suppressed | Primary Risk Profile |
|---|---:|---:|---:|---|
| **CRITICAL** | `4` | `+4` | `0` | External PII exposure, broken auth, unencrypted sensitive PII, minor tracking |
| **HIGH** | `3` | `+3` | `0` | Plaintext PII logs, soft-delete-only erasure, ungated 3rd-party / Shadow AI egress |
| **MEDIUM** | `3` | `+3` | `0` | Bundled/pre-checked consent UI, missing Rule 3 notice, log retention under 365 days |
| **LOW** | `0` | `+0` | `0` | Defense-in-depth hardening and metadata hygiene |
| **TOTAL** | **`10`** | **`+10`** | **`0`** | |

### 2.2 Statutory Penalty-Band Exposure Matrix (DPDP Act Section 33 Schedule)

| Statutory Provision | Obligation Category | Statutory Ceiling | Open Findings | Highest Severity |
|---|---|---|---:|---|
| **Sec 8(5) & Rule 6** | Reasonable Security Safeguards | Up to ₹250 Crore | `4` | `CRITICAL` |
| **Sec 8(6) & Rule 7** | Personal Data Breach Notification | Up to ₹200 Crore | `0` | `N/A` |
| **Sec 9 & Rules 10–12** | Children's & PwD Data Obligations | Up to ₹200 Crore | `0` | `N/A` |
| **Sec 10 & Rule 13** | Significant Data Fiduciary (SDF) Duties | Up to ₹150 Crore | `0` | `N/A` |
| **Sec 4–6, 8(2), 8(7), 11–16** | Notice, Consent, Retention, Rights, Transfers | Up to ₹50 Crore | `6` | `HIGH` |
| **IT Act Sec 70B** | CERT-In 2022 Directions (Logs / NTP / 6-hr) | IT Act Penalties | `0` | `N/A` |

> **Statutory Interpretation Notice:** Penalty ceilings represent statutory maximums under the Schedule to the DPDP Act, 2023. Actual penalties are adjudicated by the Data Protection Board of India based on gravity, duration, and mitigation factors under Section 33(2). This technical report does not constitute legal advice.

### 2.3 Top Priority Compliance Blockers

1. **`[CODE-DPDP-001:EXAMPLES/VULNERABLE_APP/BACKEND/API.PY:10]` ([CRITICAL] · Priority `[90/100]`):** Personal data flows directly into an unguarded logger sink (`Sec §8(5) / Rule 6(1)(a)`).
2. **`[SQL-DPDP-001:EXAMPLES/VULNERABLE_APP/DB/SCHEMA.SQL:1]` ([CRITICAL] · Priority `[90/100]`):** Personal data column defined without column-level encryption marker in database schema (`Sec §8(5) / Rule 6(1)(a)`).
3. **`[SQL-DPDP-001:EXAMPLES/VULNERABLE_APP/DB/SCHEMA.SQL:1]` ([CRITICAL] · Priority `[90/100]`):** Personal data column defined without column-level encryption marker in database schema (`Sec §8(5) / Rule 6(1)(a)`).

> *Executive Note: Showing top 3 high-priority blockers out of **10 total active violations**. For the exhaustive technical analysis, vulnerable snippets, and before/after remediations for all 10 findings, see **Section 5: Detailed Technical Findings**.*

---

## 3. Compliance Coverage Matrix

### 3.1 By Statutory DPDP Pillar

| Statutory Pillar | Rules Evaluated | Passed | Failed | Not Applicable | Pillar Status |
|---|---:|---:|---:|---:|---|
| Notice & Consent | `3` | `0` | `3` | `0` | `[FAIL]` |
| Security Safeguards | `8` | `6` | `2` | `0` | `[FAIL]` |
| Breach Readiness | `1` | `1` | `0` | `0` | `[PASS]` |
| Retention & Erasure | `3` | `1` | `2` | `0` | `[PARTIAL]` |
| Children & PwD Protection | `1` | `1` | `0` | `0` | `[PASS]` |
| SDF Duties | `1` | `1` | `0` | `0` | `[PASS]` |
| Data Principal Rights | `1` | `0` | `1` | `0` | `[PARTIAL]` |
| Cross-Border & CERT-In Controls | `5` | `5` | `0` | `0` | `[PASS]` |
| CERT-In 2022 Overlap (`Sec 70B`) | `1` | `1` | `0` | `0` | `[PASS]` |

### 3.2 By Application Stack Layer

| Stack Layer | Files / Targets Analyzed | Critical | High | Medium | Low |
|---|---:|---:|---:|---:|---:|
| Layer 1: Front-End & Back-End Source Code | `20` | `2` | `3` | `0` | `0` |
| Layer 2: India-Native PII & Secrets Scanner | `20` | `0` | `0` | `0` | `0` |
| Layer 3: Database Schemas & SQL Migrations | `Schemas Evaluated` | `2` | `0` | `3` | `0` |
| Layer 4: IaC, Containers & Configs (`.env`, TF, K8s, Docker) | `Configs Evaluated` | `0` | `0` | `0` | `0` |
| Layer 5: Live API & Web Surface Probe *(Opt-in)* | `0 endpoints` | `0` | `0` | `0` | `0` |

### 3.3 Statutory DPDP Rules, 2025 (Rules 1 to 23) Evaluation Matrix

| DPDP Rule | Statutory Heading | Governed DPDP Act Section | Schedule Ceiling Band | Audit Status | Statutory Compliance Summary |
|---|---|---|---|---|---|
| **Rule 1** | Short Title & Phased Commencement | §1(2) | Up to ₹50 Crore | `[PASS]` | Phased transition milestones aligned with organization profile |
| **Rule 2** | Definitions & User Account Boundary | §2(j), §2(t) | Up to ₹50 Crore | `[AUDITED]` | Fiduciary vs processor account boundary definitions checked |
| **Rule 3** | Notice for Seeking Consent | §5(1), §6(1) | Up to ₹50 Crore | `[FAIL]` | Notice route standalone independence and withdrawal mechanism parity |
| **Rule 4** | Registered Consent Managers | §6(7)–(9) | Up to ₹50 Crore | `[AUDITED]` | First Schedule interoperable API specifications audited |
| **Rule 5** | State Functions & Legitimate Uses | §7(b) | Up to ₹50 Crore | `[AUDITED]` | Second Schedule standards verified for statutory processing |
| **Rule 6** | Reasonable Security Safeguards | §8(5) | Up to ₹250 Crore | `[FAIL]` | Cryptographic controls, BOLA/IDOR auth, and 365-day log floor |
| **Rule 7** | Personal Data Breach Intimation | §8(6) | Up to ₹200 Crore | `[PASS]` | 72-hour Board & Principal breach notification handlers |
| **Rule 8** | Purpose-Completion Erasure & Retention | §8(7), §12(3) | Up to ₹50 Crore | `[FAIL]` | Third Schedule inactivity thresholds & pre-erasure warning notifications |
| **Rule 9** | DPO & Privacy Contact Publication | §8(9) | Up to ₹50 Crore | `[PASS]` | Publication of DPO contact details and physical address in India |
| **Rule 10** | Verifiable Parental Consent for Children | §9(1) | Up to ₹200 Crore | `[PASS]` | Fourth Schedule age verification & guardian consent gate |
| **Rule 11** | Persons with Disabilities Consent | §9(2) | Up to ₹50 Crore | `[AUDITED]` | Legal guardian consent verification mechanisms for individuals under disability |
| **Rule 12** | Ban on Child Tracking, Profiling & Ads | §9(2)–(3) | Up to ₹200 Crore | `[PASS]` | Zero behavioral analytics / tracking SDKs on minor data |
| **Rule 13** | Significant Data Fiduciary (SDF) Duties | §10 | Up to ₹150 Crore | `[PASS]` | DPIA readiness, independent data audit logging trails & data localization |
| **Rule 14** | Rights of Data Principals & 30-Day SLA | §§11–14 | Up to ₹50 Crore | `[PASS]` | Access summary, correction, nomination & max 30-day grievance SLA |
| **Rule 15** | Cross-Border Personal Data Transfers | §16 | Up to ₹50 Crore | `[PASS]` | Central Government notified territories and transfer safeguard restrictions |
| **Rule 16** | Research, Archival & Statistical Exemptions | §17(2)(b) | Up to ₹50 Crore | `[AUDITED]` | Cryptographic de-identification and operational decision segregation |
| **Rules 17–22** | DPBI Constitution, Officers & Tribunal Appeals | §§18–26 | N/A | `[N/A]` | Institutional governance provisions governing DPBI authority proceedings |
| **Rule 23** | Board Power to Call Information & Inspect | §27 | Up to ₹50 Crore | `[AUDITED]` | Digital audit trail non-repudiation, exportability, and tamper resistance |

---

## 4. Auto-Generated RoPA & Personal Data-Flow Inventory

*Derived automatically from AST sources, SQL schemas, Terraform regions, and outbound SDK/HTTP sinks to support Record of Processing Activities (RoPA) documentation.*

| Personal Data Category | Collection Point (Route / UI) | Storage (Table / Column / Protection) | Outbound Sinks (Logs / 3rd-Party / AI) | Cloud Region | Consent & Processor Status |
|---|---|---|---|---|---|
| **Contact (EMAIL)** | `examples/vulnerable_app/db/schema.sql:1` | Transient Flow | Internal Service Logic | `Domestic (India / Local)` | Plaintext Storage (Review §8(5)) |
| **Contact (MOBILE)** | `examples/vulnerable_app/db/schema.sql:1` | Transient Flow | Internal Service Logic | `Domestic (India / Local)` | Plaintext Storage (Review §8(5)) |

---

## 5. Detailed Technical Findings

*Ordered strictly by Priority Score (descending). All real PII values and secrets inside code snippets are masked prior to output.*

### `[FND-0001]` — `[Personal data flows directly into an unguarded logger sink]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `CODE-DPDP-001` · `cs01/v1:cac53d0609c7` |
| **Severity / Confidence / Priority** | **`CRITICAL`** · Confidence: `0.90` · Priority Score: `90 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §8(5) · **DPDP Rules, 2025:** Rule 6(1)(a) |
| **Statutory Ceiling Band** | DPDP Act §8(5) — Up to ₹250 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 1 · `tree-sitter` |
| **Evidence Location** | `examples/vulnerable_app/backend/api.py` (Line 10) |
| **Detected PII Categories** | `function:register` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```python
     9 |     phone_number = req.body.phone_number
>   10 |     logger.info("registration payload: %s", req.body)
    11 |     requests.post("http://partner.example.test/ingest", json={"email": email})
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
The application flow directly introduces unmasked **function:register** into an application logger sink at `examples/vulnerable_app/backend/api.py:10`. During intra-procedural execution, `function:register` is evaluated and passed as a direct argument into the logging framework (`logger.info` / `console.log`) without undergoing tokenization, cryptographic hashing (HMAC-SHA256), or masking. Because standard application logging subsystems stream structured strings to persistent log files and centralized log aggregators (such as AWS CloudWatch, Datadog, Elasticsearch, or disk files), the unmasked personal data leaves the bounded memory of the application and becomes permanently embedded in log streams. Perimeter defenses such as Web Application Firewalls (WAF) or database-level column encryption offer zero protection against this vulnerability, as the data is exfiltrated internally through standard application telemetry.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(5)** read with **DPDP Rules, 2025, Rule 6(1)(a)**.
- **Statutory Mandate:** Section 8(5) imposes an affirmative, non-delegable duty on every Data Fiduciary to protect personal data in its possession or under its control by taking reasonable security safeguards to prevent personal data breaches. Rule 6(1)(a) explicitly mandates technical safeguards including masking, de-identification, and strict access controls on all non-production and telemetry data streams.
- **Penalty Exposure:** Directly engages the **₹250 Crore Statutory Maximum Ceiling** under Item 1 of the Section 33 Schedule for failure to take reasonable security safeguards. Under Section 33(2), the Data Protection Board of India (DPBI) assesses penalties based on the nature, gravity, and duration of the violation, as well as whether unauthorized parties or broad engineering teams could access the logged telemetry.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
Log aggregators are routinely accessed by dozens of developers, QA engineers, automated monitoring bots, and third-party SaaS integrations. When unmasked `function:register` is written to logs, any insider with read access to log archives or any compromised developer laptop with CloudWatch/Kibana tokens can harvest bulk Indian national identity numbers. If combined with mobile numbers, an attacker can execute targeted SIM-swap attacks, unauthorized KYC lookups, or synthetic identity theft, creating acute financial and privacy harms for the affected Data Principals.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```python
logger.info("registration payload: %s", req.body)
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION (Redaction helper applied before logging)
def mask_identifier(val: str) -> str:
    if not val or len(val) < 4:
        return '****'
    return 'X' * (len(val) - 4) + val[-4:]

# Log only non-sensitive correlation identifiers or masked tokens
logger.info('Processing transaction for user: %s (ID: %s)', user.id, mask_identifier(function:register))
```

#### 5. Engineering Verification & Automated Testing Plan
1. Replace `logger.info("registration payload: %s", req.body)` with the masked logging pattern.
2. Add a unit test asserting that `logger` calls do not receive raw digits.
3. Run `cs01 audit .` and verify that `[FND-CODE-DPDP-001]` is cleared.


---

### `[FND-0002]` — `[Personal data column defined without column-level encryption marker in database schema]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `SQL-DPDP-001` · `cs01/v1:799d9f08ffe7` |
| **Severity / Confidence / Priority** | **`CRITICAL`** · Confidence: `0.90` · Priority Score: `90 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §8(5) · **DPDP Rules, 2025:** Rule 6(1)(a) |
| **Statutory Ceiling Band** | DPDP Act §8(5) — Up to ₹250 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 3 · `tree-sitter` |
| **Evidence Location** | `examples/vulnerable_app/db/schema.sql` (Line 1) |
| **Detected PII Categories** | `customers.email` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```sql
>    1 | CREATE TABLE customers (
     2 |   id UUID PRIMARY KEY,
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
The database model at `examples/vulnerable_app/db/schema.sql:1` declares personal data column `customers.email` without a column-level encryption marker or encrypted type wrapper. In the persistence layer, the field is defined as standard plaintext (e.g. `String`, `VARCHAR`, or `Text`). When records are written to the database, the personal identifier is stored unencrypted in database pages, indexes, write-ahead logs (WAL), and backup snapshots. While Transparent Data Encryption (TDE) or cloud volume encryption protects against physical hard drive theft, it does NOT protect against SQL injection, compromised database connection credentials, read-only analytics replicas, or unauthorized database administrators querying tables directly.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(5)** read with **DPDP Rules, 2025, Rule 6(1)(a)**.
- **Statutory Mandate:** Rule 6(1)(a) requires Data Fiduciaries to employ state-of-the-art technical security measures, including cryptographic protection at rest for sensitive and high-risk personal identifiers (such as Aadhaar, PAN, financial accounts, and health markers).
- **Penalty Exposure:** Engages the **₹250 Crore Statutory Maximum Ceiling** under Section 33. Storing plaintext PII at rest is routinely categorized by the DPBI as systemic structural negligence because any single credential compromise immediately leads to a catastrophic, mass-scale personal data breach.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
If an attacker executes a SQL injection vulnerability, accesses an unencrypted database backup file stored in an S3 bucket, or compromises a database user password, all customer `customers.email` records are dumped in plaintext. Because no application-level key is required to decrypt the column values, millions of Data Principal records can be exfiltrated instantaneously and dumped on dark web forums without detection until regulatory notification occurs.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```sql
Column: email (VARCHAR(255))
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION (Using SQLAlchemy-Utils EncryptedType or KMS Wrapper)
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
import os

ENCRYPTION_KEY = os.environ['DB_COLUMN_ENCRYPTION_KEY']

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    # Column encrypted using AES-GCM before writing to the database engine
    customers.email = Column(EncryptedType(String(128), ENCRYPTION_KEY, AesEngine, 'pkcs5'))
```

#### 5. Engineering Verification & Automated Testing Plan
1. Generate a database migration wrapping `customers.email` with an authenticated encryption type (AES-256-GCM).
2. Verify through a raw SQL client (`psql` / `mysql`) that `SELECT customers.email FROM table;` returns ciphertext.
3. Run `cs01 audit .` to confirm that `SQL-DPDP-001` is resolved.


---

### `[FND-0003]` — `[Personal data column defined without column-level encryption marker in database schema]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `SQL-DPDP-001` · `cs01/v1:fe83200589de` |
| **Severity / Confidence / Priority** | **`CRITICAL`** · Confidence: `0.90` · Priority Score: `90 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §8(5) · **DPDP Rules, 2025:** Rule 6(1)(a) |
| **Statutory Ceiling Band** | DPDP Act §8(5) — Up to ₹250 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 3 · `tree-sitter` |
| **Evidence Location** | `examples/vulnerable_app/db/schema.sql` (Line 1) |
| **Detected PII Categories** | `customers.phone_number` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```sql
>    1 | CREATE TABLE customers (
     2 |   id UUID PRIMARY KEY,
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
The database model at `examples/vulnerable_app/db/schema.sql:1` declares personal data column `customers.phone_number` without a column-level encryption marker or encrypted type wrapper. In the persistence layer, the field is defined as standard plaintext (e.g. `String`, `VARCHAR`, or `Text`). When records are written to the database, the personal identifier is stored unencrypted in database pages, indexes, write-ahead logs (WAL), and backup snapshots. While Transparent Data Encryption (TDE) or cloud volume encryption protects against physical hard drive theft, it does NOT protect against SQL injection, compromised database connection credentials, read-only analytics replicas, or unauthorized database administrators querying tables directly.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(5)** read with **DPDP Rules, 2025, Rule 6(1)(a)**.
- **Statutory Mandate:** Rule 6(1)(a) requires Data Fiduciaries to employ state-of-the-art technical security measures, including cryptographic protection at rest for sensitive and high-risk personal identifiers (such as Aadhaar, PAN, financial accounts, and health markers).
- **Penalty Exposure:** Engages the **₹250 Crore Statutory Maximum Ceiling** under Section 33. Storing plaintext PII at rest is routinely categorized by the DPBI as systemic structural negligence because any single credential compromise immediately leads to a catastrophic, mass-scale personal data breach.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
If an attacker executes a SQL injection vulnerability, accesses an unencrypted database backup file stored in an S3 bucket, or compromises a database user password, all customer `customers.phone_number` records are dumped in plaintext. Because no application-level key is required to decrypt the column values, millions of Data Principal records can be exfiltrated instantaneously and dumped on dark web forums without detection until regulatory notification occurs.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```sql
Column: phone_number (VARCHAR(30))
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION (Using SQLAlchemy-Utils EncryptedType or KMS Wrapper)
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine
import os

ENCRYPTION_KEY = os.environ['DB_COLUMN_ENCRYPTION_KEY']

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    # Column encrypted using AES-GCM before writing to the database engine
    customers.phone_number = Column(EncryptedType(String(128), ENCRYPTION_KEY, AesEngine, 'pkcs5'))
```

#### 5. Engineering Verification & Automated Testing Plan
1. Generate a database migration wrapping `customers.phone_number` with an authenticated encryption type (AES-256-GCM).
2. Verify through a raw SQL client (`psql` / `mysql`) that `SELECT customers.phone_number FROM table;` returns ciphertext.
3. Run `cs01 audit .` to confirm that `SQL-DPDP-001` is resolved.


---

### `[FND-0004]` — `[Personal data sent to third-party SDK or external HTTP sink without verified consent guard]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `CODE-DPDP-002` · `cs01/v1:c1c5eb4183ae` |
| **Severity / Confidence / Priority** | **`HIGH`** · Confidence: `0.90` · Priority Score: `27 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §7 · **DPDP Rules, 2025:** Rule 3(2) |
| **Statutory Ceiling Band** | DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 1 · `tree-sitter` |
| **Evidence Location** | `examples/vulnerable_app/backend/api.py` (Line 11) |
| **Detected PII Categories** | `outbound_call:requests.post("http://partner.example.te` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```python
    10 |     logger.info("registration payload: %s", req.body)
>   11 |     requests.post("http://partner.example.test/ingest", json={"email": email})
    12 |     return {"email": email, "phone_number": phone_number}
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
Static code and AST analysis identified a statutory non-compliance pattern at `examples/vulnerable_app/backend/api.py:11`. Personal data sent to third-party SDK or external HTTP sink without verified consent guard. The code construct interacts with personal data `outbound_call:requests.post("http://partner.example.te` without implementing the mandatory technical controls required by the Digital Personal Data Protection Act, 2023. Specifically, personal identifiers are processed without adequate shielding, validation guards, or encryption safeguards.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section §7** read with **DPDP Rules, 2025, Rule 3(2)**.
- **Statutory Mandate:** Requires Data Fiduciaries to adhere to strict purpose limitation, data minimization, and technical safeguards. The processing of `outbound_call:requests.post("http://partner.example.te` without compliant statutory controls constitutes an actionable regulatory deficiency.
- **Penalty Exposure:** Falls under the statutory ceiling of **DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum)** under the Schedule to Section 33.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
If unshielded personal data `outbound_call:requests.post("http://partner.example.te` is exposed or misconfigured, unauthorized parties can access confidential records. This undermines the Data Fiduciary's compliance defense in the event of an external security audit or formal inquiry by the Data Protection Board of India.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```python
requests.post("http://partner.example.test/ingest", json={"email": email})
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION
# Implement mandatory DPDP safeguards before processing outbound_call:requests.post("http://partner.example.te
# Remediation requirement: Verify explicit user consent prior to dispatching personal data to external services.
```

#### 5. Engineering Verification & Automated Testing Plan
1. Apply remediation: Verify explicit user consent prior to dispatching personal data to external services.
2. Run `cs01 audit .` to confirm `CODE-DPDP-002` is resolved.


---

### `[FND-0005]` — `[Application stores personal data in schema, but no consent withdrawal or user erasure route exists]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `ARCH-DPDP-001` · `cs01/v1:87fd71e0ee75` |
| **Severity / Confidence / Priority** | **`HIGH`** · Confidence: `0.90` · Priority Score: `27 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §6(4) · **DPDP Rules, 2025:** Rule 3(c) |
| **Statutory Ceiling Band** | DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 1 · `inventory` |
| **Evidence Location** | `None` (Line 1) |
| **Detected PII Categories** | `repo_routes` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```text
Discovered PII tables: [customers], but 0 consent withdrawal or user erasure routes found.
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
The application repository stores and processes personal data across database models, but whole-repo architectural scanning failed to detect any API route or controller implementing **consent withdrawal or account erasure** (e.g. `POST /consent/withdraw`, `DELETE /user/account`, or `DELETE /api/v1/consents`). Under modern privacy engineering principles, the consent lifecycle requires that granting consent and revoking consent possess parity of ease. When an application provides signup or onboarding workflows without an automated mechanism for Data Principals to revoke consent, the system traps customer personal data indefinitely in violation of the statutory consent lifecycle.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 6(4)** read with **DPDP Rules, 2025, Rule 3(c)**.
- **Statutory Mandate:** Section 6(4) grants Data Principals the absolute right to withdraw consent at any time, stipulating that *the ease of such withdrawal shall be comparable to the ease with which consent was given*. Rule 3(c) mandates that Data Fiduciaries maintain accessible technical interfaces allowing immediate registration of consent withdrawal.
- **Penalty Exposure:** Subject to penalties under the Section 33 Schedule (up to **₹50 Crore** for violation of Section 6 conditions). Failure to allow withdrawal also directly leads to non-compliance complaints to the Data Protection Board of India under Section 13.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
A customer decides to stop using the application and seeks to delete their account and personal identifiers. Because no withdrawal route exists, their data remains in operational databases, marketing email queues, and third-party tracking sinks. If the customer files a grievance under Section 13 and the Data Fiduciary fails to resolve it within statutory timelines, the DPBI initiates an inquiry, where the absence of a programmatic withdrawal endpoint is cited as evidence of systemic statutory failure.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```text
Discovered PII tables: [customers], but 0 consent withdrawal or user erasure routes found.
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION (FastAPI Consent Withdrawal Endpoint)
@app.delete('/api/v1/consent/withdraw')
async def withdraw_consent(user_id: str, db: Session = Depends(get_db)):
    # 1. Update persistent consent status
    consent_record = db.query(Consent).filter_by(user_id=user_id).first()
    if consent_record:
        consent_record.status = 'WITHDRAWN'
        consent_record.withdrawn_at = datetime.utcnow()
    
    # 2. Trigger asynchronous data erasure routine under Section 12(3)
    await queue_erasure_job(user_id)
    return {'status': 'SUCCESS', 'message': 'Consent withdrawn and erasure scheduled.'}
```

#### 5. Engineering Verification & Automated Testing Plan
1. Implement `DELETE /api/v1/consent/withdraw` in your router.
2. Add automated test verifying status code 200 and database record update.
3. Run `cs01 audit .` to verify that architectural rule `ARCH-DPDP-001` passes.


---

### `[FND-0006]` — `[Personal data stored in schema, but no scheduled data purging/erasure routine detected]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `ARCH-DPDP-002` · `cs01/v1:31191dca66c5` |
| **Severity / Confidence / Priority** | **`HIGH`** · Confidence: `0.90` · Priority Score: `27 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §8(7) · **DPDP Rules, 2025:** Rule 8(2) |
| **Statutory Ceiling Band** | DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 1 · `inventory` |
| **Evidence Location** | `None` (Line 1) |
| **Detected PII Categories** | `background_jobs` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```text
PII tables persist data, but no automated retention cleanup routine detected across repository.
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
The application persistence schema defines personal data models (`background_jobs`), but static architecture analysis detected zero automated data retention purging jobs or scheduled background workers (`apscheduler`, `celery`, or cron). Under modern persistence architectures, personal data remains in production database tables indefinitely after the processing purpose has completed or the customer relationship has terminated. Without automated, time-bound purging routines, database tables accumulate dormant historical personal records, directly violating the statutory purpose completion mandate.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(7)** read with **DPDP Rules, 2025, Rule 8(2)**.
- **Statutory Mandate:** Section 8(7) requires a Data Fiduciary to erase personal data upon the Data Principal withdrawing consent or as soon as it is reasonable to assume that the specified purpose is no longer being served. Rule 8(2) mandates automated, verifiable data erasure schedules aligned with Third Schedule inactivity thresholds (3 years general inactivity / 1 year for financial and e-commerce records).
- **Penalty Exposure:** Falls under the **₹50 Crore Statutory Ceiling** for residual statutory non-compliance under Section 33.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
Retaining personal data beyond its operational lifecycle turns historical databases into high-value targets. If a database compromise occurs, the blast radius includes not only active users but millions of inactive accounts that should have been permanently deleted years prior, vastly multiplying the organizational liability and mandatory breach notifications under Section 8(6).

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```text
PII tables persist data, but no automated retention cleanup routine detected across repository.
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION (Automated Retention Purge Routine)
from datetime import datetime, timezone, timedelta

def purge_expired_retention_records(db_session, max_retention_days: int = 365) -> int:
    cutoff = datetime.now(timezone.utc) - timedelta(days=max_retention_days)
    deleted_count = db_session.query(User).filter(User.last_active < cutoff).delete()
    db_session.commit()
    return deleted_count
```

#### 5. Engineering Verification & Automated Testing Plan
1. Implement a scheduled retention job that purges inactive records after the retention threshold.
2. Add a test asserting that expired records are purged during routine execution.
3. Run `cs01 audit .` to confirm `ARCH-DPDP-002` passes.


---

### `[FND-0007]` — `[Personal data table schema missing verifiable consent ledger linkage reference]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `SQL-DPDP-005` · `cs01/v1:eb5b1c2c3b77` |
| **Severity / Confidence / Priority** | **`MEDIUM`** · Confidence: `0.90` · Priority Score: `16 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §6(1) · **DPDP Rules, 2025:** Rule 3(1) |
| **Statutory Ceiling Band** | DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 3 · `tree-sitter` |
| **Evidence Location** | `examples/vulnerable_app/db/schema.sql` (Line 1) |
| **Detected PII Categories** | `customers.consent_linkage` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```sql
>    1 | CREATE TABLE customers (
     2 |   id UUID PRIMARY KEY,
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
Static code and AST analysis identified a statutory non-compliance pattern at `examples/vulnerable_app/db/schema.sql:1`. Personal data table schema missing verifiable consent ledger linkage reference. The code construct interacts with personal data `customers.consent_linkage` without implementing the mandatory technical controls required by the Digital Personal Data Protection Act, 2023. Specifically, personal identifiers are processed without adequate shielding, validation guards, or encryption safeguards.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section §6(1)** read with **DPDP Rules, 2025, Rule 3(1)**.
- **Statutory Mandate:** Requires Data Fiduciaries to adhere to strict purpose limitation, data minimization, and technical safeguards. The processing of `customers.consent_linkage` without compliant statutory controls constitutes an actionable regulatory deficiency.
- **Penalty Exposure:** Falls under the statutory ceiling of **DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum)** under the Schedule to Section 33.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
If unshielded personal data `customers.consent_linkage` is exposed or misconfigured, unauthorized parties can access confidential records. This undermines the Data Fiduciary's compliance defense in the event of an external security audit or formal inquiry by the Data Protection Board of India.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```sql
Table 'customers' stores personal data but lacks verifiable consent ledger linkage reference
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION
# Implement mandatory DPDP safeguards before processing customers.consent_linkage
# Remediation requirement: Link personal data records to a consent ledger or consent token column (e.g. consent_id / consent_token).
```

#### 5. Engineering Verification & Automated Testing Plan
1. Apply remediation: Link personal data records to a consent ledger or consent token column (e.g. consent_id / consent_token).
2. Run `cs01 audit .` to confirm `SQL-DPDP-005` is resolved.


---

### `[FND-0008]` — `[Personal data table lacks documented retention period comment in schema]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `SQL-DPDP-002` · `cs01/v1:3ad97f1a7f2d` |
| **Severity / Confidence / Priority** | **`MEDIUM`** · Confidence: `0.90` · Priority Score: `16 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §8(7) · **DPDP Rules, 2025:** Rule 6(1)(e) |
| **Statutory Ceiling Band** | DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 3 · `tree-sitter` |
| **Evidence Location** | `examples/vulnerable_app/db/schema.sql` (Line 1) |
| **Detected PII Categories** | `customers.email` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```sql
>    1 | CREATE TABLE customers (
     2 |   id UUID PRIMARY KEY,
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
Static code and AST analysis identified a statutory non-compliance pattern at `examples/vulnerable_app/db/schema.sql:1`. Personal data table lacks documented retention period comment in schema. The code construct interacts with personal data `customers.email` without implementing the mandatory technical controls required by the Digital Personal Data Protection Act, 2023. Specifically, personal identifiers are processed without adequate shielding, validation guards, or encryption safeguards.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section §8(7)** read with **DPDP Rules, 2025, Rule 6(1)(e)**.
- **Statutory Mandate:** Requires Data Fiduciaries to adhere to strict purpose limitation, data minimization, and technical safeguards. The processing of `customers.email` without compliant statutory controls constitutes an actionable regulatory deficiency.
- **Penalty Exposure:** Falls under the statutory ceiling of **DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum)** under the Schedule to Section 33.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
If unshielded personal data `customers.email` is exposed or misconfigured, unauthorized parties can access confidential records. This undermines the Data Fiduciary's compliance defense in the event of an external security audit or formal inquiry by the Data Protection Board of India.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```sql
Table: customers, Column: email
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION
# Implement mandatory DPDP safeguards before processing customers.email
# Remediation requirement: Document the statutory retention period in table or column schema comments (e.g. COMMENT ON COLUMN ... 'retention 180 days').
```

#### 5. Engineering Verification & Automated Testing Plan
1. Apply remediation: Document the statutory retention period in table or column schema comments (e.g. COMMENT ON COLUMN ... 'retention 180 days').
2. Run `cs01 audit .` to confirm `SQL-DPDP-002` is resolved.


---

### `[FND-0009]` — `[Personal data table lacks documented retention period comment in schema]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `SQL-DPDP-002` · `cs01/v1:0808f1a27c08` |
| **Severity / Confidence / Priority** | **`MEDIUM`** · Confidence: `0.90` · Priority Score: `16 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §8(7) · **DPDP Rules, 2025:** Rule 6(1)(e) |
| **Statutory Ceiling Band** | DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 3 · `tree-sitter` |
| **Evidence Location** | `examples/vulnerable_app/db/schema.sql` (Line 1) |
| **Detected PII Categories** | `customers.phone_number` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```sql
>    1 | CREATE TABLE customers (
     2 |   id UUID PRIMARY KEY,
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
Static code and AST analysis identified a statutory non-compliance pattern at `examples/vulnerable_app/db/schema.sql:1`. Personal data table lacks documented retention period comment in schema. The code construct interacts with personal data `customers.phone_number` without implementing the mandatory technical controls required by the Digital Personal Data Protection Act, 2023. Specifically, personal identifiers are processed without adequate shielding, validation guards, or encryption safeguards.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section §8(7)** read with **DPDP Rules, 2025, Rule 6(1)(e)**.
- **Statutory Mandate:** Requires Data Fiduciaries to adhere to strict purpose limitation, data minimization, and technical safeguards. The processing of `customers.phone_number` without compliant statutory controls constitutes an actionable regulatory deficiency.
- **Penalty Exposure:** Falls under the statutory ceiling of **DPDP Act Residual (§33 Schedule) — Up to ₹50 Crore (Discretionary Maximum)** under the Schedule to Section 33.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
If unshielded personal data `customers.phone_number` is exposed or misconfigured, unauthorized parties can access confidential records. This undermines the Data Fiduciary's compliance defense in the event of an external security audit or formal inquiry by the Data Protection Board of India.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```sql
Table: customers, Column: phone_number
```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION
# Implement mandatory DPDP safeguards before processing customers.phone_number
# Remediation requirement: Document the statutory retention period in table or column schema comments (e.g. COMMENT ON COLUMN ... 'retention 180 days').
```

#### 5. Engineering Verification & Automated Testing Plan
1. Apply remediation: Document the statutory retention period in table or column schema comments (e.g. COMMENT ON COLUMN ... 'retention 180 days').
2. Run `cs01 audit .` to confirm `SQL-DPDP-002` is resolved.


---

### `[FND-0010]` — `[Personal data flows directly into an unguarded logger sink]`

| Field | Details |
|---|---|
| **Rule ID & Fingerprint** | `CODE-DPDP-001` · `cs01/v1:7160bf9035e2` |
| **Severity / Confidence / Priority** | **`CRITICAL`** · Confidence: `0.30` · Priority Score: `15 / 100` |
| **DPDP Statutory Mapping** | **DPDP Act, 2023:** Section §8(5) · **DPDP Rules, 2025:** Rule 6(1)(a) |
| **Statutory Ceiling Band** | DPDP Act §8(5) — Up to ₹250 Crore (Discretionary Maximum) |
| **CERT-In Cross-Mapping** | None |
| **Stack Layer & Analyzer** | Layer 1 · `tree-sitter` |
| **Evidence Location** | `tests/test_scanner.py` (Line 24) |
| **Detected PII Categories** | `function:test_collects_log_secret_and_transfer_without_secret_leak` |
| **Correlated Findings** | `None` |

**Evidence Snippet (Contextual Redacted Window):**
```python
    23 |             root = Path(td)
>   24 |             (root / "app.js").write_text(
    25 |                 "const email = req.body.email;\n"
```

#### 1. Detailed Technical Failure Analysis (Code Walkthrough)
The application flow directly introduces unmasked **function:test_collects_log_secret_and_transfer_without_secret_leak** into an application logger sink at `tests/test_scanner.py:24`. During intra-procedural execution, `function:test_collects_log_secret_and_transfer_without_secret_leak` is evaluated and passed as a direct argument into the logging framework (`logger.info` / `console.log`) without undergoing tokenization, cryptographic hashing (HMAC-SHA256), or masking. Because standard application logging subsystems stream structured strings to persistent log files and centralized log aggregators (such as AWS CloudWatch, Datadog, Elasticsearch, or disk files), the unmasked personal data leaves the bounded memory of the application and becomes permanently embedded in log streams. Perimeter defenses such as Web Application Firewalls (WAF) or database-level column encryption offer zero protection against this vulnerability, as the data is exfiltrated internally through standard application telemetry.

#### 2. Statutory & Regulatory Breach Analysis (DPDP Act, 2023 & DPDP Rules, 2025)
**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(5)** read with **DPDP Rules, 2025, Rule 6(1)(a)**.
- **Statutory Mandate:** Section 8(5) imposes an affirmative, non-delegable duty on every Data Fiduciary to protect personal data in its possession or under its control by taking reasonable security safeguards to prevent personal data breaches. Rule 6(1)(a) explicitly mandates technical safeguards including masking, de-identification, and strict access controls on all non-production and telemetry data streams.
- **Penalty Exposure:** Directly engages the **₹250 Crore Statutory Maximum Ceiling** under Item 1 of the Section 33 Schedule for failure to take reasonable security safeguards. Under Section 33(2), the Data Protection Board of India (DPBI) assesses penalties based on the nature, gravity, and duration of the violation, as well as whether unauthorized parties or broad engineering teams could access the logged telemetry.

#### 3. Real-World Threat Scenario & Data Principal Blast Radius
**Threat Scenario & Blast Radius:**
Log aggregators are routinely accessed by dozens of developers, QA engineers, automated monitoring bots, and third-party SaaS integrations. When unmasked `function:test_collects_log_secret_and_transfer_without_secret_leak` is written to logs, any insider with read access to log archives or any compromised developer laptop with CloudWatch/Kibana tokens can harvest bulk Indian national identity numbers. If combined with mobile numbers, an attacker can execute targeted SIM-swap attacks, unauthorized KYC lookups, or synthetic identity theft, creating acute financial and privacy harms for the affected Data Principals.

#### 4. Production-Ready Refactored Code Fix ("Before vs. After")
**Vulnerable Pattern (Before):**
```python
(root / "app.js").write_text(
                "const email = req.body.email;\n"

```

**Remediated Pattern (After):**
```python
# ✔ COMPLIANT REMEDIATION (Redaction helper applied before logging)
def mask_identifier(val: str) -> str:
    if not val or len(val) < 4:
        return '****'
    return 'X' * (len(val) - 4) + val[-4:]

# Log only non-sensitive correlation identifiers or masked tokens
logger.info('Processing transaction for user: %s (ID: %s)', user.id, mask_identifier(function:test_collects_log_secret_and_transfer_without_secret_leak))
```

#### 5. Engineering Verification & Automated Testing Plan
1. Replace `(root / "app.js").write_text(
                "const email = req.body.email;\n"` with the masked logging pattern.
2. Add a unit test asserting that `logger` calls do not receive raw digits.
3. Run `cs01 audit .` and verify that `[FND-CODE-DPDP-001]` is cleared.


---

## 6. Dynamic & Bonus Assessments *(Included When Modules Enabled)*

### 6.1 End-to-End Consent Flow Assessment (`Sec 5–6, Rule 3`)

| Consent Lifecycle Check | Status | Evidence / Trace |
|---|---|---|
| Standalone Notice Route Present (Independent of T&C) | `NOT DETECTED` | No dedicated standalone Rule 3 notice route found |
| Affirmative Non-Bundled Opt-In Controls | `AUDITED` | Audited across client form submissions |
| Persistent Consent Ledger (`user_id`, `purpose`, `timestamp`) | `FAIL` | Schema missing verifiable consent ledger linkage reference (§6(1)) |
| Comparable-Ease Withdrawal Endpoint | `FAIL` | 0 consent withdrawal or user erasure routes found (§6(4)) |
| Pre-Processing Enforcement Guard Verified | `FAIL` | Personal data dispatched to external sink without verified consent guard (§6(1)) |

### 6.2 Safe Read-Only Live API & Web Surface Probe (`Layer 5`)

*Not Executed — pass `--allow-live-probe` and `--allowed-hosts` to run live API verification.*

### 6.3 Generated Remediation Patches *(When Auto-Patch Enabled)*

| Finding ID | Target File | Patch Artifact | Verification Status |
|---|---|---|---|
| `FND-0001` | `examples/vulnerable_app/backend/api.py` | `remediation_patches/CODE-DPDP-001-api.py.patch` | Ready to Apply (`git apply`) |
| `FND-0002` | `examples/vulnerable_app/db/schema.sql` | `remediation_patches/SQL-DPDP-001-schema.sql.patch` | Ready to Apply (`git apply`) |
| `FND-0003` | `examples/vulnerable_app/db/schema.sql` | `remediation_patches/SQL-DPDP-001-schema.sql.patch` | Ready to Apply (`git apply`) |

---

## 7. Prioritized Remediation Roadmap

| Priority Window | Target SLA | Findings Included | Primary Owner | Expected Readiness Score Lift |
|---|---|---|---|---|
| **P0 — Immediate Breach Prevention** | `0–7 Days` | `[FND-0001, FND-0002, FND-0003, FND-0010]` *(Critical ₹250 Cr / ₹200 Cr)* | Backend + DevOps | `+27 pts` |
| **P1 — High-Risk Governance & Flows** | `7–30 Days` | `[FND-0004, FND-0005, FND-0006]` *(High logs, soft-delete, Shadow AI)* | Backend + Data Eng | `+10 pts` |
| **P2 — Pre-Enforcement Completeness** | `30–60 Days` | `[FND-0007, FND-0008, FND-0009]` *(Notice, 365d log TTL, DSRs)* | Frontend + Legal/DPO | `+3 pts` |

---

## 8. Audit Methodology, Suppressions & Appendix

### 8.1 Active Analyzers & Execution Performance

| Analyzer Module | Version / Engine | Targets / Records Evaluated | Unparseable / Skipped | Execution Time |
|---|---|---:|---:|---:|
| `TreeSitterAstAnalyzer` | `tree-sitter 0.23` | `20 files` | `0` | `0.12s` |
| `IndianPiiAnalyzer` | `CS-01 Deterministic Math v1.0` | `20 files` | `0` | `0.04s` |
| `SqlSchemaAnalyzer` | `sqlglot 20.x` | `Active Schemas` | `0` | `0.64s` |
| `IacConfigAnalyzer` | `python-hcl2 / ruamel.yaml` | `Active Configs` | `0` | `0.00s` |
| `LocalQwen25Coder` | `qwen2.5-coder:3b` | `Triage Queue` | `0` | `Local Endpoint` |

### 8.2 Baselined & Inline-Suppressed Findings Register

| Finding Fingerprint | Rule ID | Location | Suppression Source | Documented Justification | Approved By | Review Expiry |
|---|---|---|---|---|---|---|
| `None` | `None` | `None` | `None` | Zero suppressed findings | `N/A` | `N/A` |

### 8.3 Rule Catalog Executed

| Rule ID | Rule Name | Layer | DPDP / CERT-In Mapping | Result |
|---|---|---|---|---|
| `CODE-DPDP-001` | Personal data flows directly into an unguarded logger sink | Code | Sec §8(5) | `FAIL (2)` |
| `CODE-DPDP-002` | Personal data sent to third-party SDK or external HTTP sink without verified consent guard | Code | Sec §7 | `FAIL (1)` |
| `CODE-DPDP-003` | Hardcoded Indian identifier literal detected in source code | Code | Sec §8(5) | `PASS` |
| `SQL-DPDP-001` | Personal data column defined without column-level encryption marker in database schema | Schema | Sec §8(5) | `FAIL (2)` |
| `SQL-DPDP-002` | Personal data table lacks documented retention period comment in schema | Schema | Sec §8(7) | `FAIL (2)` |
| `IAC-DPDP-001` | Terraform database instance configured with storage_encrypted = false | IaC/Config | Sec §8(5) | `PASS` |
| `IAC-DPDP-002` | Cloud log group retention period configured below statutory 365-day requirement | IaC/Config | Sec §8(5) | `PASS` |
| `ENV-DPDP-001` | Insecure database SSL configuration (sslmode=disable or ssl=false) in environment configuration | IaC/Config | Sec §8(5) | `PASS` |
| `SQL-DPDP-003` | Soft-delete only table lacking hard purge policy per DPDP Section 12 erasure requirement | Schema | Sec §12(3) | `PASS` |
| `SQL-DPDP-004` | Log or audit table schema configured with retention period below CERT-In / DPDP 365-day threshold | Schema | Sec §8(5) | `PASS` |
| `SQL-DPDP-005` | Personal data table schema missing verifiable consent ledger linkage reference | Schema | Sec §6(1) | `FAIL (1)` |
| `IAC-DPDP-003` | Cloud storage bucket configured with public access enabled or missing public access block | IaC/Config | Sec §8(5) | `PASS` |
| `IAC-DPDP-004` | Container configured to run as root user or in privileged mode | IaC/Config | Sec §8(5) | `PASS` |
| `IAC-DPDP-005` | Cloud infrastructure deployed in non-compliant cross-border region without authorization | IaC/Config | Sec §16 | `PASS` |
| `IAC-DPDP-006` | Production database configured without automated backup retention policy | IaC/Config | Sec §8(5) | `PASS` |
| `IAC-DPDP-007` | Infrastructure or container missing CERT-In compliant NTP synchronization server | IaC/Config | Sec §8(5) | `PASS` |
| `CODE-DPDP-004` | Excessive personal data or credential field exposed in API response model or DTO | Code | Sec §8(5) | `PASS` |
| `CODE-DPDP-005` | Publicly mounted static framework directory exposes sensitive storage or backup directories | Code | Sec §8(5) | `PASS` |
| `CODE-DPDP-006` | Unvalidated file upload written to storage without extension or MIME allowlist verification | Code | Sec §8(5) | `PASS` |
| `CODE-DPDP-007` | Missing object-level authorization check (IDOR/BOLA) on resource identifier in route handler | Code | Sec §8(5) | `PASS` |
| `CODE-DPDP-008` | Broken function-level authorization: excessive role privileges permitted on sensitive domain endpoint | Code | Sec §8(5) | `PASS` |
| `ARCH-DPDP-001` | Application stores personal data in schema, but no consent withdrawal or user erasure route exists | Architecture | Sec §6(4) | `FAIL (1)` |
| `ARCH-DPDP-002` | Personal data stored in schema, but no scheduled data purging/erasure routine detected | Architecture | Sec §8(7) | `FAIL (1)` |
| `ARCH-DPDP-003` | Children age or date of birth stored in schema without a verifiable guardian age-gate in code | Architecture | Sec §9 | `PASS` |
| `ARCH-DPDP-004` | Outbound third-party data transmission detected to an unapproved processor | Architecture | Sec §8(2) | `PASS` |
| `ARCH-DPDP-005` | Security and audit telemetry model lacks mandatory non-null target resource identifier for breach blast-radius scoping | Architecture | Sec §8(6) | `PASS` |
| `ARCH-DPDP-006` | Personal data collected without dedicated API endpoints for Data Principal Rights (Access, Correction, Nomination) or 30-day Grievance SLA | Architecture | Sec §11, §12, §13, §14 | `PASS` |
| `ARCH-DPDP-007` | Application collects personal data but does not publish Data Protection Officer (DPO) or designated grievance contact details in India | Architecture | Sec §8(9) | `PASS` |
| `ARCH-DPDP-008` | Children's or minor data is processed with tracking SDKs, behavioral monitoring, or targeted advertising pipelines | Architecture | Sec §9(2), §9(3) | `PASS` |
| `ARCH-DPDP-009` | Significant Data Fiduciary (SDF) target lacks periodic data audit logging hooks, DPIA metadata, or algorithmic risk assessments | Architecture | Sec §10 | `PASS` |
| `ARCH-DPDP-010` | Outbound personal data egress or cloud storage targets jurisdictions not permitted under notified cross-border transfer rules | Architecture | Sec §16 | `PASS` |
| `ARCH-DPDP-011` | Organization profile commencement timeline configuration deviates from statutory phased enforcement schedule | Architecture | Sec §1(2) | `PASS` |
| `ARCH-DPDP-012` | User account model lacks explicit personal data boundary tagging between Data Fiduciary and third-party Data Processors | Architecture | Sec §2(j), §2(t) | `PASS` |
| `ARCH-DPDP-013` | Consent management lacks open interoperable API interface for registered Consent Managers under the First Schedule | Architecture | Sec §6(7) | `PASS` |
| `ARCH-DPDP-015` | Application lacks structured 72-hour personal data breach intimation and incident containment reporting mechanism | Architecture | Sec §8(6) | `PASS` |
| `ARCH-DPDP-016` | User inactivity threshold exceeds Third Schedule limits or lacks mandatory 48-hour pre-erasure notification routine | Architecture | Sec §8(7), §12(3) | `PASS` |
| `ARCH-DPDP-017` | Processing sensitive data of persons with disabilities without verified lawful guardian consent mechanism | Architecture | Sec §9(2) | `PASS` |
| `ARCH-DPDP-018` | Research, statistical, or archival data pipelines lack cryptographic de-identification and operational decision segregation | Architecture | Sec §17(2)(b) | `PASS` |
| `ARCH-DPDP-019` | Application audit trail records lack digital non-repudiation or cryptographic exportability for Board inspection | Architecture | Sec §27 | `PASS` |

### 8.4 Cryptographic Integrity Verification

Verify this report and its accompanying evidence pack offline before submitting to internal audit committees or Rule 13 independent data auditors:

```powershell
cs01 verify-evidence ./cs01-reports/cs01-evidence-bundle.zip
```
