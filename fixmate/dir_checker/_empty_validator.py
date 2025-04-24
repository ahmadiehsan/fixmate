from pathlib import Path

from fixmate.dir_checker._dto import DirSpecsDto


class EmptyValidator:
    error_code = "emptry_validator"

    def validate(self, dir_specs: DirSpecsDto) -> None:
        is_hidden = any(p.startswith(".") for p in dir_specs.rel_path.parts)
        is_empty = self._is_empty(dir_specs.abs_path)

        if not is_hidden and is_empty:
            error = f"{dir_specs.rel_path}: is an empty directory [{self.error_code}]"
            dir_specs.errors.append(error)

    @staticmethod
    def _is_empty(dir_abs_path: Path) -> bool:
        black_list_names = ["__init__.py", "__pycache__"]
        is_empty = True

        for content in dir_abs_path.iterdir():
            if content.name in black_list_names:
                continue

            is_empty = False
            break

        return is_empty
