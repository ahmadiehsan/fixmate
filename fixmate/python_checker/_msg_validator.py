from __future__ import annotations

import ast
from contextlib import suppress
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fixmate.python_checker._dto import FileSpecsDto

_TStrVars = dict[str, tuple[str, int]]


class _MsgCategory(Enum):
    LOG = "log"
    EXCEPTION = "exception"


class MsgValidator:
    error_code = "msg_validator"

    def validate(self, tree: ast.AST, file_specs: FileSpecsDto) -> None:
        variables = self._collect_str_vars(tree)

        for node in ast.walk(tree):
            # Check for logging calls
            log_funcs = {"info", "debug", "error", "warning", "critical"}
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in log_funcs:
                self._check_node(node.args, variables, _MsgCategory.LOG, file_specs)

            # Check for exception raises
            if isinstance(node, ast.Raise) and isinstance(node.exc, ast.Call):
                self._check_node(node.exc.args, variables, _MsgCategory.EXCEPTION, file_specs)

    def _collect_str_vars(self, tree: ast.AST) -> _TStrVars:
        """Collect variables mapped to their first assigned string constant."""
        variables: _TStrVars = {}

        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue

            for target in node.targets:
                if not isinstance(target, ast.Name):
                    continue

                key = self._unique_key(target)
                strings = self._get_strings(node.value, variables)

                if strings:
                    variables[key] = strings[0]

        return variables

    def _unique_key(self, node: ast.Name) -> str:
        scope = self._get_scope(node)
        return f"{scope}__{node.id}"

    @staticmethod
    def _get_scope(node: ast.Name) -> str:
        current: ast.AST | None = node

        for _ in range(10):  # Check up to limited levels
            if current is None:
                break

            if isinstance(current, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                return current.name

            current = current.parent  # type: ignore[attr-defined]

        return "global"

    def _get_strings(self, node: ast.AST, variables: _TStrVars | None = None) -> list[tuple[str, int]]:
        """Extract string constants and their line numbers from an AST node."""
        known_vars = variables or {}

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return [(node.value, node.lineno)]

        if isinstance(node, ast.Name):
            return self._get_name_strings(node, known_vars)

        if isinstance(node, ast.JoinedStr):
            resolved = self._resolve_joined_string(node, known_vars)
            return [resolved] if resolved else []

        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Mod):
            resolved = self._resolve_mod_string(node, known_vars)
            return [resolved] if resolved else []

        return []

    def _get_name_strings(self, node: ast.Name, variables: _TStrVars) -> list[tuple[str, int]]:
        key = self._unique_key(node)
        if key in variables:
            return [variables[key]]

        return []

    def _resolve_joined_string(self, node: ast.JoinedStr, variables: _TStrVars) -> tuple[str, int] | None:
        value_parts: list[str] = []
        line = node.lineno

        for part in node.values:
            if isinstance(part, ast.Constant) and isinstance(part.value, str):
                value_parts.append(part.value)
                line = part.lineno
                continue

            if not isinstance(part, ast.FormattedValue):
                continue

            nested = self._get_strings(part.value, variables)
            if nested:
                value_parts.append(nested[0][0])
                line = nested[0][1]

        if not value_parts:
            return None

        return ("".join(value_parts), line)

    def _resolve_mod_string(self, node: ast.BinOp, variables: _TStrVars) -> tuple[str, int] | None:
        left_strings = self._get_strings(node.left, variables)
        if not left_strings:
            return None

        fmt, fmt_line = left_strings[0]
        right_value = self._resolve_mod_value(node.right, variables)
        if right_value is None:
            return None

        with suppress(TypeError, ValueError):
            return (fmt % right_value, fmt_line)

        return None

    def _resolve_mod_value(self, node: ast.AST, variables: _TStrVars) -> str | tuple[str, ...] | None:
        if isinstance(node, ast.Tuple):
            items: list[str] = []
            for item in node.elts:
                values = self._get_strings(item, variables)
                if not values:
                    return None
                items.append(values[0][0])
            return tuple(items)

        values = self._get_strings(node, variables)
        if values:
            return values[0][0]

        return None

    def _check_node(
        self, args: list[ast.expr], variables: _TStrVars, category: _MsgCategory, file_specs: FileSpecsDto
    ) -> None:
        for arg in args:
            strings = self._get_strings(arg, variables)

            file_rel_path = file_specs.rel_path
            cat_name = category.value

            for string, line in strings:
                if category == _MsgCategory.LOG and self._starts_with_lowercase(string):
                    error = f"{file_rel_path}:{line}: {cat_name} '{string}' starts with lowercase [{self.error_code}]"
                    file_specs.errors.append(error)

                if category == _MsgCategory.EXCEPTION and self._starts_with_uppercase(string):
                    error = f"{file_rel_path}:{line}: {cat_name} '{string}' starts with uppercase [{self.error_code}]"
                    file_specs.errors.append(error)

                if category == _MsgCategory.EXCEPTION and self._ends_with_punctuation(string):
                    error = f"{file_rel_path}:{line}: {cat_name} '{string}' ends with punctuation [{self.error_code}]"
                    file_specs.errors.append(error)

    def _starts_with_uppercase(self, string: str) -> bool:
        return bool(string) and string[0].isalpha() and string[0].isupper()

    def _starts_with_lowercase(self, string: str) -> bool:
        return bool(string) and string[0].isalpha() and string[0].islower()

    def _ends_with_punctuation(self, string: str) -> bool:
        return bool(string) and string[-1] in (".", ":", "?", "!")
