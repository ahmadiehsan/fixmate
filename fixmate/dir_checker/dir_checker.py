import logging
import os
from pathlib import Path
from typing import NoReturn

from fixmate.dir_checker._dto import DirSpecsDto
from fixmate.dir_checker._empty_validator import EmptyValidator
from fixmate.dir_checker._init_py_validator import InitPyValidator
from fixmate.helpers.dir_tools import is_blacklisted_dir, is_hidden_dir
from fixmate.helpers.logger import setup_logger

_logger = logging.getLogger(__name__)


class DirChecker:
    def __init__(self) -> None:
        self._empty_validator = EmptyValidator()
        self._init_py_validator = InitPyValidator()

    def run(self) -> NoReturn:
        setup_logger()
        repo_abs_path = Path.cwd()
        errors = self._validate_dirs(repo_abs_path)

        if errors:
            for error in errors:
                _logger.error(error)
            raise SystemExit(1)

        _logger.info("all checks passed")
        raise SystemExit(0)

    def _validate_dirs(self, repo_abs_path: Path) -> list[str]:
        errors: list[str] = []

        for root_path, dir_names, _ in os.walk(repo_abs_path):
            dir_names[:] = [d for d in dir_names if self._should_check(d)]

            for dir_name in dir_names:
                dir_abs_path = Path(root_path) / dir_name
                dir_rel_path = dir_abs_path.relative_to(repo_abs_path)
                errors.extend(self._validate_dir(dir_abs_path, dir_rel_path, repo_abs_path))

        return errors

    def _should_check(self, dir_name: str) -> bool:
        return not is_hidden_dir(dir_name) and not is_blacklisted_dir(dir_name)

    def _validate_dir(self, dir_abs_path: Path, dir_rel_path: Path, repo_abs_path: Path) -> list[str]:
        dir_specs = DirSpecsDto(repo_abs_path=repo_abs_path, abs_path=dir_abs_path, rel_path=dir_rel_path, errors=[])
        self._run_validators(dir_specs)
        return dir_specs.errors

    def _run_validators(self, dir_specs: DirSpecsDto) -> None:
        self._empty_validator.validate(dir_specs)
        self._init_py_validator.validate(dir_specs)
