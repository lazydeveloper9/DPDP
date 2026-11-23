"""
Stage 2 AST Parser
==================
Parses source code into structured AstFileRecord summaries using tree-sitter.
Extracts functions, classes, imports, assignments, string literals, and decorators.
Supports: Python, JavaScript, TypeScript, Java, Go.
"""

from __future__ import annotations
from pathlib import Path
from typing import Optional

import tree_sitter_language_pack as tslp

from cs01.models import AstFileRecord

SUPPORTED_LANGUAGES = {
    "python": "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java": "java",
    "go": "go",
}

def _node_text(node, source_bytes: bytes) -> str:
    """Return UTF-8 decoded text of an AST node."""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")

def parse_source_ast(abs_path: Path, rel_path: str, language: str) -> AstFileRecord:
    """Parse a single source file with tree-sitter and extract structural summary."""
    lang_key = SUPPORTED_LANGUAGES.get(language.lower())
    if not lang_key:
        return AstFileRecord(
            path=rel_path,
            language=language,
            parse_error=f"Unsupported language for tree-sitter AST: {language}",
        )

    try:
        source_bytes = abs_path.read_bytes()
    except OSError as exc:
        return AstFileRecord(
            path=rel_path,
            language=language,
            parse_error=f"Could not read file: {exc}",
        )

    try:
        parser = tslp.get_parser(lang_key)
        tree = parser.parse(source_bytes)
    except Exception as exc:
        return AstFileRecord(
            path=rel_path,
            language=language,
            parse_error=f"Tree-sitter parse error: {exc}",
        )

    record = AstFileRecord(path=rel_path, language=language)

    def _walk(node, current_func: Optional[dict] = None, current_decorators: Optional[list[str]] = None) -> None:
        ntype = node.type

        if ntype in (
            "function_definition",
            "method_definition",
            "function_declaration",
            "method_declaration",
            "arrow_function",
        ):
            func_name = "anonymous"
            for ch in node.children:
                if ch.type in ("identifier", "name", "property_identifier"):
                    func_name = _node_text(ch, source_bytes)
                    break

            params: list[str] = []
            for ch in node.children:
                if "parameter" in ch.type or ch.type == "formal_parameters":
                    for p in ch.children:
                        if p.type in ("identifier", "typed_parameter", "default_parameter", "typed_default_parameter", "parameter_declaration"):
                            params.append(_node_text(p, source_bytes).strip())

            func_dict = {
                "name": func_name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "params": params,
                "calls": [],
                "decorators": current_decorators or [],
                "body_snippet": _node_text(node, source_bytes)[:3000],
            }
            record.functions.append(func_dict)

            for ch in node.children:
                _walk(ch, func_dict)
            return

        if ntype in ("class_definition", "class_declaration"):
            class_name = "UnknownClass"
            bases: list[str] = []
            fields: list[dict] = []
            for ch in node.children:
                if ch.type in ("identifier", "type_identifier", "name"):
                    class_name = _node_text(ch, source_bytes)
                elif ch.type in ("argument_list", "class_heritage"):
                    for b in ch.children:
                        if b.type in ("identifier", "type_identifier", "attribute"):
                            bases.append(_node_text(b, source_bytes).strip())
                elif ch.type in ("block", "class_body"):
                    for stmt in ch.children:
                        if stmt.type in ("assignment", "annotated_assignment", "field_definition", "property_definition"):
                            fname = ""
                            ftype = ""
                            for sch in stmt.children:
                                if sch.type in ("identifier", "name", "property_identifier"):
                                    fname = _node_text(sch, source_bytes)
                                    break
                            for sch in stmt.children:
                                if sch.type in ("type", "type_annotation"):
                                    ftype = _node_text(sch, source_bytes)
                                    break
                            if fname:
                                fields.append({
                                    "name": fname,
                                    "type": ftype,
                                    "line": stmt.start_point[0] + 1,
                                    "snippet": _node_text(stmt, source_bytes)[:160],
                                })

            record.classes.append({
                "name": class_name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "bases": bases,
                "fields": fields,
                "decorators": current_decorators or [],
                "body_snippet": _node_text(node, source_bytes)[:4000],
            })

            for ch in node.children:
                _walk(ch, current_func)
            return

        if ntype in ("call", "call_expression"):
            call_text = _node_text(node, source_bytes)
            callee = ""
            for ch in node.children:
                if ch.type in ("identifier", "attribute", "member_expression", "field_expression"):
                    callee = _node_text(ch, source_bytes)
                    break

            call_entry = {
                "callee": callee or call_text.split("(")[0].strip(),
                "snippet": call_text[:160],
                "line": node.start_point[0] + 1,
            }
            record.calls.append(call_entry)
            if current_func is not None:
                current_func["calls"].append(call_entry)

        if ntype in ("string", "string_literal", "raw_string_literal"):
            val = _node_text(node, source_bytes).strip("'\"`")
            if val and len(val) >= 3:
                record.string_literals.append({
                    "value": val,
                    "line": node.start_point[0] + 1,
                    "col": node.start_point[1] + 1,
                })

        if ntype in ("assignment", "variable_declarator", "short_var_declaration"):
            var_name = ""
            for ch in node.children:
                if ch.type in ("identifier", "name"):
                    var_name = _node_text(ch, source_bytes)
                    break
            if var_name:
                record.assignments.append({
                    "name": var_name,
                    "value_snippet": _node_text(node, source_bytes)[:80],
                    "line": node.start_point[0] + 1,
                })

        if ntype in ("import_statement", "import_from_statement", "import_declaration"):
            record.imports.append({
                "snippet": _node_text(node, source_bytes).strip(),
                "line": node.start_point[0] + 1,
            })

        if ntype in ("decorator", "annotation", "decorated_definition"):
            dec_text = _node_text(node, source_bytes).strip()
            if ntype == "decorated_definition":
                decs = []
                for ch in node.children:
                    if ch.type == "decorator":
                        d_name = _node_text(ch, source_bytes).strip()
                        decs.append(d_name)
                        record.decorators.append({
                            "name": d_name,
                            "line": ch.start_point[0] + 1,
                        })
                        _walk(ch, current_func, None)
                    else:
                        _walk(ch, current_func, current_decorators=decs)
                return
            else:
                record.decorators.append({
                    "name": dec_text,
                    "line": node.start_point[0] + 1,
                })

        for child in node.children:
            _walk(child, current_func, current_decorators)

    _walk(tree.root_node)
    return record
