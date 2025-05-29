from __future__ import annotations

import ast
import fnmatch
import logging
import os
from pathlib import Path
from typing import NoReturn

import tomli

from fixmate.helpers.dir_tools import is_blacklisted_dir, is_hidden_dir
from fixmate.helpers.logger import setup_logger
from fixmate.python_checker._dto import FileSpecsDto
from fixmate.python_checker._func_validator import FuncValidator
from fixmate.python_checker._import_validator import ImportValidator
from fixmate.python_checker._msg_validator import MsgValidator

_logger = logging.getLogger(__name__)


class PythonChecker:
    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or Path("pyproject.toml")
        self._ignore_rules = self._load_ignore_rules()
        self._msg_validator = MsgValidator()
        self._import_validator = ImportValidator()
        self._func_validator = FuncValidator()

    def run(self, files_to_check: list[str] | None = None) -> NoReturn:
        setup_logger()
        files_to_check = files_to_check or []
        exec_abs_path = Path.cwd()
        errors = self._validate_files(exec_abs_path, files_to_check)

        if errors:
            for error in errors:
                _logger.error(error)
            raise SystemExit(1)

        _logger.info("All checks passed")
        raise SystemExit(0)

    def _validate_files(self, exec_abs_path: Path, files_to_check: list[str]) -> list[str]:
        errors: list[str] = []

        if files_to_check:
            file_abs_paths = [exec_abs_path / f for f in files_to_check]
        else:
            file_abs_paths = self._get_all_files(exec_abs_path)

        for file_abs_path in file_abs_paths:
            file_rel_path = file_abs_path.relative_to(exec_abs_path)
            errors.extend(self._validate_file(file_abs_path, file_rel_path, exec_abs_path))

        return errors

    def _get_all_files(self, exec_abs_path: Path) -> list[Path]:
        all_files = []

        for root_path, dir_names, file_names in os.walk(exec_abs_path):
            dir_names[:] = [d for d in dir_names if self._should_check_dir(d)]

            for file_name in file_names:
                if self._should_check_file(file_name):
                    file_abs_path = Path(root_path) / file_name
                    all_files.append(file_abs_path)

        return all_files

    def _should_check_dir(self, dir_name: str) -> bool:
        return not is_hidden_dir(dir_name) and not is_blacklisted_dir(dir_name)

    def _should_check_file(self, file_name: str) -> bool:
        return file_name.endswith(".py")

    def _validate_file(self, file_abs_path: Path, file_rel_path: Path, exec_abs_path: Path) -> list[str]:
        with file_abs_path.open() as f:
            tree = ast.parse(f.read(), filename=str(file_abs_path))

        self._set_parents(tree)
        file_specs = FileSpecsDto(
            exec_abs_path=exec_abs_path, abs_path=file_abs_path, rel_path=file_rel_path, errors=[]
        )
        self._run_validators(tree, file_specs)
        return file_specs.errors

    def _run_validators(self, tree: ast.AST, file_specs: FileSpecsDto) -> None:
        ignored_validators = self._get_ignored_validators(file_specs.rel_path)

        if "all" in ignored_validators:
            return

        if self._import_validator.error_code not in ignored_validators:
            self._import_validator.validate(tree, file_specs)

        if self._msg_validator.error_code not in ignored_validators:
            self._msg_validator.validate(tree, file_specs)

        if self._func_validator.error_code not in ignored_validators:
            self._func_validator.validate(tree, file_specs)

    def _get_ignored_validators(self, file_rel_path: Path) -> list[str]:
        """Return validators to ignore for a given file."""
        all_ignored_validators = []
        file_rel_str = str(file_rel_path)

        for ignored_path_str, ignored_validators in self._ignore_rules.items():
            if fnmatch.fnmatch(file_rel_str, ignored_path_str) or file_rel_str.startswith(ignored_path_str):
                all_ignored_validators.extend(ignored_validators)

        return all_ignored_validators

    def _set_parents(self, node: ast.AST, parent: ast.AST | None = None) -> None:
        """Recursively set parent attributes for AST nodes."""
        node.parent = parent  # type: ignore[attr-defined]
        for child in ast.iter_child_nodes(node):
            self._set_parents(child, node)

    def _load_ignore_rules(self) -> dict[str, list[str]]:
        if not self._config_path.exists():
            return {}

        with self._config_path.open("rb") as f:
            config = tomli.load(f)

        return config.get("tool", {}).get("python_checker", {}).get("per-file-ignores", {})
