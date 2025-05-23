from dataclasses import dataclass
from pathlib import Path


@dataclass
class FileSpecsDto:
    exec_abs_path: Path
    abs_path: Path
    rel_path: Path
    errors: list[str]
