import ast
from pathlib import Path

from fixmate.python_checker._dto import FileSpecsDto


class ImportValidator:
    _error_code = "import_validator"

    def validate(self, tree: ast.AST, file_specs: FileSpecsDto) -> None:
        imports = self._find_imports(tree)

        for imported_module, line in imports:
            if self._is_private_module(imported_module) and not self._is_within_package(
                imported_module, file_specs.rel_path
            ):
                error = (
                    f"{file_specs.rel_path}:{line}: "
                    f"invalid import of private module '{imported_module}' "
                    f"[{self._error_code}]"
                )
                file_specs.errors.append(error)

    @staticmethod
    def _find_imports(tree: ast.AST) -> list[tuple[str, int]]:
        """Extract imports and their line numbers from an AST node."""
        imports: list[tuple[str, int]] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend([(alias.name, node.lineno) for alias in node.names])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append((node.module, node.lineno))

        return imports

    def _is_private_module(self, imported_module: str) -> bool:
        parts = imported_module.split(".")
        return any(p.startswith("_") and not self._is_magic_module_package(p) for p in parts)

    @staticmethod
    def _is_magic_module_package(module_package_name: str) -> bool:
        return module_package_name.startswith("__") and module_package_name.endswith("__")

    @staticmethod
    def _is_within_package(imported_module: str, file_rel_path: Path) -> bool:
        file_package = ".".join(file_rel_path.parts[:-1])  # Exclude file name
        imported_module_parts = imported_module.split(".")
        imported_module_package = ".".join(imported_module_parts[:-1])  # Exclude module name
        return file_package == imported_module_package
