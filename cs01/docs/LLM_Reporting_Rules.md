# CS-01: LLM Report Generation Rules & Standards

To ensure that AI-generated DPDP compliance reports produced by **Qwen 2.5 Coder** (or any local LLM) are legally precise, actionable for engineers, and accessible for executives, the reporting engine enforces the following **10 Core Rules**.

---

## 1. Mandatory Exact Code Quoting & File Attribution
- **Rule:** Never describe a vulnerability or bug abstractly. Always quote the exact file path, line number, and offending code snippet.
- **Example:**
  ```markdown
  **Location:** `src/main.py:12`
  **Vulnerable Code:**
  ```python
  logger.info(f"User registration received: {payload.aadhaar}")
  ```
  ```

---

## 2. "Mechanics of Failure" (Explain How & Why the Code Fails)
- **Rule:** Explain *what* the code does step-by-step and *why* it violates data protection.
- **Explanation Standard:**
  > "Line 12 receives `payload.aadhaar` from the incoming HTTP request and passes it directly to `logger.info()`. Because application logs are routed in plaintext to disk and centralized logging (Elasticsearch/CloudWatch), raw 12-digit Aadhaar numbers are persisted in unencrypted log indexes without access controls or masking."

---

## 3. Grounding in India's DPDP Act, 2023 & DPDP Rules, 2025
- **Rule:** Every finding must cite the exact statutory section and the statutory maximum penalty ceiling:
  - **§8(5)**: Reasonable security safeguards (Ceiling: Up to ₹250 Crore).
  - **§8(6)**: Personal data breach notification (Ceiling: Up to ₹200 Crore).
  - **§9**: Protection of children's personal data & PwD (Ceiling: Up to ₹200 Crore).
  - **§10**: Significant Data Fiduciary (SDF) obligations (Ceiling: Up to ₹150 Crore).
  - **§6 & Rule 3**: Notice and consent requirements (Residual ceiling: Up to ₹50 Crore).
  - **Rule 6(1)(e) & Rule 8**: Automated data retention and erasure routines.

---

## 4. "Before vs. After" Production-Ready Refactored Code Fix
- **Rule:** Never just say *"sanitize this"* or *"encrypt this"*. Always provide drop-in replacement code that compiles and solves the statutory deficiency.
- **Example:**
  ```python
  # ❌ BEFORE (Vulnerable to §8(5) - ₹250 Cr Ceiling):
  logger.info(f"Processing user: {user.aadhaar_number}")

  # ✔ AFTER (DPDP-Compliant with Redaction):
  def mask_aadhaar(aadhaar: str) -> str:
      return "XXXX-XXXX-" + aadhaar[-4:] if len(aadhaar) >= 4 else "XXXX"

  logger.info(f"Processing user: {mask_aadhaar(user.aadhaar_number)}")
  ```

---

## 5. Two-Tier Audience Framing (Executive Brief + Developer Action)
- **Rule:** Every finding must be structured to serve two distinct stakeholders:
  1. **Executive Impact (For DPO / Board / Legal):** 2–3 plain-English sentences detailing business liability, regulatory risk, and potential DPBI enforcement impact.
  2. **Technical Root Cause & Fix (For Software Engineers):** Exact AST nodes, ORM models, Terraform flags, and refactored code.

---

## 6. Zero Hallucination & Redaction Integrity
- **Rule:** The LLM must strictly restrict its analysis to the findings provided in `stage5_bundle.json`.
- **Integrity Guarantee:** Never invent non-existent files or mock real identities. Any redacted placeholder (`[AADHAAR_1]`, `[PAN_1]`) must remain redacted in the report.

---

## 7. Concrete Verification Steps
- **Rule:** Every remediation recommendation must conclude with an exact verification step telling the developer how to confirm that the vulnerability has been resolved.
- **Example:**
  > "Verification: Run `cs01 audit .` or run your test suite to confirm that `CODE-DPDP-001` no longer triggers on `src/main.py`."

---

## 8. Blast Radius & Data Principal Impact Assessment
- **Rule:** Explain what real-world harm could occur if the vulnerability is exploited.
- **Examples:**
  - *Leaked Aadhaar/PAN:* Identity theft, unauthorized SIM activation, financial profiling.
  - *Missing consent withdrawal:* Data Principal unable to revoke processing under §6(4), triggering regulatory complaints to the Data Protection Board of India (DPBI).

---

## 9. Clear Distinction Between Active Leaks vs. Architectural Gaps
- **Rule:** Clearly categorize findings into:
  - **Active Exposure (P0 / Critical):** Plaintext PII flowing to loggers, console, or third-party APIs.
  - **Storage Insecurity (P1 / High):** Missing column encryption or unencrypted database disks (`storage_encrypted = false`).
  - **Architectural Gaps (P1 / High):** Absence of `/consent/withdraw` route or retention purge routines.
  - **Hygiene & Defense-in-Depth (P2 / Medium):** Incomplete security headers or log retention < 365 days.

---

## 10. Mandatory Statutory Disclaimer
- **Rule:** Every generated document must state that penalties are discretionary statutory ceilings determined by the DPBI under §33(2) after formal inquiry, and CS-01 is an automated technical auditing instrument, not formal legal counsel.
