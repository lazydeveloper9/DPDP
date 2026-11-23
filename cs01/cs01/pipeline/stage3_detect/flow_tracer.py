"""
Stage 3 Source-Sink-Guard Flow Tracer
=====================================
Builds an intra-procedural taint flow graph connecting PII ingress points (sources),
intercepting security controls (guards), and outbound egress operations (sinks).
"""

from __future__ import annotations
import re
from typing import Optional

from cs01.models import (
    RepoModel, PiiHitList, FlowGraph, DataSource, DataSink, DataGuard,
    FlowEdge, SourceType, SinkType, GuardType, PiiType, ScanConfig,
)

LOGGER_PATTERNS = re.compile(
    r"(logger\.(info|debug|warn|error|critical)|logging\.(info|debug|warning|error)|console\.(log|info|warn|error)|System\.out\.print)",
    re.I,
)

OUTBOUND_CALL_PATTERNS = re.compile(
    r"(requests\.(get|post|put|delete)|axios\.(get|post|put)|fetch\(|http\.(get|post)|HttpClient)",
    re.I,
)

DB_WRITE_PATTERNS = re.compile(
    r"(\.save\(|\.insert\(|\.update\(|session\.add|db\.commit|INSERT\s+INTO)",
    re.I,
)

HTTP_RESPONSE_PATTERNS = re.compile(
    r"(res\.json|res\.send|Response\(|JsonResponse|return\s+\{)",
    re.I,
)

REQUEST_SOURCE_PATTERNS = re.compile(
    r"(req\.body|request\.json|request\.form|request\.args|@RequestBody|request\.data)",
    re.I,
)

GUARD_MASKING_PATTERNS = re.compile(
    r"(mask|redact|anonymize|obfuscate|hash|sha256)",
    re.I,
)

GUARD_ENCRYPTION_PATTERNS = re.compile(
    r"(encrypt|cipher|aes|kms|fernet|seal)",
    re.I,
)

GUARD_CONSENT_PATTERNS = re.compile(
    r"(consent|is_consented|user_consent|opt_in|check_consent)",
    re.I,
)

def trace_flows(
    model: RepoModel,
    pii_hits: PiiHitList,
    cfg: ScanConfig,
) -> FlowGraph:
    """Construct the intra-procedural FlowGraph from parsed AST functions."""
    sources: list[DataSource] = []
    sinks: list[DataSink] = []
    guards: list[DataGuard] = []
    edges: list[FlowEdge] = []

    file_hits: dict[str, list] = {}
    for h in pii_hits.hits:
        file_hits.setdefault(h.file, []).append(h)

    for ast_file in model.ast_index:
        hits_in_file = file_hits.get(ast_file.path, [])

        for func in ast_file.functions:
            func_name = func.get("name", "anonymous")
            start_l = func.get("start_line", 1)
            end_l = func.get("end_line", start_l)
            calls = func.get("calls", [])
            params = func.get("params", [])

            func_sources: list[DataSource] = []
            func_sinks: list[DataSink] = []
            func_guards: list[DataGuard] = []

            for p in params:
                p_lower = p.lower()
                suspected: list[PiiType] = []
                for pt in PiiType:
                    if pt.value.lower() in p_lower:
                        suspected.append(pt)
                
                if suspected or any(k in p_lower for k in ("req", "request", "payload", "body", "dto")):
                    src_id = f"SRC:{ast_file.path}:{func_name}:{p}"
                    src = DataSource(
                        id=src_id,
                        source_type=SourceType.REQUEST_BODY,
                        file=ast_file.path,
                        line=start_l,
                        function_name=func_name,
                        variable_name=p,
                        pii_types_suspected=suspected,
                    )
                    sources.append(src)
                    func_sources.append(src)

            for call in calls:
                snippet = call.get("snippet", "")
                callee = call.get("callee", "")
                cline = call.get("line", start_l)

                if REQUEST_SOURCE_PATTERNS.search(snippet) or REQUEST_SOURCE_PATTERNS.search(callee):
                    src_id = f"SRC:{ast_file.path}:{cline}:{callee}"
                    src = DataSource(
                        id=src_id,
                        source_type=SourceType.REQUEST_BODY,
                        file=ast_file.path,
                        line=cline,
                        function_name=func_name,
                        variable_name=callee,
                    )
                    sources.append(src)
                    func_sources.append(src)

            for call in calls:
                snippet = call.get("snippet", "")
                callee = call.get("callee", "")
                cline = call.get("line", start_l)

                g_type: Optional[GuardType] = None
                if GUARD_MASKING_PATTERNS.search(callee):
                    g_type = GuardType.MASKING
                elif GUARD_ENCRYPTION_PATTERNS.search(callee):
                    g_type = GuardType.ENCRYPTION
                elif GUARD_CONSENT_PATTERNS.search(callee):
                    g_type = GuardType.CONSENT_CHECK

                if g_type:
                    gid = f"GUARD:{ast_file.path}:{cline}:{callee}"
                    guard = DataGuard(
                        id=gid,
                        guard_type=g_type,
                        file=ast_file.path,
                        line=cline,
                        function_name=func_name,
                        guard_function_name=callee,
                    )
                    guards.append(guard)
                    func_guards.append(guard)

            for call in calls:
                snippet = call.get("snippet", "")
                callee = call.get("callee", "")
                cline = call.get("line", start_l)

                s_type: Optional[SinkType] = None
                if LOGGER_PATTERNS.search(callee) or LOGGER_PATTERNS.search(snippet):
                    s_type = SinkType.LOGGER
                elif OUTBOUND_CALL_PATTERNS.search(callee):
                    s_type = SinkType.THIRD_PARTY_SDK
                elif DB_WRITE_PATTERNS.search(snippet):
                    s_type = SinkType.DB_WRITE
                elif HTTP_RESPONSE_PATTERNS.search(snippet):
                    s_type = SinkType.HTTP_RESPONSE

                if s_type:
                    sid = f"SINK:{ast_file.path}:{cline}:{callee}"
                    sink = DataSink(
                        id=sid,
                        sink_type=s_type,
                        file=ast_file.path,
                        line=cline,
                        function_name=func_name,
                        call_expression=snippet[:80],
                    )
                    sinks.append(sink)
                    func_sinks.append(sink)

            if func_sources and func_sinks:
                active_guard = func_guards[0] if func_guards else None
                for src in func_sources:
                    for snk in func_sinks:
                        edge_id = f"EDGE:{src.id}->{snk.id}"
                        edge = FlowEdge(
                            id=edge_id,
                            source_id=src.id,
                            sink_id=snk.id,
                            guard_id=active_guard.id if active_guard else None,
                            guard_type=active_guard.guard_type if active_guard else None,
                            file=ast_file.path,
                            function_name=func_name,
                            is_unguarded=active_guard is None,
                        )
                        edges.append(edge)

    return FlowGraph(
        sources=sources,
        sinks=sinks,
        guards=guards,
        edges=edges,
    )
