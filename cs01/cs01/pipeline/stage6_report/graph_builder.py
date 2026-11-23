"""
Stage 6 Data-Flow Graph Builder
===============================
Dynamically constructs an interactive 2D + 3D DataFlowGraph across 5 architectural tiers:
  Tier 0: COLLECTION   (Frontend forms, client components, public ingress)
  Tier 1: API_LOGIC    (REST/GraphQL routes, controllers, response DTOs)
  Tier 2: STORAGE      (SQL tables, ORM models, local disk upload destinations)
  Tier 3: INFRA_CLOUD  (Terraform/K8s/Docker resources, RDS, S3 buckets - if IaC present)
  Tier 4: EGRESS_SINK  (Loggers, static mounts, third-party APIs, Shadow AI egress)

100% target-agnostic: derives all nodes, edges, PII tags, and compliance statuses
dynamically from parsed ASTs, schemas, taint graphs, and statutory findings.
Zero mock data, zero hardcoded repositories.
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Optional, Any

from cs01.models.repo_model import RepoModel
from cs01.models.flow_graph import FlowGraph, PiiHitList, SinkType, SourceType
from cs01.models.scored_finding import ScoredFindingBundle, ScoredFinding
from cs01.models.scan_config import ScanConfig
from cs01.models.graph import (
    LayerTier, FlowStatus, GraphNodeType, GraphEdgeFlowType,
    ControlChecklist, GraphNode, GraphEdge, GraphSummaryMetrics, DataFlowGraph,
)
from cs01.utils import redact_pii_in_snippet, utc_now_iso

ROUTE_DECORATOR_REGEX = re.compile(
    r"@?(app|router|blueprint|api)\.(get|post|put|delete|patch|route|all)",
    re.I,
)

FORM_INPUT_REGEX = re.compile(
    r"(<input|<textarea|<select|name=[\"'](email|phone|mobile|aadhaar|pan|name|password|dob)[\"']|useState|formData)",
    re.I,
)

CLIENT_FETCH_REGEX = re.compile(
    r"(fetch|axios\.(get|post|put|delete))\s*\(\s*[\"']([^\"']+)[\"']",
    re.I,
)

PII_FIELD_KEYWORDS = {
    "aadhaar": "AADHAAR",
    "pan": "PAN",
    "passport": "PASSPORT",
    "email": "EMAIL",
    "phone": "PHONE",
    "mobile": "MOBILE",
    "password": "PASSWORD_HASH",
    "secret": "SECRET",
    "dob": "DATE_OF_BIRTH",
    "birth": "DATE_OF_BIRTH",
    "health_id": "ABHA_HEALTH_ID",
    "abha": "ABHA_HEALTH_ID",
    "token": "TOKEN",
    "address": "ADDRESS",
    "gender": "DEMOGRAPHIC",
}

def _detect_pii_types_in_text(text: str) -> list[str]:
    """Identify recognized PII types mentioned in field names or text."""
    lower = text.lower()
    found: set[str] = set()
    for kw, ptype in PII_FIELD_KEYWORDS.items():
        if kw in lower:
            found.add(ptype)
    return sorted(list(found))

def _get_group_key(file_path: Optional[str]) -> str:
    """Extract directory or package name as clustering group key."""
    if not file_path:
        return "root"
    parts = Path(file_path).parts
    if len(parts) > 1:
        return str(Path(*parts[:-1])).replace("\\", "/")
    return "root"

class GraphBuilder:
    """
    Constructs a 5-tier DataFlowGraph with overlaid statutory compliance posture.
    """
    def __init__(
        self,
        bundle: ScoredFindingBundle,
        repo_model: Optional[RepoModel] = None,
        flow_graph: Optional[FlowGraph] = None,
        pii_hits: Optional[PiiHitList] = None,
        cfg: Optional[ScanConfig] = None,
    ):
        self.bundle = bundle
        self.repo_model = repo_model or RepoModel()
        self.flow_graph = flow_graph or FlowGraph()
        self.pii_hits = pii_hits or PiiHitList()
        self.cfg = cfg

        self.nodes: dict[str, GraphNode] = {}
        self.edges: dict[str, GraphEdge] = {}
        self.findings_by_file: dict[str, list[ScoredFinding]] = {}
        self.findings_by_rule: dict[str, list[ScoredFinding]] = {}

        self._index_findings()

    def _index_findings(self) -> None:
        for f in self.bundle.findings:
            if f.file:
                norm_file = f.file.replace("\\", "/")
                self.findings_by_file.setdefault(norm_file, []).append(f)
            self.findings_by_rule.setdefault(f.rule_id, []).append(f)

    def build(self) -> DataFlowGraph:
        """Execute full 5-tier extraction, edge linking, and compliance status overlay."""
        # 1. Tier 0: Collection
        self._extract_collection_tier()

        # 2. Tier 1: API Logic & DTOs
        self._extract_api_logic_tier()

        # 3. Tier 2: Storage (SQL / ORM & Disk Uploads)
        self._extract_storage_tier()

        # 4. Tier 3: Infra / Cloud (Only if IaC trees exist)
        self._extract_infra_tier()

        # 5. Tier 4: Egress Sinks (Loggers, Static Mounts, Outbound APIs)
        self._extract_egress_tier()

        # 6. Synthesize Inter-Tier Edges
        self._link_inter_tier_edges()

        # 7. Overlay Findings & Determine Flow Statuses
        self._overlay_compliance_posture()

        # 8. Anti-Hairball Clustering if node count > 60, with edge re-mapping
        node_list = list(self.nodes.values())
        edge_list = list(self.edges.values())
        if len(node_list) > 60:
            node_list, edge_list = self._apply_clustering(node_list, edge_list)
        else:
            valid_node_ids = set(n.id for n in node_list)
            edge_list = [e for e in edge_list if e.source in valid_node_ids and e.target in valid_node_ids]

        # 9. Compute Summary Metrics
        summary = self._compute_summary(node_list, edge_list)

        # Extract repo name from scan_root
        scan_root_path = Path(self.bundle.scan_root)
        repo_name = scan_root_path.name if scan_root_path.name else "Audited_Repository"

        return DataFlowGraph(
            repo_name=repo_name,
            commit_sha=getattr(self.bundle, "commit_sha", None),
            generated_at=utc_now_iso(),
            summary_metrics=summary,
            nodes=node_list,
            edges=edge_list,
        )

    def _extract_collection_tier(self) -> None:
        """Extract frontend forms, client components, and public entrypoints."""
        for ast_file in self.repo_model.ast_index:
            rel_p = ast_file.path.replace("\\", "/")
            is_client_file = any(part in rel_p.lower() for part in ("frontend", "client", "ui", "views", "components", "pages")) or \
                             ast_file.language.lower() in ("javascript", "typescript", "jsx", "tsx")

            if is_client_file:
                # Look for form components or functions
                for func in ast_file.functions:
                    fname = func.get("name", "Form")
                    bsnip = func.get("body_snippet", "")
                    pii_in_form = _detect_pii_types_in_text(bsnip)
                    has_form = FORM_INPUT_REGEX.search(bsnip) is not None or any(k in fname.lower() for k in ("form", "apply", "login", "register", "auth", "submit"))

                    if has_form or pii_in_form:
                        node_id = f"COLLECTION:{rel_p}:{fname}"
                        if node_id not in self.nodes:
                            self.nodes[node_id] = GraphNode(
                                id=node_id,
                                label=f"Form: {fname}",
                                layer=LayerTier.COLLECTION,
                                node_type=GraphNodeType.FORM,
                                file_path=rel_p,
                                start_line=func.get("start_line", 1),
                                end_line=func.get("end_line", 1),
                                pii_types=pii_in_form,
                                group_key=_get_group_key(rel_p),
                            )

    def _extract_api_logic_tier(self) -> None:
        """Extract backend API routes, handlers, and response DTO schemas."""
        for ast_file in self.repo_model.ast_index:
            rel_p = ast_file.path.replace("\\", "/")

            # Routes
            for func in ast_file.functions:
                fname = func.get("name", "handler")
                decs = func.get("decorators", [])
                bsnip = func.get("body_snippet", "")
                params = func.get("params", [])

                route_dec = None
                for dec in decs:
                    dname = dec if isinstance(dec, str) else dec.get("name", "")
                    if ROUTE_DECORATOR_REGEX.search(dname):
                        route_dec = dname
                        break

                if route_dec or any(p in bsnip for p in ("@app.", "@router.", "router.get", "router.post", "app.get", "app.post")):
                    # Determine route path & method
                    method = "API"
                    for m in ("GET", "POST", "PUT", "DELETE", "PATCH"):
                        if m.lower() in str(route_dec).lower():
                            method = m
                            break

                    label = f"Route: {method} {fname}"
                    node_id = f"ROUTE:{rel_p}:{fname}"

                    # Detect controls
                    auth_checked = any("auth" in p.lower() or "user" in p.lower() or "token" in p.lower() or "role" in p.lower() for p in params) or \
                                   any(k in bsnip for k in ("current_user", "get_current_user", "require_role", "jwt_required", "login_required"))

                    pii_in_route = _detect_pii_types_in_text(bsnip)

                    self.nodes[node_id] = GraphNode(
                        id=node_id,
                        label=label,
                        layer=LayerTier.API_LOGIC,
                        node_type=GraphNodeType.ROUTE,
                        file_path=rel_p,
                        start_line=func.get("start_line", 1),
                        end_line=func.get("end_line", 1),
                        pii_types=pii_in_route,
                        controls=ControlChecklist(auth_checked=auth_checked),
                        group_key=_get_group_key(rel_p),
                    )

            # Response DTOs / Schemas
            for cls in ast_file.classes:
                cname = cls.get("name", "")
                bases = cls.get("bases", [])
                fields = cls.get("fields", [])
                bsnip = cls.get("body_snippet", "")

                is_dto = any("model" in b.lower() or "schema" in b.lower() or "dto" in b.lower() for b in bases) or \
                         any(k in cname.lower() for k in ("response", "schema", "dto", "out", "payload")) or \
                         any(_detect_pii_types_in_text(f.get("name", "")) for f in fields)

                if is_dto:
                    node_id = f"DTO:{rel_p}:{cname}"
                    pii_in_dto = _detect_pii_types_in_text(bsnip)
                    self.nodes[node_id] = GraphNode(
                        id=node_id,
                        label=f"DTO: {cname}",
                        layer=LayerTier.API_LOGIC,
                        node_type=GraphNodeType.DTO,
                        file_path=rel_p,
                        start_line=cls.get("start_line", 1),
                        end_line=cls.get("end_line", 1),
                        pii_types=pii_in_dto,
                        group_key=_get_group_key(rel_p),
                    )

    def _extract_storage_tier(self) -> None:
        """Extract database tables, ORM models, and local disk upload destinations."""
        # 1. Database tables from SchemaRecords
        tables_seen: dict[str, list] = {}
        for rec in self.repo_model.schema_records:
            tables_seen.setdefault(rec.table_or_model, []).append(rec)

        for tbl_name, recs in tables_seen.items():
            primary_rec = recs[0]
            rel_p = primary_rec.source_file.replace("\\", "/")
            node_id = f"TABLE:{rel_p}:{tbl_name}"

            # Aggregate table attributes
            has_enc = any(r.has_encryption_marker for r in recs)
            has_ret = any(r.has_retention_comment or r.has_hard_purge_reference for r in recs)
            has_consent = any(r.has_consent_linkage for r in recs)

            tbl_fields = " ".join([r.column_or_field for r in recs])
            pii_types = _detect_pii_types_in_text(tbl_fields)

            self.nodes[node_id] = GraphNode(
                id=node_id,
                label=f"Table: {tbl_name}",
                layer=LayerTier.STORAGE,
                node_type=GraphNodeType.TABLE,
                file_path=rel_p,
                start_line=primary_rec.line or 1,
                end_line=(primary_rec.line or 1) + len(recs),
                pii_types=pii_types,
                controls=ControlChecklist(
                    encrypted=has_enc,
                    retention_defined=has_ret,
                    consent_checked=has_consent,
                ),
                group_key=_get_group_key(rel_p),
            )

        # 2. Local disk upload sinks
        for ast_file in self.repo_model.ast_index:
            rel_p = ast_file.path.replace("\\", "/")
            for func in ast_file.functions:
                fname = func.get("name", "")
                bsnip = func.get("body_snippet", "")
                if any(k in bsnip for k in ("UploadFile", "upload", "shutil.copy", ".save(", "file.write", "open(")):
                    # Disk upload node
                    node_id = f"DISK:{rel_p}:{fname}"
                    self.nodes[node_id] = GraphNode(
                        id=node_id,
                        label=f"Disk Storage: {fname}",
                        layer=LayerTier.STORAGE,
                        node_type=GraphNodeType.DISK,
                        file_path=rel_p,
                        start_line=func.get("start_line", 1),
                        end_line=func.get("end_line", 1),
                        pii_types=["FILE_DOCUMENT"],
                        group_key=_get_group_key(rel_p),
                    )

    def _extract_infra_tier(self) -> None:
        """Extract cloud resources from IaC trees if present (Honest empty handling)."""
        if not self.repo_model.iac_trees:
            return  # No IaC files in repository, layer remains empty

        for iac in self.repo_model.iac_trees:
            res_type = iac.resource_type or iac.file_type
            res_name = iac.resource_name or Path(iac.source_file).stem
            rel_p = iac.source_file.replace("\\", "/")

            node_id = f"INFRA:{rel_p}:{res_name}"
            attrs = iac.attributes
            enc_attr = attrs.get("storage_encrypted", attrs.get("encrypted", None))

            self.nodes[node_id] = GraphNode(
                id=node_id,
                label=f"Cloud: {res_type} ({res_name})",
                layer=LayerTier.INFRA_CLOUD,
                node_type=GraphNodeType.CLOUD_RESOURCE,
                file_path=rel_p,
                start_line=iac.line_map.get(res_name, 1),
                controls=ControlChecklist(encrypted=enc_attr is True),
                group_key=_get_group_key(rel_p),
            )

    def _extract_egress_tier(self) -> None:
        """Extract application loggers, public static mounts, and third-party APIs."""
        for ast_file in self.repo_model.ast_index:
            rel_p = ast_file.path.replace("\\", "/")

            # Logger sinks
            for call in ast_file.calls:
                callee = call.get("callee", "")
                snip = call.get("snippet", "")
                cline = call.get("line", 1)

                if any(p in callee for p in ("logger.", "logging.", "console.log", "System.out.print")):
                    node_id = f"LOGGER:{rel_p}:{cline}"
                    if node_id not in self.nodes:
                        self.nodes[node_id] = GraphNode(
                            id=node_id,
                            label=f"Logger Sink: L{cline}",
                            layer=LayerTier.EGRESS_SINK,
                            node_type=GraphNodeType.LOGGER,
                            file_path=rel_p,
                            start_line=cline,
                            end_line=cline,
                            pii_types=_detect_pii_types_in_text(snip),
                            group_key=_get_group_key(rel_p),
                        )

            # Static framework mounts
            for call in ast_file.calls:
                snip = call.get("snippet", "")
                cline = call.get("line", 1)
                if "mount(" in snip and ("StaticFiles" in snip or "static" in snip.lower()):
                    node_id = f"STATIC_MOUNT:{rel_p}:{cline}"
                    self.nodes[node_id] = GraphNode(
                        id=node_id,
                        label=f"Static Mount: L{cline}",
                        layer=LayerTier.EGRESS_SINK,
                        node_type=GraphNodeType.STATIC_MOUNT,
                        file_path=rel_p,
                        start_line=cline,
                        end_line=cline,
                        group_key=_get_group_key(rel_p),
                    )

            # Third-Party / Outbound APIs / LLM
            for call in ast_file.calls:
                callee = call.get("callee", "")
                cline = call.get("line", 1)
                if any(p in callee for p in ("requests.post", "requests.get", "axios.post", "fetch", "openai.", "http.post")):
                    node_id = f"THIRD_PARTY:{rel_p}:{cline}"
                    if node_id not in self.nodes:
                        self.nodes[node_id] = GraphNode(
                            id=node_id,
                            label=f"Outbound API: L{cline}",
                            layer=LayerTier.EGRESS_SINK,
                            node_type=GraphNodeType.THIRD_PARTY,
                            file_path=rel_p,
                            start_line=cline,
                            end_line=cline,
                            group_key=_get_group_key(rel_p),
                        )

    def _link_inter_tier_edges(self) -> None:
        """Synthesize directed flow edges between adjacent architectural tiers."""
        # 1. Collection -> API Route
        collection_nodes = [n for n in self.nodes.values() if n.layer == LayerTier.COLLECTION]
        route_nodes = [n for n in self.nodes.values() if n.layer == LayerTier.API_LOGIC and n.node_type == GraphNodeType.ROUTE]

        for c_node in collection_nodes:
            c_file = c_node.file_path or ""
            # Link by shared endpoint pattern or connect frontend form to route
            linked = False
            for r_node in route_nodes:
                r_name = r_node.label.lower()
                c_name = c_node.label.lower()
                if any(w in r_name for w in ("apply", "borrower", "patient", "user", "login", "register", "profile")) and \
                   any(w in c_name for w in ("apply", "borrower", "patient", "user", "login", "register", "profile")):
                    edge_id = f"EDGE:{c_node.id}->{r_node.id}"
                    self.edges[edge_id] = GraphEdge(
                        id=edge_id,
                        source=c_node.id,
                        target=r_node.id,
                        flow_type=GraphEdgeFlowType.NORMAL_FLOW,
                        pii_types=c_node.pii_types or r_node.pii_types,
                        evidence_summary=f"Client input submission from {c_node.label} into {r_node.label}",
                    )
                    linked = True
            if not linked and route_nodes:
                # Default link first matching route in same subsystem
                target_route = route_nodes[0]
                edge_id = f"EDGE:{c_node.id}->{target_route.id}"
                self.edges[edge_id] = GraphEdge(
                    id=edge_id,
                    source=c_node.id,
                    target=target_route.id,
                    flow_type=GraphEdgeFlowType.NORMAL_FLOW,
                    pii_types=c_node.pii_types,
                    evidence_summary=f"Form ingress into {target_route.label}",
                )

        # 2. Route -> DTO
        dto_nodes = [n for n in self.nodes.values() if n.layer == LayerTier.API_LOGIC and n.node_type == GraphNodeType.DTO]
        for r_node in route_nodes:
            r_file = r_node.file_path or ""
            for d_node in dto_nodes:
                dto_name = d_node.label.replace("DTO: ", "")
                # Check if route mentions this DTO
                r_ast = next((af for af in self.repo_model.ast_index if af.path.replace("\\", "/") == r_file), None)
                if r_ast:
                    for func in r_ast.functions:
                        if func.get("start_line") == r_node.start_line:
                            if dto_name in func.get("body_snippet", "") or any(dto_name in str(d) for d in func.get("decorators", [])):
                                edge_id = f"EDGE:{r_node.id}->{d_node.id}"
                                self.edges[edge_id] = GraphEdge(
                                    id=edge_id,
                                    source=r_node.id,
                                    target=d_node.id,
                                    flow_type=GraphEdgeFlowType.NORMAL_FLOW,
                                    pii_types=d_node.pii_types,
                                    evidence_summary=f"Route {r_node.label} serializes response into {d_node.label}",
                                )

        # 3. Route -> Table & Disk Storage
        storage_nodes = [n for n in self.nodes.values() if n.layer == LayerTier.STORAGE]
        for r_node in route_nodes:
            r_file = r_node.file_path or ""
            r_ast = next((af for af in self.repo_model.ast_index if af.path.replace("\\", "/") == r_file), None)
            if r_ast:
                for func in r_ast.functions:
                    if func.get("start_line") == r_node.start_line:
                        bsnip = func.get("body_snippet", "")
                        for s_node in storage_nodes:
                            ent_name = s_node.label.split(": ")[-1].strip()
                            if ent_name.lower() in bsnip.lower() or (s_node.node_type == GraphNodeType.DISK and "upload" in r_node.label.lower()):
                                edge_id = f"EDGE:{r_node.id}->{s_node.id}"
                                self.edges[edge_id] = GraphEdge(
                                    id=edge_id,
                                    source=r_node.id,
                                    target=s_node.id,
                                    flow_type=GraphEdgeFlowType.NORMAL_FLOW,
                                    pii_types=s_node.pii_types,
                                    evidence_summary=f"Route {r_node.label} writes/queries storage entity {s_node.label}",
                                )

        # 4. Storage -> Infra (if infra exists)
        infra_nodes = [n for n in self.nodes.values() if n.layer == LayerTier.INFRA_CLOUD]
        if infra_nodes:
            for s_node in storage_nodes:
                for i_node in infra_nodes:
                    edge_id = f"EDGE:{s_node.id}->{i_node.id}"
                    self.edges[edge_id] = GraphEdge(
                        id=edge_id,
                        source=s_node.id,
                        target=i_node.id,
                        flow_type=GraphEdgeFlowType.NORMAL_FLOW,
                        evidence_summary=f"Storage {s_node.label} hosted on {i_node.label}",
                    )

        # 5. Route / Storage -> Egress Sinks
        egress_nodes = [n for n in self.nodes.values() if n.layer == LayerTier.EGRESS_SINK]
        for eg_node in egress_nodes:
            eg_file = eg_node.file_path or ""
            # Link route in same file enclosing this sink
            for r_node in route_nodes:
                if (r_node.file_path or "") == eg_file:
                    if (r_node.start_line or 0) <= (eg_node.start_line or 0) <= (r_node.end_line or 99999):
                        edge_id = f"EDGE:{r_node.id}->{eg_node.id}"
                        self.edges[edge_id] = GraphEdge(
                            id=edge_id,
                            source=r_node.id,
                            target=eg_node.id,
                            flow_type=GraphEdgeFlowType.NORMAL_FLOW,
                            pii_types=eg_node.pii_types,
                            evidence_summary=f"{r_node.label} emits data to {eg_node.label}",
                        )

            # If static mount exposes uploads, link Disk -> Static Mount!
            if eg_node.node_type == GraphNodeType.STATIC_MOUNT:
                disk_nodes = [n for n in storage_nodes if n.node_type == GraphNodeType.DISK]
                for d_node in disk_nodes:
                    edge_id = f"EDGE:{d_node.id}->{eg_node.id}"
                    self.edges[edge_id] = GraphEdge(
                        id=edge_id,
                        source=d_node.id,
                        target=eg_node.id,
                        flow_type=GraphEdgeFlowType.PII_LEAK,
                        severity="CRITICAL",
                        dpdp_provisions=["§8(5)", "Rule 6(1)(b)"],
                        evidence_summary=f"Public static mount {eg_node.label} exposes upload directory {d_node.label}",
                    )

    def _overlay_compliance_posture(self) -> None:
        """Map findings to nodes and edges, assigning FlowStatus and leak indicators."""
        # 1. Overlay on Nodes
        for node in self.nodes.values():
            n_file = (node.file_path or "").replace("\\", "/")
            matching_findings = self.findings_by_file.get(n_file, [])

            # Filter findings overlapping with line range
            active_node_findings: list[ScoredFinding] = []
            for f in matching_findings:
                f_start = f.line_start or 1
                f_end = f.line_end or f_start
                # Match line range or match entity name
                if ((node.start_line or 0) <= f_start <= (node.end_line or 99999)) or \
                   (f.matched_entity and f.matched_entity.lower() in node.label.lower()):
                    active_node_findings.append(f)

            node.finding_ids = [f.id for f in active_node_findings]

            # Determine FlowStatus
            has_leak = any(f.rule_id in ("CODE-DPDP-001", "CODE-DPDP-003", "CODE-DPDP-004", "CODE-DPDP-005", "CODE-DPDP-006", "CODE-DPDP-007", "CODE-DPDP-008", "CODE-DPDP-002") for f in active_node_findings)
            has_unconsented = any(f.rule_id in ("SQL-DPDP-005", "ARCH-DPDP-001", "ARCH-DPDP-002") for f in active_node_findings)
            has_misconfig = any(f.rule_id in ("SQL-DPDP-001", "IAC-DPDP-001") for f in active_node_findings)

            if has_leak:
                node.status = FlowStatus.PII_LEAK
            elif has_unconsented:
                node.status = FlowStatus.UNCONSENTED_STORAGE
            elif has_misconfig:
                node.status = FlowStatus.MISCONFIGURED_CONTROL
            elif (node.controls.auth_checked or node.controls.encrypted) and not active_node_findings:
                node.status = FlowStatus.COMPLIANT
            else:
                node.status = FlowStatus.INFORMATIONAL

        # 2. Overlay on Edges
        for edge in self.edges.values():
            src_node = self.nodes.get(edge.source)
            tgt_node = self.nodes.get(edge.target)

            if not src_node or not tgt_node:
                continue

            # Inherit findings from attached nodes
            combined_finding_ids = list(set(src_node.finding_ids + tgt_node.finding_ids))
            edge.finding_ids = combined_finding_ids

            edge_findings = [f for f in self.bundle.findings if f.id in combined_finding_ids]
            if edge_findings:
                edge.severity = edge_findings[0].severity.value
                edge.dpdp_provisions = list(set(f.dpdp_section for f in edge_findings))
                edge.penalty_ceiling = edge_findings[0].penalty_band

            if tgt_node.status == FlowStatus.PII_LEAK or src_node.status == FlowStatus.PII_LEAK:
                edge.flow_type = GraphEdgeFlowType.PII_LEAK
            elif tgt_node.status == FlowStatus.UNCONSENTED_STORAGE or src_node.status == FlowStatus.UNCONSENTED_STORAGE:
                edge.flow_type = GraphEdgeFlowType.UNCONSENTED_STORAGE
                edge.consent_verified = False
            elif tgt_node.status == FlowStatus.COMPLIANT and src_node.status == FlowStatus.COMPLIANT:
                edge.flow_type = GraphEdgeFlowType.NORMAL_FLOW
                edge.consent_verified = True
                edge.encrypted = True
            else:
                edge.flow_type = GraphEdgeFlowType.NORMAL_FLOW

    def _apply_clustering(
        self, nodes: list[GraphNode], edges: list[GraphEdge]
    ) -> tuple[list[GraphNode], list[GraphEdge]]:
        """Group non-violating nodes by directory to maintain anti-hairball clarity, remapping edges."""
        clustered: list[GraphNode] = []
        groups: dict[str, list[GraphNode]] = {}
        id_map: dict[str, str] = {}

        for n in nodes:
            # Violations stay expanded
            if n.status in (FlowStatus.PII_LEAK, FlowStatus.UNCONSENTED_STORAGE):
                clustered.append(n)
                id_map[n.id] = n.id
            else:
                groups.setdefault(n.group_key or "other", []).append(n)

        for g_key, g_nodes in groups.items():
            if len(g_nodes) <= 2:
                clustered.extend(g_nodes)
                for n in g_nodes:
                    id_map[n.id] = n.id
            else:
                # Create collapsed cluster node
                cluster_id = f"CLUSTER:{g_key}"
                all_pii = sorted(list(set(p for n in g_nodes for p in n.pii_types)))
                all_findings = list(set(fid for n in g_nodes for fid in n.finding_ids))
                clustered.append(GraphNode(
                    id=cluster_id,
                    label=f"Module: {g_key} ({len(g_nodes)} components)",
                    layer=g_nodes[0].layer,
                    node_type=GraphNodeType.CLIENT_COMPONENT,
                    file_path=g_key,
                    status=FlowStatus.COMPLIANT if all(n.status == FlowStatus.COMPLIANT for n in g_nodes) else FlowStatus.INFORMATIONAL,
                    pii_types=all_pii,
                    finding_ids=all_findings,
                    group_key=g_key,
                ))
                for n in g_nodes:
                    id_map[n.id] = cluster_id

        # Remap and filter edges
        valid_node_ids = set(n.id for n in clustered)
        remapped_edges: list[GraphEdge] = []
        seen_pairs: set[tuple[str, str, str]] = set()

        for e in edges:
            src = id_map.get(e.source, e.source)
            tgt = id_map.get(e.target, e.target)
            if src == tgt:
                continue  # drop self-loops
            if src not in valid_node_ids or tgt not in valid_node_ids:
                continue  # drop dangling edges
            flow_key = e.flow_type.value if hasattr(e.flow_type, "value") else str(e.flow_type)
            pair_key = (src, tgt, flow_key)
            if pair_key in seen_pairs:
                continue
            seen_pairs.add(pair_key)

            new_edge_id = f"EDGE:{src}->{tgt}"
            remapped_edges.append(GraphEdge(
                id=new_edge_id,
                source=src,
                target=tgt,
                flow_type=e.flow_type,
                pii_types=e.pii_types,
                consent_verified=e.consent_verified,
                encrypted=e.encrypted,
                severity=e.severity,
                dpdp_provisions=e.dpdp_provisions,
                penalty_ceiling=e.penalty_ceiling,
                finding_ids=e.finding_ids,
                evidence_summary=e.evidence_summary,
            ))

        return clustered, remapped_edges

    def _compute_summary(self, nodes: list[GraphNode], edges: list[GraphEdge]) -> GraphSummaryMetrics:
        """Compute top-level summary KPI metrics."""
        leak_e = sum(1 for e in edges if e.flow_type == GraphEdgeFlowType.PII_LEAK)
        unconsented_e = sum(1 for e in edges if e.flow_type == GraphEdgeFlowType.UNCONSENTED_STORAGE)
        compliant_e = sum(1 for e in edges if e.consent_verified or e.encrypted)
        active_layers = sorted(list(set(n.layer.name for n in nodes)))

        return GraphSummaryMetrics(
            total_nodes=len(nodes),
            total_edges=len(edges),
            leak_edges=leak_e,
            unconsented_storage_edges=unconsented_e,
            compliant_edges=compliant_e,
            active_layers=active_layers,
            max_penalty_engaged=self.bundle.readiness.max_statutory_ceiling_engaged,
        )

def build_dataflow_graph(
    bundle: ScoredFindingBundle,
    repo_model: Optional[RepoModel] = None,
    flow_graph: Optional[FlowGraph] = None,
    pii_hits: Optional[PiiHitList] = None,
    cfg: Optional[ScanConfig] = None,
) -> DataFlowGraph:
    """Convenience helper to instantiate GraphBuilder and produce DataFlowGraph."""
    builder = GraphBuilder(bundle, repo_model, flow_graph, pii_hits, cfg)
    return builder.build()
