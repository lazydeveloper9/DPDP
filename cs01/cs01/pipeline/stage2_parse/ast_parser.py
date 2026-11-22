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

    # Recursive AST walker to extract components
    def _walk(node, current_func: Optional[dict] = None) -> None:
        ntype = node.type

        # --- Functions ---
        if ntype in (
            "function_definition",
            "method_definition",
            "function_declaration",
            "method_declaration",
            "arrow_function",
        ):
            func_name = "anonymous"
            # Find identifier child for name
            for ch in node.children:
                if ch.type in ("identifier", "name", "property_identifier"):
                    func_name = _node_text(ch, source_bytes)
                    break

            # Find parameters
            params: list[str] = []
            for ch in node.children:
                if "parameter" in ch.type or ch.type == "formal_parameters":
                    for p in ch.children:
                        if p.type in ("identifier", "typed_parameter", "parameter_declaration"):
                            params.append(_node_text(p, source_bytes).strip())

            func_dict = {
                "name": func_name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
                "params": params,
                "calls": [],
            }
            record.functions.append(func_dict)

            # Traverse function body with current_func pointer
            for ch in node.children:
                _walk(ch, func_dict)
            return

        # --- Classes ---
        if ntype in ("class_definition", "class_declaration"):
            class_name = "UnknownClass"
            for ch in node.children:
                if ch.type in ("identifier", "type_identifier", "name"):
                    class_name = _node_text(ch, source_bytes)
                    break

            record.classes.append({
                "name": class_name,
                "start_line": node.start_point[0] + 1,
                "end_line": node.end_point[0] + 1,
            })

        # --- Function Calls ---
        if ntype in ("call", "call_expression"):
            call_text = _node_text(node, source_bytes)
            # Find target function name/callee
            callee = ""
            for ch in node.children:
                if ch.type in ("identifier", "attribute", "member_expression", "field_expression"):
                    callee = _node_text(ch, source_bytes)
                    break

            call_entry = {
                "callee": callee or call_text.split("(")[0].strip(),
                "snippet": call_text[:120],
                "line": node.start_point[0] + 1,
            }
            if current_func is not None:
                current_func["calls"].append(call_entry)

        # --- String Literals ---
        if ntype in ("string", "string_literal", "raw_string_literal"):
            val = _node_text(node, source_bytes).strip("'\"`")
            if val and len(val) >= 3:
                record.string_literals.append({
                    "value": val,
                    "line": node.start_point[0] + 1,
                    "col": node.start_point[1] + 1,
                })

        # --- Assignments ---
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

        # --- Imports ---
        if ntype in ("import_statement", "import_from_statement", "import_declaration"):
            record.imports.append({
                "snippet": _node_text(node, source_bytes).strip(),
                "line": node.start_point[0] + 1,
            })

        # --- Decorators / Annotations ---
        if ntype in ("decorator", "annotation", "decorated_definition"):
            dec_text = _node_text(node, source_bytes).strip()
            # If decorated_definition, extract the decorator child
            if ntype == "decorated_definition":
                for ch in node.children:
                    if ch.type == "decorator":
                        record.decorators.append({
                            "name": _node_text(ch, source_bytes).strip(),
                            "line": ch.start_point[0] + 1,
                        })
            else:
                record.decorators.append({
                    "name": dec_text,
                    "line": node.start_point[0] + 1,
                })

        # Recurse children
        for child in node.children:
            _walk(child, current_func)

    _walk(tree.root_node)
    return record
