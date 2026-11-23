"""
Stage 3 Source-Sink-Guard Flow Tracer
=====================================
Builds an interprocedural taint flow graph connecting PII ingress points (sources),
intercepting security controls (guards), and outbound egress operations (sinks).
Uses CallGraph to trace multi-function and cross-file flows with reachability tagging.
"""

from __future__ import annotations
import re
from typing import Optional

from cs01.models import (
    RepoModel, PiiHitList, FlowGraph, DataSource, DataSink, DataGuard,
    FlowEdge, SourceType, SinkType, GuardType, PiiType, ScanConfig,
)
from .call_graph import CallGraph

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
    r"(req\.body|request\.(get_json|json|form|args|values|data|POST)|req\.query|req\.params|@RequestBody|Depends\(|Body\()",
    re.I,
)

GUARD_MASKING_PATTERNS = re.compile(
    r"(mask|redact|anonymize|obfuscate|hash|sha256|tokeniz)",
    re.I,
)

GUARD_ENCRYPTION_PATTERNS = re.compile(
    r"(encrypt|cipher|aes|kms|fernet|seal)",
    re.I,
)

GUARD_CONSENT_PATTERNS = re.compile(
    r"(consent|is_consented|user_consent|opt_in|check_consent|has_consent|require_consent)",
    re.I,
)

def trace_flows(
    model: RepoModel,
    pii_hits: PiiHitList,
    cfg: ScanConfig,
) -> FlowGraph:
    """Construct the interprocedural FlowGraph from parsed AST functions and CallGraph."""
    call_graph = CallGraph(model)

    sources: list[DataSource] = []
    sinks: list[DataSink] = []
    guards: list[DataGuard] = []
    edges: list[FlowEdge] = []
    seen_edge_ids: set[str] = set()

    sources_by_func: dict[tuple[str, str], list[DataSource]] = {}
    sinks_by_func: dict[tuple[str, str], list[DataSink]] = {}
    guards_by_func: dict[tuple[str, str], list[DataGuard]] = {}

    for ast_file in model.ast_index:
        for func in ast_file.functions:
            func_name = func.get("name", "anonymous")
            func_key = (ast_file.path, func_name)
            start_l = func.get("start_line", 1)
            calls = func.get("calls", [])
            params = func.get("params", [])

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
                    sources_by_func.setdefault(func_key, []).append(src)

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
                    sources_by_func.setdefault(func_key, []).append(src)

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
                    guards_by_func.setdefault(func_key, []).append(guard)

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
                    sinks_by_func.setdefault(func_key, []).append(sink)

    # 1. Direct intra-procedural edges
    for func_key, f_sources in sources_by_func.items():
        f_file, f_name = func_key
        f_sinks = sinks_by_func.get(func_key, [])
        f_guards = guards_by_func.get(func_key, [])
        active_guard = f_guards[0] if f_guards else None
        reachability = call_graph.compute_reachability(f_file, f_name)

        for src in f_sources:
            for snk in f_sinks:
                edge_id = f"EDGE:{src.id}->{snk.id}"
                if edge_id not in seen_edge_ids:
                    seen_edge_ids.add(edge_id)
                    edges.append(
                        FlowEdge(
                            id=edge_id,
                            source_id=src.id,
                            sink_id=snk.id,
                            guard_id=active_guard.id if active_guard else None,
                            guard_type=active_guard.guard_type if active_guard else None,
                            file=f_file,
                            function_name=f_name,
                            is_unguarded=active_guard is None,
                            reachability=reachability,
                        )
                    )

    # 2. Inter-procedural two-hop edges (cross-function & cross-file)
    for func_key, f_sources in sources_by_func.items():
        caller_file, caller_name = func_key
        caller_guards = guards_by_func.get(func_key, [])
        callees = call_graph.get_callees(caller_file, caller_name)
        reachability = call_graph.compute_reachability(caller_file, caller_name)

        for callee_file, callee_name in callees:
            callee_key = (callee_file, callee_name)
            callee_sinks = sinks_by_func.get(callee_key, [])
            callee_guards = guards_by_func.get(callee_key, [])
            active_guard = callee_guards[0] if callee_guards else (caller_guards[0] if caller_guards else None)

            for src in f_sources:
                for snk in callee_sinks:
                    edge_id = f"EDGE_INTER:{src.id}->{snk.id}"
                    if edge_id not in seen_edge_ids:
                        seen_edge_ids.add(edge_id)
                        edges.append(
                            FlowEdge(
                                id=edge_id,
                                source_id=src.id,
                                sink_id=snk.id,
                                guard_id=active_guard.id if active_guard else None,
                                guard_type=active_guard.guard_type if active_guard else None,
                                file=caller_file,
                                function_name=f"{caller_name}->{callee_name}",
                                is_unguarded=active_guard is None,
                                reachability=reachability,
                            )
                        )

    return FlowGraph(
        sources=sources,
        sinks=sinks,
        guards=guards,
        edges=edges,
    )
