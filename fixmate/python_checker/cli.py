import argparse
from pathlib import Path

from fixmate.helpers.logger import setup_logger
from fixmate.python_checker.python_checker import PythonChecker


def main() -> None:
    setup_logger()

    parser = argparse.ArgumentParser(description="Python code checker")
    parser.add_argument("--config", type=Path, help="Path to pyproject.toml file")
    parser.add_argument("files", nargs="*", help="Files to check (optional)")
    args = parser.parse_args()

    PythonChecker(config_path=args.config).run(files_to_check=args.files)


if __name__ == "__main__":
    main()
