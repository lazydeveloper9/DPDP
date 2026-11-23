"""
CS-01 Test-Time IAST Middleware for FastAPI
============================================
Drop-in test middleware for integration tests.
Intercepts outgoing HTTP response bodies and verifies zero unmasked Indian PII
is leaked in transit per DPDP Act §8(5).
"""

from __future__ import annotations
import json
import re
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

AADHAAR_REGEX = re.compile(r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")

class DpdpIastMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)

        body_bytes = b""
        async for chunk in response.body_iterator:
            body_bytes += chunk

        body_str = body_bytes.decode("utf-8", errors="replace")

        # Scan for unmasked PII in response body
        leaks = []
        if AADHAAR_REGEX.search(body_str):
            leaks.append("Unmasked Aadhaar literal detected in HTTP response")
        if PAN_REGEX.search(body_str):
            leaks.append("Unmasked PAN literal detected in HTTP response")

        if leaks:
            raise AssertionError(f"[DPDP IAST Violation §8(5)] Outbound leak on {request.url.path}: {leaks}")

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
