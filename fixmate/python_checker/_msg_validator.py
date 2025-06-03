from __future__ import annotations

import ast
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
                strings = self._get_strings(node.value)

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

    @staticmethod
    def _get_strings(node: ast.AST) -> list[tuple[str, int]]:
        """Extract string constants and their line numbers from an AST node."""
        strings: list[tuple[str, int]] = []

        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            strings.append((node.value, node.lineno))
        if isinstance(node, ast.JoinedStr):
            parts = [part for part in node.values if isinstance(part, ast.Constant) and isinstance(part.value, str)]
            value = "<VAR>".join(p.value for p in parts)
            strings.append((value, parts[0].lineno))

        return strings

    def _check_node(
        self, args: list[ast.expr], variables: _TStrVars, category: _MsgCategory, file_specs: FileSpecsDto
    ) -> None:
        for arg in args:
            if not isinstance(arg, ast.Name):
                strings = self._get_strings(arg)
            else:
                key = self._unique_key(arg)
                strings = [variables[key]] if key in variables else []

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
