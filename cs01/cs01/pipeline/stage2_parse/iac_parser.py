"""
Stage 2 Infrastructure-as-Code & Container Parser
=================================================
Extracts normalized IacTree structures from:
  1. Terraform files (.tf, .hcl) via python-hcl2
  2. Kubernetes YAML manifests via ruamel.yaml
  3. Dockerfiles via dockerfile-parse
  4. Docker Compose files via ruamel.yaml
"""

from __future__ import annotations
import os
import re
from pathlib import Path
from typing import Any

import hcl2
from ruamel.yaml import YAML
from dockerfile_parse import DockerfileParser

from cs01.models import IacTree

def parse_terraform_file(abs_path: Path, rel_path: str) -> list[IacTree]:
    """Parse Terraform configuration files (.tf) with line number mapping."""
    trees: list[IacTree] = []
    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as fh:
            data = hcl2.load(fh)
    except Exception as exc:
        return [IacTree(
            source_file=rel_path,
            file_type="terraform",
            parse_error=str(exc),
        )]

    raw_lines = abs_path.read_text(encoding="utf-8", errors="replace").splitlines()
    resource_line_pattern = re.compile(r'^\s*resource\s+"([^"]+)"\s+"([^"]+)"')
    attribute_line_pattern = re.compile(r'^\s*([a-zA-Z0-9_-]+)\s*=')

    resource_lines: dict[tuple[str, str], int] = {}
    for idx, line in enumerate(raw_lines, start=1):
        m = resource_line_pattern.match(line)
        if m:
            resource_lines[(m.group(1), m.group(2))] = idx

    resources_list = data.get("resource", [])
    for res_dict in resources_list:
        if not isinstance(res_dict, dict):
            continue
        for res_type_raw, instances in res_dict.items():
            res_type = res_type_raw.strip('"')
            if not isinstance(instances, dict):
                continue
            for res_name_raw, attrs in instances.items():
                res_name = res_name_raw.strip('"')
                start_line = resource_lines.get((res_type, res_name), 1)
                
                line_map: dict[str, int] = {"__self__": start_line}
                if isinstance(attrs, dict):
                    for i in range(start_line - 1, min(len(raw_lines), start_line + 60)):
                        am = attribute_line_pattern.match(raw_lines[i])
                        if am and am.group(1) in attrs:
                            line_map[am.group(1)] = i + 1

                trees.append(
                    IacTree(
                        source_file=rel_path,
                        file_type="terraform",
                        resource_type=res_type,
                        resource_name=res_name,
                        attributes=attrs if isinstance(attrs, dict) else {"raw": attrs},
                        line_map=line_map,
                    )
                )

    return trees

def parse_kubernetes_yaml(abs_path: Path, rel_path: str) -> list[IacTree]:
    """Parse Kubernetes YAML manifests, preserving line numbers."""
    trees: list[IacTree] = []
    try:
        yaml_loader = YAML()
        yaml_loader.preserve_quotes = True
        content = abs_path.read_text(encoding="utf-8", errors="replace")
        docs = list(yaml_loader.load_all(content))
    except Exception as exc:
        return [IacTree(
            source_file=rel_path,
            file_type="kubernetes",
            parse_error=str(exc),
        )]

    for doc in docs:
        if not isinstance(doc, dict):
            continue

        kind = doc.get("kind")
        if not kind:
            continue

        metadata = doc.get("metadata", {})
        name = metadata.get("name", "unnamed") if isinstance(metadata, dict) else "unnamed"

        line_map: dict[str, int] = {}
        if hasattr(doc, "lc"):
            line_map["__self__"] = getattr(doc.lc, "line", 0) + 1

        trees.append(
            IacTree(
                source_file=rel_path,
                file_type="kubernetes",
                resource_type=str(kind),
                resource_name=str(name),
                attributes=dict(doc),
                line_map=line_map,
            )
        )

    return trees

def parse_docker_compose(abs_path: Path, rel_path: str) -> list[IacTree]:
    """Parse Docker Compose files into IacTree records."""
    trees: list[IacTree] = []
    try:
        yaml_loader = YAML()
        yaml_loader.preserve_quotes = True
        content = abs_path.read_text(encoding="utf-8", errors="replace")
        data = yaml_loader.load(content)
    except Exception as exc:
        return [IacTree(
            source_file=rel_path,
            file_type="docker_compose",
            parse_error=str(exc),
        )]

    if not isinstance(data, dict):
        return []

    services = data.get("services", {})
    if isinstance(services, dict):
        for sname, sconfig in services.items():
            if not isinstance(sconfig, dict):
                continue
            line = 1
            if hasattr(services, "lc") and hasattr(services.lc, "data"):
                pos = services.lc.data.get(sname)
                if pos and isinstance(pos, (list, tuple)):
                    line = pos[0] + 1
            trees.append(
                IacTree(
                    source_file=rel_path,
                    file_type="docker_compose",
                    resource_type="compose_service",
                    resource_name=str(sname),
                    attributes=dict(sconfig),
                    line_map={"__self__": line},
                )
            )

    return trees

def parse_dockerfile(abs_path: Path, rel_path: str) -> list[IacTree]:
    """Parse Dockerfile instructions into an IacTree."""
    try:
        dfp = DockerfileParser(path=str(abs_path))
        structure = dfp.structure
    except Exception as exc:
        return [IacTree(
            source_file=rel_path,
            file_type="dockerfile",
            parse_error=str(exc),
        )]

    attributes: dict[str, Any] = {
        "envs": {},
        "args": {},
        "baseimage": dfp.baseimage,
        "instructions": [],
    }
    line_map: dict[str, int] = {}

    for item in structure:
        ins = item.get("instruction")
        val = item.get("value")
        line = item.get("startline", 1)

        attributes["instructions"].append({"instruction": ins, "value": val, "line": line})

        if ins == "ENV" and isinstance(val, str):
            if "=" in val:
                parts = val.split("=", 1)
            else:
                parts = val.split(None, 1)
            if len(parts) >= 2:
                attributes["envs"][parts[0].strip()] = parts[1].strip()
                line_map[f"env.{parts[0].strip()}"] = line
        elif ins == "ARG" and isinstance(val, str):
            if "=" in val:
                parts = val.split("=", 1)
            else:
                parts = val.split(None, 1)
            attributes["args"][parts[0].strip()] = parts[1].strip() if len(parts) > 1 else ""
            line_map[f"arg.{parts[0].strip()}"] = line

    return [
        IacTree(
            source_file=rel_path,
            file_type="dockerfile",
            resource_type="Dockerfile",
            resource_name=abs_path.name,
            attributes=attributes,
            line_map=line_map,
        )
    ]

def parse_iac_file(abs_path: Path, rel_path: str) -> list[IacTree]:
    """Dispatch file to corresponding IaC / container parser."""
    name = abs_path.name.lower()
    if name.endswith(".tf") or name.endswith(".hcl"):
        return parse_terraform_file(abs_path, rel_path)
    elif "dockerfile" in name:
        return parse_dockerfile(abs_path, rel_path)
    elif "compose" in name and (name.endswith(".yaml") or name.endswith(".yml")):
        return parse_docker_compose(abs_path, rel_path)
    elif name.endswith(".yaml") or name.endswith(".yml"):
        try:
            content = abs_path.read_text(encoding="utf-8", errors="replace")
            if "services:" in content and "version:" in content:
                return parse_docker_compose(abs_path, rel_path)
        except Exception:
            pass
        return parse_kubernetes_yaml(abs_path, rel_path)
    return []
