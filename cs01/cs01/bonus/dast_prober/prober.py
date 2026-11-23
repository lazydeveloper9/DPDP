"""
cs01.bonus.dast_prober.prober — Opt-in DAST live HTTP probing for DPDP compliance.
Checks live technical safeguards: TLS, HSTS, security headers, and privacy notice endpoint.
Requires explicit --allow-live-probe guardrail to prevent unauthorized network requests.
"""

from __future__ import annotations
import socket
import ssl
import urllib.parse
import urllib.request
import urllib.error
from typing import Any, Optional
from pydantic import BaseModel, Field

class DastFinding(BaseModel):
    check_id: str
    severity: str
    dpdp_section: str
    message: str
    remediation: str

class DastProbeResult(BaseModel):
    target_url: str
    probed_host: str
    probed_port: int
    tls_valid: bool = False
    tls_version: Optional[str] = None
    tls_cipher: Optional[str] = None
    headers_checked: dict[str, str] = Field(default_factory=dict)
    missing_security_headers: list[str] = Field(default_factory=list)
    privacy_notice_url: Optional[str] = None
    privacy_notice_found: bool = False
    findings: list[DastFinding] = Field(default_factory=list)

SECURITY_HEADERS_REQUIRED = [
    ("Strict-Transport-Security", "CRITICAL", "§8(5)", "Missing HSTS header allows downgrade attacks."),
    ("Content-Security-Policy", "HIGH", "§8(5)", "Missing Content-Security-Policy increases XSS and PII exfiltration risk."),
    ("X-Content-Type-Options", "MEDIUM", "§8(5)", "Missing X-Content-Type-Options: nosniff allows MIME confusion."),
    ("X-Frame-Options", "MEDIUM", "§8(5)", "Missing X-Frame-Options allows clickjacking."),
]

PRIVACY_NOTICE_PATHS = [
    "/privacy",
    "/privacy-policy",
    "/privacy_policy",
    "/legal/privacy",
]

def run_dast_probe(
    url: str,
    allow_live_probe: bool = False,
    timeout: float = 5.0,
) -> DastProbeResult:
    """
    Run an opt-in live DAST probe against target URL.
    Enforces the --allow-live-probe guardrail.
    """
    if not allow_live_probe:
        raise PermissionError(
            "Live DAST probing is strictly opt-in under DPDP security guardrails. "
            "Pass --allow-live-probe to confirm you own or have explicit authorization to probe this host."
        )

    parsed = urllib.parse.urlparse(url)
    if not parsed.scheme:
        url = "https://" + url
        parsed = urllib.parse.urlparse(url)

    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    result = DastProbeResult(target_url=url, probed_host=host, probed_port=port)

    if parsed.scheme == "https":
        try:
            ctx = ssl.create_default_context()
            with socket.create_connection((host, port), timeout=timeout) as sock:
                with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                    result.tls_valid = True
                    result.tls_version = ssock.version()
                    cipher = ssock.cipher()
                    result.tls_cipher = cipher[0] if cipher else None
        except ssl.SSLError as e:
            result.tls_valid = False
            result.findings.append(DastFinding(
                check_id="DAST-TLS-001",
                severity="CRITICAL",
                dpdp_section="§8(5)",
                message=f"TLS/SSL certificate or handshake error: {e}",
                remediation="Configure a valid, trusted TLS 1.2+ certificate on production endpoints.",
            ))
        except Exception as e:
            result.tls_valid = False
            result.findings.append(DastFinding(
                check_id="DAST-CONN-001",
                severity="HIGH",
                dpdp_section="§8(5)",
                message=f"Failed to connect to {host}:{port}: {e}",
                remediation="Ensure host is reachable and accepting HTTPS connections.",
            ))

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "CS-01-DPDP-Auditor/0.1"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            headers_dict = {k.lower(): v for k, v in resp.headers.items()}
            result.headers_checked = dict(resp.headers.items())

            for hdr_name, severity, section, msg in SECURITY_HEADERS_REQUIRED:
                if hdr_name.lower() not in headers_dict:
                    result.missing_security_headers.append(hdr_name)
                    result.findings.append(DastFinding(
                        check_id=f"DAST-HDR-{hdr_name[:4].upper()}",
                        severity=severity,
                        dpdp_section=section,
                        message=msg,
                        remediation=f"Add '{hdr_name}' header to all HTTP response configurations.",
                    ))
    except urllib.error.HTTPError as e:
        headers_dict = {k.lower(): v for k, v in e.headers.items()}
        result.headers_checked = dict(e.headers.items())
        for hdr_name, severity, section, msg in SECURITY_HEADERS_REQUIRED:
            if hdr_name.lower() not in headers_dict:
                result.missing_security_headers.append(hdr_name)
    except Exception:
        pass

    base_origin = f"{parsed.scheme}://{host}" + (f":{port}" if parsed.port else "")
    for path in PRIVACY_NOTICE_PATHS:
        notice_url = urllib.parse.urljoin(base_origin, path)
        try:
            req = urllib.request.Request(
                notice_url,
                headers={"User-Agent": "CS-01-DPDP-Auditor/0.1"},
                method="HEAD",
            )
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    result.privacy_notice_found = True
                    result.privacy_notice_url = notice_url
                    break
        except Exception:
            continue

    if not result.privacy_notice_found:
        result.findings.append(DastFinding(
            check_id="DAST-NOTICE-001",
            severity="HIGH",
            dpdp_section="§5(1) & Rule 3",
            message="No accessible Privacy Notice found at standard endpoints (/privacy, /privacy-policy).",
            remediation="Publish an accessible Privacy Notice in clear and plain language under DPDP §5.",
        ))

    return result
