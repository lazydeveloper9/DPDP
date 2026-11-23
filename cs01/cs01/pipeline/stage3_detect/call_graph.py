"""
Stage 3 Cross-File Symbol Table & Call Graph
============================================
Builds a lightweight two-pass call graph across all files in RepoModel:
- Pass 1: Collects function definitions, route decorators, imports, and exports.
- Pass 2: Resolves call sites to target functions across files.
Computes reachability tags (REACHABLE_EXTERNAL, REACHABLE_INTERNAL, UNREACHABLE).
"""

from __future__ import annotations
import re
from typing import Optional

from cs01.models.repo_model import RepoModel

ROUTE_DECORATOR_REGEX = re.compile(
    r"@?(app|router|blueprint|api)\.(get|post|put|delete|patch|route|all)",
    re.I,
)

class CallGraph:
    """
    Lightweight two-pass Cross-File Symbol Table and Call Graph.
    """
    def __init__(self, model: RepoModel):
        self.model = model
        self.functions: dict[tuple[str, str], dict] = {}
        self.functions_by_name: dict[str, list[tuple[str, str]]] = {}
        self.file_imports: dict[str, list[dict]] = {}
        self.callees: dict[tuple[str, str], set[tuple[str, str]]] = {}
        self.callers: dict[tuple[str, str], set[tuple[str, str]]] = {}
        self.route_entrypoints: set[tuple[str, str]] = set()

        self._build_symbol_table()
        self._resolve_calls()

    def _build_symbol_table(self) -> None:
        for ast_file in self.model.ast_index:
            self.file_imports[ast_file.path] = ast_file.imports

            route_lines = set()
            for dec in ast_file.decorators:
                dname = dec.get("name", "")
                if ROUTE_DECORATOR_REGEX.search(dname):
                    route_lines.add(dec.get("line", -1))

            for func in ast_file.functions:
                fname = func.get("name", "anonymous")
                key = (ast_file.path, fname)
                self.functions[key] = func
                self.functions_by_name.setdefault(fname, []).append(key)

                fstart = func.get("start_line", -1)
                if any(abs(fstart - rline) <= 2 for rline in route_lines):
                    self.route_entrypoints.add(key)

    def _resolve_calls(self) -> None:
        for (caller_file, caller_func), func_dict in self.functions.items():
            caller_key = (caller_file, caller_func)
            for call in func_dict.get("calls", []):
                callee_name = call.get("callee", "")
                bare_callee = callee_name.split(".")[-1].strip()
                if not bare_callee or bare_callee in (
                    "get", "post", "put", "delete", "info", "debug", "error",
                    "append", "extend", "split", "strip", "lower", "upper",
                ):
                    continue

                same_file_key = (caller_file, bare_callee)
                if same_file_key in self.functions and same_file_key != caller_key:
                    self._add_edge(caller_key, same_file_key)
                    continue

                candidates = self.functions_by_name.get(bare_callee, [])
                for target_key in candidates:
                    if target_key != caller_key:
                        self._add_edge(caller_key, target_key)

    def _add_edge(self, caller: tuple[str, str], callee: tuple[str, str]) -> None:
        self.callees.setdefault(caller, set()).add(callee)
        self.callers.setdefault(callee, set()).add(caller)

    def get_callees(self, file: str, func_name: str) -> list[tuple[str, str]]:
        return sorted(list(self.callees.get((file, func_name), set())))

    def get_callers(self, file: str, func_name: str) -> list[tuple[str, str]]:
        return sorted(list(self.callers.get((file, func_name), set())))

    def is_route_entrypoint(self, file: str, func_name: str) -> bool:
        return (file, func_name) in self.route_entrypoints

    def compute_reachability(self, file: str, func_name: str) -> str:
        key = (file, func_name)
        if key in self.route_entrypoints:
            return "REACHABLE_EXTERNAL"

        visited = set()
        queue = [key]
        while queue:
            curr = queue.pop(0)
            if curr in visited:
                continue
            visited.add(curr)
            if curr in self.route_entrypoints:
                return "REACHABLE_EXTERNAL"
            for parent in self.callers.get(curr, set()):
                if parent not in visited:
                    queue.append(parent)

        if self.callers.get(key):
            return "REACHABLE_INTERNAL"

        return "UNREACHABLE"
