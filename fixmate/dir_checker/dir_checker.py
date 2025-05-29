from __future__ import annotations

import fnmatch
import logging
import os
from pathlib import Path
from typing import NoReturn

import tomli

from fixmate.dir_checker._dto import DirSpecsDto
from fixmate.dir_checker._empty_validator import EmptyValidator
from fixmate.dir_checker._init_py_validator import InitPyValidator
from fixmate.helpers.dir_tools import is_blacklisted_dir, is_hidden_dir
from fixmate.helpers.logger import setup_logger

_logger = logging.getLogger(__name__)


class DirChecker:
    def __init__(self, config_path: Path | None = None) -> None:
        self._config_path = config_path or Path("pyproject.toml")
        self._ignore_rules = self._load_ignore_rules()
        self._empty_validator = EmptyValidator()
        self._init_py_validator = InitPyValidator()

    def run(self, dirs_to_check: list[str] | None = None) -> NoReturn:
        setup_logger()
        dirs_to_check = dirs_to_check or []
        exec_abs_path = Path.cwd()
        errors = self._validate_dirs(exec_abs_path, dirs_to_check)

        if errors:
            for error in errors:
                _logger.error(error)
            raise SystemExit(1)

        _logger.info("All checks passed")
        raise SystemExit(0)

    def _validate_dirs(self, exec_abs_path: Path, dirs_to_check: list[str]) -> list[str]:
        errors: list[str] = []
        check_abs_paths = [exec_abs_path / d for d in dirs_to_check] if dirs_to_check else [exec_abs_path]

        for check_abs_path in check_abs_paths:
            # Check the directory itself
            check_rel_path = check_abs_path.relative_to(exec_abs_path)
            errors.extend(self._validate_dir(check_abs_path, check_rel_path, exec_abs_path))

            # Check all subdirectories
            for root_path, dir_names, _ in os.walk(check_abs_path):
                dir_names[:] = [d for d in dir_names if self._should_check(d)]

                for dir_name in dir_names:
                    dir_abs_path = Path(root_path) / dir_name
                    dir_rel_path = dir_abs_path.relative_to(exec_abs_path)
                    errors.extend(self._validate_dir(dir_abs_path, dir_rel_path, exec_abs_path))

        return errors

    def _should_check(self, dir_name: str) -> bool:
        return not is_hidden_dir(dir_name) and not is_blacklisted_dir(dir_name)

    def _validate_dir(self, dir_abs_path: Path, dir_rel_path: Path, exec_abs_path: Path) -> list[str]:
        dir_specs = DirSpecsDto(exec_abs_path=exec_abs_path, abs_path=dir_abs_path, rel_path=dir_rel_path, errors=[])
        self._run_validators(dir_specs)
        return dir_specs.errors

    def _run_validators(self, dir_specs: DirSpecsDto) -> None:
        ignored_validators = self._get_ignored_validators(dir_specs.rel_path)

        if "all" in ignored_validators:
            return

        if self._empty_validator.error_code not in ignored_validators:
            self._empty_validator.validate(dir_specs)

        if self._init_py_validator.error_code not in ignored_validators:
            self._init_py_validator.validate(dir_specs)

    def _load_ignore_rules(self) -> dict[str, list[str]]:
        if not self._config_path.exists():
            return {}

        with self._config_path.open("rb") as f:
            config = tomli.load(f)

        return config.get("tool", {}).get("dir_checker", {}).get("per-dir-ignores", {})

    def _get_ignored_validators(self, dir_rel_path: Path) -> list[str]:
        """Return validators to ignore for a given directory."""
        all_ignored_validators = []
        dir_rel_str = str(dir_rel_path)

        for ignored_path_str, ignored_validators in self._ignore_rules.items():
            if fnmatch.fnmatch(dir_rel_str, ignored_path_str) or dir_rel_str.startswith(ignored_path_str):
                all_ignored_validators.extend(ignored_validators)

        return all_ignored_validators
