from pathlib import Path

from fixmate.dir_checker._dto import DirSpecsDto


class InitPyValidator:
    _error_code = "init_py_validator"

    def validate(self, dir_specs: DirSpecsDto) -> None:
        is_hidden = any(p.startswith(".") for p in dir_specs.rel_path.parts)
        has_py_files = self._has_python_files(dir_specs.abs_path)
        has_init_py = self._has_init_py(dir_specs.abs_path)

        if not is_hidden and has_py_files and not has_init_py:
            error = f"{dir_specs.rel_path}: missing __init__.py file [{self._error_code}]"
            dir_specs.errors.append(error)

    @staticmethod
    def _has_python_files(dir_abs_path: Path) -> bool:
        for content in dir_abs_path.iterdir():
            if content.is_file() and content.suffix == ".py" and content.name != "__init__.py":
                return True

        return False

    @staticmethod
    def _has_init_py(dir_abs_path: Path) -> bool:
        return (dir_abs_path / "__init__.py").exists()
