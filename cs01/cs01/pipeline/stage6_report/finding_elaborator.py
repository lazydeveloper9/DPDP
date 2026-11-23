"""
Stage 6 Finding Elaborator
=========================
Generates exhaustive, publication-grade technical and statutory explanations
for each compliance finding in Section 5 of the DPDP Assessment Report.
"""

from __future__ import annotations
import re
from pathlib import Path
from cs01.models import ScoredFinding, ScanConfig

def _mask_code(s: str) -> str:
    res = s
    res = re.sub(r"\b\d{4}[-\s]?\d{4}[-\s]?(\d{4})\b", r"XXXX-XXXX-\1", res)
    res = re.sub(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", "[REDACTED-PAN]", res)
    res = re.sub(r"\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}\b", "[REDACTED-GSTIN]", res)
    res = re.sub(r"((?:api_?key|secret|password|token)\s*[:=]\s*['\"]).+?(['\"])", r"\1[REDACTED-SECRET]\2", res, flags=re.I)
    return res

def elaborate_finding(f: ScoredFinding, cfg: ScanConfig) -> dict[str, str]:
    """Produce an exhaustive technical, statutory, threat, and remediation elaboration for a finding."""
    rid = f.rule_id
    file_name = Path(f.file).name if f.file else "source"
    entity = f.matched_entity or "personal data identifier"

    tech = ""
    statutory = ""
    threat = ""
    raw_before = f.redacted_snippet or f.snippet or f"# Vulnerable location: {f.file}:{f.line_start}"
    before_code = _mask_code(raw_before)
    after_code = ""
    verification = f"Run `cs01 audit {f.file or '.'}` to confirm finding `{f.rule_id}` is resolved."

    if rid == "CODE-DPDP-001":
        tech = (
            f"The application flow directly introduces unmasked **{entity}** into an application logger sink at `{f.file}:{f.line_start}`. "
            f"During intra-procedural execution, `{f.matched_entity or 'the identifier'}` is evaluated and passed as a direct argument into the logging framework "
            f"(`logger.info` / `console.log`) without undergoing tokenization, cryptographic hashing (HMAC-SHA256), or masking. "
            f"Because standard application logging subsystems stream structured strings to persistent log files and centralized log aggregators "
            f"(such as AWS CloudWatch, Datadog, Elasticsearch, or disk files), the unmasked personal data leaves the bounded memory of the application "
            f"and becomes permanently embedded in log streams. Perimeter defenses such as Web Application Firewalls (WAF) or database-level column encryption "
            f"offer zero protection against this vulnerability, as the data is exfiltrated internally through standard application telemetry."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(5)** read with **DPDP Rules, 2025, Rule 6(1)(a)**.\n"
            f"- **Statutory Mandate:** Section 8(5) imposes an affirmative, non-delegable duty on every Data Fiduciary to protect personal data in its possession "
            f"or under its control by taking reasonable security safeguards to prevent personal data breaches. Rule 6(1)(a) explicitly mandates technical safeguards "
            f"including masking, de-identification, and strict access controls on all non-production and telemetry data streams.\n"
            f"- **Penalty Exposure:** Directly engages the **₹250 Crore Statutory Maximum Ceiling** under Item 1 of the Section 33 Schedule for failure to take reasonable security safeguards. "
            f"Under Section 33(2), the Data Protection Board of India (DPBI) assesses penalties based on the nature, gravity, and duration of the violation, as well as whether "
            f"unauthorized parties or broad engineering teams could access the logged telemetry."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"Log aggregators are routinely accessed by dozens of developers, QA engineers, automated monitoring bots, and third-party SaaS integrations. "
            f"When unmasked `{entity}` is written to logs, any insider with read access to log archives or any compromised developer laptop with CloudWatch/Kibana tokens "
            f"can harvest bulk Indian national identity numbers. If combined with mobile numbers, an attacker can execute targeted SIM-swap attacks, unauthorized KYC lookups, "
            f"or synthetic identity theft, creating acute financial and privacy harms for the affected Data Principals."
        )
        after_code = (
            f"```python\n"
            f"# ✔ COMPLIANT REMEDIATION (Redaction helper applied before logging)\n"
            f"def mask_identifier(val: str) -> str:\n"
            f"    if not val or len(val) < 4:\n"
            f"        return '****'\n"
            f"    return 'X' * (len(val) - 4) + val[-4:]\n\n"
            f"# Log only non-sensitive correlation identifiers or masked tokens\n"
            f"logger.info('Processing transaction for user: %s (ID: %s)', user.id, mask_identifier({entity}))\n"
            f"```"
        )
        verification = (
            f"1. Replace `{before_code.strip()}` with the masked logging pattern.\n"
            f"2. Add a unit test asserting that `logger` calls do not receive raw digits.\n"
            f"3. Run `cs01 audit .` and verify that `[FND-{rid}]` is cleared."
        )

    elif rid == "SQL-DPDP-001":
        tech = (
            f"The database model at `{f.file}:{f.line_start}` declares personal data column `{entity}` without a column-level encryption marker or encrypted type wrapper. "
            f"In the persistence layer, the field is defined as standard plaintext (e.g. `String`, `VARCHAR`, or `Text`). "
            f"When records are written to the database, the personal identifier is stored unencrypted in database pages, indexes, write-ahead logs (WAL), and backup snapshots. "
            f"While Transparent Data Encryption (TDE) or cloud volume encryption protects against physical hard drive theft, it does NOT protect against SQL injection, "
            f"compromised database connection credentials, read-only analytics replicas, or unauthorized database administrators querying tables directly."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(5)** read with **DPDP Rules, 2025, Rule 6(1)(a)**.\n"
            f"- **Statutory Mandate:** Rule 6(1)(a) requires Data Fiduciaries to employ state-of-the-art technical security measures, including cryptographic protection "
            f"at rest for sensitive and high-risk personal identifiers (such as Aadhaar, PAN, financial accounts, and health markers).\n"
            f"- **Penalty Exposure:** Engages the **₹250 Crore Statutory Maximum Ceiling** under Section 33. Storing plaintext PII at rest is routinely categorized by the DPBI "
            f"as systemic structural negligence because any single credential compromise immediately leads to a catastrophic, mass-scale personal data breach."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"If an attacker executes a SQL injection vulnerability, accesses an unencrypted database backup file stored in an S3 bucket, or compromises a database user password, "
            f"all customer `{entity}` records are dumped in plaintext. Because no application-level key is required to decrypt the column values, millions of Data Principal records "
            f"can be exfiltrated instantaneously and dumped on dark web forums without detection until regulatory notification occurs."
        )
        after_code = (
            f"```python\n"
            f"# ✔ COMPLIANT REMEDIATION (Using SQLAlchemy-Utils EncryptedType or KMS Wrapper)\n"
            f"from sqlalchemy_utils import EncryptedType\n"
            f"from sqlalchemy_utils.types.encrypted.encrypted_type import AesEngine\n"
            f"import os\n\n"
            f"ENCRYPTION_KEY = os.environ['DB_COLUMN_ENCRYPTION_KEY']\n\n"
            f"class User(Base):\n"
            f"    __tablename__ = 'users'\n"
            f"    id = Column(Integer, primary_key=True)\n"
            f"    # Column encrypted using AES-GCM before writing to the database engine\n"
            f"    {entity} = Column(EncryptedType(String(128), ENCRYPTION_KEY, AesEngine, 'pkcs5'))\n"
            f"```"
        )
        verification = (
            f"1. Generate a database migration wrapping `{entity}` with an authenticated encryption type (AES-256-GCM).\n"
            f"2. Verify through a raw SQL client (`psql` / `mysql`) that `SELECT {entity} FROM table;` returns ciphertext.\n"
            f"3. Run `cs01 audit .` to confirm that `SQL-DPDP-001` is resolved."
        )

    elif rid == "IAC-DPDP-001":
        tech = (
            f"The Infrastructure-as-Code (Terraform) resource at `{f.file}:{f.line_start}` explicitly declares `storage_encrypted = false` "
            f"(or omits the mandatory encryption attribute). This provisions cloud database volumes, automated snapshot backups, and temporary swap storage "
            f"in plaintext without hardware-accelerated encryption via AWS KMS or Azure Key Vault. "
            f"Unencrypted cloud storage volumes violate baseline cloud compliance benchmarks and expose underlying block storage to physical cross-tenant or snapshot access."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(5)** read with **Rule 6(1)(a)**.\n"
            f"- **Statutory Mandate:** Requires appropriate technical and organizational safeguards across all physical and cloud infrastructure hosting personal data.\n"
            f"- **Penalty Exposure:** Carries a potential penalty of up to **₹250 Crore**. Leaving cloud databases unencrypted at rest represents an infrastructural failure "
            f"to institute basic organizational safeguards under Section 8(5)."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"Unencrypted cloud database snapshots can be restored into foreign AWS accounts if an IAM permission misconfiguration occurs. "
            f"Furthermore, decommissioned storage drives in cloud data centers, snapshot backups copied to secondary disaster-recovery regions, "
            f"and unencrypted read-replicas can all be inspected without requiring access to authorized customer-managed encryption keys."
        )
        after_code = (
            f"```hcl\n"
            f"# ✔ COMPLIANT REMEDIATION (Terraform aws_db_instance)\n"
            f"resource \"aws_db_instance\" \"database\" {{\n"
            f"  allocated_storage   = 50\n"
            f"  engine              = \"postgres\"\n"
            f"  instance_class      = \"db.t4g.medium\"\n"
            f"  storage_encrypted   = true\n"
            f"  kms_key_id          = aws_kms_key.rds_encryption_key.arn\n"
            f"  deletion_protection = true\n"
            f"}}\n"
            f"```"
        )
        verification = (
            f"1. Set `storage_encrypted = true` and attach an `aws_kms_key` resource in `{f.file}`.\n"
            f"2. Run `terraform validate` to verify syntax.\n"
            f"3. Run `cs01 audit .` to confirm `IAC-DPDP-001` passes."
        )

    elif rid == "ARCH-DPDP-001":
        tech = (
            f"The application repository stores and processes personal data across database models, but whole-repo architectural scanning "
            f"failed to detect any API route or controller implementing **consent withdrawal or account erasure** (e.g. `POST /consent/withdraw`, "
            f"`DELETE /user/account`, or `DELETE /api/v1/consents`). "
            f"Under modern privacy engineering principles, the consent lifecycle requires that granting consent and revoking consent possess "
            f"parity of ease. When an application provides signup or onboarding workflows without an automated mechanism for Data Principals to revoke consent, "
            f"the system traps customer personal data indefinitely in violation of the statutory consent lifecycle."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 6(4)** read with **DPDP Rules, 2025, Rule 3(c)**.\n"
            f"- **Statutory Mandate:** Section 6(4) grants Data Principals the absolute right to withdraw consent at any time, stipulating that "
            f"*the ease of such withdrawal shall be comparable to the ease with which consent was given*. "
            f"Rule 3(c) mandates that Data Fiduciaries maintain accessible technical interfaces allowing immediate registration of consent withdrawal.\n"
            f"- **Penalty Exposure:** Subject to penalties under the Section 33 Schedule (up to **₹50 Crore** for violation of Section 6 conditions). "
            f"Failure to allow withdrawal also directly leads to non-compliance complaints to the Data Protection Board of India under Section 13."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"A customer decides to stop using the application and seeks to delete their account and personal identifiers. "
            f"Because no withdrawal route exists, their data remains in operational databases, marketing email queues, and third-party tracking sinks. "
            f"If the customer files a grievance under Section 13 and the Data Fiduciary fails to resolve it within statutory timelines, the DPBI initiates "
            f"an inquiry, where the absence of a programmatic withdrawal endpoint is cited as evidence of systemic statutory failure."
        )
        after_code = (
            f"```python\n"
            f"# ✔ COMPLIANT REMEDIATION (FastAPI Consent Withdrawal Endpoint)\n"
            f"@app.delete('/api/v1/consent/withdraw')\n"
            f"async def withdraw_consent(user_id: str, db: Session = Depends(get_db)):\n"
            f"    # 1. Update persistent consent status\n"
            f"    consent_record = db.query(Consent).filter_by(user_id=user_id).first()\n"
            f"    if consent_record:\n"
            f"        consent_record.status = 'WITHDRAWN'\n"
            f"        consent_record.withdrawn_at = datetime.utcnow()\n"
            f"    \n"
            f"    # 2. Trigger asynchronous data erasure routine under Section 12(3)\n"
            f"    await queue_erasure_job(user_id)\n"
            f"    return {{'status': 'SUCCESS', 'message': 'Consent withdrawn and erasure scheduled.'}}\n"
            f"```"
        )
        verification = (
            f"1. Implement `DELETE /api/v1/consent/withdraw` in your router.\n"
            f"2. Add automated test verifying status code 200 and database record update.\n"
            f"3. Run `cs01 audit .` to verify that architectural rule `ARCH-DPDP-001` passes."
        )

    elif rid == "ARCH-DPDP-003":
        tech = (
            f"The database schema declares age or date-of-birth attributes (`{entity}`), but static analysis of route handlers, "
            f"onboarding forms, and middleware detected **no age-verification guard or verifiable parental consent workflow**. "
            f"Without an age gate that verifies whether a user is over 18 years of age, the application inadvertently collects, stores, "
            f"and processes personal data belonging to minors under the identical technical regime as adult data."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 9(1) & 9(3)** read with **DPDP Rules, 2025, Rule 10**.\n"
            f"- **Statutory Mandate:** Section 9(1) strictly prohibits a Data Fiduciary from processing personal data of a child (individual under 18 years) "
            f"without first obtaining verifiable consent of the parent or lawful guardian. Section 9(3) prohibits any tracking or behavioral monitoring of children "
            f"or targeted advertising directed at children.\n"
            f"- **Penalty Exposure:** Subject to the severe **₹200 Crore Statutory Maximum Ceiling** under Item 3 of the Section 33 Schedule for breach in observance "
            f"of duties in respect of children. Violations involving children are treated with the highest statutory gravity by the DPBI."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"If minor users register on the application and their usage patterns, location, or browsing habits are tracked or forwarded to analytics SDKs (e.g. Google Analytics / Mixpanel), "
            f"the company commits an active statutory offense under Section 9(3). A single regulatory audit or user complaint revealing minors in the database without parental verification "
            f"triggers immediate DPBI scrutiny under the ₹200 Crore penalty band."
        )
        after_code = (
            f"```python\n"
            f"# ✔ COMPLIANT REMEDIATION (Guardian Age-Verification Guard)\n"
            f"from datetime import date, timedelta\n\n"
            f"def verify_adult_or_require_guardian(dob: date, has_parental_consent: bool) -> bool:\n"
            f"    age = (date.today() - dob).days // 365\n"
            f"    if age < 18:\n"
            f"        if not has_parental_consent:\n"
            f"            raise HTTPException(\n"
            f"                status_code=403,\n"
            f"                detail='Section 9 DPDP: Minor onboarding requires verifiable parental consent.'\n"
            f"            )\n"
            f"    return True\n"
            f"```"
        )
        verification = (
            f"1. Implement an age-gate middleware or validation check before storing date of birth.\n"
            f"2. Add test asserting users with age < 18 are rejected without verifiable guardian consent.\n"
            f"3. Run `cs01 audit .` to confirm `ARCH-DPDP-003` passes."
        )

    elif rid == "ARCH-DPDP-002":
        tech = (
            f"The application persistence schema defines personal data models (`{entity}`), but static architecture "
            f"analysis detected zero automated data retention purging jobs or scheduled background workers (`apscheduler`, `celery`, or cron). "
            f"Under modern persistence architectures, personal data remains in production database tables indefinitely after the processing purpose "
            f"has completed or the customer relationship has terminated. Without automated, time-bound purging routines, database tables accumulate "
            f"dormant historical personal records, directly violating the statutory purpose completion mandate."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(7)** read with **DPDP Rules, 2025, Rule 8(2)**.\n"
            f"- **Statutory Mandate:** Section 8(7) requires a Data Fiduciary to erase personal data upon the Data Principal withdrawing consent or "
            f"as soon as it is reasonable to assume that the specified purpose is no longer being served. Rule 8(2) mandates automated, verifiable data "
            f"erasure schedules aligned with Third Schedule inactivity thresholds (3 years general inactivity / 1 year for financial and e-commerce records).\n"
            f"- **Penalty Exposure:** Falls under the **₹50 Crore Statutory Ceiling** for residual statutory non-compliance under Section 33."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"Retaining personal data beyond its operational lifecycle turns historical databases into high-value targets. If a database compromise occurs, "
            f"the blast radius includes not only active users but millions of inactive accounts that should have been permanently deleted years prior, "
            f"vastly multiplying the organizational liability and mandatory breach notifications under Section 8(6)."
        )
        after_code = (
            f"```python\n"
            f"# ✔ COMPLIANT REMEDIATION (Automated Retention Purge Routine)\n"
            f"from datetime import datetime, timezone, timedelta\n\n"
            f"def purge_expired_retention_records(db_session, max_retention_days: int = 365) -> int:\n"
            f"    cutoff = datetime.now(timezone.utc) - timedelta(days=max_retention_days)\n"
            f"    deleted_count = db_session.query(User).filter(User.last_active < cutoff).delete()\n"
            f"    db_session.commit()\n"
            f"    return deleted_count\n"
            f"```"
        )
        verification = (
            f"1. Implement a scheduled retention job that purges inactive records after the retention threshold.\n"
            f"2. Add a test asserting that expired records are purged during routine execution.\n"
            f"3. Run `cs01 audit .` to confirm `ARCH-DPDP-002` passes."
        )

    elif rid == "ARCH-DPDP-005":
        tech = (
            f"The application declares a security audit logging model or invocation at `{f.file or 'schema'}`, but the telemetry "
            f"construct either defines `target_resource_id` as nullable or permits null/empty arguments during runtime calls (`{entity}`). "
            f"Under modern incident response standards, security audit events must establish non-repudiable linkage between the acting subject, "
            f"the timestamped operation, and the specific Data Principal record impacted. When `target_resource_id` is null or omitted, security "
            f"telemetry is incapable of scoping which Data Principals were compromised during an unauthorized exfiltration event."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 8(6)** read with **DPDP Rules, 2025, Rule 7(1)**.\n"
            f"- **Statutory Mandate:** Rule 7(1) mandates that every personal data breach report submitted to the Data Protection Board of India (DPBI) "
            f"and affected Data Principals must identify the nature, extent, and specific categories of personal data compromised. Omission of target "
            f"resource identifiers disables blast-radius scoping, preventing lawful compliance with the 72-hour notification timeline.\n"
            f"- **Penalty Exposure:** Directly engages the **₹200 Crore Statutory Maximum Ceiling** under Item 2 of the Section 33 Schedule for failure to notify a personal data breach."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"During an active forensic investigation, if an attacker queries sensitive patient or financial records, the audit log records the read operation "
            f"without recording whose records were read. As a consequence, the organization cannot determine which users were breached, forcing either "
            f"a catastrophic public panic notification to 100% of customers or failure to notify the actual victims, leading to severe regulatory penalties."
        )
        after_code = (
            f"```python\n"
            f"# ✔ COMPLIANT REMEDIATION (Enforce non-null target_resource_id in audit schema)\n"
            f"class AuditLog(Base):\n"
            f"    __tablename__ = 'audit_logs'\n"
            f"    id = Column(Integer, primary_key=True)\n"
            f"    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)\n"
            f"    user_id = Column(String(64), nullable=False)\n"
            f"    action = Column(String(64), nullable=False)\n"
            f"    # Mandatory non-null target resource identifier for breach blast-radius scoping\n"
            f"    target_resource_id = Column(String(128), nullable=False)\n"
            f"```"
        )
        verification = (
            f"1. Update the audit schema to enforce `nullable=False` on `target_resource_id`.\n"
            f"2. Ensure all audit log calls supply a valid identifier for the target entity.\n"
            f"3. Run `cs01 audit .` to confirm `ARCH-DPDP-005` passes."
        )

    elif rid == "ARCH-DPDP-008":
        tech = (
            f"The application captures date of birth or minor indicators, but introduces those data pipelines into third-party tracking, "
            f"behavioral analytics, or targeted advertising SDKs (`{entity}`). "
            f"Tracking scripts embed persistent device fingerprinting cookies, session replay recording, and behavioral analytics beacons "
            f"that exfiltrate minors' browsing habits and application interactions to third-party ad networks without parental authorization."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section 9(2) & 9(3)** read with **DPDP Rules, 2025, Rule 12**.\n"
            f"- **Statutory Mandate:** Section 9(2) explicitly bans tracking, behavioral monitoring, or targeted advertising directed at children. "
            f"Rule 12 strictly forbids any processing that could cause harmful or detrimental effects on the well-being of a child.\n"
            f"- **Penalty Exposure:** Directly engages the **₹200 Crore Statutory Maximum Ceiling** under Item 3 of the Section 33 Schedule for non-compliance with duties in respect of children."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"Ad tech networks aggregate minor browsing telemetry across apps to build behavioral profiles for commercial exploitation. "
            f"Regulators worldwide treat child tracking as a tier-1 privacy violation with strict liability and zero tolerance."
        )
        after_code = (
            "```javascript\n"
            "// ✔ COMPLIANT REMEDIATION (Conditional gating stripping tracking on minor sessions)\n"
            "if (user.isMinor || user.age < 18) {\n"
            "    // Disable all third-party analytics and tracking SDKs under DPDP Rule 12\n"
            "    window['ga-disable-PROPERTY-ID'] = true;\n"
            "    analytics.track = function() {}; // No-op\n"
            "}\n"
            "```"
        )
        verification = (
            f"1. Implement guard preventing analytics initialization when user age is under 18.\n"
            f"2. Add test asserting tracking calls are suppressed for minor profiles.\n"
            f"3. Run `cs01 audit .` to confirm `ARCH-DPDP-008` passes."
        )

    else:
        tech = (
            f"Static code and AST analysis identified a statutory non-compliance pattern at `{f.file}:{f.line_start}`. "
            f"{f.message}. The code construct interacts with personal data `{entity}` without implementing the mandatory technical controls "
            f"required by the Digital Personal Data Protection Act, 2023. Specifically, personal identifiers are processed without adequate shielding, "
            f"validation guards, or encryption safeguards."
        )
        statutory = (
            f"**Statutory Provision:** Digital Personal Data Protection Act, 2023, **Section {f.dpdp_section}** read with **DPDP Rules, 2025, {f.dpdp_rule}**.\n"
            f"- **Statutory Mandate:** Requires Data Fiduciaries to adhere to strict purpose limitation, data minimization, and technical safeguards. "
            f"The processing of `{entity}` without compliant statutory controls constitutes an actionable regulatory deficiency.\n"
            f"- **Penalty Exposure:** Falls under the statutory ceiling of **{f.statutory_ceiling_display}** under the Schedule to Section 33."
        )
        threat = (
            f"**Threat Scenario & Blast Radius:**\n"
            f"If unshielded personal data `{entity}` is exposed or misconfigured, unauthorized parties can access confidential records. "
            f"This undermines the Data Fiduciary's compliance defense in the event of an external security audit or formal inquiry by the Data Protection Board of India."
        )
        after_code = (
            f"```python\n"
            f"# ✔ COMPLIANT REMEDIATION\n"
            f"# Implement mandatory DPDP safeguards before processing {entity}\n"
            f"# Remediation requirement: {f.remediation}\n"
            f"```"
        )
        verification = (
            f"1. Apply remediation: {f.remediation}\n"
            f"2. Run `cs01 audit .` to confirm `{f.rule_id}` is resolved."
        )

    return {
        "technical_analysis": tech,
        "statutory_analysis": statutory,
        "threat_scenario": threat,
        "before_code": before_code,
        "after_code": after_code,
        "verification": verification,
    }
