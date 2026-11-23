"""
Stage 3 Personal Data Detector
==============================
Scans parsed RepoModel (AST string literals, schema columns, and config values)
against the Indian PII Taxonomy with mathematical validation and confidence scoring.
"""

from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from cs01.models import (
    RepoModel, PiiHitList, PiiHit, PiiType, FileRole, ScanConfig,
)
from cs01.utils import sha256_of
from .validators import (
    validate_aadhaar, validate_pan, validate_gstin, validate_upi_id,
    load_psp_handles, validate_mobile, validate_passport, validate_voter_id,
    validate_ifsc, validate_email, validate_ip_address,
)

PII_FIELD_NAME_PATTERNS: list[tuple[re.Pattern, PiiType]] = [
    (re.compile(r"(aadhaar|uidai|adhaar)", re.I), PiiType.AADHAAR),
    (re.compile(r"(pan_?no|pan_?num|pan_?card|permanent_acc)", re.I), PiiType.PAN),
    (re.compile(r"(gstin|gst_?num|gst_?no)", re.I), PiiType.GSTIN),
    (re.compile(r"(passport)", re.I), PiiType.PASSPORT),
    (re.compile(r"(voter_?id|epic_?no)", re.I), PiiType.VOTER_ID),
    (re.compile(r"(upi_?id|vpa)", re.I), PiiType.UPI_HANDLE),
    (re.compile(r"(ifsc|bank_ifsc)", re.I), PiiType.IFSC),
    (re.compile(r"(mobile|phone|contact_?no|cell_?no)", re.I), PiiType.MOBILE),
    (re.compile(r"(email|mail_?id|email_?addr)", re.I), PiiType.EMAIL),
    (re.compile(r"(ip_?addr|client_?ip)", re.I), PiiType.IP_ADDRESS),
    (re.compile(r"(lat.*long|latitude|longitude|coords|geolocation)", re.I), PiiType.GEOLOCATION),
    (re.compile(r"(device_?id|imei|mac_?addr|android_?id)", re.I), PiiType.DEVICE_ID),
    (re.compile(r"(date_?of_?birth|dob|birth_?date)", re.I), PiiType.DATE_OF_BIRTH),
    (re.compile(r"(biometric|fingerprint|retina|face_?scan)", re.I), PiiType.BIOMETRIC),
    (re.compile(r"(salary|bank_?acc|account_?no|credit_?card|debit_?card)", re.I), PiiType.FINANCIAL),
]

def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(p in normalized for p in ("/tests/", "/test/", "/spec/", "/__tests__/", "test_"))

def detect_pii(model: RepoModel, cfg: ScanConfig) -> PiiHitList:
    """Detect PII instances across all structured layers of the RepoModel."""
    hits: list[PiiHit] = []
    seen_hit_ids: set[str] = set()
    psp_handles = load_psp_handles(cfg.policy_profiles_dir)

    def _add_hit(
        pii_type: PiiType,
        file: str,
        line: int,
        col: int,
        val_str: str,
        confidence: float,
        result_desc: str,
        context_tokens: list[str] | None = None,
    ) -> None:
        hit_id = f"{pii_type.value}:{file}:{line}:{col}"
        if hit_id in seen_hit_ids:
            return
        seen_hit_ids.add(hit_id)

        is_test = _is_test_path(file)
        role = FileRole.TEST if is_test else FileRole.PRODUCTION
        
        final_conf = confidence
        if is_test and not cfg.strict_test_scanning:
            final_conf = min(0.30, confidence)

        hits.append(
            PiiHit(
                id=hit_id,
                pii_type=pii_type,
                file=file,
                line=line,
                col=col,
                confidence=final_conf,
                file_role=role,
                value_sha256=sha256_of(val_str),
                context_tokens=context_tokens or [],
                validator_result=result_desc,
            )
        )

    for ast_file in model.ast_index:
        for lit in ast_file.string_literals:
            val = lit["value"].strip()
            line = lit["line"]
            col = lit["col"]

            if re.match(r"^\d{4}\s?\d{4}\s?\d{4}$", val):
                is_valid, reason = validate_aadhaar(val)
                if is_valid:
                    _add_hit(PiiType.AADHAAR, ast_file.path, line, col, val, 0.95, "verhoeff_pass")
                    continue

            if len(val) == 10 and re.match(r"^[A-Za-z0-9]{10}$", val):
                is_valid, reason = validate_pan(val)
                if is_valid:
                    _add_hit(PiiType.PAN, ast_file.path, line, col, val, 0.90, reason)
                    continue

            if len(val) == 15:
                is_valid, reason = validate_gstin(val)
                if is_valid:
                    _add_hit(PiiType.GSTIN, ast_file.path, line, col, val, 0.95, "gstin_mod36_pass")
                    continue

            if "@" in val and len(val) <= 128:
                is_valid, reason = validate_upi_id(val, psp_handles)
                if is_valid:
                    _add_hit(PiiType.UPI_HANDLE, ast_file.path, line, col, val, 0.85, reason)
                    continue

            if re.match(r"^(?:\+91|91|0)?[6-9]\d{9}$", val.replace(" ", "").replace("-", "")):
                is_valid, reason = validate_mobile(val)
                if is_valid:
                    _add_hit(PiiType.MOBILE, ast_file.path, line, col, val, 0.80, "valid_indian_mobile")
                    continue

            if "@" in val and "." in val:
                is_valid, _ = validate_email(val)
                if is_valid:
                    _add_hit(PiiType.EMAIL, ast_file.path, line, col, val, 0.85, "valid_email")
                    continue

            if len(val) == 8:
                is_valid, _ = validate_passport(val)
                if is_valid:
                    _add_hit(PiiType.PASSPORT, ast_file.path, line, col, val, 0.80, "valid_passport")
                    continue

            if len(val) == 10:
                is_valid, _ = validate_voter_id(val)
                if is_valid:
                    _add_hit(PiiType.VOTER_ID, ast_file.path, line, col, val, 0.80, "valid_voter_id")
                    continue

            if len(val) == 11 and val[4] == "0":
                is_valid, _ = validate_ifsc(val)
                if is_valid:
                    _add_hit(PiiType.IFSC, ast_file.path, line, col, val, 0.85, "valid_ifsc")
                    continue

    for schema in model.schema_records:
        col_name = schema.column_or_field
        for pat, ptype in PII_FIELD_NAME_PATTERNS:
            if pat.search(col_name):
                _add_hit(
                    pii_type=ptype,
                    file=schema.source_file,
                    line=schema.line or 1,
                    col=1,
                    val_str=f"{schema.table_or_model}.{col_name}",
                    confidence=0.90,
                    result_desc="schema_column_match",
                    context_tokens=[schema.table_or_model, col_name, schema.data_type],
                )
                break

    for ev in model.env_vars:
        for pat, ptype in PII_FIELD_NAME_PATTERNS:
            if pat.search(ev.key):
                _add_hit(
                    pii_type=ptype,
                    file=ev.source_file,
                    line=ev.line,
                    col=1,
                    val_str=ev.key,
                    confidence=0.85,
                    result_desc="env_key_match",
                    context_tokens=[ev.key],
                )
                break

    return PiiHitList(hits=hits)
