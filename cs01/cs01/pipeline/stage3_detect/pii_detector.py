"""
Stage 3 Personal Data Detector
==============================
Scans parsed RepoModel (AST string literals, schema columns, and config values)
against the Indian PII Taxonomy with mathematical validation and confidence scoring.
Includes lexical context gating (±5 token window) and file-role confidence adjustments.
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
    validate_driving_licence, validate_abha, validate_payment_card,
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
    (re.compile(r"(driving_?licen[cs]e|dl_?no|dl_?num)", re.I), PiiType.DRIVING_LICENCE),
    (re.compile(r"(abha|health_?id|ndhm)", re.I), PiiType.ABHA_HEALTH_ID),
    (re.compile(r"(card_?no|card_?number|credit_?card|debit_?card)", re.I), PiiType.PAYMENT_CARD),
]

CONTEXT_KEYWORDS: dict[PiiType, set[str]] = {
    PiiType.AADHAAR: {"aadhaar", "uidai", "adhaar", "uid", "resident_id"},
    PiiType.PAN: {"pan", "pancard", "nsdl", "uti", "tax_id", "incometax"},
    PiiType.GSTIN: {"gstin", "gst", "tax_number", "gst_no"},
    PiiType.UPI_HANDLE: {"upi", "vpa", "bhim", "pay", "handle"},
    PiiType.MOBILE: {"mobile", "phone", "contact", "cell", "telephone", "calling", "sms", "whatsapp"},
    PiiType.PASSPORT: {"passport", "ppt", "travel_doc"},
    PiiType.VOTER_ID: {"voter", "voter_id", "epic", "election", "elector"},
    PiiType.IFSC: {"ifsc", "bank", "branch", "neft", "rtgs", "imps", "micr"},
    PiiType.DRIVING_LICENCE: {"dl", "driving", "licence", "license", "rto", "sarathi", "morth"},
    PiiType.ABHA_HEALTH_ID: {"abha", "health_id", "ndhm", "abdm", "ayushman", "health_acc"},
    PiiType.PAYMENT_CARD: {"card", "credit", "debit", "pan_num", "visa", "mastercard", "rupay", "amex", "cvv", "card_no", "card_number"},
}

ANTI_KEYWORDS = {
    "test", "mock", "dummy", "sample", "example", "placeholder", "fake", "fixture",
    "order", "invoice", "ref", "reference", "sku", "item", "product", "magic",
    "uuid", "guid", "hash", "sha256", "checksum", "token", "auth_token", "random",
}

def _is_test_path(path: str) -> bool:
    normalized = path.replace("\\", "/").lower()
    return any(p in normalized for p in (
        "/tests/", "/test/", "/spec/", "/__tests__/", "test_",
        "_backup", "backup_", "_before_", "_candidate", "_copy",
        "/fixtures/", "/fixture/", "fixture_"
    ))

def _evaluate_context(pii_type: PiiType, tokens: list[str]) -> tuple[bool, bool]:
    has_pos = any(
        any(k in tok for k in CONTEXT_KEYWORDS.get(pii_type, set()))
        for tok in tokens
    )
    has_anti = any(
        any(k in tok for k in ANTI_KEYWORDS)
        for tok in tokens
    )
    return has_pos, has_anti

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
        line_snippet: str | None = None,
    ) -> None:
        hit_id = f"{pii_type.value}:{file}:{line}:{col}"
        if hit_id in seen_hit_ids:
            return
        seen_hit_ids.add(hit_id)

        is_test = _is_test_path(file)
        role = FileRole.FIXTURE if any(x in file.lower() for x in ("_backup", "backup_", "_before_", "_candidate", "_copy", "fixture")) else (FileRole.TEST if is_test else FileRole.PRODUCTION)
        
        final_conf = confidence
        if (is_test or role in (FileRole.TEST, FileRole.FIXTURE)) and not cfg.strict_test_scanning:
            final_conf = min(0.30, confidence)

        snip = line_snippet
        if not snip:
            fpath = Path(cfg.scan_root) / file
            if fpath.exists() and fpath.is_file():
                try:
                    flines = fpath.read_text(encoding="utf-8", errors="replace").splitlines()
                    if 1 <= line <= len(flines):
                        raw_l = flines[line - 1].strip()
                        if val_str and val_str in raw_l:
                            raw_l = raw_l.replace(val_str, f"[REDACTED_{pii_type.value}]")
                        snip = raw_l[:160]
                except Exception:
                    pass

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
                line_snippet=snip,
            )
        )

    for ast_file in model.ast_index:
        source_lines: list[str] = []
        target_path = Path(cfg.scan_root) / ast_file.path
        if target_path.exists():
            try:
                source_lines = target_path.read_text(encoding="utf-8", errors="replace").splitlines()
            except Exception:
                pass

        assignments_by_line: dict[int, list[str]] = {}
        for a in ast_file.assignments:
            l = a.get("line", 1)
            assignments_by_line.setdefault(l, []).append(a.get("name", ""))

        for lit in ast_file.string_literals:
            val = lit["value"].strip()
            line = lit["line"]
            col = lit["col"]

            ctx_tokens: list[str] = []
            if source_lines:
                start_l = max(0, line - 2)
                end_l = min(len(source_lines), line + 1)
                for s in source_lines[start_l:end_l]:
                    ctx_tokens.extend(re.findall(r"[A-Za-z0-9_]+", s.lower()))
            for offset in (-1, 0, 1):
                for vname in assignments_by_line.get(line + offset, []):
                    ctx_tokens.extend(re.findall(r"[A-Za-z0-9_]+", vname.lower()))

            if re.match(r"^\d{4}\s?\d{4}\s?\d{4}$", val):
                is_valid, reason = validate_aadhaar(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.AADHAAR, ctx_tokens)
                    conf = 0.85
                    if has_pos:
                        conf += 0.10
                    if has_anti:
                        conf -= 0.35
                    _add_hit(PiiType.AADHAAR, ast_file.path, line, col, val, conf, "verhoeff_pass", ctx_tokens)
                    continue

            if len(val) == 10 and re.match(r"^[A-Za-z0-9]{10}$", val):
                is_valid, reason = validate_pan(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.PAN, ctx_tokens)
                    conf = 0.85
                    if has_pos:
                        conf += 0.10
                    if has_anti:
                        conf -= 0.35
                    _add_hit(PiiType.PAN, ast_file.path, line, col, val, conf, reason, ctx_tokens)
                    continue

            if len(val) == 15:
                is_valid, reason = validate_gstin(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.GSTIN, ctx_tokens)
                    conf = 0.90
                    if has_pos:
                        conf += 0.08
                    if has_anti:
                        conf -= 0.30
                    _add_hit(PiiType.GSTIN, ast_file.path, line, col, val, conf, "gstin_mod36_pass", ctx_tokens)
                    continue

            if "@" in val and len(val) <= 128:
                is_valid, reason = validate_upi_id(val, psp_handles)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.UPI_HANDLE, ctx_tokens)
                    conf = 0.85
                    if has_pos:
                        conf += 0.10
                    if has_anti:
                        conf -= 0.30
                    _add_hit(PiiType.UPI_HANDLE, ast_file.path, line, col, val, conf, reason, ctx_tokens)
                    continue

            if re.match(r"^(?:\+91|91|0)?[6-9]\d{9}$", val.replace(" ", "").replace("-", "")):
                is_valid, reason = validate_mobile(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.MOBILE, ctx_tokens)
                    conf = 0.80
                    if has_pos:
                        conf += 0.10
                    if has_anti:
                        conf -= 0.30
                    _add_hit(PiiType.MOBILE, ast_file.path, line, col, val, conf, "valid_indian_mobile", ctx_tokens)
                    continue

            if "@" in val and "." in val:
                is_valid, _ = validate_email(val)
                if is_valid:
                    _add_hit(PiiType.EMAIL, ast_file.path, line, col, val, 0.85, "valid_email", ctx_tokens)
                    continue

            if len(val) == 8:
                is_valid, _ = validate_passport(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.PASSPORT, ctx_tokens)
                    conf = 0.85 if has_pos else (0.50 if not has_anti else 0.20)
                    _add_hit(PiiType.PASSPORT, ast_file.path, line, col, val, conf, "valid_passport", ctx_tokens)
                    continue

            if len(val) == 10:
                is_valid, _ = validate_voter_id(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.VOTER_ID, ctx_tokens)
                    conf = 0.85 if has_pos else (0.40 if not has_anti else 0.20)
                    _add_hit(PiiType.VOTER_ID, ast_file.path, line, col, val, conf, "valid_voter_id", ctx_tokens)
                    continue

            if len(val) == 11 and val[4] == "0":
                is_valid, _ = validate_ifsc(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.IFSC, ctx_tokens)
                    conf = 0.85
                    if has_pos:
                        conf += 0.10
                    if has_anti:
                        conf -= 0.30
                    _add_hit(PiiType.IFSC, ast_file.path, line, col, val, conf, "valid_ifsc", ctx_tokens)
                    continue

            if len(val) in (15, 16):
                is_valid, reason = validate_driving_licence(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.DRIVING_LICENCE, ctx_tokens)
                    conf = 0.90 if has_pos else (0.65 if not has_anti else 0.25)
                    _add_hit(PiiType.DRIVING_LICENCE, ast_file.path, line, col, val, conf, reason, ctx_tokens)
                    continue

            cleaned_num = re.sub(r"[\s\-]", "", val)
            if len(cleaned_num) == 14 and cleaned_num.isdigit():
                is_valid, reason = validate_abha(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.ABHA_HEALTH_ID, ctx_tokens)
                    conf = 0.90 if has_pos else (0.35 if not has_anti else 0.15)
                    _add_hit(PiiType.ABHA_HEALTH_ID, ast_file.path, line, col, val, conf, reason, ctx_tokens)
                    continue

            if 13 <= len(cleaned_num) <= 19 and cleaned_num.isdigit():
                is_valid, reason = validate_payment_card(val)
                if is_valid:
                    has_pos, has_anti = _evaluate_context(PiiType.PAYMENT_CARD, ctx_tokens)
                    conf = 0.90 if has_pos else (0.60 if not has_anti else 0.25)
                    _add_hit(PiiType.PAYMENT_CARD, ast_file.path, line, col, val, conf, reason, ctx_tokens)
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
